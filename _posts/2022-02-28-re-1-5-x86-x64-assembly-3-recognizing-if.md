---
title: "Lesson 1.5: x86/x64 Assembly (3), recognizing if, loops, switch, arrays and structs"
image:
  path: /assets/img/covers/re-1-5-x86-x64-assembly-3-recognizing-if.webp
  alt: "Lesson 1.5: x86/x64 Assembly (3), recognizing if, loops, switch, arrays and structs"
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

The file `structures.c` packs in all five constructs above, one function each. `sum_array` is a loop plus access to an int array, `classify` is a multi-level nested if/else, `action_name` is a switch with five consecutive cases (a jump table candidate), and `level_up` accesses a struct through offsets. The goal is to point out the loop, the nested if, the switch jump table, the array access and the struct access by hand in a real binary, and match the asm against source you already know.

Build it at both optimization levels. The `-O0` build follows the templates closely and is easy to read, while the `-O2` build shows how much harder real-world code is.

On Linux or macOS with gcc or clang:

```
gcc -O0 -g -o structures_O0 structures.c
gcc -O2    -o structures_O2 structures.c
```

On Windows, from a Developer Command Prompt with MSVC:

```
cl /Od structures.c
cl /O2 structures.c
```

Open the binary in Ghidra (import, then auto-analyze) or IDA, go through each function in turn and answer a few questions. In `sum_array`, find the instruction that jumps backward to mark the loop, and work out the scale factor used for the array access and how it matches the `int` type. In `classify`, count the `cmp` plus conditional jump pairs and redraw the if/else tree from the jump labels. In `action_name`, decide whether the compiler built a jump table or translated the switch into an if/else chain, and if there is a table, find its address and entries. In `level_up`, list which offsets are added to the struct pointer and match them to the fields of `struct Player`. Finally compare `sum_array` between `-O0` and `-O2`: does the counter `i` still live on the stack at `-O2` or does the compiler keep it in a register, and is the loop distorted by unrolling or a changed condition form?

A few hints help. Use the graph view (the `Space` key in IDA) to see the branching blocks instead of reading text sequentially. In Ghidra the decompiler window (double-click a function) gives an approximate C version to compare with, but try reading the asm yourself first and only then open the decompiler to check. If you can't spot a jump table, look for a `jmp` to a register (an indirect jump) with a `*8` (x64) or `*4` (x86) computation right before it. Compare on your own first and open the solution once you have finished.

<div class="lab-box">
<div class="lab-head"><b>LAB 1.5</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/1.5/src/structures.c" download><i class="fa-solid fa-file-code"></i>src/structures.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Do it yourself first. What follows is a function-by-function comparison based on an x86-64 `gcc -O0` build (Linux, System V, so the first parameters are in `rdi`, `rsi` and so on). MSVC `/Od` differs slightly in the parameter registers (`rcx`, `rdx` and so on) and uses `rbp` the same way, but the templates are identical.

### 1) sum_array: loop and array

Typical asm at `-O0`, with the prologue trimmed:

```asm
    mov  [rbp-4], 0          ; total = 0
    mov  [rbp-8], 0          ; i = 0
    jmp  .check
.body:
    mov  eax, [rbp-8]        ; eax = i
    movsxd rax, eax          ; extend i to 64 bits to use as an index
    mov  rcx, [rbp-24]       ; rcx = arr (base pointer)
    mov  eax, [rcx + rax*4]  ; eax = arr[i]   <-- scale *4 => int
    add  [rbp-4], eax        ; total += arr[i]
    add  dword [rbp-8], 1    ; i++
.check:
    mov  eax, [rbp-8]
    cmp  eax, [rbp-28]       ; compare i with n
    jl   .body               ; if i < n, JUMP BACK UP to .body  <-- the loop
    mov  eax, [rbp-4]        ; return total
```

The instruction that marks the loop is `jl .body`, jumping backward, and that is the loop signature. The scale factor is `rax*4`: a 4-byte element, which matches the `int` type. With a `char*` you would see `*1` and with a `double*` you would see `*8`. The compiler puts the condition at the end and enters the loop with an initial `jmp .check`, a common template for `for` and `while` at `-O0`.

### 2) classify: nested if/else

The three thresholds (90, 70, 50) become three cmp plus jump pairs:

```asm
    cmp  dword [rbp-4], 90
    jl   .not_A
    mov  al, 'A'             ; return 'A'
    jmp  .done
.not_A:
    cmp  dword [rbp-4], 70
    jl   .not_B
    mov  al, 'B'
    jmp  .done
.not_B:
    cmp  dword [rbp-4], 50
    jl   .else_F
    mov  al, 'C'
    jmp  .done
.else_F:
    mov  al, 'F'
.done:
```

