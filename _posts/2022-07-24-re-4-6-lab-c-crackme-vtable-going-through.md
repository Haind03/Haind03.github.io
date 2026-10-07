---
title: "Lesson 4.6: Lab, a C++ crackme with a vtable, going through the vtable to find the check function"
image:
  path: /assets/img/covers/re-4-6-lab-c-crackme-vtable-going-through.webp
  alt: "Lesson 4.6: Lab, a C++ crackme with a vtable, going through the vtable to find the check function"
date: 2022-07-24 20:03:00 +0700
categories: ["Technique Reverse", "Part 04 · C++"]
tags: [reverse-engineering, cpp]
render_with_liquid: false
---
This lesson wraps up all of Part 4. You'll solve a C++ crackme where the key point is that it doesn't call the check function straightforwardly like the C crackme in Lesson 3.5. Instead it calls through a virtual function, meaning the call goes indirectly through the vtable. If you're used to the C habit of "find the `call check`", you'll come up empty here, since in the asm you only see a bare `call rcx`. Learning to trace through the vtable is the goal of this lesson.

The crackme is attached in the Lab section below. Try solving it yourself first, what's below is a guide.

## Step 1: triage, confirm it's C++

Open the binary with Detect It Easy, you'll usually see the compiler is GCC or MSVC. But the surest sign that it's C++ is elsewhere: run `nm -C` (Linux) or let IDA/Ghidra demangle, and you see names like:

```
SerialValidator::check(char const*) const
Validator::Validator()
SerialValidator::~SerialValidator()
```

Names with `::`, with parameters in parentheses, with a trailing `const`. Those are demangled C++ names. In the raw file they sit in mangled form like `_ZNK15SerialValidator5checkEPKc`. Seeing mangling tells you right away you're no longer in the flat world of C, there are classes and methods here (see Lesson 4.1 again).

Also, RTTI leaves the class name strings right in the binary. Search the Strings and you'll see `SerialValidator`, `Validator`. This is a free gift: the class names leaking out help you orient yourself.

## Step 2: the object has a vtable pointer at the start

`main` creates the object with `new SerialValidator()` and assigns it to a pointer of type `Validator*`. Because `check` is virtual, the compiler doesn't know at compile time which function will be called, so it has to look it up in a table at runtime. That table is the vtable, and every object with virtual functions carries a pointer to its class's vtable at offset 0 (the first 8 bytes of the object on x64).

Remember this picture: `object -> [vtable_ptr][field1][field2]...`, and `vtable -> [&check][&name][&destructor]...`. A virtual call is two dereferences: take the vtable_ptr from the object, then take the function address from the vtable.

## Step 3: reading the virtual call in asm

Here's the real snippet from `main` (g++ -O0, trimmed), the spot that calls `v->check(argv[1])`:

```asm
mov  rax, QWORD PTR [rbp-0x18]   ; rax = object pointer (this)
mov  rax, QWORD PTR [rax]        ; rax = vtable_ptr (first 8 bytes of the object)
mov  rcx, QWORD PTR [rax]        ; rcx = vtable[0] = address of the check function
mov  rax, QWORD PTR [rbp-0x30]
add  rax, 0x8
mov  rdx, QWORD PTR [rax]        ; rdx = argv[1] (the input string)
mov  rax, QWORD PTR [rbp-0x18]
mov  rsi, rdx                    ; rsi = parameter: input
mov  rdi, rax                    ; rdi = this (the first hidden parameter)
call rcx                         ; indirect call through the vtable
```

Notice three things. The pair `mov rax,[rax]` then `mov rcx,[rax]` is the classic signature of a virtual call: dereference the object to get the vtable, dereference the vtable to get the function pointer. The last instruction is `call rcx`, not `call <function name>`, so in the IDA/Ghidra graph there's no arrow pointing to the target function here and you can't just double-click to jump in, which is where beginners get stuck. And `rdi` gets `this` while `rsi` gets the input. This is System V (Linux). On Windows x64 it would be `rcx` for `this`, `rdx` for the input (see Lesson 4.1 again on the this pointer).

