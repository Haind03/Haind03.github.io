---
title: "Lesson 4.2: Classes, vtables, inheritance and RTTI, rebuilding the class tree"
date: 2022-06-29 21:45:00 +0700
categories: ["Technique Reverse", "Part 04 · C++"]
tags: [reverse-engineering, cpp]
render_with_liquid: false
---
If the last lesson was about the `this` pointer and name mangling, this one is the heart of C++ reversing. The reason newcomers hate C++ isn't the syntax, it's that a seemingly simple function call turns into a `call rdx` with no clue where it goes. That's a virtual call, and behind it is the vtable. Understand the vtable and you can read C++, don't and you stay stuck on a pile of mysterious `call [reg]`.

## Why vtables exist

In C++, when a class has virtual functions, the compiler has to solve a problem: at compile time it doesn't know whether `s->area()` will call `Circle::area` or `Rectangle::area`, because `s` is only a `Shape*` pointer and the real type is only known at runtime. The solution is the virtual function table (vtable for short).

The mechanism has two parts. Every class with virtual functions gets its own vtable, an array of function pointers in a read-only region (.rdata on Windows, .rodata on Linux), with each virtual function taking one slot. And every object of that class contains, at offset 0 (right at the start of the object), a pointer to its class's vtable. This pointer is called the vptr.

When calling `s->area()`, the code doesn't jump straight to a fixed address. It does three steps: take the vptr from the start of the object, go into the vtable and fetch the slot for `area`, then call the function pointer in that slot. Because Circle and Rectangle have vptrs pointing to two different vtables, the same line of code calls two different functions. That's polymorphism seen from the bottom up.

## The layout of an object

Take the lab example from this lesson:

```cpp
class Shape {
    int id;
    virtual double area() = 0;
    virtual const char* name();
    virtual ~Shape();
};
class Circle : public Shape {
    double radius;
};
```

On x86-64, a `Circle` object sits in memory like this (numbers from a real g++ compile):

```
offset 0  : vptr        (8 bytes, pointer to Circle's vtable)
offset 8  : id          (4 bytes, inherited from Shape)
offset 12 : padding     (4 bytes, to align radius to 8)
offset 16 : radius      (8 bytes, Circle's own field)
total sizeof(Circle) = 24
```

Two things are worth burning into memory. The vptr is always at offset 0, so if you see a function load `[object]` and then load `[that result]` to call, it's going through the vptr into the vtable. This is the fingerprint of C++. And the base class's fields come before the derived class's fields. Circle contains all of Shape (vptr + id) and only then radius. Single inheritance is just stacking layouts: a `Circle*` cast to `Shape*` doesn't change the address, because the Shape part is right at the start.

## Recognizing a virtual call in assembly

![Object, vtable and a virtual call through call reg+offset](/assets/img/re/part-04/vtable.svg)

Here's real asm from the function `report(Shape* s)` calling `s->name()` and `s->area()`, compiled with `g++ -O0`:

```asm
mov  QWORD PTR [rbp-0x18], rdi   ; save the parameter s (object pointer)
mov  rax, QWORD PTR [rbp-0x18]   ; rax = s
mov  rax, QWORD PTR [rax]        ; rax = *s = vptr  (read the vtable at offset 0)
mov  rdx, QWORD PTR [rax]        ; rdx = vtable[0]  (the first slot of the vtable)
mov  rdi, QWORD PTR [rbp-0x18]   ; rdi = s          (the this pointer, the first hidden parameter)
call rdx                         ; call the virtual function through the pointer
...
mov  rax, QWORD PTR [rax]        ; rax = vptr again
add  rax, 0x8                    ; rax = vtable + 8
mov  rdx, QWORD PTR [rax]        ; rdx = vtable[1]  (the second slot)
call rdx                         ; call the second virtual function
...
mov  eax, DWORD PTR [rax+0x8]    ; read s->id  (a normal field at offset 8)
```

Three characteristics jump out right away. First, there are two dereferences before the call: `mov rax,[s]` then `mov rax,[rax]`. The first gets the vptr (since the vptr is at offset 0, `[s]` is the vptr itself), and the second gets the function pointer from the vtable. This pattern is unmistakable. Second, it's `call rdx` instead of `call address`, an indirect call through a register, because the function address is only known at runtime. Third, you see `vtable[0]`, `vtable+8`, `vtable+16` and so on, where each offset is one virtual function in declaration order. Knowing this order tells you which function is being called.

Compared with a normal call (`call sub_401500`, fixed address), a virtual call always looks like `call [reg]` or `call [reg+offset]`. Seeing it means you're inside object-oriented C++ code.

## Using vtables to rebuild the class tree

The vtable isn't just a hurdle, it's also a gift: it gives you the list of all of a class's virtual functions, gathered in one place.

To rebuild the hierarchy, start by finding the vtables. They're arrays of function pointers in .rdata/.rodata, and IDA and Ghidra usually recognize them automatically and name them like `Circle::vftable` or `vtable for Circle`. Then read the slots in a vtable to learn which virtual functions that class has. Each slot points to a function, and reading that function tells you what the class does.

Next, find the constructor to know which class uses which vtable. The constructor is where the vptr gets written into offset 0 of the object (`mov [object], offset vtable`). If you see a function that writes a vtable address into `[rcx]` or `[rdi]` at the start, that's almost certainly a constructor, and it ties the object to the corresponding class. Finally, compare vtables to infer inheritance. If the vtables of Circle and Rectangle share the first few slots (same pointers, or same signatures) and then differ in the later slots, they likely share a base class.

## RTTI, the shortcut when it's there

RTTI (Run-Time Type Information) is data C++ generates to support `dynamic_cast` and `typeid`. When the binary is compiled with RTTI (the default for g++ and MSVC, unless turned off with `-fno-rtti` or `/GR-`), every polymorphic class has a `type_info` structure containing the class name as a string.

This is gold for a reverser. In a binary with RTTI, you'll see strings like `.?AVCircle@@` (MSVC) or `6Circle` (g++'s Itanium ABI) in strings, so the class name is exposed in the open. IDA (with plugins like Class Informer) and Ghidra read RTTI themselves to name vtables and classes by their original names, and `sub_xxx::vftable` suddenly becomes `Circle::vftable`. RTTI also describes inheritance relationships (the base class array), so often you can rebuild the whole tree without guessing.

On the other hand, a binary compiled with `-fno-rtti` won't have these strings. The vtables are still there but you have to name the classes yourself. So one of the first things to do when you meet C++ is check whether RTTI is present: if yes, relief, if not, roll up your sleeves and build it by hand.

## Key takeaways
Virtual functions lead to vtables: one vtable per class (an array of function pointers in .rdata/.rodata), and every object has a vptr at offset 0 pointing to its own vtable. A virtual call in asm is two dereferences then `call [reg]` or `call [reg+offset]`, where the offset picks the function by declaration order.

Single inheritance means stacked layouts, with the base class part first, so a `Derived*` cast to `Base*` doesn't change the address. The constructor writes the vptr into offset 0 of the object, so use it to tell which class an object belongs to. RTTI (if present) exposes class names as strings and IDA/Ghidra name things from it automatically, so checking for RTTI is the first thing to do on C++.
