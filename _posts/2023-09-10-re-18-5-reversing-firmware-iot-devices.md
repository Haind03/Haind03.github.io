---
title: "Lesson 18.5: Reversing firmware and IoT devices"
image:
  path: /assets/img/covers/re-18-5-reversing-firmware-iot-devices.webp
  alt: "Lesson 18.5: Reversing firmware and IoT devices"
date: 2022-09-08 16:35:00 +0700
categories: ["Reverse Engineering", "Part 18 · Advanced Topics"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
The old router in the corner of the house, the cheap camera, the smart lock, they all run a bit of embedded Linux in a few MB of flash. Reversing firmware means opening that box, which means getting the filesystem, reading the service code, finding backdoors and hardcoded credentials, and then, if you want, running the whole firmware in an emulator on your own machine without the real hardware. This lesson goes from getting the firmware to running a binary from it.

![Firmware reversing pipeline](/assets/img/re/re-18-5-reversing-firmware-iot-devices.svg)
_From a firmware image to readable service code._

It pulls together almost everything so far. The binaries are usually MIPS or ARM (see [Lesson 1.9](/posts/re-1-9-arm-arm64-basics-people-who-already/)), the format is ELF ([Lesson 1.8](/posts/re-1-8-elf-mach-o-two-formats-outside/)), and you open them in Ghidra like always.

## Getting the firmware

No firmware, nothing to reverse. There are four usual routes, from easy to hard. The easiest is downloading from the vendor's site. The manufacturer's support section often has firmware update files, and it's the most legit when it's your own device. You can also capture the packets when the device updates itself. If it downloads firmware over HTTP, intercept it with mitmproxy and you have it.

Harder is dumping via UART or JTAG/SWD. You solder onto the serial pins on the board, get into the bootloader (U-Boot) or a shell, and read the flash out, and JTAG gives deeper hardware debugging (OpenOCD). The last resort is desoldering the flash chip and reading it directly with a chip programmer (CH341A) or an SOIC8 clip with flashrom to read the SPI flash, for when every software route is locked down.

For this lesson we assume you already have a firmware image file (`.bin`).

## binwalk

A firmware image is several things laid side by side, namely the vendor header, the bootloader, a compressed kernel, and a filesystem. `binwalk` scans the whole file looking for the magic signatures of each component.

```
$ binwalk firmware.bin

DECIMAL     HEXADECIMAL   DESCRIPTION
----------------------------------------------------------
0           0x0           uImage header, ... OS: Linux, CPU: MIPS
64          0x40          LZMA compressed data
1310720     0x140000      Squashfs filesystem, little endian, version 4.0
```

You can read it right away. This is MIPS Linux firmware, with an LZMA-compressed kernel at the start, and a SquashFS (a read-only filesystem commonly used for embedded) starting at offset `0x140000`. Extract everything:

```
$ binwalk -e firmware.bin        # extract, outputs to the _firmware.bin.extracted/ folder
```

Add `-M` to recurse (extract inside extract). Also look at the entropy. `binwalk -E firmware.bin` draws an entropy graph, and flat regions close to 1.0 are compressed or encrypted data. If the whole file has uniformly high entropy, the firmware may be encrypted, and you have to find the decryption key (usually in the bootloader or an older unencrypted firmware version).

## unblob

`binwalk` is the classic but sometimes extracts wrongly or misses unusual formats. `unblob` is the more modern option. It identifies and recursively extracts hundreds of formats, and handles many cases binwalk misses.

```
$ unblob -e out/ firmware.bin
```

I run both and use whichever gives the cleaner filesystem. The goal is the full root filesystem (with `/bin`, `/etc`, `/sbin`, `/www`...).

## Going through the root filesystem

Once you have the rootfs, start looking for interesting things. A few places are always worth a look. `/etc/passwd` and `/etc/shadow` can hold hardcoded credentials, weak root password hashes, and backdoor accounts, and `john` or `hashcat` crack the hash if needed. `/etc/` in general has service configs, connection strings, certificates, and private keys (`*.pem`, `*.key`). `/www` or the web root has the admin interface and CGI scripts, where command injection often lives. And `/bin`, `/sbin` and `/usr/bin` hold the service binaries (httpd, telnetd, the vendor's proprietary binaries), which you feed into Ghidra.

A quick scan of the whole rootfs for clues:

```
$ grep -riIn "password\|admin\|backdoor\|secret\|telnet" rootfs/etc rootfs/www
$ find rootfs -name "*.pem" -o -name "*.key"
$ file rootfs/bin/httpd      # check the architecture: MIPS? ARM?
```

The `file` command tells you whether the binary is MIPS or ARM, 32 or 64 bit, and which endianness. You need that to load it into Ghidra correctly and to emulate it.

## Analyzing embedded binaries with Ghidra

Firmware service binaries are usually ELF for MIPS or ARM. Ghidra opens them all. It recognizes the architecture itself and has a decompiler for MIPS/ARM. The workflow is the same as for an x86 ELF, only the instruction set differs. If the binary is fully stripped of symbols, you still start from strings and library function calls (`system`, `strcpy`, `popen`) as usual. In IoT devices, those functions are where command injection tends to sit.

## Emulating to run and debug

Static reading has limits. Running the binary is much faster, but you don't have the actual router to plug it into. QEMU solves that by emulating a MIPS/ARM CPU on your x86 machine.

User-mode runs a single binary. Copy `qemu-arm-static` (or `qemu-mips-static`) into the rootfs and chroot into it, and the binary thinks it's running on the real device:

```
$ sudo cp $(which qemu-mipsel-static) rootfs/usr/bin/
$ sudo chroot rootfs /usr/bin/qemu-mipsel-static /bin/httpd
```

You need `binfmt_misc` and the `qemu-user-static` package installed. This works for running a single service, but it breaks easily when the binary needs infrastructure (nvram, other processes).

System-mode boots the whole firmware. QEMU builds a whole MIPS/ARM virtual machine and boots the firmware's kernel + rootfs, which is closest to the real device. Setting it up by hand is tedious, so there are automated frameworks like FirmAE (and its predecessor firmadyne). They extract automatically, guess the network config, boot the firmware in QEMU and give you access to the virtual device's web interface. The boot success rate is fairly high, which suits testing a router's web vulnerabilities without buying the device.

Once it boots, you attach `gdbserver` to debug the MIPS/ARM binary dynamically just like on x86 Linux (see [Lesson 2.6](/posts/re-2-6-gdb-pwndbg-windbg-debugging-from-command/)).

## Legal and safety

Two things to keep in mind. First, reversing firmware on a device that's your own, to learn, is fine. Distributing pre-patched firmware, cracking region locks, or attacking other people's devices is a different matter, see [Lesson 0.2](/posts/re-0-2-legal-ethics-part-everyone-wants-skip/) again. Second, firmware downloaded from unfamiliar sources is untrusted data. Extract and analyze in an isolated VM ([Lesson 0.3](/posts/re-0-3-set-up-safe-lab-before-touching/)), and don't chroot and run unfamiliar binaries on your main machine.

## Lab

The task is to get a firmware image, extract the root filesystem, pull out credentials and keys, and run a MIPS or ARM binary under QEMU. Safety first. A firmware downloaded from an unknown source is untrusted data, so work inside an isolated VM (see Lesson 0.3), and only reverse the firmware of your own devices.

For setup, install the tools:

```
sudo apt install binwalk qemu-user-static
pip install unblob        # or follow the official instructions
```

Get a real firmware for your own router or camera from the vendor's support page (for example a common router line) and name it `firmware.bin`. If you don't have one, the public sample firmware sets meant for learning (such as DVRF, IoTGoat or Damn Vulnerable Router Firmware) work too.

Start with `binwalk firmware.bin` and work out the CPU architecture, how the kernel is compressed, and what kind of filesystem there is and at which offset it starts. Look at the entropy with `binwalk -E firmware.bin` and see whether the firmware is fully encrypted (a flat entropy line close to 1.0). Extract with `binwalk -eM firmware.bin`, and if the filesystem comes out unclean, try `unblob -e out/ firmware.bin` and compare the results of the two tools. Find the root filesystem (the folder with `/bin`, `/etc` and `/www`) and open `/etc/passwd` and `/etc/shadow`. Is there a suspicious account or a weak root hash? Then scan for hard-coded credentials and keys:

```
grep -riIn "password\|admin\|secret\|telnet\|backdoor" rootfs/etc rootfs/www
find rootfs -name "*.key" -o -name "*.pem"
```

Pick a service binary (for example `rootfs/bin/httpd`) and run `file` on it to learn its architecture, then try it with chroot plus QEMU:

```
sudo cp $(which qemu-mipsel-static) rootfs/usr/bin/
sudo chroot rootfs /usr/bin/qemu-mipsel-static /bin/httpd --help
```

Replace `mipsel` with the architecture that `file` reports. Last, open that binary in Ghidra, look for calls to `system` or `popen`, and see whether any place concatenates user input into a shell command (command injection).

Some questions to think about. Why is `file` on the binary a mandatory step before loading Ghidra and before choosing QEMU? When is user-mode QEMU (chroot) not enough, so that you have to move to system mode (FirmAE)? And what do the credentials in `/etc/shadow` say about the device's security? Do it yourself before opening the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Try it yourself before reading.

### A note on the sample output

There's no specific commercial firmware in this writeup, so the `binwalk` figures below are typical output (they show the form you'll see). The carving, decompressing and credential grep part uses a simulated blob to illustrate the mechanism. One caveat is that the `binwalk` package in some distros currently has a broken `capstone` dependency (missing `CS_ARCH_ARM64`). If you hit that, install a newer version, use `unblob` instead, or carve by hand as shown below.

### Identification and entropy

Typical `binwalk` output on a MIPS router:

```
DECIMAL     HEXADECIMAL   DESCRIPTION
0           0x0           uImage header, OS: Linux, CPU: MIPS
64          0x40          LZMA compressed data (kernel)
1310720     0x140000      Squashfs filesystem, little endian, version 4.0
```

The CPU is MIPS, the kernel is LZMA-compressed, and the filesystem is SquashFS 4.0 at offset `0x140000`. `binwalk -E` gives the entropy plot. The kernel and squashfs regions are flat near 1.0 (compressed) and the header region is low. If everything is flat near 1.0 including the header, the firmware is encrypted and you have to find the key.

### Extraction

`binwalk -eM firmware.bin` produces `_firmware.bin.extracted/` with the decompressed kernel and the rootfs tree from the squashfs. When binwalk misses, `unblob -e out/ firmware.bin` often comes out cleaner. To illustrate carving by hand (really run on a simulated blob with gzip at offset 64):

```
$ dd if=firmware_demo.bin of=payload.gz bs=1 skip=64
$ file payload.gz
payload.gz: gzip compressed data, max compression
$ gunzip -c payload.gz | grep -o 'root:[^ ]*\|backdoor'
root:$1$abc$0123456789abcdef:0:0:root:/root:/bin/sh
backdoor
```

This is what binwalk automates, which is to find the signature, cut from the offset, decompress.

### Going through the rootfs

The usual findings in older router firmware are these. `/etc/passwd` has a line `root:...:0:0` with a weak MD5 crypt hash (`$1$`) that cracks in minutes with `john`. A second UID 0 account with an odd name (`admin`, `support`) is a backdoor. `/etc/` holds the web server's private key and connection strings to the vendor's server. And `/www/cgi-bin/` holds scripts that call `system()` with parameters from the query string. The scan commands are:

```
grep -riIn "password\|admin\|secret\|telnet\|backdoor" rootfs/etc rootfs/www
find rootfs -name "*.key" -o -name "*.pem"
```

### Emulating a binary

```
$ file rootfs/bin/httpd
rootfs/bin/httpd: ELF 32-bit LSB executable, MIPS, MIPS32 ... dynamically linked
$ sudo cp $(which qemu-mipsel-static) rootfs/usr/bin/
$ sudo chroot rootfs /usr/bin/qemu-mipsel-static /bin/httpd --help
```

`file` reports MIPS LSB, so use `qemu-mipsel` (little endian). If it says `MSB`, use `qemu-mips`. For an ARM binary, use `qemu-arm-static`.

### Finding command injection in Ghidra

Open `httpd` in Ghidra, which recognizes MIPS by itself. Look for xrefs to `system`, `popen` and `execve`. The dangerous spot is where the argument of `system` is built from user data (query string, POST body) without filtering. It's the most common vulnerability pattern in IoT routers.

### Answers to the questions

`file` comes before Ghidra and QEMU because you must know the architecture (MIPS vs ARM) and endianness to load the right processor in Ghidra and choose the right `qemu-*-static`. With the wrong choice the decompiler gives garbage and QEMU won't run. System mode is needed when the binary depends on nvram, multiple processes, or a whole service stack (the web UI calling a backend), since user-mode chroot only runs fairly self-contained binaries well. Then you use FirmAE or firmadyne to boot the whole firmware. As for `/etc/shadow`, a weak hash (`$1$` MD5 crypt), a default password shared across the whole product line, or a hidden UID 0 account all point to a device with poor security and quite possibly a backdoor.

</details>

## Key takeaways
You get firmware by downloading from the vendor, capturing an update, dumping UART/JTAG, or reading the flash chip directly. `binwalk` scans and extracts, entropy tells you if it's compressed/encrypted, and `unblob` helps when binwalk misses. The goal is the root filesystem, so go through `/etc/passwd`, `/etc`, `/www`, and the binaries in `/bin` and `/sbin`. `file` tells you the architecture (MIPS/ARM) so you load Ghidra correctly and pick the right QEMU. For emulation, QEMU user-mode (chroot + qemu-*-static) runs one binary, while system-mode (FirmAE/firmadyne) boots the whole firmware. Only touch your own devices, and extract firmware in an isolated VM.
