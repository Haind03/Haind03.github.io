---
title: "Lesson 4.4: Exceptions, templates and lambdas, three modern C++ things that tangle up binaries"
date: 2026-10-06 08:34:00 +0700
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

Consequences when reversing:
- **The binary bloats.** A template used with ten types is ten functions. Template-heavy libraries (STL, Boost) push the function count into the thousands.
- **You'll see many nearly identical functions**, differing only in data size or instruction type. Don't assume the author copy-pasted, that's template instantiation.
- **A tip to save effort:** understanding one version is understanding the whole family. Read `add_one<int>`, then just glance at the others to confirm the same logic. Name them consistently like `add_one_int`, `add_one_double` so you don't mix them up.

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

Meaning: **each captured variable becomes a field** of a hidden struct, and **the lambda body becomes the `operator()` method** of that struct. Calling the lambda is calling a method, so it has a `this` pointer just like lesson [4.1](/posts/tr-4-1-name-mangling-this-method-call/) described.

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

When reversing, recognize a lambda by: a small struct being built on the spot (the `mov`s writing the capture into an object on the stack), then a method call with that object as `this`. Its mangled name contains a string like `ZZ...EUl...` (U for unnamed lambda). IDA/Ghidra usually show a long convoluted name, just rename it to `lambda_xxx` to keep it easy.

## Exceptions: the price of try/catch

This is the part that tangles things the most. In the source, try/catch is tidy. In the binary, it splits into two parts: the normal running path (happy path) and the machinery that handles an exception, sitting separately, linked through data tables.

The two main ABIs differ quite a bit:

**Linux / Itanium C++ ABI.** On `throw`, the runtime calls `__cxa_throw`, then it walks back up the stack (stack unwinding) to find a handler. The information "which handlers this frame has, what needs cleaning up" isn't in the code but in dedicated sections: `.eh_frame`, `.gcc_except_table`. The place in code that catches the exception is called a landing pad. In the decompiler you see a function that seems to "end" at `ret` but still has stray code blocks after it that nobody calls directly, those are landing pads, which the runtime jumps into during unwinding.

**Windows / MSVC.** Uses a different mechanism, with funclets (sub-functions for catch blocks) and unwind data in `.pdata`/`.xdata`. You'll see pointers to `FuncInfo` tables, `__CxxFrameHandler`. Related functions: `_CxxThrowException`.

What both have in common, practically, for the reverser:
- **try/catch code is cut apart.** The try body runs straight, the catch part sits in a separate block that the main flow doesn't reach with a normal `jmp`. Don't panic when you see "orphan" code after a function, that's usually a handler.
- **Don't get lost in the unwind tables** unless you really need to. In 90% of cases when reversing a crackme or finding the main logic, you only need to know "this spot can throw, that one catches" and move on. The EH tables themselves rarely hide secrets.
- Seeing a `__cxa_throw` / `_CxxThrowException` call tells you there's an exception exit from here. Seeing `__cxa_begin_catch` / `__CxxFrameHandler` means you're in the handling area.

## Putting it together: don't let the noise hide the signal

All three of these are the compiler generating extra code around the author's real logic. The general strategy is the same: recognize them, label them, then focus on the logic. A template is many copies of one function (understand one, infer the family). A lambda is a hidden class (find `operator()` and the capture fields). An exception is code cut apart (the happy path is the main thing, the handler comes later). Knowing these three templates, you read modern C++ code without being discouraged by the number of functions and the odd blocks.

## Lab

The folder [labs/4.4/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/4.4). Build `src/modern.cpp`, then:
- Find the two instantiations `add_one<int>` and `add_one<double>` in the symbols, and compare their asm.
- Find the lambda's `operator()`, and identify which is `this` and which is the capture field.
- Mark out the try/catch block: find the throw call and where the handler sits apart.

Details and the solution are in the [README](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/4.4/README.md) and [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/4.4/solution.md).

## Key takeaways
- Templates: each type is a separate function in the binary. Many near-identical functions are usually instantiations, not copy-paste.
- Lambdas: become a hidden struct, captures become fields, the body becomes `operator()` with a `this` pointer.
- Exceptions: try/catch is split into the happy path and separate handlers, linked through unwind tables (.eh_frame/.gcc_except_table on Linux, .pdata/.xdata on Windows).
- Throw tells: `__cxa_throw` (Linux), `_CxxThrowException` (MSVC).
- Don't get lost in the EH tables, most of the time you only need to know "it may throw here, it's caught there".
