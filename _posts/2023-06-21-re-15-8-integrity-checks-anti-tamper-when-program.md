---
title: "Lesson 15.8: Integrity checks and anti-tamper"
image:
  path: /assets/img/covers/re-15-8-integrity-checks-anti-tamper-when-program.webp
  alt: "Lesson 15.8: Integrity checks and anti-tamper"
date: 2022-07-30 06:16:00 +0700
categories: ["Reverse Engineering", "Part 15 · Anti-Reversing and Bypasses"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
You find the license check, NOP a `jz`, save the file, run it again. Instead of "Correct!", the program quietly exits, or worse, runs wrong in some confusing way three functions later. Your patch wasn't wrong. The program checked its own code, saw that somebody had changed it, and reacted.

![Diagram of an integrity check and how to bypass it](/assets/img/re/re-15-8-integrity-checks-anti-tamper-when-program.svg)
_An integrity check compares a checksum, so patch the check and not the code_

That's an integrity check, also called a self-check or anti-tamper. This lesson covers how it works and how to deal with it. Patching more carefully won't help, you have to stop the check from running.

## The core idea

The program reads the bytes of its own code, computes a checksum (CRC32, or a hash), and compares it with a value embedded at build time. If they match, the code is intact. If not, someone edited it, and it reacts.

```c
uint32_t got = crc32(address_of_protected_function, size);
if (got != EXPECTED_CHECKSUM) {
    // code was modified
    exit(3);
}
```

`EXPECTED_CHECKSUM` is computed once at release and hard-coded into the binary. If you patch even a single byte in the checked region, the checksum changes, and `got != EXPECTED` becomes true.

The checked region is the compiled code (the instruction bytes), not the C logic. Changing one bit in an instruction is enough to break the checksum. In the lab that goes with this lesson, flipping one bit in the protected function does it:

```
Clean build:  checksum = 0xEE604937  -> "Correct!"
Flip 1 bit:   checksum = 0x245EBAA4  -> "Integrity check FAILED. Code was modified." (exits, exit 3)
```

Same correct input, but because the code was touched, the program refuses to run.

## Why patching directly always loses

A beginner's reflex is to patch more cleverly, for example NOP fewer bytes or change exactly one instruction. That doesn't work. The checksum doesn't care how much you changed, as long as one byte in the checked region is different it catches you. A careful patch doesn't beat a hash function.

It gets worse. Serious protectors scatter multiple layers of cross-checks, where function A checksums the region containing function B, and function B checksums the region containing function A and the license-check function. Disable one spot and another catches it. Some types don't exit right away but slowly corrupt data so that you think you patched wrong.

## The right approach: attack the check, not the code it guards

Instead of editing the guarded code, disable the check itself. There are three ways, from clean to dirty.

The first is to turn off the integrity-check function. The `verify_integrity` function usually doesn't check itself. So you overwrite its start with `mov eax, 1; ret` (bytes `B8 01 00 00 00 C3`), it always reports "intact", and then you patch the license logic freely. In the lab, after flipping a bit in the license function (the checksum is already broken), all you do is add this step:

```
Flip license bit + disable verify_integrity  ->  "Correct!" (exit 0)
```

The check function sits outside the self-checked region, so editing it doesn't break its own checksum.

The second is to patch the checksum comparison branch. If you don't want to touch the whole function, find the `cmp got, EXPECTED` followed by `jne fail` and invert or NOP that branch. The idea is the same, which is to make the comparison always "match".

The third is to patch in memory after the check has run. Let the program self-check at startup (the code on disk is intact so it passes), then use a debugger to edit the code in RAM after that point. The checksum has already run and nobody checks again. That's why runtime patching is sometimes easier than patching on disk, see [Lesson 17.1](/reverse-engineering/).

There's a fourth way that's rarely used, which is to recompute `EXPECTED` to match the patched code and overwrite the embedded value. It only works when you understand the checksum algorithm well and can find where the value is stored, and multiple cross-checking layers make it a pain.

## Where to find the integrity-check function

During static analysis, look for a function that reads its own code section, meaning a pointer into the `.text` region (the address of another function, or the image base) and then a loop over every byte. Look for a CRC loop too, with `xor`, `shr`, and a characteristic constant. CRC32 often exposes the polynomial `0xEDB88320`, see how to spot constants in [Lesson 16.1](/reverse-engineering/). Other signs are comparing the result against a hard-coded 32-bit constant and then branching to exit, and the function being called very early (in initialization, or a TLS callback, see [Lesson 15.4](/posts/re-15-4-advanced-anti-debug-self-debug-tls/)) or called repeatedly.

A dynamic tip is to set a read memory breakpoint on the code section, so you stop when some code reads memory inside its own `.text` region. A function that touches code for any reason other than executing it is very suspicious.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 15.8</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/15.8.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/15.8/src/selfcheck.c" download><i class="fa-solid fa-download"></i>src/selfcheck.c</a>
</div>
</div>

The goal is to see an integrity check catch a patch, then get past it by disabling the check function itself instead of patching the protected code more cleverly. The file `selfcheck.c` is a program that computes a CRC32 checksum over the byte range of `check_license` and compares it against an embedded value, refusing to run (exit 3) if they don't match.

The checksum depends on exactly what your compiler produces, so first capture the real value on your machine:

```sh
# 1. Build the print mode (flip MODE_PRINT to 1, or use sed)
sed 's/#define MODE_PRINT 0/#define MODE_PRINT 1/' selfcheck.c > sc_print.c
gcc -O0 -no-pie -fno-pic -o sc_print sc_print.c
./sc_print ANY          # prints: [build] checksum = 0x........ , size = ...

# 2. Paste that checksum into EXPECTED in selfcheck.c (replacing 0xDEADBEEF)
# 3. Build the real binary
gcc -O0 -no-pie -fno-pic -o sc_ok selfcheck.c
```

The `-no-pie -fno-pic` flags keep function addresses stable, which makes them easier to read in objdump and x64dbg.

Run the clean build first. `./sc_ok INTEGRITY_OK` should print "Correct!" and `./sc_ok WRONG` should print "Nope". The correct key is `INTEGRITY_OK`.

Next, patch the logic and watch the check catch it. Flip one bit somewhere inside `check_license`'s code range, simulating NOPing out a jump. Use `nm` to find `check_license`'s address, work out the file offset, flip one byte, and run it again. You should see it report "Integrity check FAILED" and exit with code 3, even when you type the correct key.

Then get past it by disabling the check function instead. Overwrite the start of `verify_integrity` with `mov eax, 1; ret` (bytes `B8 01 00 00 00 C3`). Since `verify_integrity` doesn't checksum itself, this patch doesn't break anything. Run the binary with both the license patch and this bypass in place, and it accepts the key, because the check no longer does anything.

Finally, think about what happens if the author adds a second function that checksums `verify_integrity` too. Would this same trick still work? What would you do next? As a hint, think about patching in RAM after every check has already run, or following the whole chain of checks back to its root.

A helper for finding the file offset is to use `nm <binary>` for the function's address, `objdump -h <binary>` for the VMA and file offset of `.text`, then `file_offset = addr - text_vma + text_file_offset`.

Do it yourself first, then check the full write-up with real run results below.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Everything below was actually run on Linux x86-64 (gcc 11, `-O0 -no-pie -fno-pic`).

Capturing the checksum and building:

```
$ gcc -O0 -no-pie -fno-pic -o sc_print sc_print.c   # MODE_PRINT=1
$ ./sc_print ANY
[build] checksum = 0xEE604937 , size = 51
```

The code range of `check_license` is 51 bytes, and the real checksum is `0xEE604937`. That gets pasted into `EXPECTED`, and then the real build `sc_ok` is produced with MODE_PRINT=0. This number depends on the compiler and build flags, so your machine may give a different value, just use your own.

Running the clean build:

```
$ ./sc_ok INTEGRITY_OK
Correct! License is valid.
$ ./sc_ok WRONG
Nope. Wrong key.
```

Patching the code and getting caught. Flipping one bit at the first byte of `check_license`'s range (the file offset computed from `nm` plus `objdump -h`):

```
check_license size = 51 bytes; patch file offset 0x1176
$ ./sc_patched INTEGRITY_OK
[!] Integrity check FAILED (0x245EBAA4 != 0xEE604937). The code was modified.
$ echo $?
3
```

The checksum changes from `0xEE604937` to `0x245EBAA4` from flipping a single bit. The program refuses to run even with the correct key, which is why patching the protected code directly fails.

Getting past it by disabling the check function. Overwriting the start of `verify_integrity` with `mov eax,1; ret`:

```
disabling verify_integrity at file offset 0x122b (mov eax,1; ret)
$ ./sc_bypass INTEGRITY_OK
Correct! License is valid.
$ echo $?
0
```

The binary still carries the patched, checksum-mismatched `check_license`, but `verify_integrity` now always returns 1, so nobody compares anything anymore. `verify_integrity` sits outside the range it checksums, so modifying it is safe. Attack the check, not the code it guards.

The patch bytes are `B8 01 00 00 00 C3`, which is:

```asm
mov eax, 1
ret
```

When there are multiple layers. If a second function checksums `verify_integrity` too, then as soon as you patch `verify_integrity`, that second layer catches it. At that point you either trace the whole chain of who checks whom and disable them starting from the outermost layer inward, or you leave the on-disk code untouched entirely, letting every check run and pass normally at startup, and then use a debugger to modify the code in RAM after that point, since the checksum has already run and won't run again. The principle stays the same, which is to find the moment or place where checking has already finished, and act after that.

</details>

## Key takeaways
An integrity check means the program checksums its own code and compares with an embedded value, which detects patches. Patching one byte in the checked region is enough to get caught, and a cleverer patch won't help.

Don't edit the guarded code. Disable the check function (mov eax,1; ret), or patch the comparison branch, or patch in RAM after the check has run. The check function rarely checks itself, and that's the weakness. You recognize it by reading its own .text, a CRC loop (constant 0xEDB88320), and comparing against a hard-coded constant and then exiting. Strong protectors scatter multiple cross-checking layers, so find them all before you call it done.
