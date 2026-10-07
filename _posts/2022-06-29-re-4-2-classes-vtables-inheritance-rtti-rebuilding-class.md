---
title: "Lesson 4.2: Classes, vtables, inheritance and RTTI"
image:
  path: /assets/img/covers/re-4-2-classes-vtables-inheritance-rtti-rebuilding-class.webp
  alt: "Lesson 4.2: Classes, vtables, inheritance and RTTI"
date: 2022-06-29 21:45:00 +0700
categories: ["Technique Reverse", "Part 04 · C++"]
tags: [reverse-engineering, cpp]
render_with_liquid: false
---
The last lesson covered the `this` pointer and name mangling. This one is the main part of C++ reversing. Newcomers don't hate C++ for the syntax. They hate that a simple-looking function call turns into a `call rdx` with no clue where it goes. That's a virtual call, and behind it is the vtable. Once you understand the vtable you can read C++, and if you don't you stay stuck on many `call [reg]` instructions.

## Why vtables exist

When a C++ class has virtual functions, the compiler has a problem: at compile time it doesn't know whether `s->area()` will call `Circle::area` or `Rectangle::area`, because `s` is only a `Shape*` and the real type is known at runtime. The solution is the virtual function table (vtable for short).

It has two parts. Every class with virtual functions gets its own vtable, an array of function pointers in a read-only region (.rdata on Windows, .rodata on Linux), with each virtual function taking one slot. And every object of that class contains, at offset 0, a pointer to its class's vtable. This pointer is called the vptr.

When calling `s->area()`, the code doesn't jump to a fixed address. It takes the vptr from the start of the object, goes into the vtable and fetches the slot for `area`, then calls the function pointer in that slot. Circle and Rectangle have vptrs pointing to two different vtables, so the same line of code calls two different functions. That's polymorphism seen from below.

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

Two things to remember. The vptr is always at offset 0, so if you see a function load `[object]` and then load `[that result]` to call, it's going through the vptr into the vtable. That's the typical C++ pattern. And the base class's fields come before the derived class's fields. Circle contains all of Shape (vptr + id) and only then radius. Single inheritance is just stacking layouts: a `Circle*` cast to `Shape*` doesn't change the address, because the Shape part is at the start.

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

Three things stand out. First, there are two dereferences before the call: `mov rax,[s]` then `mov rax,[rax]`. The first gets the vptr (since the vptr is at offset 0, `[s]` is the vptr itself), and the second gets the function pointer from the vtable. Second, it's `call rdx` instead of `call address`, an indirect call through a register, because the function address is only known at runtime. Third, you see `vtable[0]`, `vtable+8`, `vtable+16` and so on, where each offset is one virtual function in declaration order. Knowing that order tells you which function is being called.

A normal call is `call sub_401500` with a fixed address. A virtual call always looks like `call [reg]` or `call [reg+offset]`. If you see one, you're in object-oriented C++ code.

## Using vtables to rebuild the class tree

The vtable also helps you, because it gives you the list of all of a class's virtual functions in one place.

To rebuild the hierarchy, start by finding the vtables. They're arrays of function pointers in .rdata/.rodata, and IDA and Ghidra usually recognize them automatically and name them like `Circle::vftable` or `vtable for Circle`. Then read the slots in a vtable to learn which virtual functions that class has. Each slot points to a function, and reading that function tells you what the class does.

Next, find the constructor to know which class uses which vtable. The constructor is where the vptr gets written into offset 0 of the object (`mov [object], offset vtable`). A function that writes a vtable address into `[rcx]` or `[rdi]` at the start is almost certainly a constructor, and it ties the object to the matching class. Finally, compare vtables to infer inheritance. If the vtables of Circle and Rectangle share the first few slots (same pointers, or same signatures) and differ in the later slots, they likely share a base class.

## RTTI

RTTI (Run-Time Type Information) is data C++ generates to support `dynamic_cast` and `typeid`. When the binary is compiled with RTTI (the default for g++ and MSVC, unless turned off with `-fno-rtti` or `/GR-`), every polymorphic class has a `type_info` structure containing the class name as a string.

