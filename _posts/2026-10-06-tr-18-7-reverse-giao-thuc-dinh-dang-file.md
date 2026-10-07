---
title: "Lesson 18.7: Reversing network protocols and proprietary file formats"
date: 2026-10-06 09:53:00 +0700
categories: ["Technique Reverse", "Part 18 · Advanced Topics"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
There's a kind of problem that doesn't live in a binary but in data: a save game file nobody has documented, a homemade network protocol between client and server, a binary config format. No spec, no documentation. Your job is to look at the data samples and rebuild that spec, accurately enough to read it yourself and produce valid data yourself. This lesson is how to do that.

There are two sources of information, and good people use both: **the data itself** (comparing many samples), and **the code that handles the data** (following the parse function in the binary). The data gives you quick hypotheses, the code confirms them.

## The differential principle: change one thing, see which byte jumps

This is the strongest and easiest technique. You create several samples that differ in just one detail, then compare the hex to see which bytes change with it. The byte that changes is the field holding that detail.

Take a real example from the lab: a `.sav` save game format. Two files `save_alice.sav` and `save_rich.sav` differ only in the amount of gold (1500 versus 999999) and a flag. Compare the hex:

```
alice: 5341 5645 0200 0100 0700 0000 dc05 0000  SAVE............
rich:  5341 5645 0200 0300 0700 0000 3f42 0f00  SAVE............
                      ^^^^           ^^^^^^^^^
                      offset 6       offset 12
```

Two places differ: offset 6 (`0100` becomes `0300`) and offset 12 (`dc05 0000` becomes `3f42 0f00`). Gold 1500 = `0x05DC`, read little-endian it's `dc 05`, matching offset 12. Gold 999999 = `0x000F423F`, little-endian `3f 42 0f 00`, also matching. So offset 12 is the gold field as a little-endian u32. Offset 6 is a flag (alice didn't cheat, rich did). You just found two fields without reading a single line of code.

Do the same with `save_alice.sav` and `save_bob.sav` (differing only in name): the changed bytes start at offset 18, and right before that there's a value giving the name length. That's how you discover the length-prefix + string pair.

## Finding the magic and anchoring the structure

Almost every format starts with a fixed magic number for identification. Look at the first few bytes that are the same across all samples and you've got it. In the example above, the four bytes `53 41 56 45` are the ASCII "SAVE". The magic is the anchor: once you know it you can define the following offsets.

After the magic there's usually a version (a small number, often increasing across releases), then the fields. Separate fixed fields (the same in every sample) from variable fields (different), and among variable fields, tell numbers (little-endian on x86, read backwards, see [Lesson 1.1](/posts/tr-1-1-hex-endian-bitwise/) again) from strings (the ASCII column on the right reads out as text).

## Three common patterns

When probing, you'll meet three molds over and over:

- **Fixed field**: always the same size, for example a u32 for level, a u16 for flags. The easiest.
- **Length-prefixed**: a length value followed by exactly that many bytes. Strings and arrays often use this. In the lab, `name_len` (u16) comes before the name, and `n_items` (u16) comes before the item list. Seeing a small number followed by exactly that many bytes of data is instantly recognizable.
- **TLV (type-length-value)** or repeated records: a block repeated many times, each with the same structure. An item list `(item_id u16, qty u16)` repeated `n_items` times is a simple form of it.

And very often at the end of the file there's a **checksum** (byte sum, CRC32, or a hash) so the program can detect a modified file. If you plan to create your own valid file, you have to recompute the checksum correctly, or the program rejects it. This is why a good parser always checks the checksum (in the lab, the last field is the sum of all preceding bytes mod 2^32).

## Tools for describing structure

Once you have a hypothesis, write it down as a template so a tool can parse and highlight it:

- **010 Editor Binary Template** and **ImHex pattern** (see [Lesson 2.7](/posts/tr-2-7-hex-editor-template/)): you declare a struct, the tool colors each field on the real file, and you see where it's wrong immediately.
- **Kaitai Struct**: describe the format in a YAML file, and it generates parsers for many languages (Python, C++, Java...). Good when the format is complex and you want a reusable parser.

Finally, writing a small parser in Python with `struct.unpack` is the surest way to confirm the spec: if the parser reads every sample correctly and the checksums match, your spec is right. The lab has `parse_savefile.py` as a sample.

## Confirming with code: following the parse function

Comparing data gives hypotheses, but some ambiguities only code can answer: is this field signed or unsigned, is this number a length or an ID, which algorithm is the checksum computed with. Then open the binary that handles the file in IDA/Ghidra:

- Set a breakpoint at `CreateFile`/`fopen`/`ReadFile`/`fread` (see [Lesson 1.13](/posts/tr-1-13-nhan-dien-windows-api/)) to catch the moment it reads the file, then follow the buffer.
- Find where the magic is compared (a `cmp` with a constant that looks like "SAVE" with its bytes reversed), that's the start of the parse function.
- Reading on you'll see it add offsets, read u16/u32, multiply lengths, loop over records. Each read confirms a field in your spec.
- The checksum function reveals the real algorithm (a simple sum, or CRC with a 256-entry table, connecting to [Lesson 16.1](/posts/tr-16-1-nhan-dien-hang-so-crypto/)).

## Network protocols: same thinking, plus Wireshark

A network protocol is just a data format moving through time. The difference is you capture it with **Wireshark** instead of opening a file:

- Capture the traffic between client and server, view each packet in hex.
- Apply the same three patterns: each message usually has a header (magic/version), a length field (the total length of the rest, extremely common so you know how far to read), then the payload. Find the length field by comparing the real packet length with the number in the header.
- Use differential: do the same action in the app twice, compare the two packets, the differing parts are dynamic data (timestamp, session id, nonce), the identical parts are the fixed frame.
- If the payload looks like junk (high entropy), it's encrypted. At this point follow the code in the binary: set breakpoints at `send`/`WSASend` and `recv`, and going back up you'll see the encryption function running right before `send` (and decryption right after `recv`). Hook the right spot before encryption (or after decryption) with Frida ([Lesson 17.2](/posts/tr-17-2-frida-toan-tap/)) and you see the payload in the clear, no need to break the algorithm.

This technique is the foundation of extracting configs and understanding malware C2 protocols, and will be used again in [Lesson 19.4](/posts/tr-19-4-trich-config-c2/).

## Lab

The folder [`labs/18.7/`](https://github.com/Haind03/Technique-Reverse/tree/main/labs/18.7). You'll run `make_savefile.py` to create three `.sav` files that differ in one detail each, use differential on the hexdump to work out the structure yourself, write your own parser, then compare with `parse_savefile.py`. There's also a part on building an ImHex pattern.

## Key takeaways
- Differential is weapon number one: create samples that differ in one detail, the byte that changes is that field.
- Every format anchors on a magic number at the start, find it first.
- Three common molds: fixed field, length-prefixed (a length number then data), repeated records/TLV.
- Multi-byte numbers are read little-endian (bytes reversed), strings read directly in the ASCII column.
- Checksum at the end: to create valid data you have to recompute it correctly.
- Data gives hypotheses, code (parse function, send/recv functions) confirms the ambiguous details.
- A network protocol is a format over time: Wireshark + differential, and for encrypted payloads hook around send/recv.
