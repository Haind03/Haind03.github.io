---
title: "Lesson 18.6: Reversing Windows drivers and Linux kernel modules"
image:
  path: /assets/img/covers/re-18-6-reversing-ring-0-code-windows-drivers.webp
  alt: "Lesson 18.6: Reversing Windows drivers and Linux kernel modules"
date: 2023-09-12 11:45:00 +0700
categories: ["Reverse Engineering", "Part 18 · Advanced Topics"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
So far everything we've taken apart ran in ring-3, user-mode, where a bug only crashes one process. Ring-0, kernel-mode, is different. Code here runs with full privileges, and a small bug crashes the whole machine (a BSOD on Windows, a kernel panic on Linux). Rootkits, anti-cheat, and many anti-debug drivers (like TitanHide in lesson 15.9) live here, so sooner or later you have to go down.

This lesson doesn't teach writing drivers. It covers reading a driver you don't have the source for, and debugging it without wrecking your machine.

## First rule: always work in a VM

When reversing ring-0 code, the VM lab from lesson 0.3 is a requirement, not an option. Debugging the kernel means halting the whole operating system, so you need two machines, one running the driver (the target) and one running the debugger (the host). With a VM, the target is a VM, the host is the real machine, and they connect through a named pipe or network. If the driver breaks, only the VM crashes, and you restore a snapshot in a few seconds.

Never load an unknown driver onto your real machine to see what it does.

## Windows kernel driver: the .sys file

A Windows driver (`.sys`) is still a PE file, like the `.exe` and `.dll` in lesson 1.7, except the subsystem is Native and it links against `ntoskrnl.exe` instead of `kernel32.dll`. Open it in IDA or Ghidra as usual, but the APIs you see will be kernel ones, such as `IoCreateDevice`, `ObReferenceObjectByHandle`, `MmGetSystemRoutineAddress`, `ZwOpenKey`, not `CreateFileW`.

### DriverEntry

A driver's entry point isn't `main` but `DriverEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath)`. Start reading there. In `DriverEntry`, a driver usually does two notable things. It creates a device object (`IoCreateDevice`) and a symbolic link (`IoCreateSymbolicLink`) so user-mode can reach it, and the device name (for example `\\Device\\MyDriver`) is a clue for finding the user-mode program that controls it. It also assigns the major functions into the `DriverObject->MajorFunction[]` table, which is the spot that matters most.

### The MajorFunction table and IOCTLs

A driver communicates with user-mode through the IRP (I/O Request Packet) mechanism. `DriverObject->MajorFunction` is an array of function pointers, each slot matching one kind of request:

```
MajorFunction[IRP_MJ_CREATE]         = DriverCreateClose;   // index 0
MajorFunction[IRP_MJ_CLOSE]          = DriverCreateClose;   // index 2
MajorFunction[IRP_MJ_DEVICE_CONTROL] = DriverDeviceControl; // index 14, the most important
```

The `IRP_MJ_DEVICE_CONTROL` slot (value 0xE) is almost always the main part of the driver, because this is where `DeviceIoControl` from user-mode gets handled. Find where slot 0xE gets assigned in `DriverEntry`, jump to that function, and you're in the main logic.

Inside the device control function, the driver reads the IOCTL code from the IRP (through `IoGetCurrentIrpStackLocation`, the field `Parameters.DeviceIoControl.IoControlCode`) and then switches on each code. Each IOCTL is a command that user-mode sends down. Rebuild the table of IOCTL codes against behavior and you've understood the driver's private API.

### Working backwards from the user-mode side

If you also have the user-mode program that controls the driver, look for the `DeviceIoControl` call in it. The second parameter is the IOCTL code, and the input/output buffer parameters tell you the data structures. Put the user and kernel sides together and you understand the whole protocol. So reversing a driver is often easier when the user-mode part comes with it.

### Debugging with WinDbg in kernel mode

Debug a driver with WinDbg (mentioned in lesson 2.6) in kernel mode. On the target VM, turn on kernel debugging with `bcdedit /debug on` and configure the transport (`bcdedit /dbgsettings net ...` or serial/named pipe), then reboot. On the host, open WinDbg and attach to the kernel over the same transport.

A few commands get used a lot. `lm` lists loaded modules (find your driver), `!drvobj MyDriver 7` shows the driver object and the major function table, `bp MyDriver!DriverDeviceControl` sets a breakpoint, `!irp` shows the current IRP, and `dt` reads a struct. The target VM freezes when a breakpoint hits. That's normal, the host controls everything.

## Linux kernel module: the .ko file

On Linux, a kernel module is a `.ko` file, a relocatable ELF (mentioned in lesson 1.8). Open it in Ghidra/IDA like a normal ELF.

There are two entry points defined by macros. `module_init(func)` registers the function that runs when the module is loaded (`insmod`), which is Linux's `DriverEntry`. `module_exit(func)` runs on removal (`rmmod`).

Module info (name, license, author, parameters) sits in the `.modinfo` section, quickly read with `modinfo file.ko`. Symbols are often still fairly intact because kernel modules tend to keep function names, so it's easier to read than a stripped Windows driver.

Modules often register a character device or an entry in `/proc` or `/sys` to talk to user-mode (the equivalent of Windows' device object + IOCTL), so look for the `file_operations` struct with the `.read`, `.write`, `.unlocked_ioctl` pointers. They also sometimes hook syscalls, a classic rootkit technique that modifies `sys_call_table` to intercept `getdents` to hide files, or `kill` to receive hidden commands. If a module reads or writes `sys_call_table`, read it carefully.

For debugging, use `kgdb` connected from another machine (or QEMU, see lesson 18.5), or use `qemu` to run the kernel with the gdbstub (`-s -S`) and attach gdb from the host. Printing logs with `printk` and reading them through `dmesg` is the gentlest way to observe when you don't need to halt the kernel yet.

## What's different about ring-0

A few things trip up people used to user-mode. There's no familiar libc or Win32, only the kernel API, so you have to look up kernel function names to understand them (see lesson 1.13). Kernel addresses are shared across all processes, not isolated like user-mode (lesson 1.2), and KASLR randomizes the kernel base on every boot.

One bug crashes the whole machine, so the trial-and-error loop is much slower, and reading statically with care before running dynamically pays off. On the plus side, drivers are usually small and focused, so once you find the device control function, the rest is compact.

## Scope and ethics

Same spirit as lesson 0.2. Analyzing a driver to understand what it does, testing the security of your own product, or studying a rootkit in a defensive lab are all fine. Using this knowledge to disable the anti-cheat of an online game or to write a rootkit is not, legally or professionally. Ring-0 is where the line between research and sabotage is thinnest, so be careful.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 18.6</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/18.6.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/18.6/src/Makefile" download><i class="fa-solid fa-download"></i>src/Makefile</a>
<a class="lab-file" href="/assets/labs/18.6/src/hello_ioctl.c" download><i class="fa-solid fa-download"></i>src/hello_ioctl.c</a>
</div>
</div>

The goal is to get familiar with the structure of a `.ko` kernel module, find its entry point and how it talks to user mode, and then compare the disassembly with the source. A safety warning first, only `insmod` the module in a Linux VM you use for learning, never on your main machine. This lab doesn't require loading the module into a kernel. You only need to build the `.ko` and open it in Ghidra to read it, and if you do want to load it, do it in a VM with a snapshot.

To build the module you need the kernel headers:

```
sudo apt install build-essential linux-headers-$(uname -r)
```

The folder with `hello_ioctl.c` and its `Makefile` builds with:

```
make
```

The result is `hello_ioctl.ko`. If it won't build (missing headers, or a WSL environment with no kernel tree), you can still do the reading part by following the solution.

Run `modinfo hello_ioctl.ko` and read the `.modinfo` section. What are the license, description and author? Open `hello_ioctl.ko` in Ghidra (import it as an ELF) and find the function that `module_init` points to. A hint is to look at the symbol `init_module` or the `.init.text` section. Find the module's `file_operations` struct and see which functions the `.open` and `.unlocked_ioctl` pointers lead to. Go into the ioctl handler and rebuild the table of IOCTL codes (the commands user mode sends down) and what each one does. Finally, compare what you found with `hello_ioctl.c` and see how much of it was right.

Two questions to think about. Why is a kernel module often easier to read than a stripped Windows driver? And if this module hooked `sys_call_table` instead of creating a character device, where would you look for that sign?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The solution below follows the source `hello_ioctl.c` and the standard behavior of the module compiler. Building the `.ko` needs `linux-headers` matching your kernel, so use a Linux VM with the headers, and `make` produces `hello_ioctl.ko` and every step matches.

For `modinfo hello_ioctl.ko`, you get these (from the macros at the end of the source) `license: GPL`, `description: Lab 18.6 character device with ioctl for RE practice` and `author: Blog Reverse Engineering`, along with `vermagic` (the kernel version), `depends` and the symbol list. The `.modinfo` section holds exactly these strings, and you can also see them with `strings hello_ioctl.ko | grep -E 'license|author|description'`.

To find `module_init`, note that `module_init(hello_init)` makes the build create a symbol `init_module` pointing to `hello_init`, placed in the `.init.text` section. In Ghidra, look for `init_module` in the Symbol Tree (or `hello_init` if the name survives). The function calls `register_chrdev(0, "hello_ioctl", &hello_fops)` and then `printk` or `_printk` with the string `"hello_ioctl: loaded, major=%d"`. Going backwards from that string (the technique from Lesson 0.4) leads straight to `hello_init`. Likewise `cleanup_module` points to `hello_exit`, which calls `unregister_chrdev`.

For `file_operations`, the third parameter of `register_chrdev` is `&hello_fops`. Jump to that address and Ghidra shows an array of function pointers. The layout of `struct file_operations` puts `.open`, `.release` and `.unlocked_ioctl` at fixed offsets (depending on the kernel version). The non-null slots point to `hello_open` (return 0), `hello_release` (return 0) and `hello_ioctl`, the main logic function for `.unlocked_ioctl`. The function in the table that has a switch with many branches is `unlocked_ioctl`, the equivalent of `IRP_MJ_DEVICE_CONTROL` on Windows.

To rebuild the IOCTL table, inside `hello_ioctl` the `cmd` parameter is compared against constants. The codes are generated by the `_IO`, `_IOW` and `_IOR` macros with the magic `'H'` (0x48). `IOCTL_PING = _IO('H', 1)` is code `0x00004801` and prints "PING" and returns 0. `IOCTL_SET = _IOW('H', 2, int)` is code `0x40044802` and does a `copy_from_user` of 4 bytes into `stored_value`. `IOCTL_GET = _IOR('H', 3, int)` is code `0x80044803` and does a `copy_to_user` of `stored_value` out to user mode. The default case returns `-EINVAL` (-22). To compute `_IOW('H',2,int)`, `dir=1 (write)` sits at bit 30, `size=4` at bits 16 to 29, `type='H'=0x48` at bits 8 to 15 and `nr=2` at bits 0 to 7, which combine into `0x40044802`. `copy_from_user` and `copy_to_user` are clear markers for IOCTL_SET and IOCTL_GET. This is the module's own private API, where user mode opens `/dev/hello_ioctl` and calls `ioctl(fd, 0x40044802, &val)` to set and `ioctl(fd, 0x80044803, &out)` to get.

Comparing with the source, everything matches, with three IOCTLs, one static `stored_value` variable and a `file_operations` with three functions. The parts that tend to be off when reading are the offsets inside `file_operations` (they change with the kernel version) and `printk` being renamed to `_printk` on newer kernels.

On the questions. A `.ko` is easier to read than a stripped `.sys` because Linux kernel modules usually keep many symbols (function names in the ELF symbol table, strings in `.modinfo`, names through `__ksymtab`), while commercial Windows drivers are often stripped down to just `DriverEntry`. Also, `printk` leaves log strings describing the behavior, which makes going from strings very effective. If the module hooked `sys_call_table`, you'd look for references to the symbol `sys_call_table` (or code that scans kernel memory for this table), followed by a write of the module's function pointer into a syscall slot while saving the original pointer. The module also changes the write permission of the page holding the table (`write_cr0` clearing the WP bit, or `set_memory_rw`) before writing. That's a classic sign of a rootkit.

</details>

## Key takeaways
Always reverse ring-0 in a VM, with the target as a VM, the host running the debugger, and a snapshot before loading the driver. A Windows `.sys` is a PE whose entry point is `DriverEntry`, and the main part is `MajorFunction[IRP_MJ_DEVICE_CONTROL]` (slot 0xE) handling IOCTLs. Work backwards from `DeviceIoControl` on the user-mode side to understand IOCTL codes and buffer structures.

A Linux `.ko` is an ELF whose entry point is `module_init`, so look for `file_operations` and signs of `sys_call_table` hooking. Debug with WinDbg kernel mode on Windows, or kgdb or the QEMU gdbstub on Linux. One ring-0 bug crashes the machine, so read statically with care before running dynamically.
