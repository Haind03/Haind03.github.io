---
title: "Lesson 17.1: Patching binaries, changing one byte to change the program's fate"
date: 2023-12-06 22:03:00 +0700
categories: ["Technique Reverse", "Part 17 · Patching, Hooking, Injection"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
Reversing to understand is one thing, but a lot of the time you want the program to behave differently: skip an annoying check, turn off a message, make a branch always run. Patching means directly editing a few bytes of the binary to do that. It sounds grand but it's usually just changing a `74` byte to `90`. This lesson shows you exactly that, on a real binary.

A reminder of the boundary from [Lesson 0.2](/posts/re-0-2-legal-ethics-part-everyone-wants-skip/): patching your own crackmes, CTF binaries, or software you have the right to is fine. Patching and then distributing a crack of commercial software is illegal.

## Two foundational pairs of techniques

Almost every patch you'll ever make falls into one of two groups.

The first is changing a conditional jump. Remember from [Lesson 1.3](/posts/re-1-3-x86-x64-assembly-1-registers-instructions/) that a `cmp`/`test` pair followed by `j*` is just an `if` statement. To change the outcome of that `if`, you edit the jump instruction itself. A few short-jump opcodes (1 byte operand) you see often:

| Instruction | Opcode | Meaning |
|---|---|---|
| `je` / `jz` | `74` | jump if equal / ZF=1 |
| `jne` / `jnz` | `75` | jump if not equal / ZF=0 |
| `jmp` short | `EB` | unconditional jump |

There are three ways to edit a jump. You can change `74` to `75` (or the reverse), which inverts the condition so whichever branch was running swaps to the other. You can change `74` to `EB`, which turns the conditional jump into an always-jump. Or you can overwrite `74 xx` with `90 90`, a NOP that deletes the jump entirely so the program always falls through to the branch right after.

The second is NOPing an instruction. `90` is the opcode of `nop` (no operation), which does nothing. To disable an instruction (a `call` that checks the license, an annoying assignment) without shifting the addresses of other instructions, you overwrite it with exactly that many `90` bytes. A 5-byte `call` gets replaced by five `90`s.

The golden rule of NOPing is to count the bytes correctly. However many bytes the old instruction was, you cover it with that many `90`s, no more and no less. Miss one byte and the tail of the old instruction turns into a junk instruction, everything after it is misaligned, and the program crashes right away.

## For real: patching a crackme

Take the crackme `patchme` in [labs/17.1](https://github.com/Haind03/Technique-Reverse/blob/main/labs/17.1). It compares the password to `s3cr3t`. Here's `main` after `objdump -d -M intel` (real output from a gcc build on Linux):

```asm
4011f2:  e8 7f ff ff ff   call  401176 <check>   ; call the check function, result in eax
4011f7:  85 c0            test  eax, eax         ; eax == 0 (wrong)?
4011f9:  74 16            je    401211           ; if wrong, jump to the "Wrong" branch
4011fb:  48 8d 05 ...     lea   rax, [rip+0xe1e] ; the "Correct! Access granted." branch
401205:  e8 56 fe ff ff   call  401060 <puts>
...
401211:  48 8d 05 ...     lea   rax, [rip+0xe21] ; the "Wrong password." branch
```

The logic is clear: `check` returns 0 when wrong, `test eax,eax` then `je` jumps to `401211` and prints "Wrong". With the right password eax is non-zero, `je` doesn't jump, and it falls through to `4011fb` and prints "Correct".

To make the program always say Correct, we need the `je` at `4011f9` to never jump. The cleanest way is to NOP it. The two bytes `74 16` become `90 90`.

Find the location on disk. The bytes right before it are `85 c0` (test eax,eax), so the pattern to search for is `85 c0 74 16`. In this file it's at file offset 0x11f7, meaning the `74` byte is at 0x11f9. Change those two bytes to `90 90`:

```
before:  85 c0 74 16 ...
after:   85 c0 90 90 ...
```

Result of a real run on the patched build, entering a wrong password:

```
$ ./patchme_patched baisai
Correct! Access granted.
```

A program that used to reject every wrong password now accepts them all. The entire change was two bytes.

## Patching on disk vs patching at runtime

What we just did was patching on disk: edit the file, the change is permanent and still there the next run. The tools are a hex editor (HxD, ImHex) if you know the offset, or x64dbg (edit in the CPU window with the Space key, then menu Patches > Patch file to write out a new file).

Runtime patching is editing bytes in memory while debugging, and it only lives for that session. Use it when you want to quickly try a change without touching the file, or when the code is decrypted/unpacked at runtime so it isn't on disk to edit. In x64dbg, select the instruction and press Space to reassemble in place.

The offset relationship matters here. The address you see in the debugger is a virtual address (for example `0x4011f9`), while on disk it's a file offset (`0x11f9` in the example above). For a PE/ELF loaded at the default base without ASLR, the difference is a per-section constant. x64dbg and IDA convert it for you, but when editing by hand in a hex editor you have to compute the file offset correctly (a reminder of how to convert RVA to file offset is in [Lesson 1.7](/posts/re-1-7-pe-format-anatomy-windows-exe/)).

## Code cave: when there isn't enough room in place

Patches like the above can only change a few existing bytes. If you need to insert extra code (say a new calculation) and there isn't enough space there, use a code cave: a region of empty `00` bytes already in the binary (often at the end of a section due to alignment).

The process goes like this. Find a cave big enough (x64dbg has a plugin for finding caves, or scan for a long run of `00` in an executable section yourself), then write your new code into it. At the spot you want to intervene, put a `jmp` to the cave in place of the original instruction, and remember to copy the overwritten original instruction into the cave so it still runs. At the end of the cave, `jmp` back to right after the inserted spot.

A cave turns the limit of "can only edit in place" into "insert arbitrary code", at the price of having to be careful with jump addresses.

## Classic stumbles

Instruction size mismatch is the first. As said, NOPing too few or too many bytes breaks it, so always check how many bytes the old instruction is before overwriting. Integrity checks are the second: many programs checksum their own code (see [Lesson 15.8](/posts/re-15-8-integrity-checks-anti-tamper-when-program/)), so if you patch the code and run again it detects it and exits. The way to handle it is to not edit the checked code and disable the check function itself instead.

Relocation and ASLR come next. If you insert an absolute address in a code cave, pay attention to whether the binary has relocations, otherwise the address will be wrong when the base changes. And then there's patching the wrong place. The same `74` byte shows up thousands of times in a file, so always locate by context (the preceding bytes, e.g. `85 c0 74`) and don't just edit blindly.

## Patch or keygen?

There are two roads to get past a serial check, and you pick by the nature of the challenge. A patch fits when the program only asks right/wrong once: NOP the check, or invert the jump. It's fast and needs no understanding of the algorithm, but you have to distribute the modified build, and it's fragile if there's an integrity check. A keygen fits when the serial is generated by an algorithm from the username (see [Lesson 3.6](/posts/re-3-6-writing-keygen-when-fishing-out-serial/)): you understand the algorithm and generate valid serials yourself, without touching the binary. That's cleaner, but needs a deep understanding of the logic.

Beginners patch, good people pick the tool to fit the challenge.

## Key takeaways
`74`=je, `75`=jne, `EB`=jmp, `90`=nop. Remember these four and you can patch most simple checks. There are three ways to edit a jump: invert it (74<->75), always jump (->EB), or delete it (->90 90). A NOP must cover exactly the number of bytes of the old instruction, no more and no less.

Locate the patch spot by byte context and don't edit by a single value. Disk patches are permanent while runtime patches only live in the debug session, and a code cave lets you insert extra code when there isn't enough room in place. On meeting an integrity check, disable the check function and don't edit the code it checks.
