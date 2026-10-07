---
title: "Lesson 4.4: Exceptions, templates and lambdas, three modern C++ things that tangle up binaries"
image:
  path: /assets/img/covers/re-4-4-exceptions-templates-lambdas-three-modern-c.webp
  alt: "Lesson 4.4: Exceptions, templates and lambdas, three modern C++ things that tangle up binaries"
date: 2022-07-16 14:52:00 +0700
categories: ["Technique Reverse", "Part 04 · C++"]
tags: [reverse-engineering, cpp]
render_with_liquid: false
---
By now you can read classes, vtables, and so on. But real-world C++ code has three more things that make beginners panic when they open the decompiler: a try/catch block turns into a mess of confusing tables, a small function suddenly shows up in five or six near-identical copies, and a simple-looking lambda turns into a whole hidden class. Once you understand the mechanism behind these three, they stop being scary and become just noise you know how to skip.

## Templates: one source function, many binary functions

This is the easiest to understand so I'll start there. When you write a template:

```cpp
template <typename T>
T add_one(T x) { return x + (T)1; }
```

there's only one function in the source. But the compiler doesn't generate "one shared function" for all types. Each time you call it with a new type, it generates a whole separate function, called an instantiation. Calling `add_one<int>` and `add_one<double>` produces two completely different machine functions.

Look at the symbol list of the lab program and you see it right away:

```
int    add_one<int>(int)       -> _Z7add_oneIiET_S0_
double add_one<double>(double) -> _Z7add_oneIdET_S0_
```

And the asm of the int version (gcc -O0, name demangled):

```asm
_Z7add_oneIiET_S0_:        ; add_one<int>
    mov   [rbp-0x4], edi    ; x (parameter, int)
    mov   eax, [rbp-0x4]
    add   eax, 0x1          ; return x + 1
    ret
```

The double version uses SSE registers (xmm) and the `addsd` instruction instead of `add`, since it works on floating point. The same source logic, two different function bodies.

This has a few consequences when reversing. The binary bloats, because a template used with ten types is ten functions, and template-heavy libraries (STL, Boost) push the function count into the thousands. You'll also see many nearly identical functions, differing only in data size or instruction type, and you shouldn't assume the author copy-pasted, since that's template instantiation. To save effort, remember that understanding one version is understanding the whole family. Read `add_one<int>`, then just glance at the others to confirm the same logic, and name them consistently like `add_one_int`, `add_one_double` so you don't mix them up.

## Lambdas: a hidden class disguised as a function

A lambda looks like a tiny anonymous function, but the compiler turns it into an object. Specifically, this lambda:

```cpp
int base = n * 10;
auto make = [base](int k) { return base + k; };
make(7);
```

gets translated by the compiler into roughly:

```cpp
struct __lambda {
    int base;                 // capture by value -> field
    int operator()(int k) const { return base + k; }
};
__lambda make{ n * 10 };
make(7);                      // actually calls make.operator()(7)
```

Meaning each captured variable becomes a field of a hidden struct, and the lambda body becomes the `operator()` method of that struct. Calling the lambda is calling a method, so it has a `this` pointer just like lesson [4.1](/posts/re-4-1-c-through-reversers-eyes-name-mangling/) described.

Here's the real asm of the `operator()` of the lambda above (gcc -O0), you can see it right away:

```asm
main::{lambda(int)#1}::operator()(int) const:
    mov   [rbp-0x8], rdi     ; rdi = this (the lambda object holding the capture)
    mov   [rbp-0xc], esi     ; esi = k (the real parameter)
    mov   rax, [rbp-0x8]     ; rax = this
    mov   edx, [rax]         ; edx = this->base  (the capture is at offset 0)
    mov   eax, [rbp-0xc]     ; eax = k
    add   eax, edx           ; return base + k
    ret
```

Notice two things that confirm the model above: the first parameter `rdi` is `this` (SysV, on Windows it would be `rcx`), and `[rax]` reads the `base` field right at the start of the object. The capture has become data in the object, no longer a local variable.

When reversing, recognize a lambda by a small struct being built on the spot (the `mov`s writing the capture into an object on the stack), then a method call with that object as `this`. Its mangled name contains a string like `ZZ...EUl...` (U for unnamed lambda). IDA/Ghidra usually show a long convoluted name, just rename it to `lambda_xxx` to keep it easy.

## Exceptions: the price of try/catch

This is the part that tangles things the most. In the source, try/catch is tidy. In the binary, it splits into two parts: the normal running path (happy path) and the machinery that handles an exception, sitting separately, linked through data tables.

