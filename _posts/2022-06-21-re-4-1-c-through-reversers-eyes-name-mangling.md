---
title: "Lesson 4.1: C++ for reversers, name mangling and the this pointer"
image:
  path: /assets/img/covers/re-4-1-c-through-reversers-eyes-name-mangling.webp
  alt: "Lesson 4.1: C++ for reversers, name mangling and the this pointer"
date: 2022-06-21 10:01:00 +0700
categories: ["Technique Reverse", "Part 04 · C++"]
tags: [reverse-engineering, cpp]
render_with_liquid: false
---
At the binary level, C++ is C plus a few conventions. The compiler breaks classes, methods, templates, and exceptions down into the same assembly instructions you already know. Two things make it look strange. Function names look like gibberish, and every method call quietly passes an extra parameter. Name mangling and the this pointer explain both, and once you know them C++ gets a lot less scary.

## Why function names look like gibberish

In C, a function `add` compiles to a symbol named exactly `add`, because C doesn't allow two functions with the same name.

C++ does. You can write `add(int)` and `add(int, int)` in the same class, that's overloading. But the linker only works with symbol names, and with two functions both named `add` it can't tell which to link. The compiler puts the class info, method name, and parameter types into the symbol name. That's called name mangling.

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

It looks messy at a glance, but there are rules. `_ZN` starts it, `7Counter` is a class name 7 characters long, `3add` is a method name 3 characters long, `E` ends the name list, then `i` is int, `ii` is two ints, `v` is void. The `K` in `_ZNK` means a const method. The two `add` functions get different names from the parameter type part, so the linker can tell them apart.

That's the GCC/Clang mangling style (the Itanium standard). MSVC uses a different style, starting with a `?`:

```
?add@Counter@@QEAAXH@Z      ->  public: void __cdecl Counter::add(int)
```

It looks even stranger, but you don't need to read it by hand. Leave that to tools.

## Demangling

![Name mangling: the same method becomes different names on GCC and MSVC](/assets/img/re/part-04/name-mangling.svg)

Nobody decodes mangling by eye. With c++filt, which ships with GCC, `echo _ZN7Counter3addEi | c++filt` gives `Counter::add(int)`, and you can pipe the whole `nm` output through it to demangle in bulk. MSVC ships undname, which does the same for names of the `?...` kind. IDA and Ghidra demangle automatically, so IDA shows `Counter::add(int)` in the function list. If you see names still mangled, check the demangling setting in the options.

For a reverser, name mangling helps. A C++ binary that still has symbols gives you the class names, method names, and parameter types, far more info than C. Only when the symbols are stripped do you lose this and have to infer from structure.

## The this pointer

This is the second big difference. When you write `c.add(5)`, it looks like one parameter. But the method needs to know which object it's working on (which `c`), so the compiler passes the object's address as the first parameter. That's the this pointer.

On Linux/SysV, this is in rdi (the first parameter) and the real parameters shift down to rsi, rdx.... On Windows x64, this is in rcx and the real parameters shift down to rdx, r8....

This is the asm of `c.add(5)` on Linux (g++, -O0), with the object `c` a local variable at `[rbp-0xc]`:

```asm
lea    rax, [rbp-0xc]      ; rax = address of object c
mov    esi, 0x5            ; real parameter n = 5 into rsi (second parameter)
mov    rdi, rax            ; this = &c into rdi (first parameter, hidden)
call   _ZN7Counter3addEi   ; call Counter::add(int)
```

In C++ it's just `c.add(5)`, but at the binary level it's a function with two parameters, `add(&c, 5)`. When the first parameter (rdi/rcx) of a call is a pointer to memory holding object data, it's a method call, not a plain function.

In IDA/Ghidra pseudocode, if a function keeps using the first parameter as `a1->field`, `a1` is almost certainly this. Rename it to `this` and assign the class type, and the pseudocode gets much tidier.

## Telling a method call from a plain function

Combining the two things above lets you tell C++ from C. The clearest sign is mangled function names (`_ZN...` or `?...@@`) in the function list. Beyond that, the call loads an object pointer into rdi/rcx before the call, and that pointer is reused to access fields by offset (`[this+0]`, `[this+4]`). A constructor also runs right after memory is allocated for the object (on the stack or after `new`), usually as the first function to touch that memory.

When you see all three, stop thinking "standalone C function" and think in objects and ask what this is, what fields the class has and which method reads/writes which field. Lesson [4.2](/posts/re-4-2-classes-vtables-inheritance-rtti-rebuilding-class/) goes on to vtables and inheritance, where C++ really differs from C.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 4.1</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/4.1.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/4.1/src/counter.cpp" download><i class="fa-solid fa-download"></i>src/counter.cpp</a>
</div>
</div>

The goal is to see how C++ mangles function names and where the this pointer gets passed. You'll build a small class from `counter.cpp`, look at the mangled names in the binary, demangle them, and point out the this pointer in rdi/rcx in a method call. Build it with one of these:

```
g++ -O0 -g counter.cpp -o counter          # Linux
g++ -O0 counter.cpp -o counter.exe         # Windows MinGW
cl /EHsc /Od counter.cpp                   # Windows MSVC
```

