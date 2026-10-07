---
title: "Lesson 16.1: Identifying crypto algorithms by their constants"
image:
  path: /assets/img/covers/re-16-1-identifying-crypto-algorithms-by-their-constants.webp
  alt: "Lesson 16.1: Identifying crypto algorithms by their constants"
date: 2023-07-03 21:32:00 +0700
categories: ["Technique Reverse", "Part 16 · Crypto and Algorithms"]
tags: [reverse-engineering, crypto]
render_with_liquid: false
---
Encryption algorithms are hard to hide. Almost every standard algorithm carries a fixed set of constants (magic constants), and those numbers never change. If you see `0x67452301` at the top of a function, you're almost certainly looking at MD5 or SHA-1. This lesson shows how to use these fingerprints to mark out the crypto in a few seconds instead of reading a thousand lines of bit-twiddling loops.

## Why constants are a reliable giveaway

An algorithm like SHA-256 is defined in the standard with fixed initial values and constant tables. Anyone who implements it correctly, in C, Rust or hand-written assembly, has to embed exactly those numbers in the binary. A compiler can rename variables, optimize loops and inline functions, but it can't change `0x6a09e667` into another number and still get the right result.

The logic can be twisted, the constants can't. So searching for constants is the fastest and surest way to recognize crypto, a lot surer than trying to understand the bit-shuffling loops.

## Fingerprints worth memorizing

You don't need to remember them all, but a few of these numbers show up constantly so it's worth knowing them:

| Algorithm | Characteristic constants |
|---|---|
| MD5 | Init: `0x67452301`, `0xEFCDAB89`, `0x98BADCFE`, `0x10325476` |
| SHA-1 | Same init as MD5's four numbers above, plus `0xC3D2E1F0` |
| SHA-256 | H init starts `0x6A09E667`; the K table starts `0x428A2F98` |
| TEA / XTEA | Delta `0x9E3779B9` (the golden constant, derived from the golden ratio) |
| CRC32 | Reflected polynomial `0xEDB88320`, or a 256-entry table built from it |
| AES | 256-byte S-box (starts `63 7C 77 7B F2 6B 6F C5...`) and Rcon `01 02 04 08 10 20 40 80 1B 36` |
| Blowfish | P-array and S-boxes initialized from the digits of pi |
| RC4 | No constants, recognized by the KSA pattern (a loop that initializes a 256-byte array and then permutes it) |

There are two groups here. The ones with clear constants (MD5, SHA, AES, TEA, CRC) get caught by findcrypt right away. The ones without constants (RC4, custom XOR, custom Base64) have to be recognized by pattern, which is lesson 16.2.

## Let the tools do the boring part

You don't need to check each number by eye. Several tools scan for constants automatically. FindCrypt / findcrypt2 (an IDA plugin) scans the whole binary, marks every region matching a known algorithm signature, and prints a list with addresses, so one run gives you a crypto map. FindCrypt-Ghidra is the equivalent for Ghidra. capa (Mandiant) not only finds constants but infers high-level capabilities, for example "hash data via MD5" or "encrypt data using AES", which is handy for quick triage. signsrch scans for algorithm signatures and some common implementation patterns and runs standalone outside IDA. And if you already have a yara rule set with crypto rules, scanning a batch of samples works too.

My usual routine: open the binary, run findcrypt or capa first, and it shows a few addresses, "AES here, CRC32 over there". Then I jump straight there instead of going through the rest.

## Confirm with structure

Findcrypt is very good but not perfect. A constant table can match by coincidence, and a modified algorithm (for example AES with a substituted S-box, or CRC with a different polynomial) will make the tool misreport or miss. After the tool marks the region, glance at the function structure to confirm.

AES has a loop of 10/12/14 rounds, each round with SubBytes (S-box lookup), ShiftRows, MixColumns (multiplication in GF(2^8)), and AddRoundKey (xor). Hashes (MD5/SHA) process in 64-byte blocks, with a compression loop containing many bit rotations and additions. CRC32 is a loop over each byte, xor then a 256-entry table lookup, or shifting bits 8 times. TEA/XTEA has a loop that accumulates the delta `0x9E3779B9` over 32 rounds, operating on two 32-bit halves.

When the constants match and the loop structure matches too, you can conclude it's that algorithm. If the constants match but the structure is odd, it's likely a custom variant, and that's worth digging into.

## When constants are hidden

Sophisticated malware sometimes doesn't leave constants in the open. It may build the constant table at runtime (computing the S-box at runtime instead of embedding it), or xor the constants with a key and decode them at use. Then static findcrypt will miss. To get past it, run dynamically, set a breakpoint after the init code and dump the memory region holding the table, then run findcrypt on the dump. The constants show up in their real form in memory.

## Lab

