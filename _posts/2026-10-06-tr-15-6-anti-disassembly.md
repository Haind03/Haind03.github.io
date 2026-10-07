---
title: "Lesson 15.6: Anti-disassembly, when the disassembler itself gets fooled"
date: 2026-10-06 09:31:00 +0700
categories: ["Technique Reverse", "Part 15 · Anti-Reversing and Bypasses"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
The earlier anti-debug lessons were about getting past the debugger at runtime. This lesson is a completely different game, aimed at the static step: making IDA, Ghidra or objdump decode a pile of wrong instructions the moment you open the file, while the CPU still runs the code correctly. The reverser looks at the pseudocode and thinks it's the real logic, and it turns out to be all garbage. Once you understand these tricks you stop blindly trusting the disassembler's output.

The root of every trick is one fact: x86 has variable-length instructions, so a byte can be the start of one instruction and also the middle of another. Just fool the disassembler about where an instruction begins and everything after it is decoded wrong.

## Two ways to disassemble, two weak points

Before breaking it, you need to know how a disassembler works. There are two strategies:

The first is linear sweep, which decodes sequentially from start to end, so when one instruction ends the byte right after is the next. objdump does this by default. Its weak point is that when data is mixed into the code it keeps decoding the data as instructions, and everything is wrong from there on. The second is recursive descent (recursive traversal), which follows the control flow and jumps to the target at a `jmp`/`jcc`/`call`. IDA and Ghidra work this way, so they're smarter. Their weak point is that if they guess the jump target wrong, or are fooled into believing a branch can be reached when it actually can't, they decode wrong too.

Anti-disassembly exploits exactly those two weak points.

## Junk bytes after an unconditional jump

The most classic trick. After a `jmp` (or a `jcc` whose condition is always true) there's a junk byte. The CPU jumps away and never touches that junk byte. But a linear sweep disassembler keeps decoding the junk byte as an instruction, and since the junk byte is often the opcode that opens a multi-byte instruction, it swallows some of the real bytes after it, shifting everything.

A common example:

```
EB 01        jmp short +1      ; jumps to the byte right after 0xE8
E8           db 0xE8           ; junk byte: CALL opcode, swallows the next 4 bytes
...the real instruction starts here
```

`EB 01` means jump to the current position plus 1, i.e. skip exactly one `E8` byte. The CPU never executes `E8`. But the disassembler sees `E8` and thinks it's `call rel32`, eats 4 more address bytes, and the real instruction is torn in half. In IDA this stretch shows up messy, sometimes highlighted red.

## Overlapping instructions, one byte sequence with two meanings

This is the prettiest trick technically. The same byte sequence read from two different starting points gives two completely different instruction sequences. The author arranges it so the disassembler starts at spot A (giving a harmless instruction), while the CPU actually jumps into spot B in the middle of an instruction (giving a different one).

The classic example with the bytes `EB FF C0 48`:

```
Read from the start:
  EB FF        jmp short -1     ; looks like a jump backward
But the CPU jumps into the 2nd byte:
  FF C0        inc eax
  48 ...       (next instruction)
```

The disassembler locks onto the first reading and misses the `inc eax` the CPU actually runs. The byte `FF` is both the tail of `jmp short -1` (EB FF) and the head of `inc eax` (FF C0). One byte, two roles.

## push + ret instead of jmp

One way to hide the jump target from recursive descent. Instead of `jmp target` (where the target is visible for the disassembler to follow), people do:

```
push target_address
ret
```

`ret` takes the value on top of the stack as the return address and jumps there. In effect it's identical to `jmp target`, but the disassembler sees `ret`, thinks the function ended and stops following the flow, not knowing it actually jumps to `target`. A variant: `call` plus modifying the return address on the stack.

## Opaque predicates creating dead branches

A condition whose actual result is always fixed (for example `x*x >= 0` is always true), but the compiler/disassembler can't prove it so has to assume both branches might be reached. The author stuffs junk code or code that shifts decoding into the branch that never runs. You waste effort reading a dead branch. This was covered in detail in [Lesson 14.4](/posts/tr-14-4-obfuscation-ky-thuat/), here I only mention that it's also a form of anti-disassembly when the dead branch contains bytes that shift the decoding.

## Self-modifying code (SMC)

Code that modifies itself at runtime. On disk (and in IDA's static view) that stretch is a meaningless or encrypted byte sequence; only at runtime does a stub overwrite it with real instructions and then execute them. Statically you see garbage, because the real code doesn't exist yet when you read it. Signs: a loop that writes into the `.text` region (which should only be read and executed), or a section that is both writable and executable (W+X). With SMC, static analysis is almost helpless, you have to run dynamically until after it has modified itself and only then dump it to read. This is also the core mechanism of packers ([Lesson 14.1](/posts/tr-14-1-packer-entropy-nhan-dien/)).

## How to handle it

The good news: anti-disassembly makes the static step hard, but the CPU still has to run correctly, so the dynamic step always gives you the truth. The toolkit:

Running dynamically is the final referee. Open it in x64dbg and single-step through the suspicious stretch, and you see exactly the flow the CPU takes and exactly the instructions it executes, no matter what IDA draws. In IDA, press `U` (undefine) on the wrongly decoded stretch, then put the cursor at the exact spot where the real instruction starts (taken from the dynamic step) and press `C` (make code), and IDA decodes again from the right point. For a junk byte after a `jmp`, overwrite it with `0x90` (`nop`) so the disassembler decodes cleanly again. Since the CPU never runs that byte, patching it is harmless.

Watch for red-highlighted areas and nonsensical instructions, since IDA marks spots it isn't sure about. A `jmp short -1`, a `call` into the middle of nowhere, or a run of `db` mixed into running code are all flags for anti-disassembly. And when you recognize `push addr; ret`, follow the addr target yourself instead of believing the function ended.

The general principle: when pseudocode looks abnormally chaotic right in the middle of an otherwise normal function, don't blame yourself for reading badly, suspect the disassembler is being fooled and double check by running it dynamically.

## Lab

See [labs/15.6/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/15.6). You're given a byte sequence with junk bytes and one overlapping spot. The task is to determine the real CPU flow, point out the instruction the disassembler missed, and fix it in IDA (undefine, make code at the right place). The solution is at [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/15.6/solution.md).

## Key takeaways
x86 is variable-length, so a byte can be in the middle of one instruction and the start of another, and that's the root of every trick. A junk byte after `jmp` is never run by the CPU but shifts the disassembler, so patch it to `nop`. Overlapping instructions give the same byte sequence two meanings depending on the offset, because the CPU jumps into the middle of an instruction. `push addr; ret` hides the jump target from recursive descent.

With SMC the real code only appears at runtime and static analysis shows garbage, so you have to dump dynamically. The dynamic step is always the referee: single-step to see the real flow, then undefine and make code again in IDA.
