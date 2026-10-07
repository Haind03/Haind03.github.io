---
title: "Lesson 1.8: ELF and Mach-O, the two formats outside Windows"
image:
  path: /assets/img/covers/re-1-8-elf-mach-o-two-formats-outside.webp
  alt: "Lesson 1.8: ELF and Mach-O, the two formats outside Windows"
date: 2022-03-21 22:18:00 +0700
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

In this lab you dissect an ELF binary by hand with `readelf`, `objdump`, `nm` and `file`: you identify the file, find the entry point, list the segments and look at the PLT/GOT, then compare a stripped and a non-stripped build. You need a Linux environment. On Windows, WSL (`wsl --install`) or a light Linux VM is enough.

The sample program is `hello.c`. It calls a couple of library functions (`printf` and `strlen`) so you can see the PLT/GOT at work, and it has one internal function so the stripped and non-stripped builds differ in something visible. Build a normal copy and a stripped copy. If you cannot build, a system binary such as `/bin/ls` answers most of the questions.

```
gcc -O0 -o hello hello.c            # normal build, symbols kept
gcc -O0 -o hello_stripped hello.c
strip hello_stripped                # stripped build
```

Begin with identification. Run `file hello` and read off the bit width, whether it is dynamically or statically linked, and whether it is stripped, then repeat with `hello_stripped` and compare. Next read the header with `readelf -h hello`: note the four magic bytes, the entry point (`e_entry`), and whether the type is `ET_EXEC` or `ET_DYN`. Modern gcc builds PIE by default, so it is usually `ET_DYN`.

Then compare segments and sections. `readelf -l hello` shows the program headers (segments) and, at the bottom, the "Section to Segment mapping". Find which loadable segment holds `.text` and what permissions it has (R E). `readelf -S hello` shows the section headers, where you should locate `.text`, `.rodata`, `.data`, `.bss`, `.plt` and `.got`. The string "Hello, ELF!" will sit in one of them, which you can check with `readelf -p .rodata hello`.

For the PLT/GOT, use `objdump -d -j .plt hello` to see the PLT stubs. Then run `objdump -d hello | grep -A3 '<main>:'` and look for the calls to `printf@plt` and `strlen@plt`, and notice that `main` does not call libc directly but goes through `@plt`. `readelf -r hello` prints the relocation table, which is exactly the list of GOT slots that get filled with real addresses at run time.

For symbols, run `nm hello` and find `main` and `secret_len`. Then see what `nm hello_stripped` reports now, whether `secret_len` is still visible, and what happens to `printf` (try `nm -D hello_stripped` to see the dynamic symbols). Finally, go back to the PE lesson (Lesson 1.7) and match things up: which PE field corresponds to the ELF entry point, and which PE mechanism corresponds to the PLT/GOT? Answer everything yourself before opening the solution.

<div class="lab-box">
<div class="lab-head"><b>LAB 1.8</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/1.8/src/hello.c" download><i class="fa-solid fa-file-code"></i>src/hello.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The output below comes from a gcc build on x86-64 Linux. Your addresses will differ, but the meaning is the same.

For identification, the two files look like this.

```
$ file hello
hello: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV),
       dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2,
       ... not stripped

$ file hello_stripped
hello_stripped: ELF 64-bit LSB pie executable, x86-64, ... stripped
```

It is a 64-bit, little-endian (LSB) ELF, built as PIE (hence "pie executable"), dynamically linked to libc through the `ld-linux` interpreter. One copy is "not stripped" and the other is "stripped", and the only difference between the two files is the symbol table.

The header looks like this.

```
$ readelf -h hello
  Magic:   7f 45 4c 46 02 01 01 00 ...
  Class:                             ELF64
  Data:                              2's complement, little endian
  Type:                              DYN (Position-Independent Executable file)
  Machine:                           Advanced Micro Devices X86-64
  Entry point address:               0x1060
```

The magic is `7f 45 4c 46`, that is `0x7F` followed by "ELF". The entry point `0x1060` is not `main` but `_start` from the C runtime, which does its initialization and only then calls `main`, much like the CRT code that runs before `main` in a PE. The type is `DYN` rather than `EXEC` because it is a PIE. A PIE can run at a random base (ASLR), so the addresses in the file are offsets from the base rather than absolute addresses.

