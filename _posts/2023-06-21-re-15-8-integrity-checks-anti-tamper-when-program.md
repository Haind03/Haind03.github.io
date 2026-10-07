---
title: "Lesson 15.8: Integrity checks and anti-tamper, when the program knows you patched it"
date: 2023-06-21 10:25:00 +0700
categories: ["Technique Reverse", "Part 15 · Anti-Reversing and Bypasses"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
You find the license check, NOP a `jz`, save the file, run it again. Instead of "Correct!", the program quietly exits, or worse, runs wrong in some baffling way three functions later. You did nothing wrong in the patch step. The problem is that the program just touched its own code, saw that somebody had messed with it, and sulked.

That's an integrity check, also called a self-check or anti-tamper. This lesson covers how it works and why the right way to deal with it isn't to patch more carefully, it's to stop it from checking.

## The core idea

The program reads the bytes of its own code, computes a checksum (CRC32, or a hash), and compares it with a value embedded at build time. If they match, the code is intact. If not, someone edited it, and it reacts.

```c
uint32_t got = crc32(address_of_protected_function, size);
if (got != EXPECTED_CHECKSUM) {
    // code was modified
    exit(3);
}
```

`EXPECTED_CHECKSUM` is computed once at release and hard-coded into the binary. When you patch even a single byte in the checked region, the checksum changes, and `got != EXPECTED` becomes true.

An important point: the checked region is the compiled code (the instruction bytes), not the C logic. Changing one bit in an instruction is enough to break the checksum. In the lab that goes with this lesson, flipping just one bit in the protected function does it:

```
Clean build:  checksum = 0xEE604937  -> "Correct!"
Flip 1 bit:   checksum = 0x245EBAA4  -> "Integrity check FAILED. Code was modified." (exits, exit 3)
```

Same correct input, but because the code was touched, the program refuses to run.

## Why patching directly always loses

A beginner's reflex is to patch more cleverly: NOP fewer bytes, change exactly one instruction. Useless. The checksum doesn't care how much you changed or how cleverly, as long as one byte in the checked region is different it gives you away. You can't beat a hash function with a delicate patch.

Worse, serious protectors scatter multiple layers of cross-checks: function A checksums the region containing function B, and function B checksums the region containing function A and the license-check function. Disable one spot and another catches it. Some types don't exit right away but slowly corrupt data so that you think you patched wrong.

## The right approach: attack the guard, don't edit the door

The principle: instead of editing the guarded code, disable the guard itself. There are three ways, from clean to dirty.

The first is to turn off the integrity-check function. The `verify_integrity` function usually doesn't check itself (who guards the guard?). So you overwrite its start with `mov eax, 1; ret` (bytes `B8 01 00 00 00 C3`), it always reports "intact", and then you patch the license logic freely. In the lab, after flipping a bit in the license function (the checksum is already broken), all you do is add this step:

```
Flip license bit + disable verify_integrity  ->  "Correct!" (exit 0)
```

The check function sits outside the self-checked region, so editing it doesn't break its own checksum. The guard sleeps, the door is wide open.

The second is to patch the checksum comparison branch. If you don't want to touch the whole function, find the `cmp got, EXPECTED` followed by `jne fail` and invert/NOP that branch. Same idea: make the comparison result always "match".

The third is to patch in memory after the check has run. Let the program self-check at startup (the code on disk is intact so it passes), then use a debugger to edit the code in RAM after that point. The checksum has already run, nobody checks again. This is why runtime patching is sometimes easier than patching on disk, tying back to [Lesson 17.1](/technique-reverse/).

There's a fourth way that's rarely used: recompute `EXPECTED` to match the patched code and overwrite the embedded value. It's only feasible when you understand the checksum algorithm well and can find where the value is stored, and multiple cross-checking layers make it a pain.

## Where to find the integrity-check function

During static analysis, look for a function that reads its own code section: a pointer pointing into the `.text` region (the address of another function, or the image base) and then looping over every byte. Look for a CRC loop too, with `xor`, `shr`, and a characteristic constant. CRC32 often exposes the polynomial `0xEDB88320`, tying back to how to spot constants in [Lesson 16.1](/technique-reverse/). Other signs are comparing the result against a hard-coded 32-bit constant and then branching to exit, and the function being called very early (in initialization, or a TLS callback, see [Lesson 15.4](/posts/re-15-4-advanced-anti-debug-self-debug-tls/)) or called repeatedly many times.

A dynamic tip: set a breakpoint for when some code reads memory inside its own `.text` region (a read memory breakpoint on the code section). Any function that touches code for a reason other than executing it is very suspicious.

## Key takeaways
An integrity check means the program checksums its own code and compares with an embedded value, detecting patches. Patching one byte in the checked region is enough to give you away, and a cleverer patch won't save you.

Don't edit the guarded code. Disable the check function (mov eax,1; ret), or patch the comparison branch, or patch in RAM after the check has run. The check function rarely checks itself, and that's the weakness to exploit. You recognize it by reading its own .text, a CRC loop (constant 0xEDB88320), and comparing against a hard-coded constant and then exiting. Strong protectors scatter multiple cross-checking layers, so find them all before celebrating.
