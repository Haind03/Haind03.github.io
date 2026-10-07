---
title: "Lesson 18.6: Reversing ring-0 code, Windows drivers and Linux kernel modules"
date: 2023-09-12 11:45:00 +0700
categories: ["Technique Reverse", "Part 18 · Advanced Topics"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
So far everything we've taken apart ran in ring-3, user-mode, where a bug only crashes one process. Stepping down to ring-0, kernel-mode, is a different world: code here runs with full privileges, and a small bug doesn't crash the program, it crashes the whole machine (a BSOD on Windows, a kernel panic on Linux). Rootkits, anti-cheat, and many anti-debug drivers (like TitanHide in lesson 15.9) live here, so sooner or later you have to go down.

This lesson doesn't teach writing drivers, it teaches reading a driver you don't have the source for, and how to debug it without burning your machine.

## First rule: always work in a VM

A reminder to be sure: when reversing ring-0 code, the VM lab from lesson 0.3 is no longer an option but a requirement. The technical reason is that debugging the kernel needs to halt the whole operating system, so you need two machines, one running the driver (the target) and one running the debugger (the host). A VM solves this neatly: the target is a VM, the host is the real machine, connected through a named pipe or network. If the driver breaks, only the VM crashes, and you restore a snapshot in a few seconds.

Never load an unknown driver onto your real machine to see what it does. Once is enough to remember.

## Windows kernel driver: the .sys file

A Windows driver (`.sys`) is still a PE file, just like the `.exe` and `.dll` in lesson 1.7, except the subsystem is Native and it links against `ntoskrnl.exe` instead of `kernel32.dll`. Open it in IDA or Ghidra as usual, but the APIs you see will be kernel relatives: `IoCreateDevice`, `ObReferenceObjectByHandle`, `MmGetSystemRoutineAddress`, `ZwOpenKey`, not `CreateFileW`.

### DriverEntry, the real entry point

A driver's entry point isn't `main` but `DriverEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath)`. This is where you start reading. In `DriverEntry`, a driver usually does a couple of notable things. It creates a device object (`IoCreateDevice`) and a symbolic link (`IoCreateSymbolicLink`) so user-mode can reach it, and the device name (for example `\\Device\\MyDriver`) is a clue for finding the user-mode program that controls it. It also assigns the major functions into the `DriverObject->MajorFunction[]` table, which is the most important spot.

### The MajorFunction table and IOCTLs

A driver communicates with user-mode through the IRP (I/O Request Packet) mechanism. `DriverObject->MajorFunction` is an array of function pointers, each slot matching one kind of request:

```
MajorFunction[IRP_MJ_CREATE]         = DriverCreateClose;   // index 0
MajorFunction[IRP_MJ_CLOSE]          = DriverCreateClose;   // index 2
MajorFunction[IRP_MJ_DEVICE_CONTROL] = DriverDeviceControl; // index 14, the most important
```

The `IRP_MJ_DEVICE_CONTROL` slot (value 0xE) is almost always the heart of the driver, because this is where `DeviceIoControl` from user-mode gets handled. When reversing, find where slot 0xE gets assigned in `DriverEntry` and jump to that function and you're straight into the main logic.

Inside the device control function, the driver reads the IOCTL code from the IRP (through `IoGetCurrentIrpStackLocation`, the field `Parameters.DeviceIoControl.IoControlCode`) and then switches on each code. Each IOCTL is a command that user-mode sends down. Rebuild the table of IOCTL codes against behavior and you've understood the driver's private API.

### Working backwards from the user-mode side

A practical tip: if you also have the user-mode program that controls the driver, look for the `DeviceIoControl` call in it. The second parameter is the IOCTL code, and the input/output buffer parameters tell you the data structures. Put the user and kernel sides together and you understand the whole protocol. That's why reversing a driver is often easier when the user-mode part comes with it.

### Debugging with WinDbg in kernel mode

Debug a driver with WinDbg (mentioned in lesson 2.6) in kernel mode. On the target VM, turn on kernel debugging with `bcdedit /debug on` and configure the transport (`bcdedit /dbgsettings net ...` or serial/named pipe), then reboot. On the host, open WinDbg and attach to the kernel over the same transport.

A few commands get used a lot: `lm` lists loaded modules (find your driver), `!drvobj MyDriver 7` shows the driver object and the major function table, `bp MyDriver!DriverDeviceControl` sets a breakpoint, `!irp` shows the current IRP, and `dt` reads a struct. The target VM will freeze when a breakpoint hits, that's normal, the host controls everything.

## Linux kernel module: the .ko file

On Linux, a kernel module is a `.ko` file, a relocatable ELF (mentioned in lesson 1.8). Open it in Ghidra/IDA like a normal ELF.

There are two entry points defined by macros. `module_init(func)` registers the function that runs when the module is loaded (`insmod`), which is Linux's `DriverEntry`. `module_exit(func)` runs on removal (`rmmod`).

Module info (name, license, author, parameters) sits in the `.modinfo` section, quickly read with `modinfo file.ko`. Symbols are often still fairly intact because kernel modules tend to keep function names, so it's easier to read than a stripped Windows driver.

Modules often register a character device or an entry in `/proc` or `/sys` to talk to user-mode (the equivalent of Windows' device object + IOCTL), so look for the `file_operations` struct with the `.read`, `.write`, `.unlocked_ioctl` pointers. They also sometimes hook syscalls, a classic rootkit technique that modifies `sys_call_table` to intercept `getdents` to hide files, or `kill` to receive hidden commands. Seeing a module read/write `sys_call_table` is a red flag to read carefully.

For debugging, use `kgdb` connected from another machine (or QEMU, tying into lesson 18.5), or use `qemu` to run the kernel with the gdbstub (`-s -S`) and attach gdb from the host. Printing logs with `printk` and reading through `dmesg` is the gentlest way to observe when you don't need to halt the kernel yet.

## Why ring-0 is so different

A few things trip up people used to user-mode. There's no familiar libc or Win32, only the kernel API, so you have to look up kernel function names to understand them (tying into lesson 1.13). Kernel addresses are shared across all processes, not isolated like user-mode (lesson 1.2), and KASLR randomizes the kernel base on every boot.

One bug crashes the whole machine, so the trial-and-error loop is much slower, and reading statically with care before running dynamically pays off. On the bright side, drivers are usually small and focused, so once you find the device control function, the rest is compact.

## Scope and ethics

A reminder of the spirit of lesson 0.2: analyzing a driver to understand what it does, testing the security of your own product, or studying a rootkit in a defensive lab are all fine. Using this knowledge to disable the anti-cheat of an online game or to write a rootkit is not, both legally and professionally. Ring-0 code is where the line between research and sabotage is thinnest, so be careful.

## Lab

See `labs/18.6/`: read a simple Linux kernel module (source included for comparison), build it into a `.ko`, then open the `.ko` in Ghidra to find `module_init`, `file_operations` and the ioctl function, and compare with the source.

## Key takeaways
Always reverse ring-0 in a VM: the target is a VM, the host runs the debugger, and you take a snapshot before loading the driver. A Windows `.sys` is a PE whose entry point is `DriverEntry`, and the heart is `MajorFunction[IRP_MJ_DEVICE_CONTROL]` (slot 0xE) handling IOCTLs. Work backwards from `DeviceIoControl` on the user-mode side to understand IOCTL codes and buffer structures.

A Linux `.ko` is an ELF whose entry point is `module_init`, so look for `file_operations` and signs of `sys_call_table` hooking. Debug with WinDbg kernel mode on Windows, or kgdb or the QEMU gdbstub on Linux. One ring-0 bug crashes the machine, so read statically with care before running dynamically.
