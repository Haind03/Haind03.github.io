---
title: "Lesson 13.5: Cheat Engine, learning runtime memory through games"
date: 2023-04-03 20:01:00 +0700
categories: ["Technique Reverse", "Part 13 · Games: Unity, Unreal, Lua"]
tags: [reverse-engineering, game-hacking]
render_with_liquid: false
---
Before going further, one firm sentence: everything in this lesson is only for offline, single-player games of your own, or for the bundled Cheat Engine Tutorial. Touching online games is cheating, violates the ToS, and in many places is illegal. On top of that, anti-cheat will ban you. We learn Cheat Engine not to cheat, but because it's the most visual way to practice memory analysis: you see values in RAM change in real time, trace the address, then trace the code that touches that address. The skill carries over unchanged when analyzing malware or any other process.

Cheat Engine (CE) is a memory scanner plus debugger for Windows. It attaches to a running process and lets you search, watch and modify that process's memory.

## Scan: finding the address of a value

The core problem: you see "health = 100" on screen, but where is that number among the hundreds of MB of the game's memory? CE solves it by scanning several times and filtering down.

The two most used scan types are exact value and unknown initial value. With exact value you know the number. Health is 100, you type 100 and hit First Scan. CE may return thousands of addresses holding 100 (random coincidences). You go into the game and let health drop to 90, come back, type 90 and hit Next Scan. CE keeps only the addresses that just changed from 100 to 90. Repeat a few times and one or two addresses remain, that's the real health.

Unknown initial value is for when you don't know the number, because it's encrypted or not shown clearly (for example the health bar is just an image). For First Scan you pick "Unknown initial value". Then each time the value goes up you choose Increased value, when it goes down you choose Decreased value, and when it stays the same you choose Unchanged. This filters by the trend of change instead of by the number, which is extremely powerful for hidden values.

Picking the right data type matters too: 4 Bytes (int) is the default for most game values, but sometimes it's Float (fractional health), Double, or 2 Bytes. Wrong type and it will never show up.

Once found, double-click the address to move it to the lower table, then tick Active to freeze the value so the game can't subtract health anymore.

## The problem: the address changes every run

You freeze health successfully, close the game, reopen it, and the old address points at garbage. Because the health object lives on the heap, it gets allocated somewhere different each run (plus ASLR, see Lesson 1.2 again). An absolute address is useless across sessions.

The fix is a pointer path: instead of remembering the final address, you find a chain of pointers starting from a fixed address (the game module's base, which doesn't change relatively) going through a few offsets to reach the value. Something like `[[base + 0x10] + 0x8] + 0x4C`. This chain is stable across runs because it hangs off the program's structure and not off the random heap location.

CE has Pointer Scan to find it automatically: right-click the health address, Pointer scan for this address, and CE works backwards to see which pointers lead there. You run the pointer scan, restart the game, then rescan with the new address to throw out the wrong paths. A few rounds and you get a reusable pointer path.

## Find out what accesses this address

This is the feature that turns CE from a toy into a real reversing tool. Right-click the health address and choose Find out what accesses this address. CE sets a hardware breakpoint and lists every instruction that touches that address. You'll see lines like:

```
mov [rax+4C], ecx      ; instruction that writes the new health
sub [rbx+4C], edx      ; instruction that subtracts health on a hit
```

The instruction `sub [rbx+4C], edx` is where the game subtracts health. Now you know exactly which code handles health, and you can look at the rbx register to get the base address of the character object, and from there work out the whole struct. This is exactly the "go from data to code" mindset of Lesson 0.4, except done on live memory.

## Auto Assembler and code injection

Once you've found the instruction that subtracts health, you can disable it. The simplest way is a NOP (see Lesson 17.1): right-click the instruction, Replace with code that does nothing, CE overwrites it with nops, and health stops dropping. But a blunt NOP can break other logic that shares the same instruction.

The cleaner way is code injection through an Auto Assembler (AA) script. The idea is like a code cave: you insert a jump from the original instruction to an empty region, do your extra work there (for example skip the health subtraction only when it's the player's character and not some other address), then jump back. CE generates the script skeleton from the Auto Assemble menu, the "Code injection" template. A typical AA script:

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

`aobscanmodule` (array-of-bytes scan) finds the instruction by byte pattern instead of a hard-coded address, so the script survives across runs and even some minor updates. This is a pattern you'll see again when writing hooks (Lesson 17.3).

## ReClass.NET: rebuilding structs in memory

When `find out what accesses` gives you the base address of the character object, you'll want to know the whole struct: health at offset 0x4C, where's mana, where are the coordinates. ReClass.NET does exactly that: you point it at the base address, it shows the memory region as a table and lets you assign a type to each offset (int, float, pointer, string, nested struct). Bit by bit you rebuild the object's struct definition, just like recovering structs in IDA in Lesson 3.3, only on live memory instead of a static binary. Once the struct is built you export it to a C++ header and reuse it when writing tools.

## Why this lesson matters beyond games

Strip off the game costume and here's what you just learned: scanning memory to locate data, tracing pointer paths to get stable addresses through ASLR, hardware breakpoints to find code that touches data, code injection via AOB scan, and rebuilding structs at runtime. All five skills are the bread and butter of malware analysis and of any dynamic analysis. Cheat Engine just happens to be the most fun way to practice them.

## Lab
See `labs/13.5/`. Use the bundled Cheat Engine Tutorial (legal, made for learning) or an offline game of your own: find values with exact and unknown scans, build a pointer path that survives a restart, use find out what accesses to find the handling instruction, and try a simple AA script.

## Key takeaways
Only use it on your own offline/single-player games, since online is cheating and illegal. Use an exact value scan when you know the number, and unknown with increased/decreased when the value is hidden, picking the right type (4 Bytes, Float...). Heap addresses change every run, so you need a pointer path hanging off the module base to be stable.

Find out what accesses this address sets a hardware breakpoint to find code that touches the data, which is going from data to code. Code injection via an AA script and aobscanmodule is cleaner and more durable than a blunt NOP. ReClass.NET rebuilds runtime structs, like recovering structs in IDA but on live memory, and all of these skills carry over fully to malware analysis and any dynamic analysis.
