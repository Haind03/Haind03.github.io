---
title: "Lesson 14.1: How packers work and how to spot one"
image:
  path: /assets/img/covers/re-14-1-packers-work-spot-one.webp
  alt: "Lesson 14.1: How packers work and how to spot one"
date: 2023-04-04 11:06:00 +0700
categories: ["Reverse Engineering", "Part 14 · Packers and Obfuscation"]
tags: [reverse-engineering, packer, obfuscation]
render_with_liquid: false
---
Everyone doing RE hits this sooner or later. You open a file in IDA, ready to find the logic, and you see a few dozen instructions and then a jump into a region of junk bytes. No meaningful strings, an empty import table, nothing makes sense no matter how long you read. You're not bad at this. The file is packed, and you're only looking at the shell.

This lesson helps you recognize that in a minute, instead of wasting an evening reading code that never runs.

## What a packer does to a program

A packer is simple in idea. Take the program's original code, compress or encrypt it into a block of data, then attach a small piece of code called the stub (or unpacking stub). At runtime the stub runs first. It decompresses/decrypts that data block back into the original code in memory, then jumps there so the program runs normally.

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

The important consequence for RE is that the real code only exists in readable form in memory at runtime, not on disk. Static analysis (opening the file in IDA/Ghidra) only sees the stub and a lot of unreadable data. To see the real code, you have to let it unpack itself and then grab it, which is what lessons [14.2](/posts/re-14-2-unpacking-upx-automatic-manual/) and [14.3](/posts/re-14-3-dumping-process-rebuilding-iat-scylla/) cover.

## OEP

When the stub finishes decompressing, it has to jump back to the program's real starting point. That point is called the OEP (Original Entry Point), the entry point the program would have if it weren't packed.

Manual unpacking mostly comes down to finding the OEP. Reaching the OEP means the stub has finished unpacking and the original code is fully in memory, so that's when you dump. You'll see the OEP again and again in Part 14.

## Spotting a packed file in a minute

You don't need to unpack to know whether a file is packed. A few signs:

### 1. High entropy

Entropy measures how random data is, on a scale from 0 to 8. Normal code and text have entropy around 5 to 6.5. Compressed or encrypted data looks almost random, so entropy goes up close to 8.0. A section with entropy 7.8 or higher is almost certainly compressed or encrypted.

Detect It Easy (DIE) has an Entropy button that plots entropy per region of the file. A clean file has a moderately bumpy entropy line. A packed file has a flat block right up near 8.

### 2. A suspiciously poor import table

A normal Windows program calls dozens to hundreds of API functions, so its import table (IAT) is long. A packed file is different. The stub doesn't need many APIs, just a few to rebuild the imports itself after unpacking, typically `LoadLibraryA` and `GetProcAddress`. A fully featured exe whose import table has only a handful of functions, including `LoadLibrary` and `GetProcAddress`, is a strong sign of a packer.

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

The standard compiler sections are `.text`, `.data`, `.rdata`, `.rsrc`. A strange name should make you suspicious.

### 4. A section that's both writable and executable

Normal code lives in a read-and-execute only section (R-X). But the stub has to write the unpacked code into a region and then run it, so that region needs both write and execute permission (RWX, or a section with both WRITE and EXECUTE). A section that's both writable and executable is suspicious, rarely seen in clean software (see [Lesson 1.2](/posts/re-1-2-process-memory-map-where-everything-happens/) again).

### 5. Very few meaningful strings

The strings in the original code (messages, URLs, paths) are compressed/encrypted and vanish from the `strings` output. What remains is usually just the stub's strings. A big exe where `strings` comes out nearly empty is suspicious.

## Packer vs protector

These two words get mixed up a lot. A packer is mainly for compression (reducing size) or hiding code at a basic level. UPX is the classic example, originally made to compress exes, and a plain packer is relatively easy to remove. A protector aims at anti-analysis. Besides compressing/encrypting, it adds anti-debug, anti-VM, anti-dump, integrity checks, and the heaviest of all, virtualization (turning code into the bytecode of a private VM). Themida, VMProtect and Enigma belong to this group, and removing a protector is many levels harder.

The line isn't absolute (many modern packers come with some protection), but knowing which kind you're up against decides whether you spend an hour or a week. Anti-debug and anti-VM are in Part 15, virtualization is [Lesson 14.5](/reverse-engineering/).

## Packer triage workflow

Make this a habit whenever you suspect a file is packed. Drag the file into DIE and see whether it recognizes a packer (DIE has signatures for most common packers). Click the Entropy button and look for a flat block near 8.0. Check the import table, whether it's abnormally poor with only `LoadLibrary`/`GetProcAddress`, and check the section names for strange ones. Then conclude whether it is packed or not, and if so what kind, packer or protector.

After this you know what you're holding and can choose a tactic, for UPX, a single `upx -d` (lesson 14.2), for a custom packer, unpack manually to find the OEP, for a strong protector, decide whether it's worth it.

