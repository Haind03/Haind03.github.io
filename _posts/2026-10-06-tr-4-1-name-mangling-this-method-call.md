---
title: "Lesson 4.1: C++ through a reverser's eyes, name mangling and the this pointer"
date: 2026-10-06 08:31:00 +0700
categories: ["Technique Reverse", "Part 04 · C++"]
tags: [reverse-engineering, cpp]
render_with_liquid: false
---
At the binary level, C++ isn't a new language but C plus a few conventions. The compiler breaks classes, methods, templates, and exceptions down into the same assembly instructions you already know. The problem is that it does so in a way that makes function names look like cat scratches and every method call quietly passes an extra parameter. Understanding those two things, name mangling and the this pointer, gets you past 80% of the fear of C++.

## Why function names turn into cat scratches

In C, a function `add` compiles to a symbol named exactly `add`. Simply because C doesn't allow two functions with the same name.

C++ does. You can write `add(int)` and `add(int, int)` in the same class, that's overloading. But the linker only works with symbol names, and with two functions both named `add`, how does it know which to link? The compiler's solution: stuff the class info, method name, and parameter types into the symbol name. That process is called name mangling.

Take a real class:

```cpp
class Counter {
    int value;
public:
    Counter(int start) : value(start) {}
    void add(int n)        { value += n; }
    void add(int n, int m) { value += n + m; }
    int  get() const       { return value; }
};
```

Compile with g++ and look at the symbols (the `nm` command), and you see the real names in the binary:

```
_ZN7Counter3addEi      ->  Counter::add(int)
_ZN7Counter3addEii     ->  Counter::add(int, int)
_ZN7CounterC1Ei        ->  Counter::Counter(int)      (constructor)
_ZNK7Counter3getEv     ->  Counter::get() const
```

It looks messy at a glance, but there are rules: `_ZN` starts it, `7Counter` is a class 7 characters long, `3add` is a method 3 characters long, `E` ends the name list, then `i` is int, `ii` is two ints, `v` is void. The `K` in `_ZNK` means a const method. The two `add` functions now have different names thanks to the parameter type part, and the linker can tell them apart.

That's the GCC/Clang mangling style (the Itanium standard). MSVC uses a different style, starting with a `?`:

```
?add@Counter@@QEAAXH@Z      ->  public: void __cdecl Counter::add(int)
```

Looks even stranger, but you don't need to read it by hand. Leave that to tools.

## Demangle: giving names back to the reader

![Name mangling: the same method becomes different names on GCC and MSVC](/assets/img/technique-reverse/assets/phan-04/name-mangling.svg)

Nobody sits and decodes mangling by eye. With c++filt, which ships with GCC, `echo _ZN7Counter3addEi | c++filt` gives `Counter::add(int)` right away, and you can pipe the whole `nm` output through it to demangle in bulk. MSVC ships undname, which does the same for names of the `?...` kind. IDA and Ghidra demangle automatically, so IDA shows `Counter::add(int)` right in the function list and you barely have to do anything. If you see names still in mangled form, check the demangling config in the options.

The important point for a reverser is that name mangling is a gift, not a barrier. A C++ binary that still has symbols tells you the class names, method names, and parameter types, far more info than C. Only when the binary has its symbols stripped do you lose this gift and have to infer from structure.

## this pointer, the hidden parameter of every method

This is the second big difference. When you write `c.add(5)`, it looks like just one parameter. But the method needs to know which object it's working on (which `c`), so the compiler quietly passes the object's address as the first parameter. That's the this pointer.

The rule to memorize: on Linux/SysV, this is in rdi (the first parameter) and the real parameters shift down to rsi, rdx..., while on Windows x64, this is in rcx (the first parameter) and the real parameters shift down to rdx, r8...

Look at the real asm of `c.add(5)` on Linux (g++, -O0), with the object `c` a local variable at `[rbp-0xc]`:

```asm
lea    rax, [rbp-0xc]      ; rax = address of object c
mov    esi, 0x5            ; real parameter n = 5 into rsi (second parameter)
mov    rdi, rax            ; this = &c into rdi (first parameter, hidden)
call   _ZN7Counter3addEi   ; call Counter::add(int)
```

Translated back to C++ it's just `c.add(5)`, but at the binary level it's a function with two parameters: `add(&c, 5)`. When you see a call whose first parameter (rdi/rcx) is a pointer to memory holding object data, you're looking at a method call, not a plain function.

A practical tip: in IDA/Ghidra pseudocode, if a function keeps using the first parameter as `a1->field`, it's almost certainly `a1` is this, and you should rename it to `this` and assign the class type. The pseudocode gets much tidier.

## Telling a method call from a plain function

Combining the two things above gives you a way to recognize you're looking at C++ and not C. The clearest sign is mangled function names (`_ZN...` or `?...@@`) in the function list. Beyond that, the call always loads an object pointer into rdi/rcx before the call, and that pointer is reused to access fields by offset (`[this+0]`, `[this+4]`). A constructor also runs right after memory is allocated for the object (on the stack or after `new`), usually as the first function to touch that memory.

When you see all three, drop the "standalone C function" thinking and start thinking in objects: what is this, what fields the class has, which method reads/writes which field. Lesson [4.2](https://github.com/Haind03/Technique-Reverse/blob/main/phan-04-cpp/4.2-class-vtable-ke-thua.md) goes on into vtables and inheritance, where C++ really differs from C.

## Lab

The folder [labs/4.1/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/4.1). You'll build a small class, look at the mangled names in the binary, demangle them, and point out the this pointer in rdi/rcx in a method call. When you're done compare with [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/4.1/solution.md).

## Key takeaways
C++ at the binary level is C plus a few conventions, not a new world. Name mangling stuffs class, method and parameter types into the symbol name to support overloading, with GCC/Clang using `_ZN...` and MSVC using `?...@@`. Don't decode it by hand: use c++filt, undname, or let IDA/Ghidra demangle automatically. C++ symbols are a gift because they give class, method and parameter names, more than C does.

Every method has a hidden parameter this, in rdi on Linux and rcx on Windows x64. A call that loads an object pointer into rdi/rcx and then accesses fields by offset is a method call.

---
Previous: Part 3 C · [Back to index](/technique-reverse/) · Next: 4.2 Classes, vtables, inheritance, RTTI
