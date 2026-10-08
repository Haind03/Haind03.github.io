---
title: "Lesson 15.6: Anti-disassembly"
image:
  path: /assets/img/covers/re-15-6-anti-disassembly-when-disassembler-itself-gets.webp
  alt: "Lesson 15.6: Anti-disassembly"
date: 2023-06-09 14:05:00 +0700
categories: ["Reverse Engineering", "Part 15 · Anti-Reversing and Bypasses"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
The earlier anti-debug lessons were about getting past the debugger at runtime. This one targets the static step, making IDA, Ghidra or objdump decode many wrong instructions the moment you open the file, while the CPU still runs the code correctly. You read the pseudocode, think it's the real logic, and it turns out to be garbage. Once you know these tricks you stop trusting the disassembler's output blindly.

Every trick rests on one fact, that x86 has variable-length instructions, so a byte can be the start of one instruction and also the middle of another. Fool the disassembler about where an instruction begins and everything after it is decoded wrong.

## Two ways to disassemble, two weak points

To break a disassembler you need to know how it works. There are two strategies.

The first is linear sweep, which decodes from start to end, so when one instruction ends the next byte starts the next. objdump does this by default. Its weak point is that when data is mixed into the code, it keeps decoding the data as instructions, and everything is wrong from there on. The second is recursive descent (recursive traversal), which follows the control flow and jumps to the target at a `jmp`/`jcc`/`call`. IDA and Ghidra work this way, so they're smarter. Their weak point is that if they guess the jump target wrong, or are fooled into thinking a branch can be reached when it can't, they decode wrong too.

Anti-disassembly exploits those two weak points.

## Junk bytes after an unconditional jump

The most classic trick. After a `jmp` (or a `jcc` whose condition is always true) there's a junk byte. The CPU jumps away and never touches that byte. But a linear sweep disassembler keeps decoding it as an instruction, and since the junk byte is often the opcode that opens a multi-byte instruction, it swallows some of the real bytes after it and shifts everything.

A common example:

```
EB 01        jmp short +1      ; jumps to the byte right after 0xE8
E8           db 0xE8           ; junk byte: CALL opcode, swallows the next 4 bytes
...the real instruction starts here
```

`EB 01` means jump to the current position plus 1, i.e. skip exactly one `E8` byte. The CPU never executes `E8`. But the disassembler sees `E8`, thinks it's `call rel32`, eats 4 more address bytes, and the real instruction is torn in half. In IDA this stretch shows up messy, sometimes highlighted red.

## Overlapping instructions

This is the neatest trick technically. The same byte sequence read from two different starting points gives two completely different instruction sequences. The author arranges it so the disassembler starts at spot A (giving a harmless instruction), while the CPU actually jumps into spot B in the middle of an instruction (giving a different one).

The classic example with the bytes `EB FF C0 48`:

```
Read from the start:
  EB FF        jmp short -1     ; looks like a jump backward
But the CPU jumps into the 2nd byte:
  FF C0        inc eax
  48 ...       (next instruction)
```

The disassembler locks onto the first reading and misses the `inc eax` the CPU actually runs. The byte `FF` is both the tail of `jmp short -1` (EB FF) and the head of `inc eax` (FF C0).

## push + ret instead of jmp

One way to hide the jump target from recursive descent. Instead of `jmp target` (where the target is visible for the disassembler to follow), people do:

```
push target_address
ret
```

`ret` takes the value on top of the stack as the return address and jumps there. It's identical to `jmp target`, but the disassembler sees `ret`, thinks the function ended and stops following the flow, not knowing it actually jumps to `target`. A variant is `call` plus modifying the return address on the stack.

## Opaque predicates creating dead branches

A condition whose result is always fixed (for example `x*x >= 0` is always true), but the compiler/disassembler can't prove it, so it has to assume both branches might be reached. The author puts junk code, or code that shifts decoding, into the branch that never runs, and you waste effort reading a dead branch. This was covered in [Lesson 14.4](/posts/re-14-4-code-level-obfuscation-when-program-flow/). I mention it here because it also counts as anti-disassembly when the dead branch contains bytes that shift the decoding.

## Self-modifying code (SMC)

Code that modifies itself at runtime. On disk (and in IDA's static view) that stretch is a meaningless or encrypted byte sequence. Only at runtime does a stub overwrite it with real instructions and then execute them. Statically you see garbage, because the real code doesn't exist yet. Signs include a loop that writes into the `.text` region (which should only be read and executed), or a section that is both writable and executable (W+X). With SMC, static analysis is almost helpless. You have to run dynamically until after it has modified itself and only then dump it to read. This is also the core mechanism of packers ([Lesson 14.1](/posts/re-14-1-packers-work-spot-one/)).

## How to handle it

Anti-disassembly makes the static step hard, but the CPU still has to run correctly, so the dynamic step always gives you the truth.

Running dynamically is the final referee. Open it in x64dbg and single-step through the suspicious stretch, and you see exactly the flow the CPU takes and the instructions it executes, no matter what IDA draws. In IDA, press `U` (undefine) on the wrongly decoded stretch, then put the cursor at the exact spot where the real instruction starts (taken from the dynamic step) and press `C` (make code), and IDA decodes again from the right point. For a junk byte after a `jmp`, overwrite it with `0x90` (`nop`) so the disassembler decodes cleanly again. The CPU never runs that byte, so patching it is harmless.

Watch for red-highlighted areas and nonsensical instructions, since IDA marks spots it isn't sure about. A `jmp short -1`, a `call` into the middle of nowhere, or a run of `db` mixed into running code are all flags for anti-disassembly. And when you recognize `push addr; ret`, follow the addr target yourself instead of believing the function ended.

When pseudocode looks abnormally chaotic in the middle of an otherwise normal function, don't blame yourself for reading badly. Suspect the disassembler is being fooled, and double check by running it dynamically.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 15.6</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/15.6.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/15.6/src/overlap_demo.asm" download><i class="fa-solid fa-download"></i>src/overlap_demo.asm</a>
</div>
</div>

The goal is to train your eye to spot junk bytes and overlapping instructions, and to work out the real CPU flow instead of trusting the disassembler's first pass. The file `overlap_demo.asm` holds two byte sequences with comments. This is a hand-reading exercise, nothing to build. If you want to try it in a real tool, you can paste the bytes into a binary file and open it in IDA or Ghidra, or use an online disassembler.

For the first sequence, `EB 01 E8 B8 2A 00 00 00 C3`, decode it by hand the way a linear sweep would, and write down the wrong instruction sequence you get. Then compute the target of `jmp short +1` and write out the real CPU flow. What value does this function return? Which byte is junk, meaning the CPU never touches it, and if you patch it to `0x90` (nop), does the disassembler now decode it correctly?

For the second sequence, `31 C0 EB FF C0 48 FF C0 C3`, decode it from the start and see what instructions you get. Where does `EB FF` point to? Decode again starting from that byte and find the two instructions the disassembler missed. What is the real return value?

In IDA, describe the steps you'd take to fix the display, including which key undefines the wrong decoding and which key makes code at the correct offset.

Two questions to think about. Why does running it dynamically (single-stepping in x64dbg) always give the correct flow even when IDA draws it wrong? And between linear sweep and recursive descent, which is more easily fooled by an overlapping instruction, and why?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This is a byte-reading exercise, so the values below come from analyzing the x86 opcodes directly, with no build or run needed. You can confirm them with any disassembler.

The junk byte sequence, `EB 01 E8 B8 2A 00 00 00 C3`. A linear sweep decodes it wrong:

```
EB 01            jmp short +1
E8 B8 2A 00 00   call <rel32 = 0x00002AB8>   ; wrongly swallows 4 bytes of the real instruction
00 C3            add bl, al                   ; garbage from here on
```

This goes wrong starting right at the byte `E8`. The real CPU flow is that `EB 01` is `jmp short rel8` with rel8 = 0x01, and the target is the address of the next instruction (right after `EB 01`) plus 1, which skips exactly one byte, `E8`. The CPU never touches `E8`:

```
EB 01            jmp short +1        ; jump to the byte B8
                 (E8 is skipped)
B8 2A 00 00 00   mov eax, 0x2A       ; eax = 42
C3               ret
```

The function returns 42. The junk byte is `E8` (the opcode for CALL rel32). The CPU never runs it, so patching it to `0x90` (nop) is harmless, and after that patch the disassembler decodes it correctly as `jmp short +1`, then `nop`, then `mov eax, 0x2A`, then `ret`. The flow doesn't change, it's just cleaner for a human to read.

The overlapping instruction sequence, `31 C0 EB FF C0 48 FF C0 C3`. Decoding from the start, the way a disassembler locks onto it:

```
31 C0            xor eax, eax        ; eax = 0
EB FF            jmp short -1        ; rel8 = 0xFF = -1
```

For `EB FF`, the target is (the address of the byte right after `FF`) plus (-1), which lands on that very `FF` byte. So the CPU jumps into the middle, into the byte `FF` that is itself the tail end of `EB FF`. Decoding again starting from that `FF` byte gives the real CPU flow:

```
FF C0            inc eax             ; eax = 1
48 FF C0         inc rax             ; REX.W + FF C0 = inc rax, eax = 2
C3               ret
```

The disassembler misses both `inc` instructions. The byte `FF` plays two roles, as the tail of `jmp short -1` and the head of `inc eax`. The real return value is 2.

Fixing it in IDA. Put the cursor on the wrongly decoded section and press `U` (Undefine) to clear the wrong code definition. Put the cursor exactly at the offset where the real instruction begins (the byte `B8` in the first sequence, or the byte `FF` in the second, found from the dynamic run), then press `C` (make Code) so IDA decodes again from the correct point. For the junk byte, you can press `D` to force it to show as data (`db 0E8h`) so it stops throwing things off, or patch it to a `nop`.

Why does running dynamically always give the right answer? Because the CPU doesn't care what the disassembler thinks. It fetches the byte at rip, decodes it according to the hardware's own rules, executes it, and updates rip. Single-stepping shows you exactly the instruction sequence the hardware actually runs, while every static view is only a guess about where instructions begin.

Why is linear sweep easier to fool? It decodes blindly in sequence without following the real flow, so an inserted junk byte throws it off completely. Overlapping instructions can fool both approaches, but recursive descent at least follows jumps, so it sometimes catches the real target. Its weak points are `push addr; ret` and opaque predicates, which make it guess the wrong target or stop early.

</details>

## Key takeaways
x86 is variable-length, so a byte can be in the middle of one instruction and the start of another, and every trick here comes from that. A junk byte after `jmp` is never run by the CPU but shifts the disassembler, so patch it to `nop`. Overlapping instructions give the same byte sequence two meanings depending on the offset, because the CPU jumps into the middle of an instruction. `push addr; ret` hides the jump target from recursive descent.

With SMC the real code only appears at runtime and static analysis shows garbage, so you have to dump dynamically. The dynamic step is the referee. Single-step to see the real flow, then undefine and make code again in IDA.
