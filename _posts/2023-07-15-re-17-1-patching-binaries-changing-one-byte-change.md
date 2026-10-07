---
title: "Lesson 17.1: Patching binaries"
image:
  path: /assets/img/covers/re-17-1-patching-binaries-changing-one-byte-change.webp
  alt: "Lesson 17.1: Patching binaries"
date: 2023-07-15 23:12:00 +0700
categories: ["Technique Reverse", "Part 17 · Patching, Hooking, Injection"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
Reversing to understand is one thing, but often you want the program to behave differently, such as to skip an annoying check, turn off a message, make a branch always run. Patching means editing a few bytes of the binary directly. It's usually just changing a `74` byte to `90`. This lesson shows exactly that, on a real binary.

A reminder of the boundary from [Lesson 0.2](/posts/re-0-2-legal-ethics-part-everyone-wants-skip/) is that patching your own crackmes, CTF binaries or software you have the right to is fine. Patching and then distributing a crack of commercial software is illegal.

## Two kinds of patch

Almost every patch you'll make is one of two kinds.

The first is changing a conditional jump. Remember from [Lesson 1.3](/posts/re-1-3-x86-x64-assembly-1-registers-instructions/) that a `cmp`/`test` pair followed by `j*` is an `if` statement. To change the outcome you edit the jump instruction itself. A few short-jump opcodes (1 byte operand) you see often:

| Instruction | Opcode | Meaning |
|---|---|---|
| `je` / `jz` | `74` | jump if equal / ZF=1 |
| `jne` / `jnz` | `75` | jump if not equal / ZF=0 |
| `jmp` short | `EB` | unconditional jump |

There are three ways to edit a jump. Change `74` to `75` (or the reverse), which inverts the condition so whichever branch was running swaps to the other. Change `74` to `EB`, which turns the conditional jump into an always-jump. Or overwrite `74 xx` with `90 90`, a NOP that deletes the jump so the program always falls through to the branch right after.

The second is NOPing an instruction. `90` is the opcode of `nop` (no operation), which does nothing. To disable an instruction (a `call` that checks the license, an annoying assignment) without shifting the addresses of other instructions, you overwrite it with exactly that many `90` bytes. A 5-byte `call` gets replaced by five `90`s.

Count the bytes carefully when you NOP. However many bytes the old instruction was, cover it with that many `90`s, no more and no less. Miss one byte and the tail of the old instruction becomes a junk instruction, everything after it is misaligned, and the program crashes.

## Patching a crackme

Take the crackme `patchme` (`patchme.c`, in the Lab section below). It compares the password to `s3cr3t`. Here's `main` after `objdump -d -M intel` (real output from a gcc build on Linux):

```asm
4011f2:  e8 7f ff ff ff   call  401176 <check>   ; call the check function, result in eax
4011f7:  85 c0            test  eax, eax         ; eax == 0 (wrong)?
4011f9:  74 16            je    401211           ; if wrong, jump to the "Wrong" branch
4011fb:  48 8d 05 ...     lea   rax, [rip+0xe1e] ; the "Correct! Access granted." branch
401205:  e8 56 fe ff ff   call  401060 <puts>
...
401211:  48 8d 05 ...     lea   rax, [rip+0xe21] ; the "Wrong password." branch
```

`check` returns 0 when wrong, then `test eax,eax` and `je` jump to `401211` and print "Wrong". With the right password eax is non-zero, `je` doesn't jump, and it falls through to `4011fb` and prints "Correct".

To make the program always say Correct, the `je` at `4011f9` must never jump. The cleanest way is to NOP it. The two bytes `74 16` become `90 90`.

Find the location on disk. The bytes right before it are `85 c0` (test eax,eax), so the pattern to search for is `85 c0 74 16`. In this file it's at file offset 0x11f7, so the `74` byte is at 0x11f9. Change those two bytes to `90 90`:

```
before:  85 c0 74 16 ...
after:   85 c0 90 90 ...
```

A real run of the patched build, entering a wrong password:

```
$ ./patchme_patched baisai
Correct! Access granted.
```

A program that used to reject every wrong password now accepts them all. The whole change was two bytes.

## Patching on disk vs at runtime

What we just did is patching on disk. You edit the file, the change is permanent and still there the next run. The tools are a hex editor (HxD, ImHex) if you know the offset, or x64dbg (edit in the CPU window with the Space key, then menu Patches > Patch file to write out a new file).

Runtime patching edits bytes in memory while debugging, and it only lasts for that session. I use it to quickly try a change without touching the file, or when the code is decrypted or unpacked at runtime so it isn't on disk to edit. In x64dbg, select the instruction and press Space to reassemble in place.

The offset relationship matters here. The address you see in the debugger is a virtual address (for example `0x4011f9`), while on disk it's a file offset (`0x11f9` in the example above). For a PE/ELF loaded at the default base without ASLR, the difference is a constant per section. x64dbg and IDA convert it for you, but when editing by hand in a hex editor you need to compute the file offset correctly (converting RVA to file offset is covered in [Lesson 1.7](/posts/re-1-7-pe-format-anatomy-windows-exe/)).

## Code cave

The patches above only change a few existing bytes. If you need to insert extra code (say a new calculation) and there isn't enough space, use a code cave, which is a region of empty `00` bytes already in the binary (often at the end of a section because of alignment).

The process is to find a cave big enough (x64dbg has a plugin for finding caves, or you can scan for a long run of `00` in an executable section), then write your new code into it. At the spot you want to change, put a `jmp` to the cave in place of the original instruction, and remember to copy the overwritten original instruction into the cave so it still runs. At the end of the cave, `jmp` back to right after the inserted spot.

A cave lets you go from "can only edit in place" to "insert any code", but you have to be careful with jump addresses.

## Common mistakes

Instruction size mismatch is the first. NOPing too few or too many bytes breaks things, so always check how many bytes the old instruction is before overwriting. Integrity checks are the second. Many programs checksum their own code (see [Lesson 15.8](/posts/re-15-8-integrity-checks-anti-tamper-when-program/)), so if you patch the code and run again it detects the change and exits. Don't edit the checked code, disable the check function itself instead.

Relocation and ASLR come next. If you insert an absolute address in a code cave, check whether the binary has relocations, otherwise the address will be wrong when the base changes. And then there's patching the wrong place. The same `74` byte shows up thousands of times in a file, so always locate by context (the preceding bytes, e.g. `85 c0 74`) and don't edit blindly.

## Patch or keygen?

There are two ways past a serial check, and you pick by the kind of challenge. A patch fits when the program only asks right or wrong once, and you NOP the check, or invert the jump. It's fast and needs no understanding of the algorithm, but you have to distribute the modified build, and it's fragile if there's an integrity check. A keygen fits when the serial is generated by an algorithm from the username (see [Lesson 3.6](/posts/re-3-6-writing-keygen-when-fishing-out-serial/)). You understand the algorithm and generate valid serials yourself without touching the binary. That's cleaner, but you need to understand the logic well.

Beginners tend to patch everything. I'd pick whichever fits the challenge.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 17.1</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/17.1.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/17.1/src/patchme.c" download><i class="fa-solid fa-download"></i>src/patchme.c</a>
</div>
</div>

The goal is to turn `patchme`, which rejects every wrong password, into a program that accepts every password, by patching exactly one jump instruction. Do it both ways, on disk with a hex editor, and at runtime in x64dbg. Build it with one of these:

```
# Linux
gcc -O0 -no-pie -fno-stack-protector patchme.c -o patchme

# Windows (MinGW)
x86_64-w64-mingw32-gcc -O0 patchme.c -o patchme.exe

# Windows (MSVC)
cl /Od patchme.c
```

Try it first:

```
./patchme s3cr3t     -> Correct! Access granted.
./patchme wrong      -> Wrong password.
```

Open the binary in IDA or Ghidra (or use `objdump -d -M intel patchme`). Find `main` and locate the `test eax, eax` and `je` pair right after `call check`, which is the `if` that decides Correct versus Wrong. Work out the opcode of that `je` (it should be `74`) and its operand byte.

To patch on disk, use a hex editor (HxD or ImHex) or Python to find the byte sequence `85 c0 74` (test eax,eax; je) and change `74 xx` into `90 90`. Save to a new file, run it with a wrong password and confirm it prints "Correct". To patch at runtime, open the binary in x64dbg, set a breakpoint on the `je`, run to it, press Space to change the `je` into `nop nop` (or into a `jmp` to the Correct branch), continue and confirm. Then try something different and, instead of a NOP, change the `je` (`74`) into `jne` (`75`) and watch the behavior invert, so the right password is rejected, and work out why.

Three questions to think about. Why does NOPing the `je` make the program always say Correct while switching to `jne` inverts it? If `patchme` computed a checksum of `main` and compared it (an integrity check), would an on-disk patch still work, and what would you do differently? And can this kind of patch produce a valid serial, and when are you forced to write a keygen instead of patching?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The numbers below are real, taken from a gcc build on Linux (`gcc -O0 -no-pie -fno-stack-protector`). The exact offsets can differ a little with the compiler and flags, but the method is the same.

To locate the check, `objdump -d -M intel patchme` shows this in `main`:

```asm
4011f2:  e8 7f ff ff ff   call  401176 <check>
4011f7:  85 c0            test  eax, eax
4011f9:  74 16            je    401211 <main+0x6b>   ; jump to the "Wrong" branch
4011fb:  48 8d 05 ...     lea   rax, ...             ; the "Correct! Access granted." branch
...
401211:  48 8d 05 ...     lea   rax, ...             ; the "Wrong password." branch
```

`check` returns 0 when the password is wrong. `test eax,eax` sets ZF=1 when eax=0, and then `je` jumps to `401211` and prints "Wrong". With the right password eax is non-zero, `je` doesn't jump, and execution falls through to `4011fb` and prints "Correct".

For the on-disk patch, the pattern to search for is `85 c0 74 16` (test eax,eax; je). In this file it sits at file offset 0x11f7, so the `je` byte (`74`) is at 0x11f9. Patch it with Python (equivalent to editing in HxD or ImHex):

```python
f = open('patchme_patched', 'r+b')
f.seek(0x11f9)
print(f.read(2).hex())   # -> 7416   (je 0x16)
f.seek(0x11f9)
f.write(b'\x90\x90')     # NOP NOP
f.close()
```

The result of a real run with a wrong password:

```
$ ./patchme_patched wrongpw
Correct! Access granted.
```

The `je` is gone, so the program always falls into the Correct branch.

For the runtime patch in x64dbg, open `patchme.exe` and press F9 to reach the entry. Press Ctrl+G to go to `main` and set a breakpoint on the `je` after `test eax,eax`. Run with F9, enter a wrong password and stop at the `je`. Select the `je` instruction, press Space and type `nop` (x64dbg fills in both NOP bytes), or type the address of the Correct branch to turn it into a `jmp`. Press F9 to continue and you see "Correct! Access granted.". To keep it permanently, use the Patches menu (Ctrl+P) and then Patch File.

Changing `74` to `75` (jne) inverts the logic. With a wrong password (eax=0, ZF=1) the `jne` doesn't jump and falls into the Correct branch, while with the right password (eax non-zero) the `jne` jumps to the Wrong branch. So that patch accepts only wrong passwords and rejects the right one. It helps for understanding the mechanism, but NOP is what you want if you need to accept everything.

On the questions. NOP removes the jump entirely, so execution always falls into the Correct branch regardless of ZF, which is "accept everything". Switching to `jne` only flips the condition, so whichever branch was running becomes the other one, and the behavior is inverted and not always Correct. With an integrity check, a direct code patch no longer works because the program checksums `main` (or the code section), sees the changed bytes, the checksum is wrong and it exits (see [Lesson 15.8](/posts/re-15-8-integrity-checks-anti-tamper-when-program/)). The way around it is to find and disable the `verify_integrity` function itself (patch it to always return "ok") instead of changing the code it checks, or to patch in RAM after the check has already run. And a patch doesn't generate a serial, it only makes the binary stop checking and gives you no valid serial. When the goal is a real serial (for example to activate on another machine that you can't patch, or because a CTF task asks you to submit the correct serial), you have to understand the algorithm and write a keygen (see [Lesson 3.6](/posts/re-3-6-writing-keygen-when-fishing-out-serial/)). Patching and keygens serve two different needs.

</details>

## Key takeaways
`74`=je, `75`=jne, `EB`=jmp, `90`=nop. Remember these four and you can patch most simple checks. There are three ways to edit a jump, which are to invert it (74<->75), always jump (->EB), or delete it (->90 90). A NOP must cover exactly the number of bytes of the old instruction, no more and no less.

Locate the patch spot by byte context and don't edit by a single value. Disk patches are permanent while runtime patches only live in the debug session, and a code cave lets you insert extra code when there isn't enough room in place. If you meet an integrity check, disable the check function and don't edit the code it checks.