The two main ABIs differ quite a bit. On Linux with the Itanium C++ ABI, a `throw` makes the runtime call `__cxa_throw`, and then it walks back up the stack (stack unwinding) to find a handler. The information "which handlers this frame has, what needs cleaning up" isn't in the code but in dedicated sections: `.eh_frame`, `.gcc_except_table`. The place in code that catches the exception is called a landing pad. In the decompiler you see a function that seems to "end" at `ret` but still has stray code blocks after it that nobody calls directly, and those are landing pads, which the runtime jumps into during unwinding.

On Windows with MSVC, a different mechanism is used, with funclets (sub-functions for catch blocks) and unwind data in `.pdata`/`.xdata`. You'll see pointers to `FuncInfo` tables and `__CxxFrameHandler`, and a related function is `_CxxThrowException`.

What both have in common, practically, for the reverser is this. try/catch code is cut apart: the try body runs straight, and the catch part sits in a separate block that the main flow doesn't reach with a normal `jmp`, so don't panic when you see "orphan" code after a function, because that's usually a handler. Also don't get lost in the unwind tables unless you really need to. In 90% of cases when reversing a crackme or finding the main logic, you only need to know "this spot can throw, that one catches" and move on, and the EH tables themselves rarely hide secrets. Seeing a `__cxa_throw` / `_CxxThrowException` call tells you there's an exception exit from here, and seeing `__cxa_begin_catch` / `__CxxFrameHandler` means you're in the handling area.

## Putting it together: don't let the noise hide the signal

All three of these are the compiler generating extra code around the author's real logic. The general strategy is the same: recognize them, label them, then focus on the logic. A template is many copies of one function (understand one, infer the family). A lambda is a hidden class (find `operator()` and the capture fields). An exception is code cut apart (the happy path is the main thing, the handler comes later). Knowing these three templates, you read modern C++ code without being discouraged by the number of functions and the odd blocks.

## Lab

The file `modern.cpp` shows what three pieces of modern C++ turn into at the binary level, so that you aren't thrown off when you meet them in a decompiler later. The task is to build it, then find the two instantiations `add_one<int>` and `add_one<double>` in the symbols and compare their asm, find the lambda's `operator()` and identify which is `this` and which is the capture field, and mark out the try/catch block by finding the throw call and the handler that sits apart from it.

On Linux:

```
g++ -O0 -g -fno-inline -o modern modern.cpp
```

With MinGW on Windows:

```
g++ -O0 -g -fno-inline -o modern.exe modern.cpp
```

With MSVC in a Developer Command Prompt:

```
cl /EHsc /Zi modern.cpp
```

`-fno-inline` keeps the functions separate so they are easy to read, and `/EHsc` turns on exceptions for MSVC. A test run should print this:

```
add_one int=2 double=2.5
lambda=17
div=100
caught: divide by zero
```

Start with the template. List the symbols and look for the two copies of `add_one` with `nm -C modern | grep add_one`. How many functions are there, and why does one template in the source produce several machine functions? Then compare the asm of `add_one<int>` and `add_one<double>` with `objdump -d -M intel -C modern | less`. Which instruction does the int version use to add, and which registers and instructions does the double version use instead? Next the lambda. Find its `operator()` (the name contains `{lambda(int)#1}`, or the mangled form `_ZZ4mainENKUliE_clEi`). In its asm, work out what the first parameter (`rdi` on Linux) is, and what the line `mov edx, [rax]` is reading, relating it to the captured variable `base`. In `main`, find where the lambda object is built: the instructions that write the captured value into an area of the stack before the call are the hidden constructor of the closure.

For the exceptions, find the throw call in `main` or `safe_div`. On Linux look for `__cxa_throw` and `__cxa_allocate_exception`, and with MSVC look for `_CxxThrowException`. Work out where the catch block sits. On Linux, watch for blocks of code after the function's `ret` that the main flow never jumps to, which are landing pads. With MSVC you can also open the binary in PE-bear and find the `.pdata` and `.xdata` sections, which hold the unwind data for exceptions.

Two questions are worth thinking about. If a program uses both `std::vector<int>` and `std::vector<std::string>`, how many sets of vector functions do you expect in the binary? And why would capture by value and capture by reference give different field layouts in the closure? Do it yourself before opening the solution.

<div class="lab-box">
<div class="lab-head"><b>LAB 4.4</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/4.4/src/modern.cpp" download><i class="fa-solid fa-file-code"></i>src/modern.cpp</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

