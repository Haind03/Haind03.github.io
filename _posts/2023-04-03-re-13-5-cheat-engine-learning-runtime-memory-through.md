---
title: "Lesson 13.5: Cheat Engine and runtime memory"
image:
  path: /assets/img/covers/re-13-5-cheat-engine-learning-runtime-memory-through.webp
  alt: "Lesson 13.5: Cheat Engine and runtime memory"
date: 2023-04-03 20:01:00 +0700
categories: ["Technique Reverse", "Part 13 · Games: Unity, Unreal, Lua"]
tags: [reverse-engineering, game-hacking]
render_with_liquid: false
---
One firm rule first: everything in this lesson is only for offline, single-player games of your own, or for the bundled Cheat Engine Tutorial. Touching online games is cheating, violates the ToS, and in many places is illegal. Anti-cheat will also ban you. We use Cheat Engine not to cheat, but because it's the most visual way to practice memory analysis: you see values in RAM change in real time, trace the address, then trace the code that touches that address. The same skill works when analyzing malware or any other process.

Cheat Engine (CE) is a memory scanner plus debugger for Windows. It attaches to a running process and lets you search, watch and modify that process's memory.

## Scan: finding the address of a value

You see "health = 100" on screen, but where is that number among the hundreds of MB of the game's memory? CE finds it by scanning several times and filtering down.

The two most used scan types are exact value and unknown initial value. With exact value you know the number. Health is 100, you type 100 and hit First Scan. CE may return thousands of addresses holding 100 (random coincidences). You go into the game and let health drop to 90, come back, type 90 and hit Next Scan. CE keeps only the addresses that just changed from 100 to 90. Repeat a few times and one or two addresses remain, and that's the real health.

Unknown initial value is for when you don't know the number, because it's encrypted or not shown clearly (for example the health bar is just an image). For First Scan you pick "Unknown initial value". Then each time the value goes up you choose Increased value, when it goes down you choose Decreased value, and when it stays the same you choose Unchanged. This filters by the trend of change instead of by the number, which works well for hidden values.

Picking the right data type matters too. 4 Bytes (int) is the default for most game values, but sometimes it's Float (fractional health), Double, or 2 Bytes. With the wrong type it never shows up.

Once found, double-click the address to move it to the lower table, then tick Active to freeze the value so the game can't subtract health anymore.

## The address changes every run

You freeze health, close the game, reopen it, and the old address points at garbage. The health object lives on the heap, so it gets allocated somewhere different each run (plus ASLR, see Lesson 1.2 again). An absolute address is useless across sessions.

The fix is a pointer path. Instead of remembering the final address, you find a chain of pointers starting from a fixed address (the game module's base, which doesn't change relatively) going through a few offsets to reach the value. Something like `[[base + 0x10] + 0x8] + 0x4C`. This chain is stable across runs because it hangs off the program's structure and not the random heap location.

CE has Pointer Scan to find it automatically: right-click the health address, Pointer scan for this address, and CE works backwards to see which pointers lead there. You run the pointer scan, restart the game, then rescan with the new address to throw out the wrong paths. After a few rounds you get a reusable pointer path.

## Find out what accesses this address

This feature is what makes CE a real reversing tool. Right-click the health address and choose Find out what accesses this address. CE sets a hardware breakpoint and lists every instruction that touches that address. You'll see lines like:

```
mov [rax+4C], ecx      ; instruction that writes the new health
sub [rbx+4C], edx      ; instruction that subtracts health on a hit
```

The instruction `sub [rbx+4C], edx` is where the game subtracts health. Now you know which code handles health, and you can look at the rbx register to get the base address of the character object, and from there work out the whole struct. This is the "go from data to code" idea of Lesson 0.4, done on live memory.

## Auto Assembler and code injection

Once you've found the instruction that subtracts health, you can disable it. The simplest way is a NOP (see Lesson 17.1): right-click the instruction, Replace with code that does nothing, CE overwrites it with nops, and health stops dropping. But a plain NOP can break other logic that shares the same instruction.