## Lab

The goal is to train your eye to recognize a packed file without unpacking it, using Detect It Easy (DIE). You need a few clean exes for comparison, such as `die.exe`, `dnSpy.exe`, or any system exe like notepad or calc, and a packed file to compare against. If you have UPX, make one yourself:

```
copy C:\Windows\System32\notepad.exe test.exe
upx test.exe
```

If you don't have UPX, any packed sample you already have in your learning environment works too.

Drag a clean exe into DIE and note what compiler it recognizes, how many sections there are and their names. Click the Entropy button on that clean file and look at the curve. What's the rough average value, and is there any block that's flat near 8.0? Then drag the packed file into DIE and see whether it recognizes a packer, and if so, which one. Click Entropy on the packed file and compare the chart with the clean one, noting where the compressed block sits and its entropy. Open the section view for both files and compare section names, section count, and permissions, specifically whether any section is both WRITE and EXECUTE. Finally open the import table for both and count the imported functions. Is the packed one noticeably poorer, and do you see `LoadLibraryA` and `GetProcAddress`?

A few questions to think through. Why does compressed data have entropy near 8.0 while ordinary code only sits around 5 to 6.5? If a file has high entropy but DIE doesn't recognize any packer, what does that tell you (the hint is a custom or encrypting packer with no public signature)? And why is the packed file's import table so poor when the original program calls plenty of APIs?

Do it yourself first, then open the solution below.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

A clean exe in DIE. For a clean exe from a standard compiler, DIE usually shows the linker (Microsoft Linker or GCC/MinGW), sometimes the compiler and tool too. The familiar sections are `.text` (code), `.rdata` (constants, strings, the IAT), `.data`, `.rsrc`, and sometimes `.reloc` and `.pdata`. All the names are the standard ones.

Entropy of the clean file. The entropy curve is jagged, with the `.text` code section around 6.0 to 6.5, data sections lower, and the resource region varying with its content. No block is flat near 8.0, and the average is usually under 6.5.

A packed file in DIE. With UPX, DIE recognizes it immediately and reports "UPX" with a version. With other packers, DIE shows the matching name if it has a signature. With a custom or self-encrypting packer, DIE might only report high entropy without naming anything, which is itself a clue (see the second question).

Entropy of the packed file. A flat, horizontal block appears right near the 8.0 level, which is the region holding the compressed original code. This is the clearest difference from the clean file. The stub (the code that decompresses things) has lower entropy because it's real, runnable code.

Comparing sections. The clean file has `.text`, `.rdata`, `.data`, `.rsrc` and so on with standard permissions (`.text` is R-X, `.data` is RW-). The UPX file has sections renamed to `UPX0` and `UPX1` (with `.rsrc` kept). `UPX0` usually has zero size on disk, since it only reserves memory space to hold the decompressed code, while `UPX1` holds the compressed data and the stub. The section that ends up holding the decompressed code is both WRITE and EXECUTE, which is suspicious.

The import table. The clean file has dozens to hundreds of functions from several DLLs (kernel32, user32, gdi32 and so on). The packed file has very few, often just kernel32 with `LoadLibraryA` and `GetProcAddress` plus a handful more. The reason is explained below.

On why compressed data has high entropy, compression removes redundancy and repetition, leaving a byte sequence that's distributed almost uniformly and randomly. Entropy measures that randomness, so it climbs close to the maximum of 8 bits per byte. Ordinary code has a lot of repeated patterns (commonly used opcodes, strings, alignment zero bytes), which keeps its entropy lower.

On high entropy with no packer name, it's likely a custom packer, a self-written one, or a separate encryption layer that DIE has no signature for. This comes up often with malware. In that case there's no `upx -d` shortcut, you have to unpack manually. Run it in a debugger, let the stub decompress itself, find the OEP and dump it (Lessons 14.2 and 14.3).

On the poor import table, the original code calls plenty of APIs, but those calls live inside the part that's compressed. While the file is still on disk, they don't exist yet as ordinary imports. The stub only needs `LoadLibraryA` and `GetProcAddress` so that once decompression finishes, it can load the needed DLLs itself and look up function addresses, rebuilding the IAT in memory. That's why rebuilding the IAT is its own separate step during unpacking (Lesson 14.3).

</details>

## Key takeaways
A packer compresses/encrypts the original code and adds a stub that unpacks it at runtime, so the real code only appears in memory at runtime, not on disk. The OEP (Original Entry Point) is where every unpack ends. Once you're there, the original code is ready in memory.

There are five signs of packing, which are entropy near 8.0, poor imports (LoadLibrary/GetProcAddress), strange section names, a section that's both writable and executable, and few strings. Use Detect It Easy for quick identification (signatures + entropy). Packers compress while protectors resist analysis (adding anti-debug/anti-VM/virtualization), so work out which one you have before deciding how much effort to spend.
