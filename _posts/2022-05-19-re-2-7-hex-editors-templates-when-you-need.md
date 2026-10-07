---
title: "Lesson 2.7: Hex editors and templates, when you need to see every byte"
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

The exercises and writeup are at `labs/2.7/`. You'll use ImHex (or 010) to parse a PE file header with a pattern, patch a byte in a small file and observe the change, and write a pattern yourself for a simple file format.

## Key takeaways
A hex editor is for when you need to see and edit down to the byte: patching bytes, fixing magic/headers, reading unfamiliar formats. You can quickly recognize a file from its start: `4D 5A` is PE, `7F 45 4C 46` is ELF, `50 4B` is ZIP.

HxD is light for quick patching, ImHex is free and strong for reversers, and 010 Editor is strongest for templates but paid. Templates and patterns turn bare bytes into named, typed fields, which is the key to reading file structure, and ImHex's `@ offset` syntax lets you place a struct at an exact position, even one taken from another field.
