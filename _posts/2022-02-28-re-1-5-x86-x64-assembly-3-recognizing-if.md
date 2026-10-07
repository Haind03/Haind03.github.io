---
title: "Lesson 1.5: x86/x64 Assembly (3), recognizing if, loops, switch, arrays and structs"
date: 2022-02-28 23:13:00 +0700
categories: ["Technique Reverse", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Lesson 1.3 gave you the instruction set. Lesson 1.4 gave you the stack frame. Now for the most fun part: putting them together to read out high-level structure. A compiler takes your tidy `for` statement and grinds it into a pile of `cmp`, `jmp`, `inc`. The reverser's job is to go the other way: look at that pile and recognize "ah, this is a loop".

Good news: compilers are very mechanical. They translate each construct using a few fixed templates. Learn the templates and you can read, like memorizing letter shapes. This lesson is that set of templates.

## if / else: one jump skipping a block

The simplest construct, you already met it in lesson 1.3. The key point is that the compiler jumps over the block of instructions when the condition isn't met. Notice the logic is often inverted: `if (a == b)` in C gets translated to "if a is NOT equal to b, jump away".

```asm
    mov  eax, [rbp-4]     ; eax = x
    cmp  eax, 5
    jne  else_branch      ; x != 5, jump down to else
    mov  dword [rbp-8], 1 ; y = 1  (if body)
    jmp  end_if
else_branch:
    mov  dword [rbp-8], 2 ; y = 2  (else body)
end_if:
```

Translated to C:

```c
if (x == 5)
    y = 1;
else
    y = 2;
```

The pattern is a `cmp`/`test`, a conditional jump to the "else" label, and at the end of the if body an unconditional `jmp` that jumps over the else block. Seeing that `jmp` at the end of a block is the sign there's an `else`. Without it it's usually a plain `if`.

### Nested ifs

An if inside an if is just several layers of the template above stacked up, with more jump labels. Don't try to read it in one pass, follow it one cmp/jump pair at a time. IDA and Ghidra draw a graph view that shows the branching blocks much more clearly than reading text sequentially, use it.

## Loops: a jump backwards

This is the unmistakable signature of a loop: a jump instruction pointing back up to an address before it. Normal code runs downward, so seeing a jump upward almost certainly means a loop.

A typical `for (i = 0; i < n; i++)`:

```asm
    mov  dword [rbp-4], 0   ; i = 0
loop_check:
    mov  eax, [rbp-4]
    cmp  eax, [rbp-8]       ; compare i with n
    jge  loop_end          ; i >= n, exit
    ; ----- loop body here -----
    mov  eax, [rbp-4]
    inc  eax
    mov  [rbp-4], eax      ; i++
    jmp  loop_check        ; <--- JUMPS BACK UP, the sign of a loop
loop_end:
```

Translated to C:

```c
for (int i = 0; i < n; i++) {
    // loop body
}
```

To read a loop quickly, look for four pieces. There's the initialization of the counter before the label (here `i = 0`), the condition at the top (cmp plus the exit jump), the body in the middle, and finally the increment or decrement of the counter followed by a backwards jmp to the condition.

`while` and `for` compile to almost the same thing, the only difference being whether there's an init part and an increment part. `do...while` puts the condition at the end, so it's even more compact (no unconditional jmp at the start of the loop). Seeing the condition checked at the bottom of the loop block means `do...while`.

## switch-case: when the compiler uses a jump table

A small `switch` with a few cases is often compiled into a chain of if/else if (cmp against each value in turn). But when there are many cases with consecutive values (0, 1, 2, 3...), it uses a much faster trick: a jump table, a table of addresses. Instead of comparing one by one, it uses the value as an index straight into the table and jumps.

```asm
    mov  eax, [rbp-4]      ; eax = switch value
    cmp  eax, 3
    ja   default_case     ; greater than 3 (unsigned), go to default
    ; eax is used as the index into the address table
    lea  rcx, [jump_table]
    mov  rcx, [rcx + rax*8] ; fetch the address of case number eax (each entry is 8 bytes on x64)
    jmp  rcx              ; jump to the case

jump_table:
    dq case_0
    dq case_1
    dq case_2
    dq case_3
```

Translated to C:

```c
switch (x) {
    case 0: ...; break;
    case 1: ...; break;
    case 2: ...; break;
    case 3: ...; break;
    default: ...;
}
```

The pattern is a `cmp` bounding the upper limit with `ja` to default, then an indirect jump like `jmp [table + index*8]`. Seeing a `jmp` to a register (not a fixed label) along with a `*4` or `*8` is almost certainly a jump table. Good news: IDA and Ghidra recognize jump tables automatically and show the cases for you, no need to trace by hand.

## Array access: multiply by the element size

An array in memory is elements laid out one after another. To get `arr[i]`, the CPU computes `base address + i * element_size`. That multiplication gives away that it's an array, and also tells you the size of each element.

```asm
    mov  rax, [rbp-8]      ; rax = base pointer of the array
    mov  ecx, [rbp-4]      ; ecx = i
    mov  edx, [rax + rcx*4] ; edx = arr[i], each element 4 bytes -> int
```

Translated to C:

```c
int x = arr[i];   // arr is int*, so multiply by 4
```

Reading the multiplier tells you the type. A `*1` means a byte array (char, uint8), `*2` means short (16 bit), `*4` means int or float (32 bit), and `*8` means long long, double, or a pointer on x64.

The full syntax of an x86 memory operand is `[base + index*scale + displacement]`, for example `[rax + rcx*4 + 0x10]`. Each component means something, and the next section shows that this `displacement` is often the sign of a struct.

## Struct access: adding a fixed offset

A struct is also fields laid out one after another, but it differs from an array: you access it with a fixed offset (the field's position in the struct) rather than an index multiplied by a size. Seeing a pointer being added to different constants (0, 4, 8, 0x10...) to pull out values means it's a struct.

```asm
    mov  rax, [rbp-8]     ; rax = pointer to the struct
    mov  ecx, [rax]        ; read the field at offset 0
    mov  edx, [rax+4]      ; read the field at offset 4
    mov  r8,  [rax+8]      ; read the field at offset 8
```

Translated to C:

```c
struct Thing {
    int   a;   // offset 0
    int   b;   // offset 4
    void *c;   // offset 8
};
int x = t->a;
int y = t->b;
void *z = t->c;
```

Quick way to tell arrays from structs: an array uses a varying index times a size (`rcx*4`), a struct uses constant offsets (`+4`, `+8`). An array is "the same type, many elements", a struct is "many different types, each at a fixed spot".

In IDA you can declare a struct (press `Y` to set a type, or create the struct in Local Types) and assign it to the pointer, and `[rax+8]` instantly turns into `t->c`, which is a pleasure to read. Lesson [3.3](/posts/re-3-3-structs-assembly-art-recovering-them/) goes deep on recovering structs.

## Summary of the templates

Stick this next to your screen when you're starting out:

| What you see in asm | Most likely |
|---|---|
| `cmp`/`test` + conditional jump + `jmp` over a block | if / else |
| A jump back up to an address above | loop |
| A variable gets `inc`/`dec` then compared at the top/bottom of a block | loop counter |
| `jmp` to a register + `index*4` or `*8` from a table | switch with a jump table |
| `[base + index*scale]`, scale is 1/2/4/8 | array access, scale tells the type |
| `[base + constant]` with several different constants | struct access, the constants are field offsets |

Don't memorize blindly. The surest way is to write your own C code, build it, and open it in Ghidra/IDA to see what the compiler turned it into. That's exactly the lab below.

## Lab

The `labs/1.5/` folder has a C file that packs in all five constructs above. Build it (instructions are in the lab's README), open the binary in Ghidra or IDA, and point out by hand where the nested if is, where the loop is, where the switch jump table is, where the array is. When you're done, compare against `labs/1.5/solution.md`.

Try both optimization levels: build with `-O0` (easy to read, close to the templates) then rebuild with `-O2` (the compiler optimizes, more distortion). Compare the two to see how optimization makes code harder to read, this is a more valuable real-world lesson than any theory.

## Key takeaways
For if/else, look for a cmp plus a conditional jump over a block, where a `jmp` at the end of the if body usually means there's an else, and remember the condition logic is often inverted. Loops are recognized by a jump back up, and you look for four pieces: init, condition, body, increment. do...while puts the condition at the end of the block.

A switch with many consecutive cases becomes a jump table, recognized by an indirect `jmp` plus `index*8`, and IDA/Ghidra rebuild the cases automatically. Arrays look like `[base + index*scale]` where the scale (1/2/4/8) gives the element size, while structs look like `[base + constant offset]` where each offset is a field. Building your own code and inspecting it is the fastest way to learn.