So how do you know `call rcx` actually calls `SerialValidator::check`? There are two ways. Statically, `vtable[0]` is loaded from the vtable pointer, and the vtable of `SerialValidator` is assigned by the constructor. Follow the constructor (or let IDA/Ghidra's RTTI analysis attach it automatically) and you get the vtable, where the first slot points to `check`. Once RTTI is there, IDA usually names the vtable `SerialValidator::vftable` itself and you just open it and read. Dynamically, set a breakpoint at `call rcx` and look at the value of `rcx` at runtime, which is exactly the address of `check`. Press step-into and you're straight in the function. This is the shortcut when the static vtable analysis is messy.

## Step 4: reading the logic in check

Once you're inside `SerialValidator::check`, the rest is like a C crackme. The logic it does:

```c
if (strlen(input) != 12) return false;
for (int i = 0; i < 12; i++) {
    uint8_t t = (input[i] ^ 0x5A) + i;
    if (t != expected[i]) return false;
}
return true;
```

The 12-byte `expected` array lives in the object (a field of `SerialValidator`, filled in by the constructor). The algorithm transforms each character then compares with a constant, the same form as Lesson 3.5, the only difference being that now you have to go through the vtable to reach it.

## Step 5: reverse it to find the password

The transform `t = (c ^ 0x5A) + i` is invertible: `c = (expected[i] - i) ^ 0x5A`. A few lines of Python give you the password. The details of the numbers and the full solution are in the "Show solution" block below.

## Why this lesson matters

With a C crackme you find the `call check` and you're done. A C++ crackme with virtual functions doesn't give you that. Lots of real software, especially game engines and big applications, is full of virtual calls, interfaces, plugins. Getting used to tracing through the vtable (recognizing the two-dereference pattern, using RTTI, or setting a breakpoint to read the function pointer at runtime) is a skill you'll use for life when reversing C++.

## Key takeaways
Names with `::` and parameters after demangling, along with class name strings from RTTI, are a sure sign of C++. An object with virtual functions carries a vtable pointer at offset 0. A virtual call in asm looks like `mov reg,[obj]` then `mov reg2,[reg]` then `call reg2`, with no target function name. `this` is the first hidden parameter, in rdi on Linux or rcx on Windows. When you're stuck with a static vtable, set a breakpoint at `call reg` and read the register value to learn the target function.

## Lab

The file `crackme.cpp` is a C++ crackme whose check function is called through a virtual function (the vtable) rather than a direct call. The goal is to find the password. The source contains the build commands as well. On Linux or macOS:

```
g++ -O0 -std=c++17 -o crackme crackme.cpp
```

On Windows with MSVC, in a Developer Command Prompt:

```
cl /EHsc /Od crackme.cpp
```

or with MinGW:

```
g++ -O0 -std=c++17 -o crackme.exe crackme.cpp
```

Run it as `./crackme <password>`. Start with triage: use DIE to confirm the compiler, use `nm -C` (or let IDA/Ghidra demangle) to see the class and method names, and look for the RTTI strings (`SerialValidator`, `Validator`) in the Strings view. Then open the binary in IDA or Ghidra, find `main`, and identify where the object is created (`new`) and where `check` is called. Point out the asm that makes the virtual call, recognizing the two dereferences (object to vtable to function pointer) and the `call reg` instruction. Trace to the real `check` function in one of two ways: read the vtable through RTTI, or set a breakpoint at the `call reg` and read the register. Read the logic in `check`: the required length, the transform applied to each character, and the array of constants it compares against. Invert the transform to compute the password, writing a few lines of Python if you need to, and finally run `./crackme <your_password>` to confirm it prints "Correct!".

Some questions to think about. Why does the `check` call site have no arrow to the target function in IDA's graph? If the class has many virtual functions, how do you know which vtable slot is `check`? And this check algorithm is invertible, so what if it used a one-way hash instead? Do it yourself before opening the solution.

<div class="lab-box">
<div class="lab-head"><b>LAB 4.6</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/4.6/src/crackme.cpp" download><i class="fa-solid fa-file-code"></i>src/crackme.cpp</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The correct password is `V7abl3_Cr4ck` (12 characters): entering it prints `Correct! You passed the C++ crackme.` and any other input is rejected. The password does not appear in the binary's `strings`.

### 1. Triage

```
$ nm -C crackme | grep -i check
SerialValidator::check(char const*) const
```

The name has `::`, a `char const*` parameter and a `const` suffix, so this is a C++ method. In Strings you also see `SerialValidator` and `Validator` left behind by RTTI. The conclusion is a C++ binary with at least two classes and a function named `check`.

### 2. The path in main to the virtual call

`main` creates `new SerialValidator()`, assigns it to a `Validator* v`, then calls `v->check(argv[1])`. Because `check` is virtual, the asm calls indirectly. The real excerpt (g++ -O0):

```asm
mov  rax, QWORD PTR [rbp-0x18]   ; this (object pointer)
mov  rax, QWORD PTR [rax]        ; vtable_ptr = *object
mov  rcx, QWORD PTR [rax]        ; vtable[0] = &SerialValidator::check
mov  rax, QWORD PTR [rbp-0x30]
add  rax, 0x8
mov  rdx, QWORD PTR [rax]        ; argv[1]
mov  rax, QWORD PTR [rbp-0x18]
mov  rsi, rdx                    ; arg: input
mov  rdi, rax                    ; this
call rcx                         ; call through the vtable
```

Two consecutive dereferences (`mov rax,[rax]` then `mov rcx,[rax]`) followed by `call rcx` are the signature of a virtual call. `rdi` is this and `rsi` is the input (System V). A fast way into `check` is to set a breakpoint at `call rcx`, run, read `rcx`, and step in. Alternatively, let IDA or Ghidra use RTTI to label the vtable and open the first slot.

### 3. The logic in check

```c
bool SerialValidator::check(const char* input) const {
    if (strlen(input) != 12) return false;
    for (int i = 0; i < 12; i++) {
        uint8_t t = (input[i] ^ 0x5A) + i;
        if (t != expected[i]) return false;
    }
    return true;
}
```

`expected` is a 12-byte field of the object, filled in by the constructor:

```
0x0C, 0x6E, 0x3D, 0x3B, 0x3A, 0x6E, 0x0B, 0x20, 0x30, 0x77, 0x43, 0x3C
```

### 4. Inverting it

From `t = (c ^ 0x5A) + i` we get `c = (t - i) ^ 0x5A`:

```python
expected = [0x0C,0x6E,0x3D,0x3B,0x3A,0x6E,0x0B,0x20,0x30,0x77,0x43,0x3C]
pw = ''.join(chr(((expected[i]-i) & 0xFF) ^ 0x5A) for i in range(len(expected)))
print(pw)   # V7abl3_Cr4ck
```

Running `./crackme V7abl3_Cr4ck` again gives "Correct!". Done.

The only hard part compared with a C crackme is that the call goes through the vtable, and recognizing the pattern and using RTTI or a runtime breakpoint gets you past it. When the check algorithm is invertible (XOR and addition here), you compute the password directly. If it used a one-way hash it could not be inverted, and you would have to brute-force or patch instead.

</details>

