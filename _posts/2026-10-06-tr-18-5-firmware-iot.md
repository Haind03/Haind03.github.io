---
title: "Lesson 18.5: Reversing firmware and IoT devices"
date: 2026-10-06 09:51:00 +0700
categories: ["Technique Reverse", "Part 18 · Advanced Topics"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
The old router in the corner of the house, the cheap camera, the smart lock, they all run a bit of embedded Linux stuffed into a few MB of flash. Reversing firmware is opening up that black box: getting the filesystem, reading the service code, finding backdoors and hardcoded credentials, and then, if you want, running the whole firmware in an emulator on your own machine without the real hardware. This lesson goes from getting the firmware to running a binary from it.

This is the stage that pulls together almost everything you've learned: the binaries are usually MIPS or ARM (tying to [Lesson 1.9](/posts/tr-1-9-arm-arm64-co-ban/)), the format is ELF ([Lesson 1.8](/posts/tr-1-8-elf-va-mach-o/)), and you still open them in Ghidra like always.

## Getting the firmware in hand first

No firmware, nothing to reverse. Four familiar routes, from easy to hard:

- **Download from the vendor's site.** The manufacturer's support/download section often has firmware update files. The easiest, and the most legit when it's your own device.
- **Capture the packets when the device updates itself.** The device downloads firmware over HTTP, intercept it with mitmproxy and you have it.
- **Dump via UART or JTAG/SWD.** Solder onto the serial pins on the board, get into the bootloader (U-Boot) or a shell, read the flash out. JTAG gives deeper hardware debugging rights (OpenOCD).
- **Desolder the flash chip and read it directly.** Use a chip programmer (CH341A) or an SOIC8 clip with flashrom to read the SPI flash. When every software route is locked down, this is the last resort.

For this lesson we assume you already have a firmware image file (`.bin`).

## binwalk: the first knife

A firmware image is several things laid side by side: the vendor header, the bootloader, a compressed kernel, and a filesystem. `binwalk` scans the whole file looking for the magic signatures of each component.

```
$ binwalk firmware.bin

DECIMAL     HEXADECIMAL   DESCRIPTION
----------------------------------------------------------
0           0x0           uImage header, ... OS: Linux, CPU: MIPS
64          0x40          LZMA compressed data
1310720     0x140000      Squashfs filesystem, little endian, version 4.0
```

You can read it right away: this is MIPS Linux firmware, with an LZMA-compressed kernel at the start, and a SquashFS (a read-only filesystem commonly used for embedded) starting at offset `0x140000`. Extract everything:

```
$ binwalk -e firmware.bin        # extract, outputs to the _firmware.bin.extracted/ folder
```

Add `-M` to recurse (extract inside extract). A small but important tip: look at the **entropy**. `binwalk -E firmware.bin` draws an entropy graph, and flat regions close to 1.0 are compressed or encrypted data. If the whole file has uniformly high entropy, the firmware may be encrypted, and you have to find the decryption key (usually in the bootloader or an older unencrypted firmware version).

## unblob: when binwalk gives up

`binwalk` is the classic but sometimes extracts wrongly or misses unusual formats. `unblob` is the more modern option: it identifies and recursively extracts hundreds of formats, and handles many cases binwalk misses.

```
$ unblob -e out/ firmware.bin
```

Practical habit: run both. Whichever gives the cleaner filesystem, use that. The goal is to get the full **root filesystem** (with `/bin`, `/etc`, `/sbin`, `/www`...).

## Digging through the root filesystem

Once you have the rootfs, it's time to hunt for gold. A few places always worth a look:

- **`/etc/passwd`, `/etc/shadow`.** Hardcoded credentials, weak root password hashes, backdoor accounts. `john` or `hashcat` crack the hash if needed.
- **`/etc/` in general.** Service configs, connection strings, certificates, private keys (`*.pem`, `*.key`).
- **`/www` or the web root.** The admin interface, CGI scripts, where command injection often lives.
- **`/bin`, `/sbin`, `/usr/bin`.** The service binaries (httpd, telnetd, the vendor's proprietary binaries). This is what you feed into Ghidra.

A quick scan of the whole rootfs for clues:

```
$ grep -riIn "password\|admin\|backdoor\|secret\|telnet" rootfs/etc rootfs/www
$ find rootfs -name "*.pem" -o -name "*.key"
$ file rootfs/bin/httpd      # check the architecture: MIPS? ARM?
```

The `file` command tells you whether the binary is MIPS or ARM, 32 or 64 bit, which endianness. That's the info you need to load it into Ghidra correctly and to emulate it.

## Analyzing embedded binaries with Ghidra

Firmware service binaries are usually ELF for MIPS or ARM. Ghidra opens them all: it recognizes the architecture itself and has a decompiler for MIPS/ARM. The workflow is identical to reversing an x86 ELF, only the instruction set differs. If the binary is fully stripped of symbols, you still start from strings and library function calls (`system`, `strcpy`, `popen`) as usual. In IoT devices, those functions are where command injection tends to sit.

## Emulating to run and debug for real

Static reading has limits. Running the binary is much faster, but you don't have the actual router to plug it into. QEMU solves that: it emulates a MIPS/ARM CPU right on your x86 machine.

**User-mode (run a single binary).** Copy `qemu-arm-static` (or `qemu-mips-static`) into the rootfs and chroot into it, and the binary thinks it's running on the real device:

```
$ sudo cp $(which qemu-mipsel-static) rootfs/usr/bin/
$ sudo chroot rootfs /usr/bin/qemu-mipsel-static /bin/httpd
```

You need `binfmt_misc` and the `qemu-user-static` package installed. This is good for running a single service, but easy to trip on when the binary needs infrastructure (nvram, other processes).

**System-mode (boot the whole firmware).** QEMU builds a whole MIPS/ARM virtual machine and boots the firmware's kernel + rootfs, the closest to the real device. Setting it up by hand is pretty painful, so there are automated frameworks:

- **FirmAE** (and its predecessor **firmadyne**): extracts automatically, guesses the network config, boots the firmware in QEMU and gives you access to the virtual device's web interface. The boot success rate is fairly high, very suitable for testing a router's web vulnerabilities without buying the device.

Once it boots, you attach `gdbserver` to debug the MIPS/ARM binary dynamically just like debugging on x86 Linux (tying to [Lesson 2.6](/posts/tr-2-6-gdb-pwndbg-windbg/)).

## A word on legal and safety

Two things not to forget. First, reversing firmware on a device **that's your own** to learn is fine, but distributing pre-patched firmware, cracking region locks, or attacking other people's devices is a different matter entirely, see [Lesson 0.2](/posts/tr-0-2-phap-ly-dao-duc/) again. Second, firmware downloaded from unfamiliar sources is also untrusted data: extract and analyze in an isolated VM ([Lesson 0.3](/posts/tr-0-3-dung-lab-an-toan/)), don't chroot and run unfamiliar binaries on your main machine.

## Key takeaways
- Getting firmware: download from the vendor, capture an update, dump UART/JTAG, or read the flash chip directly.
- `binwalk` scans and extracts; check entropy to know if it's compressed/encrypted; `unblob` when binwalk misses.
- The goal is the root filesystem: dig through `/etc/passwd`, `/etc`, `/www`, and the binaries in `/bin` `/sbin`.
- `file` tells you the architecture (MIPS/ARM) so you load Ghidra correctly and pick the right QEMU.
- Emulating: QEMU user-mode (chroot + qemu-*-static) runs one binary, system-mode (FirmAE/firmadyne) boots the whole firmware.
- Only touch your own devices, extract firmware in an isolated VM.
