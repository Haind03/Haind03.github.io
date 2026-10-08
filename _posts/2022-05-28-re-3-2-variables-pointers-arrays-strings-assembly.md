---
title: "Lesson 3.2: Variables, pointers, arrays and strings in assembly"
image:
  path: /assets/img/covers/re-3-2-variables-pointers-arrays-strings-assembly.webp
  alt: "Lesson 3.2: Variables, pointers, arrays and strings in assembly"
date: 2022-05-28 21:14:00 +0700
categories: ["Reverse Engineering", "Part 03 · C"]
tags: [reverse-engineering, c]
render_with_liquid: false
---
C code revolves around four things, variables, pointers, arrays and strings. The compiler turns all of them into similar-looking memory accesses, so at a glance they're easy to mix up. But each has its own pattern in assembly. Learn to recognize them and you can read most C code without the source.

All the asm below is real output of `gcc -O0` on the file `datatypes.c`, Intel syntax, System V (Linux). On Windows the order of parameter registers is different (rcx, rdx...) but the idea is identical.

## Local and global variables

Where a variable lives tells you what kind it is.

Local variables live on the stack, always accessed through `rbp` (or `rsp`) with an offset:

```asm
mov    DWORD PTR [rbp-0x4], 0x0     ; a local int variable = 0
```

`[rbp-something]` is almost certainly a local variable. IDA names them `var_4`, `var_8`. Ghidra calls them `local_...`.

Global variables live at a fixed address in the `.data` section (with an initial value) or `.bss` (initialized to 0). On x64 they're accessed through an address relative to `rip` (RIP-relative):

```asm
mov    edx, DWORD PTR [rip+0x2db1]   ; # 4010 <g_initialized>   read a global variable
mov    DWORD PTR [rip+0x2dbe], eax   ; # 4028 <g_zero>          write a global variable
```

The comments `<g_initialized>` and `<g_zero>` are added by objdump itself. They're symbol names because this file isn't stripped. In a real stripped binary you only see `[rip+offset]` pointing to an address in `.data`, and that's the sign of a global variable. IDA displays it as `dword_xxxx`.

So `[rbp-x]` is local, and `[rip+x]` (or an absolute address in .data/.bss) is global.

## Pointers

![Pointers and arrays in memory](/assets/img/re/part-03/pointers-arrays.svg)

A pointer is a variable whose value is an address. What confuses beginners is the dereference step, taking the value at that address. In assembly, a dereference is always two steps, load the pointer into a register, then access through that register's brackets.

Look at the function `my_strlen`:

```asm
mov    rax, QWORD PTR [rbp-0x18]   ; rax = pointer s (read the pointer variable)
movzx  eax, BYTE PTR [rax]         ; eax = *s   (dereference: read the byte at address rax)
test   al, al                      ; compare that byte with 0
jne    ...                         ; not '\0' yet, keep looping
```

In the first two lines, `[rbp-0x18]` is the pointer variable `s` itself (a pointer is also an 8-byte local variable), while `[rax]` is what `s` points to. Telling "reading the pointer" apart from "reading what the pointer points to" is the main skill here.

A pointer is 8 bytes so it uses `QWORD PTR`. A `QWORD PTR` load followed right away by an access through `[register]` usually means a pointer.

### Pointer to pointer

It's just one more level. The function `retarget(char **pp, char *newtarget)` writes `*pp = newtarget`:

```asm
mov    rax, QWORD PTR [rbp-0x8]    ; rax = pp (the outer pointer)
mov    rdx, QWORD PTR [rbp-0x10]   ; rdx = newtarget
mov    QWORD PTR [rax], rdx        ; *pp = newtarget  (write into the cell pp points to)
```

The last line writes `rdx` into `[rax]`, the memory cell `pp` points to. Each level of pointer adds one more "load then access through brackets". Count the levels of brackets and you've counted the stars.

## Arrays

