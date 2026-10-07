---
title: "Lesson 15.3: Anti-debug group 3, timing and traps"
image:
  path: /assets/img/covers/re-15-3-anti-debug-group-3-timing-traps.webp
  alt: "Lesson 15.3: Anti-debug group 3, timing and traps"
date: 2023-05-12 11:29:00 +0700
categories: ["Technique Reverse", "Part 15 · Anti-Reversing and Bypasses"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
The previous two groups (API and PEB) rely on asking the operating system "am I being debugged?". This group is sneakier: it doesn't ask anyone, it works it out from two things a debugger can't hide. One is time: a debugger makes the program run thousands of times slower when you step. The other is exceptions: a debugger has to wedge itself between the program and the exception handling mechanism, and that wedging leaves a trace.

Understanding this group matters because there's no neat API call for you to put a breakpoint on, so ScyllaHide can't always take care of everything either.

## Timing: a debugger stretches time

The idea is so simple it's beautiful. A normal chunk of code finishes in a few hundred CPU cycles. If you're single-stepping through it in a debugger, each instruction costs millions of cycles (because the debugger stops, updates the UI, waits for you to press a key). The program just needs to measure the time at two points and compare: if the difference is abnormally large, someone is definitely watching.

### RDTSC, the CPU's stopwatch

The `rdtsc` instruction (Read Time-Stamp Counter) returns the number of CPU cycles since boot, with the result in the `edx:eax` pair (edx is the high 32 bits, eax the low 32 bits). The classic pattern:

```asm
rdtsc                 ; read timestamp 1
mov   rsi, rax        ; save it (eax = low part)
; ... the code being measured, usually short ...
rdtsc                 ; read timestamp 2
sub   rax, rsi        ; rax = cycle difference
cmp   rax, 10000h     ; compare against a threshold
ja    debugger_found  ; difference too large, being stepped
```

Translated: "measure how many cycles the middle part took, and raise the alarm if it exceeds the threshold". If you see two `rdtsc` instructions a short distance apart followed by `sub` and `cmp`, it's almost certainly a timing check.

### API variants

Not everyone uses `rdtsc`. The same idea can be measured with APIs: `QueryPerformanceCounter` for a high-resolution counter, `GetTickCount` / `GetTickCount64` which count milliseconds since boot, and `timeGetTime` or C's `time()` for a coarser reading.

The pattern is still: call to get a timestamp, run a chunk, call again to get a second timestamp, subtract, compare to a threshold. With these APIs you do have a place to set a breakpoint.

### Getting past timing checks

The weakness of a timing check is that it's just a `cmp` followed by a jump. The cleanest fix is to patch the jump: find `ja debugger_found` (or `jg`, `jb` depending on the build), then invert the condition or nop it out. You don't care about the time value, you just need the flow not to go into the alarm branch.

You can also fake the return value by editing `rax` after the second `rdtsc` or `GetTickCount` call so the difference becomes small. ScyllaHide has options that handle some timing checks (for example normalizing `rdtsc`, hooking GetTickCount), but it doesn't cover every homemade variant, so patching by hand is still the reliable weapon.

A practical tip: don't step through the part between the two timestamps. Put a breakpoint after the second measurement and let it run straight there (F9), so the middle part runs at real speed and the difference doesn't get inflated.

## Traps: throw an exception and see who catches it

The second group takes advantage of how Windows (and debuggers) handle exceptions. Normally, if a program causes an exception, the operating system hands it to the program's handler (SEH/VEH, see Lesson 1.12). But when a debugger is attached, the debugger gets to look at the exception first. If the debugger "swallows" the exception instead of passing it back to the program, the program knows someone is interfering.

### INT 3, a double-edged sword

The byte `0xCC` is the `int 3` instruction, which is exactly the software breakpoint every debugger uses. The anti-debug trick: the program itself places an `int 3` along with its own exception handler.

```asm
    ; install a SEH/VEH pointing to our own handler earlier
    int 3                 ; deliberately trigger a breakpoint
    ; if execution gets HERE, the handler was NOT called
    ; -> the debugger swallowed the int 3 -> being debugged
    jmp debugger_found
handler:
    ; no debugger: our own handler caught it
    ; -> carry on normally
```

The logic is the opposite of what you'd expect: if the program's handler runs, it's not being debugged (the program caught its own breakpoint). If execution runs straight through `int 3` and the handler is never called, the debugger intercepted the breakpoint, which means it's being debugged.

### INT 2D and ICEBP (0xF1)

Two siblings few people know about but which get used a lot because they mess with debuggers. `int 2d` is a kind of kernel breakpoint. Under a debugger, it shifts the instruction pointer by one byte in an unpredictable way, and the way the debugger handles it differs from running freely. `icebp` (opcode `0xF1`, also called int 1) generates a single-step exception, and many debuggers handle it wrong and give away their presence.

If you see odd opcodes like `0xCD 0x2D` or `0xF1` sitting in the middle of normal-looking code, suspect an anti-debug trap rather than real code.

### Hardware breakpoint detection via DR0-DR7

Your hardware breakpoints live in the debug registers DR0 through DR3 (addresses) and DR7 (enable/disable). The program can read them itself to detect this: call `GetThreadContext` with the `CONTEXT_DEBUG_REGISTERS` flag, then check whether DR0-DR3 are nonzero or whether any bit of DR7 is set. If so, someone has set a hardware breakpoint.

```asm
    ; CONTEXT.Dr0 .. Dr3 nonzero  or  Dr7 != 0
    ; -> hardware breakpoint present -> being analyzed
```

### Single-step detection via the trap flag

The trap flag (TF) in the flags register, when set, makes the CPU raise an exception after every instruction (this is the single-step mechanism itself). Some tricks set TF themselves and then check whether the exception arrives as expected, or push the flags onto the stack (`pushfd`) and inspect the TF bit.

### Getting past the trap group

For INT 3 / INT 2D / ICEBP, configure x64dbg to pass the exception back to the program instead of swallowing it. Go to Options > Exceptions and add the relevant exception codes to the ignore list, so the program's handler receives them like it would when running freely. Or just patch the trap instruction to `nop`.

For hardware breakpoint detection, don't use hardware breakpoints, use software breakpoints instead, or have ScyllaHide/TitanHide hide the DR registers from `GetThreadContext`. The trap flag check usually also comes down to patching the branch that compares the result.

The general rule for the whole of group 3: don't try to fight each individual measurement. Find the final point where every check funnels into one jump that decides "being debugged or not", then neutralize that jump. A lot of complicated layers of measurement usually pour into one or two branches.

## Lab

The goal is to see with your own eyes a timing check (RDTSC) and a trap check (INT 3) detect a debugger, and then get past both. The program is `timing_check.c`. It is harmless, and only prints a verdict on whether it sees a debugger. Use it for learning.

On Windows both checks run. Build with MinGW or MSVC.

```
gcc -O0 timing_check.c -o timing_check.exe
cl /Od timing_check.c
```

On Linux only the RDTSC part is built, because the INT 3 check uses SEH and is left out when the target is not Windows.

```
gcc -O0 timing_check.c -o timing_check
```

First run it freely (double-click or from a terminal). You should see a small RDTSC delta, a few hundred cycles, and the verdict that no debugger was found. Then open it in x64dbg, set a breakpoint at `main`, and single-step (F7 or F8) through the part between the two `rdtsc` instructions. Continue and watch the delta jump into the millions and the program report "debugger detected".

Now get past it without stepping. Put a breakpoint right after the second `rdtsc` and press F9 to run straight to it. The measured section runs at full speed, the delta is small again, and the check does not fire. You can also get past it by patching: find the conditional jump after the `cmp` of the timing check and invert or nop it. For the INT 3 check, go to Options > Exceptions in x64dbg and configure it to pass the exception breakpoint (0x80000003) on to the program, then watch the program's `__except` handler catch it just as it did when running freely.

Some questions to think about. Why does running straight through with F9 not trigger the timing check while single-stepping does? In the INT 3 check, why does "my own handler ran" mean you are NOT being debugged? And if you patch the jump, do you still need to care about the delta value? Try it yourself before opening the solution.

<div class="lab-box">
<div class="lab-head"><b>LAB 15.3</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/15.3/src/timing_check.c" download><i class="fa-solid fa-file-code"></i>src/timing_check.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

I verified it on Linux, built with `gcc -O0 timing_check.c -o timing_check`. That covers only the RDTSC part, since the INT 3 part is Windows SEH and is dropped on other systems. Running it freely gives this.

```
[timing] delta = 374 cycles
=> Verdict: no debugger found, running normally
```

The delta of 374 cycles when running freely is far below the threshold of 100000. This is a real number from the build machine. On Windows under x64dbg, when you single-step through the measured section, the delta jumps into the millions and the check fires.

The free run is the baseline: a small delta of a few hundred cycles, and the verdict that there is no debugger.

Single-stepping gives the check away. In x64dbg, if you press F7 or F8 one instruction at a time through the `for` loop between the two `rdtsc` instructions, every pause in the debugger costs a lot of real cycles, so `t2 - t1` balloons. Then `cmp rax, 100000` and `ja` branch into the "detected" path.

The way past it without touching the code is to run straight through. Put a breakpoint right after the second `rdtsc` (or right before the `cmp`), then press F9 from before the first `rdtsc`. The CPU runs the middle part at full speed with no debugger interrupting each instruction, so the delta stays small. This is the simplest way past a timing check: never single-step the part between two measurement points.

The patch approach looks for this pair.

```asm
cmp rax, 100000h   ; or some other threshold value
ja  detected
```

There are two ways. Change `ja` into a `jmp` that goes over to the safe path, or nop the `ja` instruction (fill it with 0x90) so execution always falls through to the "no debugger" path. After the patch the delta value no longer matters, because the flow never branches into the alarm path.

For the INT 3 trap, the code uses `__debugbreak()` (which emits `int 3`) inside a `__try` block. With no debugger, nobody swallows the exception, so it falls into the program's own `__except`, `handled = 1`, and the function returns 0 (not being debugged). With a debugger that swallows the `int 3`, the `__except` block does not run, `handled` stays 0, and the function returns 1 (being debugged). To get past it, go to Options > Exceptions in x64dbg and add `0x80000003` (STATUS_BREAKPOINT) to the list so the debugger passes it on to the program instead of handling it itself. Then `__except` catches it as it does in a free run, and the check does not fire. Another way is to nop the `int 3` instruction and the checking branch.

On the questions, first, F9 lets the CPU run the measured section continuously at hardware speed, and the debugger does not step in between instructions, so it adds no time. Single-stepping makes the debugger stop after every instruction, and each stop costs a lot of real cycles that add up and inflate the delta. Second, the program places the `int 3` itself and installs its own handler for it. With no debugger, the program's handler catches its own breakpoint. With a debugger, the debugger takes the `int 3` first and (in the default configuration) swallows it, so the program's handler does not run, and that is the sign of being debugged. Third, no: once the jump has been neutralized, the flow always takes the "no debugger" path whatever the delta is. This is why patching the branch is the most durable approach against every group 3 anti-debug technique.

</details>

## Key takeaways
Group 3 doesn't ask the OS, it works things out from time and exceptions, so it's harder to hook than the API group. Two `rdtsc` a short distance apart followed by `sub` + `cmp` + jump is a timing check, and GetTickCount/QueryPerformanceCounter give the equivalent. To get past timing, don't step through the measured part (run straight to after timestamp 2), or patch the jump, or fake the value.

Traps work by the program placing its own int 3 / int 2d / icebp and seeing whether the debugger swallows the exception. The logic is usually inverted: the handler running means not being debugged. To get past them, configure the debugger to pass the exception back to the program, or nop the trap instruction.

Hardware breakpoints get detected via DR0-DR7, so switch to software breakpoints or use ScyllaHide/TitanHide to hide the debug registers. In general, find the final deciding jump and neutralize it instead of fighting every single measurement.