The task is to see the magic constants of crypto algorithms in a binary, and to use automatic tools to narrow down the region. The file `hashdemo.c` is a program that embeds the MD5 init values, MD5's T table, and the TEA delta. Build it on Linux with `gcc -O0 -o hashdemo hashdemo.c`, or on Windows with `gcc -O0 -o hashdemo.exe hashdemo.c` or `cl hashdemo.c`. For tools you can use Detect It Easy, IDA with FindCrypt, Ghidra with FindCrypt-Ghidra, or capa.

Build `hashdemo` and open it in IDA or Ghidra, then run FindCrypt (IDA) or FindCrypt-Ghidra and see which region it marks and which algorithm it names. Next search by hand: use a byte-sequence search for `01 23 45 67` (which is `0x67452301` in little-endian) and note which section it lands in. If you have capa, run `capa hashdemo` and see which capabilities it reports. Then open `tea_round` in the disassembly and check whether the constant `0x9E3779B9` appears intact, and if not, what the compiler turned it into. Finally, confirm that each constant you found matches an algorithm in the table of this lesson.

Two questions to think about. Why does `0x67452301` appear in the binary as the bytes `01 23 45 67` (hint: little-endian, Lesson 1.1)? And if a programmer changed the MD5 init values to other numbers (a "custom" MD5), could FindCrypt still catch it, and how else would you recognize it? Do it yourself before opening the solution.

<div class="lab-box">
<div class="lab-head"><b>LAB 16.1</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/16.1/src/hashdemo.c" download><i class="fa-solid fa-file-code"></i>src/hashdemo.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The figures below come from a real `gcc -O0` build on Linux x86-64.

### FindCrypt narrows the region

FindCrypt scans the binary and matches the `md5_state` and `md5_T` arrays against known MD5 signatures, reporting something like "MD5 initial values" and "MD5 T-table" with addresses in `.data` or `.rodata`. This is the fastest way: you know MD5 is there before reading a single line of code.

### Searching by hand

`0x67452301` is stored little-endian, so on disk it is the byte string `01 23 45 67`. Searching for it in the binary finds it in the initialized data region (the `md5_state` array). A Python check on the build confirms it:

```
MD5 0x67452301   -> FOUND at offset 0x3010 (.data region)
MD5 T0 0xd76aa478 -> FOUND at offset 0x1171 (embedded in .rodata/.text)
```

### capa

If you have capa, it usually reports a capability such as "hash data via MD5" or flags a reference to the MD5 constants, because capa has rules that recognize these init values. capa answers at the level of what the program does, rather than where the constants are.

### The TEA delta and compiler optimization

This is the most important lesson of the lab. In the source, `tea_round` adds `0x9E3779B9`:

```c
return sum + 0x9e3779b9u;
```

But the real disassembly is:

```asm
tea_round:
    ...
    mov    -0x4(%rbp),%eax
    sub    $0x61c88647,%eax      ; NOT add 0x9e3779b9
    ...
```

The compiler recognized that `+ 0x9E3779B9` is equivalent to `- 0x61C88647` (because `0x9E3779B9 = -0x61C88647` read as a signed 32-bit number, in two's complement: `0x100000000 - 0x9E3779B9 = 0x61C88647`). It chose a `sub` with the smaller constant. So searching for `B9 79 37 9E` as little-endian bytes in this code will MISS, because the constant has been transformed. FindCrypt still catches TEA in implementations that use the delta directly, but when it shows up as an optimized immediate you have to watch for the two's complement form `0x61C88647` as well. That's why you should confirm by structure and not only by byte strings.

### Matching the algorithms

The values `0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476` are MD5 (or SHA-1 if `0xC3D2E1F0` is also present). The table starting `0xD76AA478...` is MD5's T table. `0x9E3779B9` (or the form `0x61C88647`) is the TEA/XTEA delta.

### Answers to the questions

`0x67452301` becomes `01 23 45 67` because x86 is little-endian: the lowest byte is stored first (Lesson 1.1). If the MD5 init values were changed to other numbers, FindCrypt wouldn't match the standard signature and would miss it. You then recognize it by structure: a compression loop that processes 64-byte blocks, four state variables, many rotate and add operations, and four rounds of 16 steps. That structure is characteristic of MD5 even when the constants have been replaced, which is when confirming by structure saves you.

</details>

## Key takeaways
Standard crypto algorithms carry fixed constants, and the compiler can't change them. Know a few common numbers: MD5/SHA `0x67452301`, SHA-256 `0x6A09E667`, TEA delta `0x9E3779B9`, CRC32 `0xEDB88320`. Run findcrypt/capa/signsrch first to mark out the crypto instead of reading it by hand.

Confirm with the loop structure, so you don't trust a coincidental signature. If constants are built or decoded at runtime, dump the memory and scan again.