Accessing `arr[i]` is really `*(arr + i)`, and since each element is several bytes wide, the index has to be multiplied by the element size (the scale). Look at the loop summing an int array in `sum_array`:

```asm
mov    eax, DWORD PTR [rbp-0x4]    ; eax = i
cdqe                               ; extend i to 64-bit
lea    rdx, [rax*4+0x0]            ; rdx = i*4   (4 = sizeof(int), this is the scale)
mov    rax, QWORD PTR [rbp-0x18]   ; rax = arr (base address)
add    rax, rdx                    ; rax = arr + i*4
mov    eax, DWORD PTR [rax]        ; eax = arr[i]
add    DWORD PTR [rbp-0x8], eax    ; total += arr[i]
```

The pattern is `index * element_size` added to the base. `*4` means an int array (or 32-bit pointers), `*8` is a long array or 64-bit pointers, `*2` is a short array. The compiler often folds all of it into a single instruction like `mov eax, [rax+rcx*4]`, which you learn to read as "array element".

IDA/Ghidra often recognize it and show `arr[i]`, but when they guess the type wrong, the scale number `*4`, `*8` helps you fix it by hand.

## C strings

A C string has no length field. It's an array of `char` ending with a `0x00` byte (the null terminator). So every string operation is a loop that runs until it hits a 0 byte. Know that pattern well.

Look back at `my_strlen`, where the loop reads each byte (`movzx eax, BYTE PTR [rax]`), `test al, al` asks whether it's 0 yet, and if not it advances the pointer (`add QWORD PTR [rbp-0x18], 1`) and counts one more. "Read a byte, then test al, al", repeated, is the signature of string handling.

There are a few variants. Comparing two strings has two pointers advancing together, comparing each pair of bytes and exiting when they differ. That's the core of `strcmp`, and where passwords often get compared. Copying a string (`strcpy`) reads a byte from the source, writes it to the destination, and stops at 0. String literals sit in `.rdata`/`.rodata`, accessed via `lea rax, [rip+offset]`, and objdump and IDA show the string content directly, so the Strings window leads you to where it's used.

In a crackme, look for the loop "read a byte, test, jump" next to a string literal. That's usually where the input is compared with the answer.

## Letting the decompiler help

When the data types are right, IDA/Ghidra pseudocode reads like real C. When it guesses wrong (for example shows a pointer as `int`), you set the type yourself. In IDA, put the cursor on the variable and press `Y` to edit the type, or `N` to rename. In Ghidra, `Ctrl+L` retypes and `L` renames.

Every time you change a variable to `char *` or `int[5]`, the decompiler updates every place that uses it and the whole function clears up. That's the normal loop of read, guess the type, set the type, read again.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 3.2</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/3.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/3.2/src/datatypes.c" download><i class="fa-solid fa-download"></i>src/datatypes.c</a>
</div>
</div>

This lab trains your eye to tell four basic C data kinds apart when reading assembly or pseudocode, without leaning on symbol names. Build `datatypes.c` unoptimized so it stays readable. On Linux or WSL:

```
gcc -O0 -g -o datatypes datatypes.c
```

On 64-bit Windows with MinGW:

```
x86_64-w64-mingw32-gcc -O0 -g -o datatypes.exe datatypes.c
```

Or with MSVC:

```
cl /Od /Zi datatypes.c
```

Open the binary in IDA or Ghidra, run auto-analysis, and answer the following function by function. In `main`, which instructions read and write the globals `g_initialized` and `g_zero`, what kind of addressing do they use (the hint is RIP-relative), and where does the local variable `local` sit relative to `rbp`? In `my_strlen`, find the two instructions that dereference the pointer `*s` and explain why it takes two steps, then mark the loop that walks the string and the instruction that checks for the null terminator. In `sum_array`, find the formula that computes the address of `arr[i]`, read off the scale, and say what element size it implies. In `retarget`, find the instruction that performs `*pp = newtarget` and explain why this is a pointer to a pointer. Finally, rename and retype a few variables in the decompiler (`N` and `Y` in IDA, `L` and `Ctrl+L` in Ghidra) and watch how the pseudocode changes.

