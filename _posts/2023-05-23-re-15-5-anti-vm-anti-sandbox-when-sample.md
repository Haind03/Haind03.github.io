---
title: "Lesson 15.5: Anti-VM and anti-sandbox"
image:
  path: /assets/img/covers/re-15-5-anti-vm-anti-sandbox-when-sample.webp
  alt: "Lesson 15.5: Anti-VM and anti-sandbox"
date: 2023-05-23 14:29:00 +0700
categories: ["Reverse Engineering", "Part 15 · Anti-Reversing and Bypasses"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
You set up a proper lab following Lesson 0.3, drag the sample into the VM, hit run, and nothing happens. No network calls, no file writes, it just exits. It's easy to think the sample is broken or harmless. Often it looked around, saw it was in a virtual machine, and decided to do nothing. This is anti-VM and anti-sandbox, and you need to understand it before dynamic analysis can work.

Anti-debug targets whoever attached a debugger. Anti-VM targets the environment, such as VMware, VirtualBox, QEMU, or automated sandboxes like Cuckoo, CAPE and the online services. The malware's logic is simple. Researchers run me in a VM and real users run me on a real machine, so if I see a VM I stay quiet to avoid being analyzed.

This lesson goes through the common checks, how to recognize them when reading code, and how to make your VM look real enough that the sample runs.

## CPUID

The CPU's `cpuid` instruction returns information about the processor, and two places in it give away a hypervisor.

First, when you call `cpuid` with `eax = 1`, bit 31 of `ecx` is the "hypervisor present bit". On a real machine this bit is 0, in almost every VM it's 1. Just one bit, but enough.

```asm
    mov  eax, 1
    cpuid
    bt   ecx, 31        ; check bit 31
    jc   running_in_vm  ; carry = 1 means inside a hypervisor
```

Second, when you call `cpuid` with `eax = 0x40000000`, the VM returns a vendor string in `ebx:ecx:edx`. VMware returns "VMwareVMware", VirtualBox/KVM return "KVMKVMKVM", Hyper-V returns "Microsoft Hv", Xen returns "XenVMMXenVMM". A real machine returns garbage or empty.

```asm
    mov  eax, 0x40000000
    cpuid
    ; ebx, ecx, edx now hold a string like "VMwareVMware"
```

If you see `cpuid` with the constant `0x40000000` in code, there's almost certainly a hypervisor check. I'd put my first breakpoint there.

## Traces left on the system (artifacts)

The VM and its guest tools leave a lot of traces that malware scans for. In the registry there are keys like `HKLM\SOFTWARE\VMware, Inc.\VMware Tools`, `HKLM\HARDWARE\...\SystemBiosVersion` containing "VBOX" or "VMWARE", and the VirtualBox Guest Additions keys. On disk there are files and drivers such as `C:\Windows\System32\drivers\vmmouse.sys`, `vmhgfs.sys`, `VBoxMouse.sys`, `VBoxGuest.sys`, and the VMware Tools install folder. Services and processes include `vmtoolsd.exe`, `VBoxService.exe` and `vmware.exe`. Devices give it away too, with disk drive names containing "VMware" or "VBOX" and the display adapter "VirtualBox Graphics Adapter".

In code, these checks show up as calls to `RegOpenKeyEx`, `CreateFile`, `Process32Next`, `GetAdaptersInfo` with the distinctive strings above as parameters. Run `strings` or FLOSS on the sample, and if you see many strings such as "VBoxGuest", "vmtoolsd", "VMware" strings, it has anti-VM.

## MAC address and hardware

Every network card manufacturer has its own MAC prefix (OUI). VMs use fixed prefixes. VMware often uses `00:05:69`, `00:0C:29`, `00:1C:14`, `00:50:56`; VirtualBox uses `08:00:27`. Malware reads the MAC through `GetAdaptersInfo` and compares the first three bytes.

Other hardware gets inspected too, such as the number of CPU cores (`GetSystemInfo`, analysis VMs often have only 1-2 cores), RAM size (`GlobalMemoryStatusEx`, under 2-4 GB is suspicious), disk size (under 60 GB). Analysis machines are usually configured minimally, and that gives them away.

## Signs of an automated sandbox

A sandbox differs from a manual VM in that nobody is sitting there driving it, and it fast-forwards time to get through thousands of samples a day. Malware uses both of those.

The first is the lack of user interaction. Malware checks whether the mouse moves (`GetCursorPos` twice, spaced apart, and if the values are identical there's no person), whether the foreground window changes, whether there's a double-click. If nobody interacts, it's likely a sandbox.

The second is sleep skipping. Malware calls `Sleep(600000)` (10 minutes) and then does its work. To save time, sandboxes often fast-forward sleeps and return immediately. Malware measures real time before and after the `Sleep` (with `GetTickCount` or system time), and if 10 minutes pass but the clock only jumped a few seconds, it knows time is being skipped and stays quiet.

Machine and user names also give sandboxes away. Many use usernames like "sandbox", "malware", "virus", "john doe", or sample computer names, and malware compares against a list.

## Getting past it: make the VM look real

When analyzing, you want the sample to believe it's on a real machine. There are two directions.

The first is hardening the VM, which means to remove VMware Tools/Guest Additions (or don't install them), change the MAC to a real card's prefix, raise the CPU core count and RAM, add a big disk, create fake files and usage history so it looks like a user's machine, and change the machine and user names to normal ones. There are community scripts like VBoxHardenedLoader, or you can use QEMU with a stealth configuration.

The second, once you know where the check is (from static or dynamic analysis), is to patch or hook it. Set a breakpoint at `cpuid` and edit `ecx` to clear bit 31; set a breakpoint at `RegOpenKeyEx` for the VM keys and force it to return a "not found" error; patch the `jc running_in_vm` branch so it doesn't jump. This is fast when you only need to get past a few specific checks to see the real behavior.

In practice the two work together. Hardening gets you past most automated samples, and patch/hook handles the sophisticated checks hardening can't cover.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 15.5</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/15.5.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/15.5/src/antivm.c" download><i class="fa-solid fa-download"></i>src/antivm.c</a>
</div>
</div>

The goal is to see a program recognize that it's running inside a VM, and to practice getting past that check. The file is `antivm.c`, a program that checks a few VM indicators (the CPUID hypervisor bit, the vendor string, and a registry artifact on Windows) and prints a conclusion. Build it with `cl antivm.c` on Windows with MSVC, or `x86_64-w64-mingw32-gcc antivm.c -o antivm.exe` with MinGW. On Linux or WSL, only the CPUID part works, using `gcc antivm.c -o antivm -DLINUX_BUILD`.

Run `antivm` on a real machine if you have one and check that the hypervisor bit reads 0. Then run it inside VMware, VirtualBox or WSL and check that the bit reads 1 and a vendor string shows up. Open `antivm.exe` in IDA or Ghidra, find the `cpuid` calls and the constant `0x40000000`, and identify the branch that decides "running in a VM". In x64dbg, set a breakpoint on `cpuid`, run to it, and once it returns, change `ecx` to clear bit 31 (AND with `0x7FFFFFFF`), then continue and confirm the program now reports it looks like a real machine. Finally try a static patch instead, changing the branch that checks bit 31 so it never treats the machine as a VM.

Two questions to think about. Why is a single bit (ECX[31]) enough to give away a VM, while registry artifacts aren't nearly as reliable? And if a piece of malware combines five anti-VM checks, is patching each one in the debugger really the fastest approach, or is hardening the VM itself better?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Real output from an actual run. Building the Linux version and running it inside WSL2 (itself a lightweight VM on Hyper-V):

```
$ gcc antivm.c -o antivm -DLINUX_BUILD
$ ./antivm
[+] Hypervisor present bit (CPUID.1:ECX[31]) = 1
    CPUID 0x40000000 vendor: "Microsoft Hv"

==> Conclusion: running inside a VM/hypervisor
```

This matches the theory from the lesson. ECX bit 31 is 1 under virtualization, and the `0x40000000` leaf returns a real vendor string ("Microsoft Hv" since WSL2 runs on Hyper-V). On a real bare-metal machine, this bit is 0 and the vendor string is empty. The registry part only compiles on Windows (`_WIN32`), so the Linux build here skips it. On VMware or VirtualBox under Windows it would pick up the artifact keys.

To find the checks in a disassembler, look in IDA or Ghidra for the `cpuid` instruction. There are two spots. One is a `cpuid` right after `mov eax, 1`, followed by code extracting bit 31 of ECX (usually `shr ecx, 31`, or `bt ecx, 31` / `and ecx, 0x80000000`), and the other is a `cpuid` after `mov eax, 0x40000000`, followed by instructions copying ebx/ecx/edx into a buffer. The constant `0x40000000` is distinctive, so searching for that immediate value finds it right away.

To get past it in x64dbg, set a breakpoint on the address of the first `cpuid` (leaf 1). Run (F9) to it, then step over `cpuid` (F8), at which point ECX holds the feature bits. In the Registers pane, change ECX by ANDing it with `0x7FFFFFFF` to clear bit 31, either by double-clicking ECX and typing the new value, or via the command box with `ecx = ecx & 0x7FFFFFFF`. Continue running, and the program now sees bit 31 as 0. If the vendor string check is still active, you also have to handle the `cpuid` leaf `0x40000000` call (forcing ebx/ecx/edx to 0 after it returns), otherwise the vendor branch still gives it away. This is why patching each check individually gets tiring once there are several.

For a static patch, at the branch that checks bit 31, change the jump instruction. For example, if there's a `jc running_in_vm` (jump on carry), change it to a `nop`, or invert the condition so it never takes the VM branch. Save the patch (Ctrl+P in x64dbg) and run the patched file.

Why does one bit matter more than artifacts? The hypervisor present bit is set by the CPU or hypervisor itself according to the specification, so it's consistent across every standard VM. Registry or file artifacts can be removed (removing VMware Tools gets rid of them), so they're less reliable. On the other hand, even a hardened VM can still be given away if an artifact was left behind by accident.

What about several checks at once? If a sample has five checks, patching each one by hand on every run is tiring and easy to get wrong. Hardening the VM itself (hiding the hypervisor bit at the QEMU/VMware configuration level, removing guest tools, changing the MAC address, bumping up resources) solves it once for every run and every sample, so for serious analysis hardening wins. Patching or hooking individual checks is better for a handful of one-off cases or when you don't control the VM's configuration.

</details>

## Key takeaways
A sample that "does nothing" in a VM usually has anti-VM, it isn't broken. The two classic hypervisor checks are `cpuid` eax=1 bit 31 of ecx, and `cpuid` eax=0x40000000 returning a vendor string. VMware and VirtualBox leave registry, file, driver, service and process artifacts, and these show up in `strings`.

A MAC OUI like 00:0C:29 or 08:00:27, few CPU cores, little RAM and a small disk are all VM flags. Sandboxes give themselves away through lack of mouse interaction and sleep skipping. To get past it, harden the VM to look real, or patch/hook each identified check.