For a reverser this is very handy. In a binary with RTTI you'll see strings like `.?AVCircle@@` (MSVC) or `6Circle` (g++'s Itanium ABI), so the class name is right there. IDA (with plugins like Class Informer) and Ghidra read RTTI themselves to name vtables and classes by their original names, and `sub_xxx::vftable` becomes `Circle::vftable`. RTTI also describes inheritance relationships (the base class array), so often you can rebuild the whole tree without guessing.

A binary compiled with `-fno-rtti` won't have these strings. The vtables are still there but you have to name the classes yourself. So one of the first things to do with C++ is check whether RTTI is present. If it is, good. If not, build it by hand.

## Lab

The goal is to find a vtable yourself in a C++ binary, recognize the vptr at the start of an object, and rebuild the inheritance relationships between classes. The source is `shapes.cpp`, with a base class `Shape` (which has virtual functions) and two derived classes, `Circle` and `Rectangle`. Build it in one of these ways. On Linux, easiest to read:

```sh
g++ -O0 -g -fno-inline -o shapes shapes.cpp
```

On Linux, a build without RTTI for comparison:

```sh
g++ -O0 -fno-rtti -o shapes_nortti shapes.cpp
```

With MinGW on Windows:

```sh
g++ -O0 -g -o shapes.exe shapes.cpp
```

With MSVC in a Developer Command Prompt:

```
cl /EHsc /Od /Zi shapes.cpp
```

Open the binary in IDA or Ghidra and run auto-analysis. Start by finding the vtables. Look in `.rdata` (Windows) or `.rodata` (Linux) for arrays of function pointers. IDA or Ghidra may already have named them something like `vtable for Circle`, so list the vtables you see. Then read the contents of one vtable: each slot points to a function, so follow each pointer and guess which virtual function it is (`area`, `name`, the destructor).

Next recognize the vptr in an object. Find the `report` function and spot the asm that loads the vptr from offset 0 of the object and then calls indirectly. This is the "two dereferences then `call [reg]`" pattern. In the same function find where `s->id` is read. At which offset in the object is it, and why isn't it offset 0? After that, find the constructors, the functions that write a vtable address into offset 0 of a new object. Which vtable does the constructor of `Circle` write, and which does that of `Rectangle`? Using the vtables and constructors, draw the relationships: which class is the parent and which are the children.

Finally compare builds with and without RTTI. Open both `shapes` and `shapes_nortti`. In the RTTI build, look for the class name strings (`Circle`, `Rectangle`) in the strings. Does the `-fno-rtti` build still have them, and does it still have the vtables? Two questions to think about: if you change `Shape*` to a pointer to a concrete derived class and call the function, is the call still indirect through the vtable, and why can the compiler call directly (devirtualization)? And why is the destructor usually in the vtable?

<div class="lab-box">
<div class="lab-head"><b>LAB 4.2</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/4.2/src/shapes.cpp" download><i class="fa-solid fa-file-code"></i>src/shapes.cpp</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The figures below come from a real compile with `g++ 11.4` on x86-64 Linux (`g++ -O0 -g -fno-inline`). The names are mangled following the Itanium ABI. MSVC uses different names but the same idea.

Running `nm -C shapes | grep vtable` gives three vtables: `vtable for Shape`, `vtable for Circle` and `vtable for Rectangle`. Every polymorphic class has exactly one vtable, placed in a read-only region (`.data.rel.ro` or `.rodata` on Linux, `.rdata` on Windows).

Each slot of a vtable is a function pointer, in the order the virtuals were declared. For `Circle`:

```
vtable Circle:
  [0] Circle::area      (double area())
  [1] Circle::name      (const char* name())
  [2] Circle::~Circle   (destructor, normal version)
  [3] Circle::~Circle   (deleting destructor)
```

The vtable of `Rectangle` has the same layout but its slots point to `Rectangle::area` and `Rectangle::name`. Because the structures match, one call site calls different functions depending on the object.

The real asm of `report` (function `_Z6reportP5Shape`) shows the vptr:

