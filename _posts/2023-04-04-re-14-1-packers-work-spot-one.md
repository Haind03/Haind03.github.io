---
title: "Lesson 14.1: How packers work, and how to spot one"
date: 2023-04-04 11:06:00 +0700
categories: ["Technique Reverse", "Part 14 · Packers and Obfuscation"]
tags: [reverse-engineering, packer, obfuscation]
render_with_liquid: false
---
There's a moment everyone doing RE runs into: you open a file in IDA, eager to find the logic, and you see just a few dozen instructions and then a jump into a region of pure junk bytes. No meaningful strings, an empty import table, nothing makes sense no matter how long you read. It's not that you're bad at this. The file is packed, and what you're looking at is only the shell.

This lesson helps you recognize that in a minute, instead of wasting a whole evening reading code that never runs.

## What a packer does to a program

The idea of a packer is very simple. Take the program's original code, compress or encrypt it into a block of data, then attach a small piece of code called the stub (or unpacking stub). At runtime the stub works first: it decompresses/decrypts that data block back into the original code in memory, then jumps there so the program runs normally.

```
File on disk:                 At runtime (in memory):
+------------------+          +------------------+
| unpacking stub   |  --->    | stub (already ran)|
+------------------+          +------------------+
| original code,   | unpack   | original code IS |  <- only now readable
| compressed/      |  ---->   | in the clear here|
| encrypted (junk) |          |                  |
+------------------+          +------------------+
```

The most important consequence for RE: **the real code only exists in readable form in memory at runtime, not on disk.** So static analysis (opening the file in IDA/Ghidra) only sees the stub and a pile of junk. To see the real code, you have to let it unpack itself and then grab it, which is what lessons [14.2](https://github.com/Haind03/Technique-Reverse/blob/main/phan-14-packer-obfuscation/14.2-unpack-upx.md) and [14.3](https://github.com/Haind03/Technique-Reverse/blob/main/phan-14-packer-obfuscation/14.3-dump-rebuild-iat.md) are about.

## OEP: the destination of every unpack

When the stub finishes the decompression part, it has to jump back to the program's real starting point. That point is called the OEP (Original Entry Point), which is the entry point the program would have if it weren't packed.

The whole craft of manual unpacking boils down to one sentence: find the OEP. Reaching the OEP means the stub has finished unpacking, the original code is fully in memory, and this is the golden moment to dump. Remember this OEP, it keeps coming back throughout Part 14.

## Spotting a packed file in a minute

You don't need to unpack to know whether a file is packed. A few obvious signs:

### 1. High entropy

Entropy measures how "random" data is, on a scale from 0 to 8. Normal code and text have entropy around 5 to 6.5. Compressed or encrypted data looks almost random, so entropy shoots up close to 8.0. If you see a section with entropy 7.8 or higher, it's almost certainly compressed or encrypted.

Detect It Easy (DIE, included in this repo in the parent folder `die_win64_portable_3.08_x64`) has an Entropy button that plots entropy per region of the file. A clean file has a moderately bumpy entropy line. A packed file has a flat block right up near 8.

### 2. A suspiciously poor import table

A normal Windows program calls dozens to hundreds of API functions, so its import table (IAT) is long. A packed file is different: the stub doesn't need many APIs yet, it just needs a few functions to rebuild the imports itself after unpacking, typically `LoadLibraryA` and `GetProcAddress`. So when you see a fully featured exe whose import table has only a handful of functions, including `LoadLibrary` and `GetProcAddress`, that's a very strong sign of a packer.

### 3. Strange section names

Packers often name sections after their own brand. A few familiar ones:

| Section name | Packer/protector |
|---|---|
| `UPX0`, `UPX1` | UPX |
| `.vmp0`, `.vmp1` | VMProtect |
| `.themida`, `.winlice` | Themida/WinLicense |
| `.aspack`, `.adata` | ASPack |
| `.petite` | Petite |
| `.enigma1` | Enigma Protector |

The standard compiler sections are `.text`, `.data`, `.rdata`, `.rsrc`. A strange name should make you suspicious right away.

### 4. A section that's both writable and executable

Normal code lives in a read-and-execute only section (R-X). But the stub has to write the unpacked code into a region and then run it, so that region needs both write and execute permission (RWX, or a section with both WRITE and EXECUTE). A section that's both writable and executable is a red flag, rarely seen in clean software (see [Lesson 1.2](/posts/re-1-2-process-memory-map-where-everything-happens/) again).

### 5. Very few meaningful strings

The strings in the original code (messages, URLs, paths) are compressed/encrypted and so vanish from the `strings` output. What remains is usually just the stub's strings. A big exe where `strings` comes out nearly empty is suspicious.

## Packer vs protector: same family, different purpose

These two words get mixed up a lot, so let's separate them clearly. A packer is mainly for compression (reducing size) or hiding code at a basic level. UPX is the classic example, originally made to compress exes, and a plain packer is relatively easy to remove. A protector aims at anti-analysis. Besides compressing/encrypting, it adds anti-debug, anti-VM, anti-dump, integrity checks, and the heaviest of all, virtualization (turning code into the bytecode of a private VM). Themida, VMProtect and Enigma belong to this group, and removing a protector is many levels harder.

The line isn't absolute (many modern packers come with some protection), but knowing which kind you're up against decides whether you spend an hour or a week. Anti-debug and anti-VM are the content of Part 15, virtualization is [Lesson 14.5](https://github.com/Haind03/Technique-Reverse/blob/main/phan-14-packer-obfuscation/14.5-virtualization.md).

## Packer triage workflow

Turn this into a habit, whenever you suspect a file is packed. Drag the file into DIE and see whether it recognizes a packer (DIE has signatures for most common packers). Click the Entropy button and look for a flat block near 8.0. Check the import table, whether it's abnormally poor with only `LoadLibrary`/`GetProcAddress`, and check the section names for strange ones. Then conclude: packed or not, and if so what kind, packer or protector.

After this step you know what you're holding and can choose a tactic: for UPX, a single `upx -d` (lesson 14.2), for a custom packer, unpack manually to find the OEP, for a strong protector, weigh whether it's worth it.

## Key takeaways
A packer compresses/encrypts the original code and adds a stub that unpacks it at runtime, so the real code only appears in memory at runtime, not on disk. The OEP (Original Entry Point) is the destination of every unpack: once you're there, the original code is ready in memory.

There are five signs of packing: entropy near 8.0, poor imports (LoadLibrary/GetProcAddress), strange section names, a section that's both writable and executable, and few strings. Use Detect It Easy for quick identification (signatures + entropy). Packers compress while protectors resist analysis (adding anti-debug/anti-VM/virtualization), so know which one you have to pick your effort.
