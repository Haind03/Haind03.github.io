---
title: "Lesson 18.7: Reversing network protocols and proprietary file formats"
image:
  path: /assets/img/covers/re-18-7-reversing-network-protocols-proprietary-file-formats.webp
  alt: "Lesson 18.7: Reversing network protocols and proprietary file formats"
date: 2023-09-22 10:37:00 +0700
categories: ["Technique Reverse", "Part 18 · Advanced Topics"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
Some problems don't live in a binary but in data, such as a save game file nobody has documented, a homemade network protocol between client and server, a binary config format. No spec, no documentation. Your job is to look at data samples and rebuild the spec, accurately enough to read the data yourself and produce valid data yourself.

There are two sources of information, and I use both, the data itself (comparing many samples), and the code that handles the data (following the parse function in the binary). The data gives quick hypotheses, and the code confirms them.

## Differential analysis: change one thing, see which byte changes

This is the strongest and easiest technique. You create several samples that differ in just one detail, then compare the hex to see which bytes change with it. The bytes that change are the field holding that detail.

Take a real example from the lab, a `.sav` save game format. Two files `save_alice.sav` and `save_rich.sav` differ only in the amount of gold (1500 versus 999999) and a flag. Compare the hex:

```
alice: 5341 5645 0200 0100 0700 0000 dc05 0000  SAVE............
rich:  5341 5645 0200 0300 0700 0000 3f42 0f00  SAVE............
                      ^^^^           ^^^^^^^^^
                      offset 6       offset 12
```

Two places differ, offset 6 (`0100` becomes `0300`) and offset 12 (`dc05 0000` becomes `3f42 0f00`). Gold 1500 = `0x05DC`, read little-endian it's `dc 05`, matching offset 12. Gold 999999 = `0x000F423F`, little-endian `3f 42 0f 00`, also matching. So offset 12 is the gold field as a little-endian u32. Offset 6 is a flag (alice didn't cheat, rich did). Two fields found without reading a line of code.

Do the same with `save_alice.sav` and `save_bob.sav` (differing only in name), and the changed bytes start at offset 18, and right before that there's a value giving the name length. That's how you find a length-prefix + string pair.

## Finding the magic and anchoring the structure

Almost every format starts with a fixed magic number for identification. Look at the first few bytes that are the same across all samples. In the example above, the four bytes `53 41 56 45` are the ASCII "SAVE". The magic is the anchor, and once you know it you can define the following offsets.

After the magic there's usually a version (a small number, often increasing across releases), then the fields. Separate fixed fields (the same in every sample) from variable fields (different), and among variable fields, tell numbers (little-endian on x86, read backwards, see [Lesson 1.1](/posts/re-1-1-reading-hexdump-like-text/) again) from strings (the ASCII column on the right reads as text).

## Three common patterns

When probing, you'll meet three patterns over and over. The first is the fixed field, always the same size, for example a u32 for level or a u16 for flags. It's the easiest. The second is the length-prefixed field, a length value followed by exactly that many bytes. Strings and arrays often use this. In the lab, `name_len` (u16) comes before the name, and `n_items` (u16) comes before the item list. A small number followed by exactly that many bytes of data is easy to recognize. The third is TLV (type-length-value) or repeated records, a block repeated many times, each with the same structure. An item list `(item_id u16, qty u16)` repeated `n_items` times is a simple form of it.

Very often at the end of the file there's a checksum (byte sum, CRC32, or a hash) so the program can detect a modified file. If you plan to create your own valid file, you have to recompute the checksum correctly, or the program rejects it. That's why a good parser always checks the checksum (in the lab, the last field is the sum of all preceding bytes mod 2^32).

## Tools for describing structure

Once you have a hypothesis, write it down as a template so a tool can parse and highlight it. With a 010 Editor Binary Template or an ImHex pattern (see [Lesson 2.7](/posts/re-2-7-hex-editors-templates-when-you-need/)), you declare a struct, the tool colors each field on the real file, and you see right away where it's wrong. Kaitai Struct lets you describe the format in a YAML file and generates parsers for many languages (Python, C++, Java...), which is good when the format is complex and you want a reusable parser.

Writing a small parser in Python with `struct.unpack` is the surest way to confirm the spec. If the parser reads every sample correctly and the checksums match, your spec is right. The lab has `parse_savefile.py` as a sample.

## Confirming with code: following the parse function

Comparing data gives hypotheses, but some ambiguities only code can answer, such as whether this field is signed or unsigned, is this number a length or an ID, which algorithm is the checksum computed with. Then open the binary that handles the file in IDA/Ghidra. Set a breakpoint at `CreateFile`/`fopen`/`ReadFile`/`fread` (see [Lesson 1.13](/posts/re-1-13-recognizing-windows-apis-when-reversing-reading/)) to catch the moment it reads the file, then follow the buffer. Find where the magic is compared (a `cmp` with a constant that looks like "SAVE" with its bytes reversed), which is the start of the parse function.