Two things to think about afterwards. If the binary were stripped, could you still tell globals from locals, and based on what? And if you rebuild with `-O2`, does the compiler keep the dereference steps separate?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

All the assembly below is real `gcc -O0` output (System V, Intel syntax). Addresses on your machine may differ, but the patterns are the same.

In `main`, globals are accessed RIP-relative:

```asm
mov    edx, DWORD PTR [rip+0x2db1]   ; # <g_initialized>   reads g_initialized
mov    DWORD PTR [rip+0x2dbe], eax   ; # <g_zero>          writes g_zero
```

The local `local` lives on the stack as `[rbp-x]`, for example `mov DWORD PTR [rbp-0x24], 0x2a` (0x2a is 42). The rule is that `[rip+...]` or a fixed address in .data/.bss means global, and `[rbp-...]` means local.

The pointer dereference in `my_strlen` looks like this:

```asm
mov    rax, QWORD PTR [rbp-0x18]   ; rax = s        (reads the pointer variable itself)
movzx  eax, BYTE PTR [rax]         ; eax = *s       (reads the byte at the address s points to)
```

It takes two steps because the CPU can't read the pointer variable and dereference it in a single instruction. You first load the pointer's value into a register, and only then access memory through `[register]`.

Array access in `sum_array`:

```asm
lea    rdx, [rax*4+0x0]            ; rdx = i*4      scale = 4
mov    rax, QWORD PTR [rbp-0x18]   ; rax = arr
add    rax, rdx                    ; rax = arr + i*4
mov    eax, DWORD PTR [rax]        ; eax = arr[i]
```

The scale is 4, so each element is 4 bytes wide, which means `int`. A `*8` would mean 8-byte elements (a long or a 64-bit pointer).

The pointer to a pointer in `retarget`:

```asm
mov    rax, QWORD PTR [rbp-0x8]    ; rax = pp
mov    rdx, QWORD PTR [rbp-0x10]   ; rdx = newtarget
mov    QWORD PTR [rax], rdx        ; *pp = newtarget
```

The last line writes into `[rax]`, the cell that `pp` points to. `pp` is itself a pointer, and it points to another pointer (`p` in `main`), so there are two levels. You load `pp` once and then write through the brackets once, which corresponds to `char **`.

The string loop in `my_strlen`:

```asm
.loop:
  add  DWORD PTR [rbp-0x4], 1      ; n++
  add  QWORD PTR [rbp-0x18], 1     ; s++  (advance the pointer one byte)
.check:
  mov  rax, QWORD PTR [rbp-0x18]
  movzx eax, BYTE PTR [rax]        ; read *s
  test al, al                      ; *s == 0 ?  <-- null terminator check
  jne  .loop                       ; not zero yet, so loop
```

`test al, al` followed by `jne` is the null terminator check, and it's the common signature of every C string-processing loop.

On the two questions, a stripped binary still lets you tell the two kinds apart, because you go by the access pattern (RIP-relative or a fixed .data address versus `[rbp-x]`) and not by symbol names. With `-O2` the compiler often merges steps (for example `movzx eax, BYTE PTR [rdi]` directly, dropping the intermediate variable) and sometimes vectorizes or unrolls the string loop. That's harder to read, but the `index*scale` array formula and the null-check pattern are still there.

</details>

## Key takeaways
`[rbp-x]` is a local variable, while `[rip+x]` or a fixed address in .data/.bss is a global variable. A pointer is a variable holding an address, and a dereference is always loading the pointer into a register and then accessing `[register]`, so counting the levels of brackets is counting the stars. An array access adds `index * element_size` to the base, where `*4` is int and `*8` is a 64-bit pointer.

C strings end with a 0 byte, and the pattern "read a byte, test al,al, jump" is string handling. Setting the right type in the decompiler (`Y` in IDA, `Ctrl+L` in Ghidra) makes the whole function much easier to read.