```asm
mov  QWORD PTR [rbp-0x18], rdi   ; s = parameter
mov  rax, QWORD PTR [rbp-0x18]   ; rax = s
mov  rax, QWORD PTR [rax]        ; rax = *s = vptr   <-- reads the vtable at offset 0
mov  rdx, QWORD PTR [rax]        ; rdx = vtable[0]   (area)
mov  rdi, QWORD PTR [rbp-0x18]   ; rdi = s = this
call rdx                         ; call the virtual
```

That's the "two dereferences then `call [reg]`" pattern: `mov rax,[s]` takes the vptr (because it sits at offset 0), `mov rdx,[rax]` takes the vtable slot, and `call rdx` calls it. The second call, `name()`, is the same except for an `add rax, 0x8` to get `vtable[1]`.

Near the end of the function the ordinary field is read:

```asm
mov  eax, DWORD PTR [rax+0x8]    ; s->id
```

`id` is at offset 8, not 0, because offset 0 is already taken by the vptr (8 bytes on x64). That's why every field of a polymorphic class is shifted by 8 bytes compared to what you'd expect. The object layouts (checked with `sizeof` and `offsetof`) are:

```
Shape : vptr(0), id(8)              sizeof = 16
Circle: vptr(0), id(8), radius(16)  sizeof = 24  (offset 12 is padding)
```

The constructor `Circle::Circle` contains an instruction that writes a vtable address to the start of the object:

```asm
lea  rax, [rip + vtable_Circle + 16]   ; points to the first function slot of the vtable
mov  QWORD PTR [rcx], rax              ; write the vptr at offset 0 of the object
```

g++ points the vptr at the first function slot, which is vtable + 16 because the first two slots are the offset-to-top and the typeinfo pointer. A function that begins by writing a vtable address into `[this]` is a constructor, and it binds the object to the matching class. `Circle` writes the Circle vtable and `Rectangle` writes the Rectangle vtable. From the vtables and constructors the class tree is:

```
        Shape  (abstract, pure virtual area())
        /    \
   Circle   Rectangle
```

The signs of inheritance: `Circle` and `Rectangle` both begin with the same object prefix as `Shape` (vptr + id), their constructors call `Shape::Shape` before setting their own vptr, and the RTTI (below) declares `Shape` as the base.

A normal build has RTTI, and `nm -C` shows `typeinfo for Shape / Circle / Rectangle` and `typeinfo name for Shape / Circle / Rectangle`. The strings also contain Itanium style RTTI names: `5Shape`, `6Circle`, `9Rectangle` (the number is the length of the name). IDA (Class Informer) and Ghidra read these to name classes automatically. With `-fno-rtti` no typeinfo symbols remain and the RTTI name strings are gone, but the vtables are still there (`vtable for Circle` still exists). So without RTTI you can still rebuild the hierarchy through the vtables and constructors, you just lose the free class names.

One caution: in this lab the strings "Circle", "Rectangle" and "Shape" still appear in both builds, but those are string literals returned by the `name()` function, not RTTI. Don't confuse the two. The real signs of RTTI are the mangled strings `6Circle` and `9Rectangle` and the `typeinfo` symbols.

On the questions: if you call through a pointer of a concrete type (`Circle* c; c->area()`), the compiler knows the type for certain and calls `Circle::area` directly, without the vtable. That's devirtualization, and a virtual call only appears when the static type is the base class and the real type is known only at run time. The destructor is in the vtable because `delete base_ptr` has to call the destructor of the actual derived class, a decision made at run time, so it needs to be virtual too.

To confirm, build and run it:

```
[1] Circle area=12.57
[2] Rectangle area=12.00
```

The same `report(shapes[i])` line prints a different name and area for the two objects, which shows that virtual dispatch through the vtable works as analyzed.

</details>

## Key takeaways
Virtual functions lead to vtables: one vtable per class (an array of function pointers in .rdata/.rodata), and every object has a vptr at offset 0 pointing to its own vtable. A virtual call in asm is two dereferences then `call [reg]` or `call [reg+offset]`, where the offset picks the function by declaration order.

Single inheritance means stacked layouts, with the base class part first, so a `Derived*` cast to `Base*` doesn't change the address. The constructor writes the vptr into offset 0 of the object, so use it to tell which class an object belongs to. RTTI (if present) exposes class names as strings and IDA/Ghidra name things from it automatically, so checking for RTTI is the first thing to do on C++.