There are three `cmp` plus `jl` pairs. Each "true" branch ends with `jmp .done`, and that trailing jmp at the end of a body is the sign that an else branch follows. The logic is inverted: `if (score >= 90)` becomes `cmp 90; jl .not_A` (if it is LESS than 90, skip the A branch), which is very typical. The whole nested if/else tree can be rebuilt from the chain of labels `.not_A -> .not_B -> .else_F`.

### 3) action_name: switch

With 5 consecutive cases 0..4, gcc, clang and MSVC at optimized levels usually build a jump table. A common form:

```asm
    mov  eax, [rbp-4]        ; action
    cmp  eax, 4
    ja   .default           ; >4 (unsigned) -> default. Note ja also catches negative numbers
    mov  eax, eax            ; zero-extend
    lea  rcx, [rel .table]
    movsxd rax, dword [rcx + rax*4]  ; the table holds 4-byte offsets
    add  rax, rcx
    jmp  rax                 ; INDIRECT JUMP to the case  <-- jump table signature
.table:
    dd  .case0 - .table
    dd  .case1 - .table
    dd  .case2 - .table
    dd  .case3 - .table
    dd  .case4 - .table
```

The signature is `cmp eax, 4` plus `ja .default` (the bounds check), then `jmp rax` (an indirect jump through a register) with the target loaded from `[table + index*4]`. At `-O0`, some compilers instead translate this switch into an if/else chain comparing 0, 1, 2, 3, 4 in turn. If you see that, it is correct and there is no table, and building with `-O2` forces a jump table out. IDA and Ghidra recognize the table by themselves and label it `jpt_` along with the list of cases, so you don't have to chase offsets by hand. One trick worth knowing is that `ja` (unsigned) guards both the upper bound and negative values in one instruction, because a negative number treated as unsigned is huge.

### 4) level_up: struct through offsets

```asm
    mov  rax, [rbp-8]       ; rax = p (struct pointer)
    mov  edx, [rax+8]       ; p->level      (offset 8)
    add  edx, 1
    mov  [rax+8], edx       ; p->level += 1
    mov  rax, [rbp-8]
    mov  edx, [rax+4]       ; p->score      (offset 4)
    add  edx, 100
    mov  [rax+4], edx       ; p->score += 100
    mov  rax, [rbp-8]
    cmp  dword [rax+4], 500 ; if (p->score >= 500)
    jl   .skip
    mov  rax, [rbp-8]
    mov  byte [rax+12], 'S' ; p->grade = 'S' (offset 12)
.skip:
```

Matching the offsets to `struct Player`:

| Offset | Field | Type | Size |
|---|---|---|---|
| 0 | id | int | 4 |
| 4 | score | int | 4 |
| 8 | level | int | 4 |
| 12 | grade | char | 1 |

To tell it apart from an array, notice that the offset constants here are different (`+4`, `+8`, `+12`) and added to the same pointer, with no scaled index. That is a struct, not an array. `grade` is a `char`, so it uses `mov byte`, while the int fields use 32-bit operations, so the instruction size also gives away the field type. In IDA, declaring `struct Player` and setting the type of `p` (key `Y`) turns `[rax+8]` into `p->level`, which reads much better.

### 5) Comparing -O0 and -O2 (sum_array)

The typical differences are these. The counter `i` and `total` are no longer on the stack, because the compiler keeps them in registers (for example `total` in `eax` and `i` in `ecx`), so the repeated `[rbp-x]` reads are gone. The prologue and epilogue are leaner, and sometimes `rbp` is dropped entirely as a frame pointer (frame pointer omission). The loop may change its condition form, or with a known constant n the compiler sometimes unrolls a few iterations or even computes the result in advance. At high optimization it may also use SIMD instructions to add several elements at once.

The lesson is that the templates of this lesson are most accurate at `-O0`. Real-world code is usually built at `-O2` or higher, so you have to get used to variables living in registers and structures being shuffled. The decompiler (Ghidra or Hex-Rays) exists to carry that heavy part, but understanding the original templates tells you what the decompiler is reconstructing and when it gets it wrong.

</details>

## Key takeaways
For if/else, look for a cmp plus a conditional jump over a block, where a `jmp` at the end of the if body usually means there's an else, and remember the condition logic is often inverted. Loops are recognized by a jump back up, and you look for four pieces: init, condition, body, increment. do...while puts the condition at the end of the block.

A switch with many consecutive cases becomes a jump table, recognized by an indirect `jmp` plus `index*8`, and IDA/Ghidra rebuild the cases automatically. Arrays look like `[base + index*scale]` where the scale (1/2/4/8) gives the element size, while structs look like `[base + constant offset]` where each offset is a field. Building your own code and inspecting it is the fastest way to learn.