The cleaner way is code injection through an Auto Assembler (AA) script. It works like a code cave: you insert a jump from the original instruction to an empty region, do your extra work there (for example skip the health subtraction only when it's the player's character and not some other address), then jump back. CE generates the script template from the Auto Assemble menu, the "Code injection" template. A typical AA script:

```
[ENABLE]
aobscanmodule(hpInj, game.exe, 29 50 4C)   // find the byte pattern of the instruction sub [rax+4C],edx
alloc(newmem, 256, hpInj)

newmem:
  cmp rax, [playerBase]     // only block it if it's the player's object
  jne originalcode
  jmp return                // skip the health subtraction
originalcode:
  sub [rax+4C], edx
return:

hpInj:
  jmp newmem

[DISABLE]
hpInj:
  db 29 50 4C               // restore the original instruction
```

`aobscanmodule` (array-of-bytes scan) finds the instruction by byte pattern instead of a hard-coded address, so the script survives across runs and even some minor updates. You'll see this pattern again when writing hooks (Lesson 17.3).

## ReClass.NET: rebuilding structs in memory

When `find out what accesses` gives you the base address of the character object, you'll want the whole struct: health at offset 0x4C, where's mana, where are the coordinates. ReClass.NET does that. You point it at the base address, it shows the memory region as a table and lets you assign a type to each offset (int, float, pointer, string, nested struct). Bit by bit you rebuild the object's struct definition, like recovering structs in IDA in Lesson 3.3, only on live memory instead of a static binary. Once the struct is built you export it to a C++ header and reuse it when writing tools.

## Beyond games

Here's what you learned: scanning memory to locate data, tracing pointer paths to get stable addresses through ASLR, hardware breakpoints to find code that touches data, code injection via AOB scan, and rebuilding structs at runtime. All five are used in malware analysis and in any dynamic analysis. Cheat Engine is just a fun way to practice them.

## Lab

On the legal side, this lab only uses the Cheat Engine Tutorial (it ships with Cheat Engine, is legal and was made for learning) or an offline, single-player game of your own. Never apply any of this to an online game, since that's cheating, breaks the terms of service and is illegal in many places. Install Cheat Engine (cheatengine.org) and open the Cheat Engine Tutorial (Help > Cheat Engine Tutorial, or run Tutorial-x86_64 from the install folder). ReClass.NET is optional, for the last task.

Start with an exact value scan. In Tutorial Step 2, attach Cheat Engine to the tutorial process, scan for the current health value, press "Hit me" so the health changes, run Next Scan, and repeat until one address is left. Edit the value to pass the step. Next, the step with an unknown initial value, where you can't read the number. Use Unknown initial value and then Increased, Decreased or Unchanged following the trend to narrow the region down. Then freeze: move the address into the lower table, tick Active to freeze it, and confirm the game can no longer subtract from it.

For the pointer path, in the pointer step of the tutorial find the value, use Pointer scan for this address, restart (or press Change value so the address changes), rescan to eliminate wrong paths, take one stable pointer path and test it again. Then right-click the value's address, choose Find out what accesses this address, read the list of instructions and work out which one writes or subtracts the value. Write down that instruction and the base register of the object.

Two advanced tasks follow. For code injection, take the instruction from the previous step and write an Auto Assembler script that uses `aobscanmodule` to block that instruction conditionally, then toggle the script on and off and observe. For ReClass.NET, point it at the object's base address, assign types to a few offsets and rebuild part of the struct.

Two questions to think about. Why does freezing an absolute address break after restarting the game, while a pointer path doesn't? And which kind of breakpoint does Find out what accesses use, and why doesn't it shift other addresses the way a software breakpoint does?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Do all the tasks before reading this. The writeup describes the procedure on the Cheat Engine Tutorial (the version that comes with CE), and the steps are the same on an offline game of your own.

For the exact value scan, use Open Process and choose the Tutorial process. Set Value Type to 4 Bytes, type the current health value (for example 100) and press First Scan. Press "Hit me" in the tutorial so the health changes (for example to 95), type 95 and press Next Scan. Repeat 2 or 3 times and the list shrinks to one address. Double-click it to move it into the table, change it to 1000 and press Hit me once more so the tutorial acknowledges it. Repeated scans filter by the intersection of the result sets, which is why a few rounds take you from thousands of addresses to one.

