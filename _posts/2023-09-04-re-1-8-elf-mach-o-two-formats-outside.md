---
title: "Lesson 1.8: ELF and Mach-O, the two formats outside Windows"
date: 2023-09-04 20:30:00 +0700
categories: ["Technique Reverse", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Last lesson cut open the Windows PE. But reversing doesn't only live on Windows: servers run Linux, Android phones are Linux at the core, and Macs and iPhones use their own format. If PE is the "passport" of a Windows file, then ELF is Linux's and Mach-O is Apple's. Understand these three and you can read the header of almost every binary you'll meet in your life.

The good news: all three solve the same problem (packaging code, data, and the info on how to load it into memory), so learning one lets you pick up the other two fast. This lesson focuses on ELF because you'll meet it the most, then skims Mach-O and compares.

## ELF: the backbone of Linux

ELF (Executable and Linkable Format) is used for everything that runs on Linux: executables, `.so` libraries, `.o` object files, even core dumps. It's easy to recognize: the first 4 bytes are always `7F 45 4C 46`, that is `0x7F` followed by the three ASCII characters "ELF". Open any file in `/bin` with a hex editor and you'll see it right away.

### The header, the map at the top of the file

The ELF header sits at the start of the file and tells you the core things. The magic (`7F 45 4C 46`) confirms this is ELF. The class says 32-bit (ELFCLASS32) or 64-bit (ELFCLASS64), and the endianness says little or big endian. The type is `ET_EXEC` (fixed-address executable), `ET_DYN` (shared object or PIE, can run at any address), or `ET_REL` (object file). The machine field gives the CPU architecture: x86-64, ARM, MIPS, RISC-V... The entry point (`e_entry`) is the virtual address where code starts running, the same idea as PE's `AddressOfEntryPoint`. The header also records the location of the program header table and the section header table.

Quick commands to read it:

```
readelf -h ./a.out      # read the ELF header
file ./a.out            # one-line summary: type, bits, dynamic/static, stripped or not
```

### Two header tables, a common source of confusion

This is where ELF differs from PE and trips up a lot of people: ELF has two description tables, serving two different purposes.

The program header table tells the loader (the OS) how to load the file into memory at runtime. Its unit is the segment, and each segment is a block that gets mapped into memory with permissions (R/W/X). The section header table tells the linker and analysis tools which sections the file is divided into (.text, .data...). At runtime the loader doesn't need this table.

In short: segments are for running, sections are for analysis. A segment usually bundles several sections. For example the code segment contains both `.text` and `.rodata`. When a file is stripped, the section headers may be trimmed down, but the program headers can't be missing, because without them the file can't run.

```
readelf -l ./a.out      # program headers (segments) + which sections belong to which segment
readelf -S ./a.out      # section headers
```

### The familiar sections

Many are like PE, just named a bit differently. `.text` is code with R-X permissions. `.data` holds initialized globals, RW. `.bss` holds globals equal to 0 and takes no space on disk. `.rodata` is read-only data, constants and strings, and your "Access denied" string is here. `.plt` and `.got` are the heart of dynamic linking, covered below. `.symtab` and `.strtab` are the symbol and name tables, which is what gets cut when you strip. `.dynsym` and `.dynstr` hold symbols for dynamic linking, and these don't get stripped because they're needed at runtime.

### PLT and GOT, how Linux calls library functions

When a program calls `printf` from libc, at compile time it doesn't know what address `printf` is at (libc is placed randomly by ASLR on each run). Linux solves this with the PLT/GOT pair, and you'll see these two names for the rest of your Linux reversing life, so get them straight now.

The GOT (Global Offset Table) is a table of pointers. Each slot will hold the real address of an external function, filled in at runtime. The PLT (Procedure Linkage Table) is small stubs of code that sit in between. Your code doesn't call `printf` directly but calls `printf@plt`.

The lazy binding mechanism, resolving the address only when the function is first called, works like this: on the first call to `printf@plt`, it jumps through the GOT to the dynamic linker's resolver, finds the real address of `printf`, writes it into the GOT slot, and then makes the call. From then on, `printf@plt` jumps straight through the GOT to the saved address, with no need to resolve again.

For a reverser, what to remember: seeing `call printf@plt` means an external function is being called, and to know its real address at runtime you look at the matching GOT slot in the debugger. The GOT is also a classic attack target (GOT overwrite), but that's the exploit side of things.

### Stripped or not

Like PE, an ELF binary can keep or drop symbol info. If it's not stripped, `.symtab` is still there and function and variable names show up nicely in Ghidra/IDA, which is easy going. If it's stripped, `.symtab` is cut and only `.dynsym` remains (imported library functions still show names, but the author's internal functions become `sub_xxxx`). Most real software and malware is stripped.

```
nm ./a.out              # list symbols (says "no symbols" if stripped)
strip ./a.out           # strip it yourself to see the difference
```

## Mach-O: Apple's format

macOS and iOS use Mach-O. The way of thinking is like ELF but the names and a few details differ.

The magic is `0xFEEDFACE` (32-bit) or `0xFEEDFACF` (64-bit). Fun fact: the Apple folks deliberately made it spell "feed face". A Mach-O can also be a fat binary (universal binary): one file can bundle several architectures at once, for example x86-64 and ARM64 for both Intel and Apple Silicon machines. The magic of a fat file is `0xCAFEBABE`. When reversing, you usually have to extract the architecture you need with `lipo`.

Load commands replace ELF's program headers. It's a list of instructions for the loader: which segment maps where, which libraries are needed, where the entry point is, what the code signature looks like. Mach-O also has segments, named in uppercase with two underscores: `__TEXT` (code, read-only) and `__DATA` (writable data). Inside each segment there are sections like `__text`, `__cstring`.

Tools on a Mac:

```
otool -hv binary        # header and load commands
otool -l binary         # list all load commands in full
lipo -info binary       # see which architectures the file contains
lipo binary -thin arm64 -output binary_arm64   # extract one architecture
nm binary               # symbols
```

Objective-C and Swift also have their own metadata sections for the runtime, but that's for Part 12 to handle. Here you only need to get used to the Mach-O skeleton.

## Comparing the three formats so it sticks

| Concept | PE (Windows) | ELF (Linux) | Mach-O (Apple) |
|---|---|---|---|
| Magic | `MZ` then `PE\0\0` | `7F 45 4C 46` | `FEEDFACE/FACF`, fat `CAFEBABE` |
| Memory loading description | Section table | Program header (segment) | Load commands (segment) |
| Code | .text | .text | `__TEXT`/`__text` |
| Read-only data | .rdata | .rodata | `__TEXT`/`__cstring` |
| Importing external functions | IAT | PLT/GOT | stubs / `__la_symbol_ptr` |
| Entry point | AddressOfEntryPoint | e_entry | LC_MAIN |
| Multiple architectures in one file | No | No | Yes (fat binary) |

Looking at this table you can see all three tell the same story, just with different vocabulary. Learn ELF well and reading PE and Mach-O is just looking up the names.

## Lab

The lab is at [labs/1.8/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/1.8). You'll use `readelf`, `objdump`, `nm` yourself to dissect an ELF binary, find the entry point, list the segments, and observe PLT/GOT. There's a hello world file to build and a sample writeup to compare against. If you don't have a Linux machine, running in WSL or a light VM is enough.

## Key takeaways
The ELF magic is `7F 'E' 'L' 'F'`, Mach-O is `FEEDFACE/FACF`, and a fat binary is `CAFEBABE`. ELF has two tables: the program header (segments, for the loader to run) and the section header (sections, for analysis). Segments are for running, sections are for reading.

PLT/GOT is how Linux calls library functions, with lazy binding filling the real address into the GOT on the first call. Stripping cuts `.symtab` (internal functions become sub_xxx) but `.dynsym` stays, so imported function names are still visible. Mach-O can be a fat binary containing multiple architectures, and you use `lipo` to extract one. PE, ELF and Mach-O share the same ideas, only the names differ.
