---
title: "Lesson 15.8: Integrity checks and anti-tamper, when the program knows you patched it"
image:
  path: /assets/img/covers/re-15-8-integrity-checks-anti-tamper-when-program.webp
  alt: "Lesson 15.8: Integrity checks and anti-tamper, when the program knows you patched it"
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

## Lab

The goal is to see with your own eyes an integrity check catching a patch, then get past it by disabling the check function itself rather than trying to patch the protected code more cleverly. The file `selfcheck.c` is a program that computes a CRC32 checksum over the byte range of `check_license` and compares it against an embedded value, refusing to run (exit 3) if they don't match.

Since the checksum depends on exactly what your compiler produces, you first need to capture the real value on your machine:

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

Run the clean build first: `./sc_ok INTEGRITY_OK` should print "Correct!" and `./sc_ok WRONG` should print "Nope". The correct key is `INTEGRITY_OK`.

Next, patch the logic and watch the check catch it. Flip one bit somewhere inside `check_license`'s code range, simulating NOPing out a jump. Use `nm` to find `check_license`'s address, work out the file offset, flip one byte, and run it again. You should see it report "Integrity check FAILED" and exit with code 3, even when you type the correct key.

Then get past it by disabling the check function instead. Overwrite the start of `verify_integrity` with `mov eax, 1; ret` (bytes `B8 01 00 00 00 C3`). Since `verify_integrity` doesn't checksum itself, this patch doesn't break anything. Running the binary with both the license patch and this bypass in place, it now accepts the key, because the guard has been put to sleep.

Finally, think about what happens if the author adds a second function that checksums `verify_integrity` too. Would this same trick still work? What would you do next? As a hint, think about patching in RAM after every check has already run, or chasing the whole chain of checks back to its root.

A helper for finding the file offset: use `nm <binary>` for the function's address, `objdump -h <binary>` for the VMA and file offset of `.text`, then `file_offset = addr - text_vma + text_file_offset`.

Do it yourself first, then check the full write-up with real run results below.

<div class="lab-box">
<div class="lab-head"><b>LAB 15.8</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/15.8/src/selfcheck.c" download><i class="fa-solid fa-file-code"></i>src/selfcheck.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Everything below was actually run on Linux x86-64 (gcc 11, `-O0 -no-pie -fno-pic`).

Capturing the checksum and building:

```
$ gcc -O0 -no-pie -fno-pic -o sc_print sc_print.c   # MODE_PRINT=1
$ ./sc_print ANY
[build] checksum = 0xEE604937 , size = 51
```

The code range of `check_license` is 51 bytes, and the real checksum is `0xEE604937`. That gets pasted into `EXPECTED`, and then the real build `sc_ok` is produced with MODE_PRINT=0. Note that this number depends on the compiler and build flags, so your machine may give a different value, just use your own.

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

The checksum changes from `0xEE604937` to `0x245EBAA4` from flipping a single bit. The program refuses to run even with the correct key, which is exactly why patching the protected code directly fails.

Getting past it by disabling the check function. Overwriting the start of `verify_integrity` with `mov eax,1; ret`:

```
disabling verify_integrity at file offset 0x122b (mov eax,1; ret)
$ ./sc_bypass INTEGRITY_OK
Correct! License is valid.
$ echo $?
0
```

The binary still carries the patched, checksum-mismatched `check_license`, but `verify_integrity` now always returns 1, so nobody compares anything anymore. `verify_integrity` sits outside the range it checksums, so modifying it is safe. The core lesson is to attack the guard, not the door.

The patch bytes are `B8 01 00 00 00 C3`, which is:

```asm
mov eax, 1
ret
```

When there are multiple layers. If a second function checksums `verify_integrity` too, then as soon as you patch `verify_integrity`, that second layer catches it. At that point you either trace the whole chain of who checks whom and disable them starting from the outermost layer inward, or you leave the on-disk code untouched entirely, letting every check run and pass normally at startup, and then use a debugger to modify the code in RAM after that point, since the checksum has already run and won't run again. The underlying principle stays the same: find the moment or place where checking has already finished, and act after that.

</details>

## Key takeaways
An integrity check means the program checksums its own code and compares with an embedded value, detecting patches. Patching one byte in the checked region is enough to give you away, and a cleverer patch won't save you.

Don't edit the guarded code. Disable the check function (mov eax,1; ret), or patch the comparison branch, or patch in RAM after the check has run. The check function rarely checks itself, and that's the weakness to exploit. You recognize it by reading its own .text, a CRC loop (constant 0xEDB88320), and comparing against a hard-coded constant and then exiting. Strong protectors scatter multiple cross-checking layers, so find them all before celebrating.