All the asm below is real output from `g++ -O0 -g -fno-inline` on Linux x86-64, demangled and annotated. MSVC differs in the details but the ideas are the same.

### Template

```
$ nm -C modern | grep add_one
000000000000148d W double add_one<double>(double)
000000000000147a W int add_one<int>(int)
```

There are two functions even though the source has a single template. The compiler generates a separate instantiation for each type that is called (`int` and `double`). The `W` means a weak symbol, so the linker can merge duplicate copies from several files.

`add_one<int>`:

```asm
_Z7add_oneIiET_S0_:
    mov   [rbp-0x4], edi    ; x
    mov   eax, [rbp-0x4]
    add   eax, 0x1          ; integer addition with 'add'
    ret
```

`add_one<double>` uses SSE registers and floating-point instructions:

```asm
_Z7add_oneIdET_S0_:
    movsd [rbp-0x8], xmm0   ; x (double) passed in xmm0
    movsd xmm1, [rbp-0x8]
    movsd xmm0, [constant 1.0]
    addsd xmm0, xmm1        ; floating-point addition with 'addsd'
    ret
```

The difference is the data type: int goes through general-purpose registers and `add`, while double goes through `xmm` and `addsd`. The logic `x + 1` is the same, but there are two function bodies.

### Lambda

The lambda's `operator()`:

```asm
main::{lambda(int)#1}::operator()(int) const:   ; _ZZ4mainENKUliE_clEi
    mov   [rbp-0x8], rdi    ; rdi = this (the closure object)
    mov   [rbp-0xc], esi    ; esi = k (the real parameter)
    mov   rax, [rbp-0x8]    ; rax = this
    mov   edx, [rax]        ; edx = this->base  (capture at offset 0)
    mov   eax, [rbp-0xc]    ; eax = k
    add   eax, edx          ; return base + k
    ret
```

The first parameter `rdi` is `this`, like in every C++ method (Lesson 4.1). A lambda is callable because it is really the `operator()` method of a hidden struct. The line `mov edx, [rax]` reads the first field of the object, which is the variable `base` captured by value. The capture is no longer a local variable but data living inside an object. In `main`, before the call, there are instructions that build the object: they compute `base = n*10` and `mov` it into the closure object's stack area. That is the closure's hidden constructor.

### Exceptions

When `b == 0`, `safe_div` calls this chain:

```asm
safe_div:
    ...
    cmp   [rbp-0x8], 0          ; b == 0 ?
    jne   .divide
    mov   edi, 0x10
    call  __cxa_allocate_exception   ; allocate the exception object
    ...
    call  __cxa_throw                ; throw
.divide:
    mov   eax, [rbp-0x4]
    cdq
    idiv  dword [rbp-0x8]            ; a / b
    ret
```

Seeing `__cxa_throw` tells you this is the point where the exception is thrown. In `main` the `try` block runs straight through, while the `catch` block is compiled into a landing pad: a separate stretch of code that begins with `__cxa_begin_catch`, calls `e.what()` and then `printf`, and ends with `__cxa_end_catch`. The main flow never `jmp`s there, and the runtime jumps in while unwinding the stack. The navigation data for unwinding lives in `.eh_frame` and `.gcc_except_table`, not in the code. You can look at it with:

```
readelf -S modern | grep -E 'eh_frame|except'
```

On MSVC, opening PE-bear shows `.pdata` (RUNTIME_FUNCTION) and `.xdata` (unwind info), along with the `_CxxThrowException` call and the `__CxxFrameHandler` handler.

### Answers to the questions

`std::vector<int>` and `std::vector<std::string>` are two different instantiations, so the binary has two separate sets of vector functions (push_back, allocate, destructor and so on). This is the main reason C++ binaries that use a lot of the STL grow so large. Capture by value stores a copy of the variable as a field, like `base` above. Capture by reference stores a pointer to the original variable as the field, so the field is an address (8 bytes) rather than a value, and `operator()` has to dereference once more.

</details>

## Key takeaways
With templates, each type is a separate function in the binary, so many near-identical functions are usually instantiations and not copy-paste. Lambdas become a hidden struct where captures become fields and the body becomes `operator()` with a `this` pointer. With exceptions, try/catch is split into the happy path and separate handlers, linked through unwind tables (.eh_frame/.gcc_except_table on Linux, .pdata/.xdata on Windows). The throw tells are `__cxa_throw` (Linux) and `_CxxThrowException` (MSVC). Don't get lost in the EH tables, since most of the time you only need to know "it may throw here, it's caught there".