For the unknown initial value, run First Scan with Scan Type = Unknown initial value. When the value goes up, choose Scan Type = Increased value and Next Scan, when it goes down choose Decreased value, and when it doesn't change choose Unchanged. A few rounds following the trend find it even though you never knew the real number. This helps with health shown as a bar, lightly encrypted values or hidden XP. For freezing, tick the Active column in the lower table. CE writes that value back continuously, so the game can't subtract from it, and you can use it to hold health, time or ammo.

For the pointer path, find the value's address as in the first task. Right-click, choose Pointer scan for this address, accept the defaults and save the .PTR file. Press Change value in the tutorial (or restart the process) and the old address becomes garbage. Find the new address, open Pointer scan > Rescan memory and enter the new address, and CE eliminates the paths that no longer lead correctly. Repeat 2 or 3 times until few paths remain. Double-click a path to add it to the table, where it appears as `["Tutorial-x86_64.exe"+xxxxx]+offset`. This path is reusable across runs because it hangs off the module base. On the first question, an absolute address points into an object on the heap, and the heap is allocated somewhere different on every run (plus ASLR), so next time it's garbage. A pointer path starts from the module base (which only shifts with the module's ASLR, something CE handles itself) and walks through fixed offsets in the struct, so it leads to the object wherever it sits.

For Find out what accesses, right-click the address and choose Find out what accesses this address. CE sets a hardware breakpoint (using debug registers DR0 to DR3, see Lesson 15.3) and lists the instructions that touch the address. Trigger it in the game (take damage and so on) and the list shows an instruction like `sub [rbx+4C],eax`. Select the instruction, choose More information and look at the value of rbx: that's the base address of the object, and `+4C` is the offset of health in the struct. On the second question, a hardware breakpoint is executed by the CPU through debug registers and doesn't modify the instruction bytes in memory. A software breakpoint has to overwrite the first byte of an instruction with 0xCC (INT3), which changes the code and can be detected or break a checksum. A hardware breakpoint is transparent to the code, so nothing shifts.

For code injection with an Auto Assembler script, start from the `sub [rbx+4C],eax` instruction. Right-click the instruction in the Memory Viewer, choose the Auto Assemble > Code Injection template and CE generates a template. Edit it to skip the health subtraction only when the object is the player (compare rbx with the base you already know) and leave everything else untouched. Use `aobscanmodule(inj, Tutorial-x86_64.exe, <instruction bytes>)` instead of a hardcoded address so the script survives across runs. `[ENABLE]` inserts a jump to newmem and `[DISABLE]` restores the original bytes, and you toggle it with the script's checkbox in the table. This is better than a plain NOP because NOP-ing the whole instruction stops every object using that instruction from being subtracted (enemies included) and can break the game, while a conditional injection only affects the object you want.

For ReClass.NET, open it, attach to the process, create a new class and set the address to the object base from the Find out what accesses task. Assign a type to each offset: +0x4C is an int health, and probe the neighboring offsets for mana, level, a name pointer and so on. When the struct takes shape, export it as a C++ header. This is struct recovery (Lesson 3.3), but done on live memory.

The five skills in this lab (scans to locate data, pointer paths to beat ASLR, hardware breakpoints to find code, AOB code injection and runtime struct rebuilding) are the foundation of dynamic analysis and carry over directly when you analyze malware in Part 19.

</details>

## Key takeaways
Only use it on your own offline/single-player games, since online is cheating and illegal. Use an exact value scan when you know the number, and unknown with increased/decreased when the value is hidden, picking the right type (4 Bytes, Float...). Heap addresses change every run, so you need a pointer path hanging off the module base to be stable.

Find out what accesses this address sets a hardware breakpoint to find code that touches the data, which is going from data to code. Code injection via an AA script and aobscanmodule is cleaner and more durable than a plain NOP. ReClass.NET rebuilds runtime structs, like recovering structs in IDA but on live memory, and all of these skills carry over to malware analysis and any dynamic analysis.
