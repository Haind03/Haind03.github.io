---
title: "Lesson 3.3: Structs in assembly and the art of recovering them"
image:
  path: /assets/img/covers/re-3-3-structs-assembly-art-recovering-them.webp
  alt: "Lesson 3.3: Structs in assembly and the art of recovering them"
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

The goal here is to recognize a struct in a binary and rebuild it in IDA or Ghidra, watching the pseudocode change from `*(a1 + N)` to `player->field`. Build `inventory.c` unoptimized so it stays readable, with one of these commands:

```
# Linux
gcc -O0 -g -o inventory inventory.c

# Windows, MSVC (Developer Command Prompt)
cl /Od /Zi inventory.c

# Windows, MinGW
gcc -O0 -g -o inventory.exe inventory.c
```

Open the binary in your tool and run auto-analysis. Find the two functions `update_player` and `print_player`. If the binary is stripped, start from the format string in `print_player` (the one containing `id=`, `score=` and so on) and follow the xref back. Read the pseudocode of `update_player` before assigning any struct and write down every offset accessed on the first pointer parameter. Then rebuild `struct Player` in the tool, inferring each field's type from how it is used: a 4-byte read is an int, a 1-byte access is a char, and use with a double instruction means a double. Assign `Player *` to the parameter of both `update_player` and `print_player` and read the pseudocode again. Finally, check `sizeof` and the offsets against your layout, paying attention to the padding.

Some questions to think about. Why does `score` sit at offset 8 and not 5, even though `rank` takes only 1 byte? Why is `sizeof(struct Player)` 48 and not the sum of the fields (4+1+4+16+8+4 = 37)? And which field gets the most padding in front of it, and why?

<div class="lab-box">
<div class="lab-head"><b>LAB 3.3</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/3.3/src/inventory.c" download><i class="fa-solid fa-file-code"></i>src/inventory.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Build the struct yourself before reading this. The real layout of `struct Player`, checked with `offsetof` and `sizeof` (gcc x86-64, and the same result with MSVC x64 since the alignment rules are the same), is:

| Field | Type | Offset | Size |
|---|---|---|---|
| id | int | 0 | 4 |
| rank | char | 4 | 1 |
| (padding) | | 5 | 3 |
| score | int | 8 | 4 |
| name | char[16] | 12 | 16 |
| (padding) | | 28 | 4 |
| balance | double | 32 | 8 |
| level | int | 40 | 4 |
| (trailing padding) | | 44 | 4 |

`sizeof(struct Player)` is 48.

On the padding: `rank` at offset 4 takes only 1 byte (up to offset 5). But `score` is an `int` and needs an address divisible by 4, so the compiler inserts 3 padding bytes (offsets 5, 6, 7) to push `score` to offset 8. That is why you see the accesses jump from `+4` to `+8`. `name[16]` ends at offset 28. `balance` is a `double` and needs 8-byte alignment, so 4 padding bytes (offsets 28 to 31) put `balance` at offset 32. The whole struct must have a size divisible by the largest alignment inside it (8, because of the `double`), so after `level` (which ends at offset 44) another 4 bytes bring the total to 48. The fields actually in use add up to 37 bytes, but with padding the struct takes 48, which is something newcomers often miscount when rebuilding a struct. The most padding in front of a field is at `score` (3 bytes) and `balance` (4 bytes), and `balance` gets the largest gap.

The `update_player` pseudocode before assigning the struct (as IDA might show it, with variable names that can differ) is:

```c
void update_player(__int64 a1, int a2)
{
    *(_DWORD *)(a1 + 8) += a2;                         // score += gained
    if ( *(_DWORD *)(a1 + 8) > 100 && *(_BYTE *)(a1 + 12) )  // score > 100 && name[0]
    {
        ++*(_DWORD *)(a1 + 40);                        // level++
        *(_BYTE *)(a1 + 4) = 'A';                      // rank = 'A'
    }
    *(double *)(a1 + 32) = *(double *)(a1 + 32) + (double)a2 * 1.5;  // balance
}
```

Notice the offsets that appear: 8 (score), 12 (name), 40 (level), 4 (rank), 32 (balance). From them you infer the types. `+8` and `+40` are read as 4 bytes (DWORD), so they are int. `+12` is read as 1 byte (BYTE), so it is a char or the start of a char array. `+4` is written as a 1-byte char. `+32` is used in a double operation, so it is a double.

After building `struct Player` and assigning `Player *p`:

```c
void update_player(Player *p, int gained)
{
    p->score += gained;
    if ( p->score > 100 && p->name[0] )
    {
        ++p->level;
        p->rank = 'A';
    }
    p->balance = p->balance + (double)gained * 1.5;
}
```

It nearly matches the original source, and that is the value of recovering the struct.

When you have no source, you recognize each field's type like this. An offset read or written with 4 bytes (`_DWORD`, an `eXX` register) is most likely an `int`. An offset read or written with 1 byte (`_BYTE`, an `Xl` register) is a `char`, or the first element of a char array if a loop later walks through it. An offset used in a floating point instruction (`movsd`, `addsd`, or a `double` type in the pseudocode) is a `double`. A continuous range of offsets accessed with a running index is an array. Here `name` starts at offset 12 and `strcpy` and `printf %s` walk through it, so it is a `char[16]`. If you assign types and the offsets of the later fields come out shifted, you usually guessed the size of an earlier field wrong (for example declaring `short` instead of `int`). Fix that field and everything lines up again.

</details>

## Key takeaways
A struct in assembly is a base address plus a constant offset, and each offset is a field. Arrays use `[base + index*scale]` with a changing index, while structs use `[base + constant]` with different types. Padding/alignment makes offsets non-contiguous, which is normal and not an error. In IDA you use Local Types/Structures, type the C declaration, and assign the type with `Y`, and in Ghidra you use the Data Type Manager, Auto Create Structure, and retype with Ctrl+L. Building structs is one of the highest-return things when reading C/C++ code.