For segments versus sections:

```
$ readelf -l hello
Program Headers:
  Type           Offset   VirtAddr           Flags  Align
  LOAD           0x001000 0x0000000000001000 R E    0x1000
  LOAD           0x002000 0x0000000000002000 R      0x1000
  LOAD           0x002xxx 0x0000000000003xxx RW     0x1000
  ...
 Section to Segment mapping:
  Segment ... .text ...        <- inside the LOAD with flags R E
  Segment ... .rodata ...      <- LOAD with flags R
  Segment ... .data .bss ...   <- LOAD with flags RW
```

The key point is that `.text` lives in a loadable segment with flags R E (read and execute, not write), while `.data` and `.bss` live in an RW segment. A segment groups several sections with the same permissions so the loader can map them in one go. As the lesson said, segments are for running and sections are for analysis.

```
$ readelf -p .rodata hello
  [     8]  Hello, ELF!
  [    14]  string length is %d
```

As expected, the constant strings are in `.rodata`.

For the PLT/GOT:

```
$ objdump -d hello | grep -A12 '<main>:'
0000000000001169 <main>:
    ... lea    rax,[rip+0xe8c]        # load the address of the "Hello, ELF!" string
    ... call   1050 <puts@plt>        # printf("%s\n", msg) optimized into puts
    ... call   1060 ...               # or strlen@plt depending on the build
```

`main` does not call libc directly. It calls `puts@plt` or `strlen@plt`, which are stubs in the PLT. gcc often replaces `printf("%s\n", x)` with `puts(x)` when optimizing, so do not be surprised to see `puts`.

```
$ readelf -r hello
Relocation section '.rela.plt' ...
  Offset          Info           Type           Sym. Name
  0000000000003fc8 ...           R_X86_64_JUMP_SLOT   puts@GLIBC
  0000000000003fd0 ...           R_X86_64_JUMP_SLOT   strlen@GLIBC
```

Each `JUMP_SLOT` line is a GOT slot (at offsets `0x3fc8`, `0x3fd0` and so on) that the dynamic linker fills with the real address of `puts` or `strlen` the first time they are called (lazy binding). Before the first call the GOT slot points back at the resolver, and afterwards it points straight at the function in libc.

For symbols:

```
$ nm hello | grep -E 'main|secret_len'
0000000000001169 T main
0000000000001145 t secret_len     <- lowercase 't': local symbol

$ nm hello_stripped
nm: hello_stripped: no symbols

$ nm -D hello_stripped
                 U puts@GLIBC_2.2.5
                 U strlen@GLIBC_2.2.5
```

After stripping, `nm` normally sees nothing because `.symtab` has been cut, so `secret_len` and `main` lose their names. But `nm -D` (dynamic symbols, read from `.dynsym`) still lists `puts` and `strlen`, because the imported functions need their names at run time for the linker to resolve them and cannot be stripped. That is exactly what the lesson said: strip kills internal function names, not the names of imported library functions.

Finally, the comparison with PE. The ELF `e_entry` corresponds to the PE `AddressOfEntryPoint`. The PLT/GOT corresponds to the IAT (Import Address Table). `.rodata` corresponds to `.rdata`. A LOAD segment corresponds to a section mapped according to its characteristics, and the `ld-linux` interpreter corresponds to the Windows loader plus ntdll. It is the same skeleton with different names, so moving from Windows reversing to Linux, or the other way round, is mostly a matter of translating vocabulary.

</details>

## Key takeaways
The ELF magic is `7F 'E' 'L' 'F'`, Mach-O is `FEEDFACE/FACF`, and a fat binary is `CAFEBABE`. ELF has two tables: the program header (segments, for the loader to run) and the section header (sections, for analysis). Segments are for running, sections are for reading.

PLT/GOT is how Linux calls library functions, with lazy binding filling the real address into the GOT on the first call. Stripping cuts `.symtab` (internal functions become sub_xxx) but `.dynsym` stays, so imported function names are still visible. Mach-O can be a fat binary containing multiple architectures, and you use `lipo` to extract one. PE, ELF and Mach-O share the same ideas, only the names differ.
