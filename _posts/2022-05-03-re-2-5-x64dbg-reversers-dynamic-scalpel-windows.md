---
title: "Lesson 2.5: x64dbg, the reverser's dynamic scalpel on Windows"
date: 2022-05-03 10:03:00 +0700
categories: ["Technique Reverse", "Part 02 · The Toolkit"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
If IDA and Ghidra let you read code while it stands still, x64dbg lets you watch code while it's breathing. It's a free, open source ring-3 (user-mode) debugger, and almost everyone doing RE on Windows opens it daily. This lesson takes you from finding the interface confusing to confidently setting breakpoints, inspecting registers, and patching a check.

x64dbg is really two builds in one package: `x64dbg.exe` for 64-bit binaries and `x32dbg.exe` for 32-bit. Pick the wrong one and it won't load, so check how many bits the target file is first (lesson [2.1](/posts/re-2-1-five-minute-triage-die-strings-pe/) handles that).

## The screen layout, don't let it scare you

The first time you open it, x64dbg throws a pile of panels in your face. There are really only a few you use all the time, and once you have those you're set.

The CPU tab is the main one and the most important part. On the left is the disassembly, where you see each instruction about to run, and the line being executed (at `rip`) is highlighted. This is where you live most of the time. In the top right of the CPU tab, Registers shows the value of every register right now (`rax`, `rcx`, flags...), and you read and edit directly there. Dump, at the bottom left, shows memory as hex at any address, so when you want to know what data a pointer points to, look there. Stack, at the bottom right, shows the stack contents at `rsp`, useful for reading parameters and return addresses.

A few other panels help when you need them. Graph shows the current function as a block diagram like IDA, which makes branching flow easy to see. Memory Map is a map of all the process's memory regions with R/W/X permissions and the module occupying each one; open it when you need to know which module an address belongs to, or to hunt for suspicious RWX regions (mentioned in lesson [1.2](/posts/re-1-2-process-memory-map-where-everything-happens/)). Breakpoints lists every breakpoint currently set, and Call Stack shows the chain of functions called to get to the current spot, which tells you "who called me".

No need to memorize it all yet. Open CPU, glance at Registers and Stack, and that's enough to start.

## Breakpoints, what makes a debugger

A breakpoint is a stopping point you plant in the code. Run to it, the program freezes, and you can inspect to your heart's content. There are three kinds, each with its own job.

The software breakpoint (key `F2`) is the most commonly used. It's set at the instruction line the cursor is on. x64dbg quietly overwrites the first byte of the instruction with `0xCC` (the INT3 instruction) and restores it when it stops. It's fast and there's no limit on count, but since it modifies a byte, some programs that do integrity checks can detect it.

The hardware breakpoint uses the CPU's debug registers DR0 to DR7 and doesn't modify code bytes, so it's harder to detect. The downside is that you get at most 4. Set it by right-clicking the instruction, then Breakpoint, Hardware.

The memory breakpoint stops when a memory region is read, written, or executed. It's extremely useful when you want to know "who touches this variable", or to catch the moment a packer writes decrypted code and then jumps to run it.

### Breakpoint by API name, a tip that saves hours

Instead of hunting for addresses, you set a breakpoint right on an API function by name, typed in the Command box at the bottom of the window:

```
bp VirtualAlloc
bp CreateFileW
bp strcmp
bp MessageBoxW
```

Now every time the program calls that function you stop right at the start of the function, and following the Win64 calling convention (lesson [1.4](/posts/re-1-4-x86-x64-assembly-2-stack-frames/)) the parameters are already sitting in `rcx`, `rdx`, `r8`, `r9`. This is the fastest way to catch the exact moment the program reads a file, compares a string, or expands memory.

## Controlling execution: step and run

Once stopped, you drive the program forward beat by beat. These keys have to become reflex:

| Key | Action |
|---|---|
| `F7` | Step into: run one instruction, and if it's a `call`, step into the function |
| `F8` | Step over: run one instruction, and if it's a `call`, run the whole function and stop at the next instruction |
| `F9` | Run: continue to the next breakpoint |
| `Ctrl+F9` | Execute till return: run until the current function `ret`s, used to quickly get out of a library function you don't care about |
| `F4` | Run to selection: run to exactly the line you selected, like a one-time breakpoint |

Rule of thumb: use `F8` to glide through quickly, and only `F7` into a function when it's really worth looking at. If you `F7` into some endless library function, `Ctrl+F9` jumps back out. The full shortcut list is in the [cheatsheet](/posts/re-resources-cheatsheet-shortcuts-quick-reference/).

## Reading and editing data at runtime

Stopped, now you inspect. A few operations you repeat over and over. Right-click a register or operand that holds an address and choose Follow in Dump, and the Dump window jumps there; use it when `rax` is a pointer to a string and you want to read that string. Follow in Disassembler does the same for code addresses. To edit a register, double-click the value in Registers and type the new one. Want to force a function to return "true"? Stop right before `ret` and set `rax = 1`. You can also click the ZF flag in the flags panel to flip it, which changes the direction of a conditional jump without editing code.

## Patch: editing the instruction directly

This is the fun part. Say you find a `jne` that jumps to the "Wrong password" branch, and you want it to always take the right branch. Select the `jne` line and press `Space` (or right-click, Assemble). Type the new instruction: change `jne` to `je` to flip the condition, type `nop` to remove the jump entirely, or change it to `jmp` to jump unconditionally. Press OK and the instruction is changed in memory, so you can run it right away.

Remember that this patch only lives in memory, close it and it's gone. To save it as a new `.exe` file, open Patches with `Ctrl+P`, look at the list of changes, then Patch File to write it to disk. Deeper patching techniques (code caves, patching on disk vs at runtime) are saved for lesson [17.1](https://github.com/Haind03/Technique-Reverse/tree/main/phan-17-patch-hook-frida).

## Plugins worth knowing

x64dbg is powerful partly thanks to plugins, and two come up early. ScyllaHide hides the debugger's presence from user-mode anti-debug techniques. A lot of protected programs behave differently when they see they're being debugged, and ScyllaHide makes them think no one is watching; details are in lesson [15.9](https://github.com/Haind03/Technique-Reverse/tree/main/phan-15-anti-reverse). Scylla dumps the process and rebuilds the import table (IAT) after unpacking, and is used in lesson [14.3](https://github.com/Haind03/Technique-Reverse/tree/main/phan-14-packer-obfuscation).

## The standard rhythm: static first, dynamic after

Don't open x64dbg and blindly `F8` from the entry point until morning. The effective way is to combine it with static analysis, exactly like the workflow in lesson [0.4](/posts/re-0-4-reverse-engineering-workflow-not-get-lost/). In IDA/Ghidra, narrow down the interesting spot (for example the serial check function, found by working backwards from a message string) and write down the related address or API name. Then go to x64dbg and set a breakpoint right there, by address (`bp 0x...`) or API name. Run, let the program reach it, and inspect registers and memory to see the real values that static analysis can't give you.

Static draws the map, dynamic confirms. x64dbg is the second half of that pair.

## Lab

Practice setting breakpoints, reading comparison operands, and patching a jump: see [labs/2.5/](https://github.com/Haind03/Technique-Reverse/blob/main/labs/2.5). You'll build a small crackme, enter a wrong serial, let x64dbg show you the correct serial right in a register, and finally patch it to accept any serial.

## Key takeaways
Use `x64dbg.exe` for 64-bit and `x32dbg.exe` for 32-bit, and pick the right build. The panels that matter are CPU (disassembly), Registers, Dump, Stack and Memory Map. Breakpoints come in three kinds: software (`F2`, fast, modifies a byte), hardware (harder to detect, max 4), and memory (catches access to a memory region). `bp APIName` in the Command box stops at the start of an API function, with parameters already in rcx/rdx/r8/r9.

For control, `F7` steps into, `F8` steps over, `F9` runs, `Ctrl+F9` goes to return, and `F4` runs to the selected line. To patch, press `Space` to assemble a new instruction and `Ctrl+P` to save to a file. Always narrow down with static first, then set dynamic breakpoints in the right place.
