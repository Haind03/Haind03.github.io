---
title: "Lesson 3.3: Structs in assembly and the art of recovering them"
date: 2022-06-05 14:55:00 +0700
categories: ["Technique Reverse", "Part 03 · C"]
tags: [reverse-engineering, c]
render_with_liquid: false
---
There's a moment in a reverser's life you'll remember forever: the first time you assign a struct to a pointer in IDA, and a whole pseudocode function that was a tangled mess suddenly turns into code that reads like a book. `*(a1 + 8)` becomes `player->score`, `*(a1 + 16)` becomes `player->name`. Recovering structs is one of the highest-return skills when reversing C/C++ code. This lesson teaches you to recognize a struct and rebuild it.

## What a struct looks like in assembly

The CPU doesn't know what a struct is. To it, a struct is just a block of contiguous bytes, and accessing a field is taking the base address and adding a fixed offset. That's exactly the fingerprint you need to look for.

Say there's this C struct:

```c
struct Player {
    int   id;        // offset 0, 4 bytes
    int   score;     // offset 4, 4 bytes
    char  name[16];  // offset 8, 16 bytes
    int   level;     // offset 24, 4 bytes
};
```

A function that takes a `Player*` pointer and reads the fields comes out as assembly like this:

```asm
; rcx = pointer to Player (first parameter on Windows x64)
mov  eax, [rcx]          ; read id      -> offset 0
mov  edx, [rcx+4]        ; read score   -> offset 4
lea  r8,  [rcx+8]        ; get the address of name -> offset 8
mov  r9d, [rcx+18h]      ; read level   -> offset 24 (0x18)
```

Notice the pattern: the same base register (`rcx`) is added to fixed constants `+0`, `+4`, `+8`, `+0x18`. That's the signature of a struct. Each offset is a field.

## Telling a struct from an array

Beginners often mix these two up, but they differ clearly in how the address is computed.

An array has an index multiplied by the element size, so the offset is a variable. You see `[base + index*scale]`, where `index` is a register that changes in a loop and `scale` is 1/2/4/8.

```asm
mov eax, [rsi+rcx*4]   ; arr[rcx], an int array
```

A struct has a constant offset, and each field can be a different type. You see `[base + constant]`.

```asm
mov eax, [rsi+8]       ; some_struct->field_at_8
```

Quick rule: multiplication by an index (`*4`, `*8`) means think array, while adding fixed constants with fields of different types means think struct. An array of structs combines both: `[base + index*sizeof_struct + field_offset]`, for example `[rsi + rcx*32 + 4]` is `players[rcx].score` when the struct is 32 bytes wide.

## The padding and alignment trap

![Struct layout in memory with padding](/assets/img/re/part-03/struct-layout.svg)

Don't expect the fields to sit tightly together. The compiler inserts padding bytes so each field sits at an address divisible by its size (alignment). For example:

```c
struct Messy {
    char  a;    // offset 0
    int   b;    // offset 4  (NOT 1, because int needs 4-byte alignment)
    char  c;    // offset 8
    // 7 bytes of padding here
    double d;   // offset 16 (double needs 8-byte alignment)
};  // sizeof = 24, not 14
```

So when you see the offset jump from `+0` to `+4` even though the first field is only 1 byte, don't panic: that's padding. When you rebuild the struct in the tool, declare the right type for each field and the tool computes the padding for you. If the offsets are still off, it's usually because you guessed the type of an earlier field wrong.

## Recovering a struct in IDA

This is the real workflow, repeated over and over. First open the decompiler (F5), where you see the ugly `*(a1 + N)` pile. Then open Local Types (Shift+F1) or Structures (Shift+F9) and create a new struct. You can type the C declaration directly:

```c
struct Player { int id; int score; char name[16]; int level; };
```

Go back to the pseudocode, right-click the pointer variable (`a1`), and choose "Convert to struct pointer", or set the type with the `Y` key and type `Player *`. IDA instantly changes every `*(a1 + 8)` to `a1->name`. Read it again, and fix the field names to match their meaning as you understand more.

A tip: if you don't know yet what's in the struct, use the IDA feature that lets you read and add fields as you go. Each time you see a new offset being accessed, add a field at that offset. IDA also has "Create new struct from this access" in some versions to gather the offsets you've seen automatically.

## Recovering a struct in Ghidra

Similar but different operations. Open the Data Type Manager (the window at the bottom right), right-click the program's archive, and choose New > Structure. Add each field with a type and name, or use "Auto Create Structure": in the Decompiler, right-click the pointer variable and choose Auto Fill in Structure / Auto Create Structure, and Ghidra probes the accesses and builds a draft struct for you. Then assign the pointer type to the variable (right-click > Retype Variable, or Ctrl+L) and Ghidra updates the pseudocode. Refine the field names in the Data Type Manager, and every place that uses the struct updates with it.

Ghidra's strength is that Auto Create Structure is fairly smart with optimized code, while IDA gives a faster experience typing C declarations. Either works, what matters is the habit: when you see a pointer being accessed at several fixed offsets, build a struct right away.

## Before and after, why it's worth the effort

Before assigning the struct, the pseudocode:

```c
if ( *(a1 + 4) > 100 && *(_BYTE *)(a1 + 8) )
    *(a1 + 24) = *(a1 + 24) + 1;
```

After assigning `Player *`:

```c
if ( player->score > 100 && player->name[0] )
    player->level++;
```

The same code, but the second you can read and understand in two seconds. Multiply that difference by hundreds of functions in a real program and you see why the pros take the trouble to build structs from the start.

## Lab

Source code and instructions are at `labs/3.3/`. In short: build a C program that uses a struct with several field types, open it in IDA or Ghidra, read the raw pseudocode, then rebuild the struct and compare before/after. The file `solution.md` has the struct layout and each field's offset for you to check against, but build it yourself before opening it.

## Key takeaways
A struct in assembly is a base address plus a constant offset, and each offset is a field. Arrays use `[base + index*scale]` with a changing index, while structs use `[base + constant]` with different types. Padding/alignment makes offsets non-contiguous, which is normal and not an error. In IDA you use Local Types/Structures, type the C declaration, and assign the type with `Y`, and in Ghidra you use the Data Type Manager, Auto Create Structure, and retype with Ctrl+L. Building structs is one of the highest-return things when reading C/C++ code.