First look at the mangled names. On Linux run `nm counter | grep -i counter` and write down the symbol names of the two `add` functions and of the constructor. Where do they differ? Then pipe the output through `c++filt` with `nm counter | grep -i counter | c++filt`, and compare with the original names in the source. Why do the two `add` functions need different names?

Then find the this pointer. Open the binary in IDA or Ghidra (or use `objdump -d -M intel counter`), find `main` and look at the code that calls `c.add(5)`. Which argument is loaded into rdi (Linux) or rcx (Windows) just before the `call`, and what is that value? In the call `c.add(1, 2)`, three things are loaded before the call, this and the two numbers. Which registers do they go into, and in what order?

If you have MSVC, build with it too and compare its `?...@@` style of mangled names with the `_ZN...` style of GCC, using `undname` to demangle. Two more questions to think about. If the binary is stripped of symbols, can you still demangle, and how would you tell which class a function is a method of? And if a function's pseudocode is full of `a1->field`, what is `a1` most likely to be?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The results below come from a real build with g++ (-O0) on Linux x86-64. `nm counter | grep -i counter` prints:

```
_ZN7Counter3addEi      W
_ZN7Counter3addEii     W
_ZN7CounterC1Ei        W
_ZN7CounterC2Ei        W
_ZNK7Counter3getEv     W
```

Through `c++filt`:

```
_ZN7Counter3addEi    ->  Counter::add(int)
_ZN7Counter3addEii   ->  Counter::add(int, int)
_ZN7CounterC1Ei      ->  Counter::Counter(int)
_ZN7CounterC2Ei      ->  Counter::Counter(int)
_ZNK7Counter3getEv   ->  Counter::get() const
```

Decoding the Itanium rules (GCC/Clang) goes like this. `_ZN` opens a name that has a namespace or class, `7Counter` is a name 7 characters long, `Counter`, and `3add` is a method 3 characters long, `add`. `E` closes the list of nested names, and what follows are the parameter types, where `i` is int, `ii` is (int, int), `v` is void. `_ZNK` (with a `K`) means a const method, so `get() const`. The constructor appears twice, as `C1` and `C2` (complete object versus base object constructor), and both demangle to `Counter::Counter(int)`.

The two `add` functions need different names because the linker only sees symbols, and `add(int)` and `add(int, int)` sharing the name `add` would collide. Mangling puts the parameter types into the name (`Ei` versus `Eii`), so they become two separate symbols. That's how overloading works at the link level.

For the this pointer, the part of `main` that calls `c.add(5)`, where the object `c` is a local variable at `[rbp-0xc]`, looks like this:

```asm
lea    rax, [rbp-0xc]      ; rax = &c
mov    esi, 0x5            ; n = 5  -> rsi (second argument)
mov    rdi, rax            ; this = &c -> rdi (first, hidden argument)
call   _ZN7Counter3addEi
```

this (`&c`) is in rdi, and the real argument `n=5` is pushed down to rsi. At the binary level `add` is a function of two arguments, `add(this, n)`. The call `c.add(1, 2)` looks like:

```asm
lea    rax, [rbp-0xc]
mov    edx, 0x2           ; m = 2 -> rdx (third argument)
mov    esi, 0x1           ; n = 1 -> rsi (second argument)
mov    rdi, rax           ; this -> rdi (first argument)
call   _ZN7Counter3addEii
```

The SysV register order is rdi (this), rsi (n), rdx (m). On Windows x64 it would be rcx (this), rdx (n), r8 (m).

MSVC mangles the same method into this form:

```
?add@Counter@@QEAAXH@Z     ->  public: void __cdecl Counter::add(int)
```

You decode it with `undname "?add@Counter@@QEAAXH@Z"`. The syntax is different but it carries the same information, which is class, method and parameter types. The this pointer on Win64 goes in rcx.

On the reflection questions, a stripped binary often still keeps the mangled names of exported functions or dynamic symbols, but internal static functions lose their names. Then you infer the class from structure, since functions that receive a pointer in rdi/rcx and then access the same set of offsets are working on one class, and grouping them lets you rebuild the class. If the pseudocode is full of `a1->field`, then `a1` is almost certainly this. Rename it to `this` and assign the class type so IDA or Ghidra shows field names instead of offsets. As a final check, the program prints `18` (10 + 5 + 1 + 2 = 18), which matches the `Counter` logic.

</details>

## Key takeaways
C++ at the binary level is C plus a few conventions. Name mangling puts class, method and parameter types into the symbol name to support overloading, with GCC/Clang using `_ZN...` and MSVC using `?...@@`. Don't decode it by hand, use c++filt, undname, or let IDA/Ghidra demangle automatically. C++ symbols help you because they give class, method and parameter names, more than C does.

Every method has a hidden parameter this, in rdi on Linux and rcx on Windows x64. A call that loads an object pointer into rdi/rcx and then accesses fields by offset is a method call.

---
Previous: Part 3 C · [Back to index](/technique-reverse/) · Next: 4.2 Classes, vtables, inheritance, RTTI
