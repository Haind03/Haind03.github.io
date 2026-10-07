---
title: "Lesson 1.7: The PE format, anatomy of a Windows .exe"
date: 2022-03-16 14:18:00 +0700
categories: ["Technique Reverse", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Every `.exe`, `.dll`, `.sys` on Windows follows the same mold called PE (Portable Executable). Understanding this mold explains a lot: why DIE knows what a file was written in, why packers can hide code, where the entry point is so you can place your first breakpoint, and why a function from `kernel32.dll` can be called from your program. This lesson cuts open a PE from the top of the file down, just enough for you to poke around in PE-bear by hand.

## The big picture first

![PE file structure: DOS header, PE signature, File header, Optional header, section table and sections](/assets/img/technique-reverse/assets/phan-01/pe-structure.svg)

A PE file is laid out sequentially like this, from offset 0 down:

```
+-----------------------------+  offset 0
|  DOS header  (starts "MZ")   |
|  DOS stub                    |
+-----------------------------+
|  PE signature  ("PE\0\0")    |
|  File header                 |   <- NT headers
|  Optional header             |
+-----------------------------+
|  Section table               |  describes each section
+-----------------------------+
|  .text   (code)              |
|  .rdata  (constants, strings,IAT)|
|  .data   (globals)           |
|  .rsrc   (resources)         |
|  ...                         |
+-----------------------------+
```

The first parts (the headers) are the "birth certificate" describing the file. The rest is the actual content. The Windows loader reads the headers to know what to load where.

## The DOS header and the legendary "MZ"

Open any exe in a hex editor and the first two bytes are always `4D 5A`, the ASCII characters "MZ". This is the magic number that identifies a PE file. "MZ" stands for Mark Zbikowski, a Microsoft engineer from the DOS days. Seeing `4D 5A` at offset 0 tells you right away you're holding a Windows executable.

The DOS header has only one field that really matters to us: `e_lfanew` at offset `0x3C`. It's a number pointing to where the NT headers start. In other words: read 4 bytes at offset `0x3C`, jump there, and you arrive at the real PE part.

Right after the DOS header is the DOS stub, a tiny DOS program that prints the familiar "This program cannot be run in DOS mode." if someone runs the file on DOS. For RE it's harmless, skip it.

## NT headers, where the real declarations are

At the position `e_lfanew` points to, you find the PE signature first: 4 bytes `50 45 00 00`, i.e. "PE\0\0". This confirms "the PE part starts here".

Next is the file header (also called the COFF header), which has a few notable fields. `Machine` is the architecture: `0x14C` is x86 (32-bit) and `0x8664` is x64, which is how you decide between x32dbg and x64dbg. `NumberOfSections` is how many sections the file has, and `Characteristics` holds descriptive flags, for example whether this is an EXE or a DLL.

Then comes the optional header (the name "optional" is misleading, it's mandatory for executables). This is the part rich in information. `Magic` is `0x10B` for PE32 (32-bit) and `0x20B` for PE32+ (64-bit). `AddressOfEntryPoint` is the entry point, where code starts running. It's an RVA (explained right below), and your first breakpoint when debugging usually goes here. `ImageBase` is the virtual address the file wants to be loaded at. The classic is `0x400000` for 32-bit exes. With ASLR on, the loader actually puts it somewhere else, but ImageBase is the reference point for calculations. `SectionAlignment` and `FileAlignment` are the alignment of sections in memory and on disk, and these two numbers are why RVAs and file offsets don't line up. Finally `DataDirectory` is an array of pointers to the important tables (Import, Export, Relocation, TLS, Resource...). You'll keep coming back here.

## RVA and file offset, the trap when calculating by hand

This is the concept that confuses beginners the most, so read slowly.

A file offset (also called raw offset) is the position in bytes from the start of the file, while the file is on disk. Hex editors use this. An RVA (Relative Virtual Address) is the position counted from ImageBase, once the file is loaded into memory. IDA, debuggers, and the fields in the PE header use this.

The two numbers differ because the alignment on disk (`FileAlignment`, usually 0x200) is different from the alignment in memory (`SectionAlignment`, usually 0x1000). The same code byte has one file offset but a different RVA.

For the conversion, first find the section containing that RVA, meaning which section's `[VirtualAddress, VirtualAddress + VirtualSize)` range the RVA falls in. Then compute the offset within the section: `delta = RVA - VirtualAddress` (of that section). The file offset is then `PointerToRawData` (of that section) `+ delta`.

In short: `file_offset = RVA - section.VirtualAddress + section.PointerToRawData`.

To get the real virtual address (VA): `VA = ImageBase + RVA`. When IDA gives you a VA like `0x401500` and you want to find that byte on disk, you work backwards: VA minus ImageBase gives the RVA, then apply the formula above to get the file offset.

Luckily PE-bear and CFF Explorer do all of this math for you, with a button to convert RVA to offset. But understand the formula so you don't panic when the two numbers don't match.

## Section table

Right after the NT headers is an array, each element describing one section. Each entry gives the name (`.text`, `.data`...), `VirtualAddress` (RVA when loaded), `VirtualSize` (size in memory), `PointerToRawData` (file offset on disk), `SizeOfRawData` (size on disk), and `Characteristics` (R/W/X permissions).

The familiar sections are `.text` for code (flags are usually readable + executable), `.rdata` for read-only data such as constants, strings, and importantly the IAT, `.data` for writable globals, `.rsrc` for resources (icons, dialogs, version info, sometimes a payload hidden in here), and `.reloc` for relocation info.

Triage tip: if you see an odd section named something like `.UPX0`, `.vmp0`, or a `.text` with a huge `VirtualSize` but `SizeOfRawData` near zero, that's a sign the file is packed. The real code gets unpacked into the virtual region at runtime.

## Import Directory and IAT, how you call other people's functions

Your program calls `MessageBoxW`, but the code of `MessageBoxW` lives in `user32.dll`, not in your file. How does it get connected?

PE solves this with the Import Directory. For each DLL it needs (`kernel32.dll`, `user32.dll`...), it lists which functions are imported from that DLL. When the loader loads the program, it also loads these DLLs, finds the real address of each function (through that DLL's Export Directory, see below), and writes those addresses into a table called the IAT (Import Address Table).

In assembly, a call to an imported function looks like `call [IAT_entry]`, an indirect call through a slot in the IAT. When reading code, if you see a `call` to an address in `.rdata`, it's almost certainly an API call, and PE-bear/IDA will translate the function name for you.

Why the IAT matters for RE: the import table is a free summary of functionality. Seeing `CreateFileW`, `WriteFile` imported means the program touches files. Seeing `socket`, `send`, `WSAStartup` means networking. Seeing `VirtualAllocEx`, `WriteProcessMemory`, `CreateRemoteThread` makes you suspect injection right away. And when unpacking a file, rebuilding the IAT is the last step (Scylla does this, see Lesson 14.3), because a file dumped from memory usually has the IAT wrong.

## Export Directory

The opposite of import. A DLL "exports" functions for others to use, and the Export Directory lists them along with the RVA to each function's code. A function can be exported by name or only by ordinal (sequence number). When reversing a DLL, the Export Directory gives you the list of public entry points, a good place to start reading.

## Relocation

ImageBase is only a wish. When that address is already taken (or ASLR moves it), the loader has to load the file at a different base, and every absolute address hard-coded in the code has to be fixed up. The `.reloc` table lists the places that need fixing. You rarely read this table by hand, but know it exists so you understand why the same file runs at a different address every time.

## TLS directory and TLS callbacks, an anti-debug trap

TLS (Thread Local Storage) is the mechanism that gives each thread its own copy of data. What matters for RE is the TLS callback: these are functions registered in the TLS directory, and the loader calls them even before the entry point (before `main`).

This is a spot malware and protectors love to abuse: put the debugger check in a TLS callback, and it runs before you get a chance to set a breakpoint at the entry point, detecting you before you could observe anything. If you set a breakpoint at the entry point but the program already "knows" there's a debugger and exits, check the TLS directory. x64dbg has an option to break at TLS callbacks, turn it on. Details in Lesson 15.4.

## It all shows up in PE-bear

That's enough theory. Open PE-bear (or CFF Explorer), drag an exe in, and you'll see each part I just described appear as a tree: the DOS header, the NT headers with the Optional header's full fields, the section table with each section's permissions, the Import table with the list of DLLs and functions. DIE is less detailed but gives you a quick picture: compiler, entropy, packed or not. The usual workflow: DIE for quick triage, PE-bear for a close look.

## Lab

See [labs/1.7/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/1.7). The tasks include finding the entry point by hand, listing the sections, reading the IAT of an exe on your machine, and an exercise converting RVA to file offset using the formula above. A sample solution is in `solution.md`, but do it before you open it.

## Key takeaways
A PE file starts with "MZ" (`4D 5A`), and `e_lfanew` at offset 0x3C points to the NT headers, which start with "PE\0\0". Machine tells x86 (0x14C) from x64 (0x8664), AddressOfEntryPoint is where code starts, and ImageBase is the preferred base.

RVA is counted from ImageBase (used in memory/IDA) while file offset is counted from the start of the file (on disk). The conversion is `offset = RVA - VirtualAddress + PointerToRawData` of the section containing it. The IAT is the table of imported function addresses, and also a summary of what the program does.

An odd section, or a large VirtualSize with a small SizeOfRawData, is a sign of packing. TLS callbacks run before the entry point, a common place to hide anti-debug.
