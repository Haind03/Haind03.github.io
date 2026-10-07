---
title: "Lesson 2.7: Hex editors and templates, when you need to see every byte"
image:
  path: /assets/img/covers/re-2-7-hex-editors-templates-when-you-need.webp
  alt: "Lesson 2.7: Hex editors and templates, when you need to see every byte"
date: 2022-05-19 09:48:00 +0700
categories: ["Technique Reverse", "Part 02 · The Toolkit"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
A disassembler gives you a view at the instruction level, a debugger gives you a view at runtime. But sometimes you just want to crack a file open and look straight at every byte: fix a broken magic number, patch one byte to get past a check, or read some weird file format nobody wrote a parser for. That's when a hex editor speaks up. It's the crudest scalpel in the toolkit but also the most honest one.

This lesson won't teach you every button of the three programs. It only tells you when you need a hex editor, which one to pick, and most importantly the template/pattern concept that turns a pile of bytes into a readable structure.

## When you really need a hex editor

Most of the time you won't open a hex editor, because IDA and x64dbg already have their own hex windows. But there are a few situations where a standalone hex editor is much faster and tidier.

One is patching bytes directly in a file. You found in the debugger that a `jne` (opcode `75`) needs to become `je` (opcode `74`), and now you want to edit the file on disk directly so the patch lasts. Open the hex editor, jump to the offset, type over it, save. Done. Patch details are in [Lesson 17.1](/technique-reverse/).

Another is fixing a magic number or header, when a file has a few corrupted bytes at the start or someone deliberately changed the magic to hide the file type, and you restore it by hand. A third is reading a file format nobody knows, like a binary config file, a save game, or a homemade container. With no parser, you work out the structure yourself through hex. And the last is quickly checking a file: what are the first four bytes? `4D 5A` is PE, `7F 45 4C 46` is ELF, `50 4B` is ZIP. Often a glance at the start of the file is all you need.

## Three options, pick by need

### HxD, light and good enough

HxD is a free Windows hex editor, light and quick to open. It does the basics well: view, edit bytes, search for hex or text strings, compare two files, and open disks and process memory too. If you only need to patch a few bytes or quickly look at a file, HxD is enough and there's nothing more to think about. Weakness: it doesn't understand structure, to it everything is just bytes.

### 010 Editor, the king of Binary Templates

010 Editor is commercial software (with a trial version), and what makes it worth the money is Binary Template. This is a standout feature. Instead of looking at bare bytes, you run a template (a script describing the file's structure) and 010 breaks the file into fields with names, types, and colors. A PE file becomes a tree of the DOS header, NT headers, section table, with each field's value clearly shown. The community has written templates for hundreds of formats (PE, ELF, ZIP, PNG, PCAP...), so you download one and run it.

If your work often involves reading file structures, 010 saves hours of manual byte hunting.

### ImHex, built for reversers and free

ImHex is an open source hex editor, born for RE people. It has nearly all the nice things of 010 without the cost. Its pattern language is equivalent to Binary Template, describing file structure with C-like syntax. Its data inspector shows, when you put the cursor on a byte, the value if interpreted as u8/u16/u32, float, or time, in both little and big endian, which is extremely handy for guessing data types. It also has a built-in disassembler, an entropy graph, views in many encodings, a node interface for processing data, and a store of ready-made patterns you can download in the app.

For beginners who don't want to spend money, ImHex is the best default choice. The rest of this lesson uses ImHex as the example.

## Template/pattern: turning bytes into structure

This is the most important idea in the lesson. A binary file is really typed fields laid out one after another: a 4-byte number here, a string there, an array of structs behind it. The naked eye looking at hex has a hard time separating them. A template is how you tell the tool about that layout, and then it colors and labels things for you.

Take the start of a PE file as an example. The PE standard begins with a DOS header, in which two important fields are the magic `MZ` at offset 0 and `e_lfanew` at offset 0x3C (pointing to the NT headers). With ImHex's pattern language, you describe it like this:

```c
// Trimmed-down ImHex pattern for the start of a PE
struct DosHeader {
    char     magic[2];   // must be "MZ"
    u8       rest[58];    // skip the middle part
    u32      e_lfanew;    // offset to the NT headers
};

struct NtHeaders {
    char     signature[4];   // "PE\0\0"
    u16      machine;        // 0x8664 = x64, 0x14C = x86
    u16      numberOfSections;
};

DosHeader dos @ 0x00;              // place DosHeader at offset 0
NtHeaders nt  @ dos.e_lfanew;      // place NtHeaders at the offset that e_lfanew points to
```

Run this pattern on an `.exe` file and ImHex shows `dos.magic = "MZ"`, `dos.e_lfanew = 0x100` (say), then jumps there and reads `nt.signature = "PE"`, `nt.machine = 0x8664`. You just read the architecture and the number of sections without counting bytes by hand. The `@ address` syntax is the charm of the pattern language: you place a struct at an exact offset, even an offset taken from another field.

Once you get this idea, you apply it to every format: write a pattern yourself for a save game, a binary config file, and the tool takes it apart for you. This is exactly the first step of reversing file formats, the topic of [Lesson 18.7](/technique-reverse/).

## Quick comparison of the three tools

| | HxD | 010 Editor | ImHex |
|---|---|---|---|
| Price | free | commercial | free, open source |
| Platform | Windows | cross-platform | cross-platform |
| Template/pattern | none | Binary Template (strong, lots ready-made) | Pattern language (strong, free) |
| Data inspector | basic | yes | very good |
| Disasm/entropy | none | partial | yes |
| Good for | quick byte patching | professional structure reading | reversers in general, beginners |

Short advice: install HxD for quick patches, install ImHex as your main tool. You only need 010 when you work a lot with file formats and want its huge library of templates.

## Lab

This lab gets you used to working at the byte level, parsing a file structure with a pattern, and patching one byte on purpose. The tool is ImHex (preferred, free) or 010 Editor, and HxD works for the byte patching task. You need any PE file to look at, for example a small exe you already have, or one you build yourself from `target.c`. The second task also needs a file called `mini.bin`, which you create yourself. To build the target with MinGW on Windows:

```
x86_64-w64-mingw32-gcc target.c -o target.exe
```

or with MSVC:

```
cl target.c
```

For the first task, parse a PE header with a pattern. Open a `.exe` in ImHex and look at the first 16 bytes. Confirm the first two bytes are `4D 5A` ("MZ"). Go to offset `0x3C` and read the little-endian `u32` there. That is `e_lfanew`, the offset to the NT headers. Jump to that offset and confirm the four bytes `50 45 00 00` ("PE\0\0"). Then open the ImHex pattern editor, paste the pattern from `pe_header.hexpat`, run it, and compare the fields (`machine`, `numberOfSections`) with what you read by hand. Is your file x86 (machine `0x14C`) or x64 (`0x8664`), and how many sections does it have?

For the second task, patch a byte and watch the effect. Create `mini.bin` containing exactly the text `PASS=0`: open the hex editor, type in the ASCII bytes of the string (`50 41 53 53 3D 30`) and save. Open it again, find the last byte `30` ('0'), change it to `31` ('1') and save. Open the file in a plain text viewer such as Notepad and confirm it now reads `PASS=1`. This is a miniature version of byte patching: find the right offset, change the right value, save.

For the third task, write a pattern for a homemade format. Suppose a score file has this layout:

```
offset 0: u32 magic = 0x53434F52  ("SCOR" as a number)
offset 4: u16 version
offset 6: u16 count
offset 8: an array of count elements, each consisting of:
             char name[8]
             u32 score
```

Write an ImHex pattern that describes it, using `pe_header.hexpat` as a reference for the `struct` and `@` syntax. Then create a sample file with exactly this layout and run the pattern to check that it splits the file correctly.

<div class="lab-box">
<div class="lab-head"><b>LAB 2.7</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/2.7/pe_header.hexpat" download><i class="fa-solid fa-file-code"></i>pe_header.hexpat</a>
<a class="lab-file" href="/assets/labs/2.7/target.c" download><i class="fa-solid fa-file-code"></i>target.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Do everything before reading this. For the first task, these are the fixed bytes you should see. At offset `0x00`, `4D 5A` is "MZ", the magic of the DOS header, and every PE starts like this. At offset `0x3C` there is a little-endian `u32` that is `e_lfanew`. If you read `C0 00 00 00` the value is `0x000000C0`, remembering to reverse the bytes because of little-endian (see [Lesson 1.1](/posts/re-1-1-reading-hexdump-like-text/)). Jump to offset `0xC0` and the four bytes `50 45 00 00` are "PE\0\0", the signature of the NT headers. Right after the signature comes `machine` (u16): `4C 01` read backwards is `0x014C` (x86), and `64 86` read backwards is `0x8664` (x64). The next two bytes are `numberOfSections`.

When you run `pe_header.hexpat`, ImHex shows these fields already decoded, and you only compare them with the numbers you read by hand. If they match, you understand both the manual reading and what the pattern does for you. A sample answer for a typical x64 exe is machine = `0x8664`, so x64, and `numberOfSections` is usually 5 to 7 depending on the compiler. The nice point to take away is that `e_lfanew` is a pointer inside the file. The pattern uses `NtHeaders nt @ dos.e_lfanew;` to place the struct at exactly that offset, which is why a pattern is stronger than staring at raw hex.

For the second task, `PASS=0` in hex is `50 41 53 53 3D 30`. The last byte `30` is the character '0' (in the ASCII table of [Lesson 1.1](/posts/re-1-1-reading-hexdump-like-text/), '0' = 0x30). Change `30` to `31`, save, and Notepad shows `PASS=1`. Changing exactly one byte at the right offset is enough to change behavior. When you patch a jump in a real exe the principle is identical, except that you change an opcode (for example `75` to `74` to turn `jne` into `je`) instead of an ASCII character.

For the third task the pattern is:

```c
#pragma endian little

struct Entry {
    char name[8];
    u32  score;
};

struct ScoreFile {
    u32  magic;     // expected 0x53434F52
    u16  version;
    u16  count;
    Entry entries[count];   // array length comes from the count read above
};

ScoreFile file @ 0x00;
```

The key point is that `Entry entries[count];` uses the `count` field it just read to know how long the array is. That is the real power of a pattern language: it handles structures of dynamic length, something that is almost impossible to separate by eye in raw hex. To make the sample file, write `52 4F 43 53` (which is 0x53434F52 with its bytes reversed) at the start, then the version, the count, and `count` entries. Run the pattern and ImHex lists each entry with its name and score decoded.

Two pitfalls come up often. One is forgetting endianness: the magic `0x53434F52` written to a little-endian file lies as `52 4F 43 53`, and getting the order wrong means the magic won't match. The other is miscounting the length of `name`, since being off by one byte shifts the whole array that follows.

</details>

## Key takeaways
A hex editor is for when you need to see and edit down to the byte: patching bytes, fixing magic/headers, reading unfamiliar formats. You can quickly recognize a file from its start: `4D 5A` is PE, `7F 45 4C 46` is ELF, `50 4B` is ZIP.

HxD is light for quick patching, ImHex is free and strong for reversers, and 010 Editor is strongest for templates but paid. Templates and patterns turn bare bytes into named, typed fields, which is the key to reading file structure, and ImHex's `@ offset` syntax lets you place a struct at an exact position, even one taken from another field.
