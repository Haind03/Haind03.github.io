---
title: "Lesson 16.1: Identifying crypto algorithms by their constants"
date: 2023-12-01 14:52:00 +0700
categories: ["Technique Reverse", "Part 16 · Crypto and Algorithms"]
tags: [reverse-engineering, crypto]
render_with_liquid: false
---
Here's some good news for reversers: encryption algorithms are very hard to hide. Not because their code is easy to read, but because almost every standard algorithm carries a fixed set of constants (magic constants), and those numbers never change. Seeing `0x67452301` at the top of a function means you're almost certainly looking at MD5 or SHA-1. This lesson teaches how to use exactly these fingerprints to mark out the crypto in a few seconds instead of reading a thousand lines of bit-twiddling loops.

## Why constants are a reliable giveaway

An algorithm like SHA-256 is defined in the standard with fixed initial values and constant tables. Anyone who implements the standard correctly, whether in C, Rust or hand-written assembly, has to embed exactly those numbers in the binary. A compiler can rename variables, optimize loops, inline functions, but it can't change `0x6a09e667` into another number and still get the right result.

In other words: the logic can be twisted, the constants can't. That's why searching for constants is the fastest and surest way to recognize crypto, much surer than trying to understand the bit-shuffling loops.

## A set of fingerprints worth memorizing

You don't need to remember them all, but a few of these numbers show up constantly so it pays to know them by heart:

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

Notice the two groups. The group with clear constants (MD5, SHA, AES, TEA, CRC) gets caught by findcrypt right away. The group without constants (RC4, custom XOR, custom Base64) has to be recognized by pattern, which is for lesson 16.2.

## Let the tools do the boring part

You don't sit there probing each number by eye. There's a whole set of tools that scan for constants automatically. FindCrypt / findcrypt2 (an IDA plugin) scans the whole binary, marks every region matching a known algorithm signature, and prints a list with addresses, so one run gives you a crypto map. FindCrypt-Ghidra is the equivalent for Ghidra. capa (Mandiant) not only finds constants but infers high-level capabilities, for example "hash data via MD5" or "encrypt data using AES", which is very handy for quick triage. signsrch scans for algorithm signatures and some common implementation patterns and runs standalone outside IDA. And if you already have a yara rule set with crypto rules, scanning a batch of samples works too.

The real workflow is very tidy: open the binary, run findcrypt or capa first, and it shows you a few addresses, "AES here, CRC32 over there". You jump straight there instead of swimming in the rest.

## Confirm with structure, don't trust blindly

Findcrypt is very good but not magic. A constant table can match by coincidence, or a modified algorithm (for example AES with a substituted S-box, or CRC with a different polynomial) will make the tool misreport or miss. After the tool marks the region, always glance at the function structure to confirm.

AES has a loop of 10/12/14 rounds, each round with SubBytes (S-box lookup), ShiftRows, MixColumns (multiplication in GF(2^8)), and AddRoundKey (xor). Hashes (MD5/SHA) process in 64-byte blocks, with a compression loop containing many bit rotations and additions. CRC32 is a loop over each byte, xor then a 256-entry table lookup, or shifting bits 8 times. TEA/XTEA has a loop that accumulates the delta `0x9E3779B9` over 32 rounds, operating on two 32-bit halves.

When the constants match and the loop structure matches too, only then do you conclude for sure. If the constants match but the structure is odd, it's likely a custom variant, and that's the interesting place to dig deeper.

## When constants are hidden

Sophisticated malware sometimes doesn't leave constants bare. It may build the constant table at runtime (computing the S-box at runtime instead of embedding it), or xor the constants with a key and decode them at use. Then static findcrypt will miss. How to get past it: run dynamically, set a breakpoint after the init code and dump the memory region holding the table, then run findcrypt on the dump. At that point the constants show up in their true form in memory.

## Key takeaways
Standard crypto algorithms carry fixed constants, and the compiler can't change them. Know a few common numbers: MD5/SHA `0x67452301`, SHA-256 `0x6A09E667`, TEA delta `0x9E3779B9`, CRC32 `0xEDB88320`. Run findcrypt/capa/signsrch first to mark out the crypto instead of reading it by hand.

Always confirm with the loop structure, to avoid trusting a coincidental signature. If constants are built or decoded at runtime, dump the memory and scan again.