Reading on, you'll see it add offsets, read u16/u32, multiply lengths, and loop over records. Each read confirms a field in your spec. The checksum function reveals the real algorithm (a simple sum, or CRC with a 256-entry table, see [Lesson 16.1](/posts/re-16-1-identifying-crypto-algorithms-by-their-constants/)).

## Network protocols

A network protocol is just a data format moving over time. The difference is you capture it with Wireshark instead of opening a file. Capture the traffic between client and server and view each packet in hex. Then apply the same three patterns. Each message usually has a header (magic/version), a length field (the total length of the rest, extremely common so you know how far to read), then the payload. Find the length field by comparing the real packet length with the number in the header.

Use differential analysis here too by doing the same action in the app twice and compare the two packets. The differing parts are dynamic data (timestamp, session id, nonce) and the identical parts are the fixed frame.

If the payload looks like junk (high entropy), it's encrypted. Then follow the code in the binary by setting breakpoints at `send`/`WSASend` and `recv`, and going back up you'll see the encryption function running right before `send` (and decryption right after `recv`). Hook the right spot before encryption (or after decryption) with Frida ([Lesson 17.2](/posts/re-17-2-frida-full-inspecting-modifying-program-while/)) and you see the payload in the clear, with no need to break the algorithm.

The same technique is used for extracting configs and understanding malware C2 protocols, and comes back in [Lesson 19.4](/posts/re-19-4-extracting-config-c2-pulling-out-brain/).

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 18.7</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/18.7.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/18.7/src/make_savefile.py" download><i class="fa-solid fa-download"></i>src/make_savefile.py</a>
<a class="lab-file" href="/assets/labs/18.7/src/parse_savefile.py" download><i class="fa-solid fa-download"></i>src/parse_savefile.py</a>
<a class="lab-file" href="/assets/labs/18.7/src/save_alice.sav" download><i class="fa-solid fa-download"></i>src/save_alice.sav</a>
<a class="lab-file" href="/assets/labs/18.7/src/save_bob.sav" download><i class="fa-solid fa-download"></i>src/save_bob.sav</a>
<a class="lab-file" href="/assets/labs/18.7/src/save_rich.sav" download><i class="fa-solid fa-download"></i>src/save_rich.sav</a>
</div>
</div>

The goal is to take a few data samples, work out the structure of a proprietary file format yourself, and write a parser, without reading the spec first. You need `python3` (for the generator and the parser) and a hex editor (ImHex, 010 Editor, or the `xxd` command). Run the generator, which produces `save_alice.sav`, `save_bob.sav` and `save_rich.sav`:

```
python3 -I make_savefile.py
```

Treat `make_savefile.py` as a black box until you're done. The three samples are made to differ in just one detail each so that you can use differential analysis.

Hexdump all three files (`xxd save_alice.sav` and so on) and find the common magic number at the start. Compare `save_alice.sav` with `save_rich.sav`, which differ in the amount of gold and one flag. Which bytes change? Work out the offset and type of the gold field and the flags field, remembering little-endian. Then compare `save_alice.sav` with `save_bob.sav`, which differ only in the name. Find the length-prefix plus string pair, meaning where the length value sits and what offset the name starts at. After the name there is a repeated list of items, so find the field that counts the items and the structure of each item. Next, work out what the last four bytes are (the hint is to change one byte in the middle of the file and see whether it plays a verification role). Finally, write your own `my_parse.py` with `struct.unpack` that prints every field, and run it on all three samples. Compare the result with `parse_savefile.py`, the reference solution. If everything matches, your spec is right.

As an extension, write an ImHex pattern (`.hexpat`) that describes this format, so the tool colors each field when you open a `.sav` file (see Lesson 2.7 again). You can also edit the gold amount in a `.sav` file with a hex editor and then recompute the checksum so the file stays valid. That step is what turns "can read" into "can create".

Three questions to think about. Why is differential analysis (comparing several samples that differ in one detail) faster than guessing byte by byte? What if you have no generator to produce samples at will (the hint is to work inside the program that produces the file, changing one value each time)? And when are you forced to open the binary and read the parse function instead of just looking at the data?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Every hexdump and value below is real output from `make_savefile.py` and `parse_savefile.py` run with Python 3.11.9. The three samples in xxd form:

```
save_alice.sav (37 bytes):
00000000: 5341 5645 0200 0100 0700 0000 dc05 0000  SAVE............
00000010: 0500 616c 6963 6502 0065 0003 00cd 0001  ..alice..e......
00000020: 0055 0500 00                             .U...

save_bob.sav (35 bytes):
00000000: 5341 5645 0200 0100 0700 0000 dc05 0000  SAVE............
00000010: 0300 626f 6202 0065 0003 00cd 0001 0088  ..bob..e........
00000020: 0400 00                                  ...

save_rich.sav (37 bytes):
00000000: 5341 5645 0200 0300 0700 0000 3f42 0f00  SAVE........?B..
00000010: 0500 616c 6963 6502 0065 0003 00cd 0001  ..alice..e......
00000020: 0006 0500 00                             .....
```

