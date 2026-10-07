---
title: "Lesson 2.5: x64dbg basics"
image:
  path: /assets/img/covers/re-2-5-x64dbg-reversers-dynamic-scalpel-windows.webp
  alt: "Lesson 2.5: x64dbg basics"
date: 2022-05-03 10:03:00 +0700
categories: ["Technique Reverse", "Part 02 · The Toolkit"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
IDA and Ghidra let you read code while it stands still. x64dbg lets you watch it run. It's a free, open source ring-3 (user-mode) debugger, and almost everyone doing RE on Windows opens it daily. This lesson goes from finding the interface confusing to setting breakpoints, inspecting registers, and patching a check.

x64dbg is two builds in one package, with `x64dbg.exe` for 64-bit binaries and `x32dbg.exe` for 32-bit. Pick the wrong one and it won't load, so check how many bits the target file is first (lesson [2.1](/posts/re-2-1-five-minute-triage-die-strings-pe/) handles that).

## The screen layout

The first time you open it, x64dbg shows many panels. Only a few are used all the time.

The CPU tab is the main one. On the left is the disassembly, where you see each instruction about to run, and the line being executed (at `rip`) is highlighted. You spend most of your time here. In the top right of the CPU tab, Registers shows the value of every register right now (`rax`, `rcx`, flags...), and you can read and edit there. Dump, at the bottom left, shows memory as hex at any address, so when you want to know what data a pointer points to, look there. Stack, at the bottom right, shows the stack contents at `rsp`, useful for reading parameters and return addresses.

A few other panels help when you need them. Graph shows the current function as a block diagram like IDA, which makes branching easy to see. Memory Map shows all the process's memory regions with R/W/X permissions and the module occupying each one. Open it when you need to know which module an address belongs to, or to hunt for suspicious RWX regions (mentioned in lesson [1.2](/posts/re-1-2-process-memory-map-where-everything-happens/)). Breakpoints lists every breakpoint currently set, and Call Stack shows the chain of functions called to get to the current spot, so you can see who called you.

No need to memorize it all yet. Open CPU, glance at Registers and Stack, and that's enough to start.

## Breakpoints

A breakpoint is a stopping point you plant in the code. Run to it, the program freezes, and you can inspect. There are three kinds.

The software breakpoint (key `F2`) is the most commonly used. It's set at the instruction line the cursor is on. x64dbg overwrites the first byte of the instruction with `0xCC` (the INT3 instruction) and restores it when it stops. It's fast and there's no limit on count, but since it modifies a byte, programs that do integrity checks can detect it.

The hardware breakpoint uses the CPU's debug registers DR0 to DR7 and doesn't modify code bytes, so it's harder to detect. The downside is you get at most 4. Set it by right-clicking the instruction, then Breakpoint, Hardware.

The memory breakpoint stops when a memory region is read, written, or executed. It's useful when you want to know who touches a variable, or to catch the moment a packer writes decrypted code and then jumps to run it.

### Breakpoint by API name

Instead of hunting for addresses, you can set a breakpoint on an API function by name, typed in the Command box at the bottom of the window:

```
bp VirtualAlloc
bp CreateFileW
bp strcmp
bp MessageBoxW
```

Now every time the program calls that function you stop at the start of the function, and following the Win64 calling convention (lesson [1.4](/posts/re-1-4-x86-x64-assembly-2-stack-frames/)) the parameters are already in `rcx`, `rdx`, `r8`, `r9`. This is the fastest way to catch the exact moment the program reads a file, compares a string, or allocates memory.

## Controlling execution

Once stopped, you move the program forward step by step. These keys should become reflex:

| Key | Action |
|---|---|
| `F7` | Step into: run one instruction, and if it's a `call`, step into the function |
| `F8` | Step over: run one instruction, and if it's a `call`, run the whole function and stop at the next instruction |
| `F9` | Run: continue to the next breakpoint |
| `Ctrl+F9` | Execute till return: run until the current function `ret`s, used to quickly get out of a library function you don't care about |
| `F4` | Run to selection: run to exactly the line you selected, as a one-time breakpoint does |

I use `F8` to move through quickly, and only `F7` into a function when it's worth looking at. If you `F7` into some long library function, `Ctrl+F9` jumps back out. The full shortcut list is in the [cheatsheet](/posts/re-resources-cheatsheet-shortcuts-quick-reference/).

## Reading and editing data at runtime

Once stopped, you inspect. Right-click a register or operand that holds an address and choose Follow in Dump, and the Dump window jumps there. Use it when `rax` is a pointer to a string and you want to read that string. Follow in Disassembler does the same for code addresses. To edit a register, double-click the value in Registers and type the new one. To force a function to return "true", stop right before `ret` and set `rax = 1`. You can also click the ZF flag in the flags panel to flip it, which changes the direction of a conditional jump without editing code.

## Patching

Say you find a `jne` that jumps to the "Wrong password" branch, and you want it to always take the right branch. Select the `jne` line and press `Space` (or right-click, Assemble). Type the new instruction, for example change `jne` to `je` to flip the condition, type `nop` to remove the jump entirely, or change it to `jmp` to jump unconditionally. Press OK and the instruction is changed in memory, so you can run it right away.

This patch only lives in memory, close the debugger and it's gone. To save it as a new `.exe` file, open Patches with `Ctrl+P`, look at the list of changes, then Patch File to write it to disk. Deeper patching techniques (code caves, patching on disk vs at runtime) are in lesson [17.1](/posts/re-17-1-patching-binaries-changing-one-byte-change/).

## Plugins worth knowing

Two plugins come up early. ScyllaHide hides the debugger from user-mode anti-debug techniques. A lot of protected programs behave differently when they see they're being debugged, and ScyllaHide makes them think no one is watching; details are in lesson [15.9](/posts/re-15-9-bypassing-anti-debug-from-mouse-click/). Scylla dumps the process and rebuilds the import table (IAT) after unpacking, and is used in lesson [14.3](/posts/re-14-3-dumping-process-rebuilding-iat-scylla/).

## Static first, dynamic after

Don't open x64dbg and press `F8` from the entry point until morning. Combine it with static analysis, like the workflow in lesson [0.4](/posts/re-0-4-reverse-engineering-workflow-not-get-lost/). In IDA/Ghidra, narrow down the interesting spot (for example the serial check function, found by working backwards from a message string) and write down the address or API name. Then go to x64dbg and set a breakpoint there, by address (`bp 0x...`) or API name. Run, let the program reach it, and inspect registers and memory to see the real values that static analysis can't give you.

Static draws the map and dynamic confirms it. x64dbg is the second half of that pair.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 2.5</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/2.5.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/2.5/src/serial_check.c" download><i class="fa-solid fa-download"></i>src/serial_check.c</a>
</div>
</div>

Here you practice setting breakpoints, reading comparison operands to find the correct serial, and patching a jump. You'll build a small crackme from `serial_check.c`, enter a wrong serial, let x64dbg show you the correct serial in a register, and finally patch the program to accept any serial. You need `x64dbg.exe` (the 64-bit build, since we build 64-bit) and a compiler, either MSVC or MinGW-w64, on Windows.

```
cl /Od /Zi serial_check.c                       REM MSVC
gcc -O0 -g serial_check.c -o serial_check.exe   REM MinGW
```

Run it once to see it reject a random serial:

```
serial_check.exe ABC-123
Wrong serial.
```

For the dynamic approach, which is the fastest, open `serial_check.exe` in x64dbg, type `bp strcmp` in the Command box and press `F9` to run. If MinGW inlines `strcmp` and it never stops, put a breakpoint at the call to `check` instead, or search for the string "RE-" and break in the function that uses it. When it stops in `strcmp`, the first two parameters are in `rcx` and `rdx` (Win64), one being the serial you typed and the other the correct serial. Right-click `rcx` and `rdx`, choose Follow in Dump and read the strings, and you have the correct serial. Run the program again with that serial and confirm you get "Correct! Welcome."

Then cross-check statically. Open the same file in IDA or Ghidra, find the `make_serial` function, read how the serial is computed and work it out by hand. The result must match what the debugger gave you. If `bp strcmp` doesn't stop, the function may be inlined or static. In that case put a breakpoint at the start of `main` and `F8` your way to the comparison, or use Search for > String references to find "Wrong serial" and place a breakpoint before it. The correct serial depends on the fixed `name` in the code, so it doesn't change between runs.

Last, patch the program so it accepts any serial. After `check` returns, look for a `test eax, eax` followed by a `je`/`jne` that branches to the "Wrong serial" path. Use `Space` to change the jump (for example turn `jne` into `je`, or `nop` the jump, or force `rax = 1` before the branch). Run it with any serial and it should print "Correct! Welcome." Press `Ctrl+P`, choose Patch File to save `serial_check_patched.exe`, and run it again outside the debugger to be sure.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Do the whole lab before reading this. The logic lives in `make_serial`. It uses `name = "reverser"` and adds up the ASCII code of each character, so r+e+v+e+r+s+e+r = 114+101+118+101+114+115+101+114 = 878. The serial is `"RE-" + (878 * 7)`, which is `RE-6146`. To check:

```
serial_check.exe RE-6146
Correct! Welcome.
```

To get the serial with x64dbg, open `serial_check.exe` and let it stop at the entry point (the system breakpoint). In the Command box type `bp strcmp`, press Enter, then `F9`. With MSVC `/Od` the call into the CRT `strcmp` is usually caught, and if not you put the breakpoint at the call to `check` in `main`. When it stops at the top of `strcmp`, `rcx` points to the first string (the serial you typed) and `rdx` to the second (the correct serial generated by `make_serial`), following the Win64 calling convention from Lesson 1.4. Right-click `rdx` and choose Follow in Dump. The Dump window shows `52 45 2D 36 31 34 36 00`, which read as ASCII is `RE-6146`. If you enter the serial through stdin, run `serial_check.exe` with no arguments, type any wrong serial, and x64dbg stops at `strcmp` the same way.

For the static cross-check, open `make_serial` in Ghidra or IDA. You see a loop that accumulates the character codes of the constant string "reverser" (it sits in .rdata, so find it in the Strings window), then a multiplication by 7 and a call to `sprintf` with the format `"RE-%d"`. Computing 878*7 = 6146 by hand matches the dynamic result, which is a good way to confirm one direction of analysis against the other.

For the patch, the typical pattern in `main` after the call to `check` (MSVC /Od, abbreviated) is:

```asm
call check
test eax, eax         ; eax = result of check (0 = wrong, 1 = correct)
je   loc_wrong        ; if eax == 0, jump to the "Wrong serial" branch
...                   ; the "Correct!" branch
loc_wrong:
...                   ; prints "Wrong serial."
```

There are three ways to patch it, and you pick one. You can flip the condition. Select `je loc_wrong`, press `Space` and change it to `jne loc_wrong`. Now the correct serial is rejected and wrong ones are accepted, a bit backwards, but for the lab a random serial will pass. You can remove the jump. Change `je loc_wrong` to `nop` (x64dbg inserts enough nops to fill the instruction length), so the flow never takes the wrong branch and always prints "Correct!". Or you can force the result. Put a breakpoint at `test eax, eax` and set `eax = 1` in Registers each time it stops, which leaves the code untouched but has to be repeated on every run. For an exported file I'd `nop` the jump (or turn `je` into a `jmp` straight to the correct branch).

To save the patch, press `Ctrl+P`, check the list of changes, choose Patch File and save `serial_check_patched.exe`. Run it outside the debugger:

```
serial_check_patched.exe anything-at-all
Correct! Welcome.
```

To sum up, a breakpoint on an API name (`bp strcmp`) takes you straight to the moment of comparison, where the correct serial is in the parameters. Static and dynamic analysis confirm each other, since reading `make_serial` gives the same answer the debugger showed. Patching a single jump is the most common way past a check, and `nop` is the safe choice because it doesn't shift any addresses.

</details>

## Key takeaways
Use `x64dbg.exe` for 64-bit and `x32dbg.exe` for 32-bit, and pick the right build. The panels that matter are CPU (disassembly), Registers, Dump, Stack and Memory Map. Breakpoints come in three kinds, which are software (`F2`, fast, modifies a byte), hardware (harder to detect, max 4), and memory (catches access to a memory region). `bp APIName` in the Command box stops at the start of an API function, with parameters already in rcx/rdx/r8/r9.

For control, `F7` steps into, `F8` steps over, `F9` runs, `Ctrl+F9` goes to return, and `F4` runs to the selected line. To patch, press `Space` to assemble a new instruction and `Ctrl+P` to save to a file. Always narrow down with static first, then set dynamic breakpoints in the right place.
