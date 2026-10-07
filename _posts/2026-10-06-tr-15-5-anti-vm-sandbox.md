---
title: "Lesson 15.5: Anti-VM and anti-sandbox, when the sample knows it's being watched"
date: 2026-10-06 09:30:00 +0700
categories: ["Technique Reverse", "Part 15 · Anti-Reversing and Bypasses"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
You set up a proper lab following Lesson 0.3, drag the sample into the VM, hit run, and it does nothing. No network calls, no file writes, it exits quietly. It's easy to think the sample is broken or harmless. In fact it just looked around, saw it was sitting in a virtual machine, and decided to play dead. This is anti-VM and anti-sandbox, and understanding it is a precondition for successful dynamic analysis.

Unlike anti-debug (which targets whoever attached a debugger), anti-VM targets the environment: VMware, VirtualBox, QEMU, or automated sandboxes like Cuckoo, CAPE, the online services. The malware's logic is very simple: researchers run me in a VM, real users run me on a real machine, so if I see a VM I stay quiet to avoid being analyzed.

This lesson goes through the common checks, how to recognize them when reading code, and how to make your VM look real enough that the sample will perform.

## CPUID, the bluntest question

The CPU's `cpuid` instruction returns information about the processor, and it has two places that give away a hypervisor.

First, when you call `cpuid` with `eax = 1`, bit 31 of `ecx` is the "hypervisor present bit". On a real machine this bit is 0, in almost every VM it's 1. Just one bit, but enough to give it away.

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

Seeing `cpuid` with the constant `0x40000000` in code means almost certainly there's a hypervisor check. This is where you should put your first breakpoint.

## Traces left on the system (artifacts)

The VM and its guest tools leave a whole series of traces that malware scans for. In the registry there are keys like `HKLM\SOFTWARE\VMware, Inc.\VMware Tools`, `HKLM\HARDWARE\...\SystemBiosVersion` containing "VBOX" or "VMWARE", and the VirtualBox Guest Additions keys. On disk there are files and drivers such as `C:\Windows\System32\drivers\vmmouse.sys`, `vmhgfs.sys`, `VBoxMouse.sys`, `VBoxGuest.sys`, and the VMware Tools install folder. Services and processes include `vmtoolsd.exe`, `VBoxService.exe` and `vmware.exe`. Devices give it away too, with disk drive names containing "VMware" or "VBOX" and the display adapter "VirtualBox Graphics Adapter".

In code, these checks show up as calls to `RegOpenKeyEx`, `CreateFile`, `Process32Next`, `GetAdaptersInfo` with the distinctive strings above as parameters. Tip: run `strings` or FLOSS on the sample, and if you see a pile of "VBoxGuest", "vmtoolsd", "VMware" strings you know right away it has anti-VM.

## MAC address and hardware

Every network card manufacturer has its own MAC prefix (OUI). VMs use fixed prefixes: VMware often uses `00:05:69`, `00:0C:29`, `00:1C:14`, `00:50:56`; VirtualBox uses `08:00:27`. Malware reads the MAC through `GetAdaptersInfo` and compares the first three bytes.

Other hardware gets inspected too: number of CPU cores (`GetSystemInfo`, analysis VMs often have only 1-2 cores), RAM size (`GlobalMemoryStatusEx`, under 2-4 GB is suspicious), disk size (under 60 GB). Analysis machines are usually configured minimally, and that minimalism is what gives them away.

## Signs of an automated sandbox

A sandbox differs from a manual VM in that nobody is sitting there driving it, and it fast-forwards to get through thousands of samples a day. Malware exploits exactly those two points.

The first is the lack of user interaction. Malware checks whether the mouse moves (`GetCursorPos` twice, spaced apart, and if identical there's no person), whether the foreground window changes, whether there's a double-click. If nobody interacts, it's likely a sandbox.

The second is sleep skipping. Malware calls `Sleep(600000)` (10 minutes) and then does its work. To save time, sandboxes often "fast-forward" sleeps and return immediately. Malware measures real time before and after the `Sleep` (with `GetTickCount` or system time), and if 10 minutes pass but the clock only jumped a few seconds, it knows it's being fast-forwarded and stays quiet.

Characteristic machine and user names also give sandboxes away. Many use usernames like "sandbox", "malware", "virus", "john doe", or sample computer names, and malware compares against this list.

## How to get past it: make the VM look real

When analyzing, your goal is to make the sample believe it's on a real machine. There are two directions.

The first direction is hardening the VM: remove VMware Tools/Guest Additions (or don't install them), change the MAC to a real card's prefix, raise the CPU core count and RAM, create fake files and usage history so it looks like a user's machine, change the machine and user names to normal ones, add more cores and a big disk. There are community scripts like VBoxHardenedLoader, or you can use QEMU with a stealth configuration.

The second direction, once you know where the check is (thanks to static/dynamic analysis), is to simply patch or hook: set a breakpoint at `cpuid` and edit `ecx` to clear bit 31; set a breakpoint at `RegOpenKeyEx` for the VM keys and force it to return a "not found" error; patch the `jc running_in_vm` branch so it doesn't jump. This is fast when you only need to get past a few specific checks to see the real behavior.

In practice the two directions complement each other: hardening gets you past most automated samples, and patch/hook handles the sophisticated checks hardening can't cover.

## Lab

See `labs/15.5/`. You'll build a C program that demonstrates the CPUID hypervisor check along with a few artifact checks, run it on a real machine and in a VM to see the different results, then practice patching it so it always reports "real machine".

## Key takeaways
A sample that "does nothing" in a VM usually has anti-VM, it isn't broken. The two classic hypervisor checks are `cpuid` eax=1 bit 31 of ecx, and `cpuid` eax=0x40000000 returning a vendor string. VMware and VirtualBox leave registry, file, driver, service and process artifacts, and these are exposed through strings.

A MAC OUI like 00:0C:29 or 08:00:27, few CPU cores, little RAM and a small disk are all VM flags. Sandboxes give themselves away through lack of mouse interaction and sleep skipping. To get past it, harden the VM to look real, or patch/hook each identified check.