The first four bytes of every sample are `53 41 56 45`, ASCII "SAVE". That's the magic, the anchor for all the offsets that follow.

For gold and flags, the differential between alice and rich shows two differences. At offset 6 it's `0100` (alice) versus `0300` (rich). That's the flags u16, where alice is 0b01 (hardcore) and rich is 0b11 (hardcore plus cheats_used). At offset 12 it's `dc05 0000` versus `3f42 0f00`. In little-endian that's `0x000005DC` = 1500 for alice and `0x000F423F` = 999999 for rich, so offset 12 is the gold, a little-endian u32.

For the name, alice and bob differ from offset 16 onward. At offset 16 it's `0500` (alice) versus `0300` (bob), which in little-endian is 5 and 3, exactly the lengths of "alice" and "bob". That's name_len, a u16. At offset 18 the ASCII string begins, and `61 6c 69 63 65` is "alice" and `62 6f 62` is "bob". The string isn't null-terminated, and its length comes from name_len. Because bob is 2 characters shorter, the bob file is exactly 2 bytes smaller (35 versus 37).

Right after the name (for alice, offset 18+5 = 23) comes the item list. `0200` is n_items = 2 (u16). Item 1 is `6500 0300`, item_id 0x65 = 101 with qty 3. Item 2 is `cd00 0100`, item_id 0xCD = 205 with qty 1. Each item is `(item_id u16, qty u16)`, repeated n_items times.

The last four bytes are a u32 checksum, the sum of every preceding byte mod 2^32. The real values are alice = 1365 (`55 05 00 00`), bob = 1160 (`88 04 00 00`) and rich = 1286 (`06 05 00 00`). The reference parser checks `checksum_ok` and all three are True. Changing a byte in the middle of the file without updating the checksum makes `checksum_ok` False, which is how a program detects a tampered file.

The parser results are:

```
save_alice.sav -> {'version': 2, 'flags': 1, 'level': 7, 'gold': 1500, 'name': 'alice', 'items': [(101, 3), (205, 1)], 'checksum': 1365, 'checksum_ok': True}
save_bob.sav   -> {'version': 2, 'flags': 1, 'level': 7, 'gold': 1500, 'name': 'bob',   'items': [(101, 3), (205, 1)], 'checksum': 1160, 'checksum_ok': True}
save_rich.sav  -> {'version': 2, 'flags': 3, 'level': 7, 'gold': 999999,'name': 'alice', 'items': [(101, 3), (205, 1)], 'checksum': 1286, 'checksum_ok': True}
```

The complete spec is:

```
offset 0  : magic      4 bytes  "SAVE"
offset 4  : version    u16  (=2)
offset 6  : flags      u16  (bit0 hardcore, bit1 cheats_used)
offset 8  : level      u32
offset 12 : gold       u32
offset 16 : name_len   u16
offset 18 : name       name_len bytes of ASCII, not null-terminated
next      : n_items    u16
each item : item_id u16 + qty u16   (repeated n_items times)
file end  : checksum   u32  = sum(every preceding byte) mod 2^32
```

A reference ImHex pattern:

```c
#pragma endian little
struct Item { u16 item_id; u16 qty; };
struct Save {
    char magic[4];
    u16 version;
    u16 flags;
    u32 level;
    u32 gold;
    u16 name_len;
    char name[name_len];
    u16 n_items;
    Item items[n_items];
    u32 checksum;
};
Save save @ 0x00;
```

On the reflection questions, differential analysis is faster because it isolates each field. Instead of guessing the meaning of 37 bytes, you only look at the 2 to 4 bytes that change with exactly the detail you just altered, and every new sample pins down one more field. Without a generator, work inside the program that produces the file (play a game and save with different gold amounts, or send the same network command twice), changing one variable at a time and saving a sample each time. You have to open the binary when the data can't answer the question, such as whether a field is signed or unsigned, whether a number is a length or an ID, and the specific checksum or encryption algorithm. The parse function and the checksum function in the binary are the final source of truth.

</details>

## Key takeaways
Differential analysis comes first, which means creating samples that differ in one detail, and the bytes that change are that field. Every format anchors on a magic number at the start, so find it first. There are three common patterns, fixed field, length-prefixed (a length number then data), and repeated records/TLV.

Multi-byte numbers are read little-endian (bytes reversed) and strings are read directly in the ASCII column. A checksum at the end means that to create valid data you have to recompute it correctly. Data gives hypotheses, and code (the parse function, the send/recv functions) confirms the ambiguous details. A network protocol is a format over time, so use Wireshark + differential analysis, and for encrypted payloads hook around send/recv.
