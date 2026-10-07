---
title: "Lesson 4.3: STL in binaries, reading std::string and std::vector like a native"
date: 2023-09-27 21:35:00 +0700
categories: ["Technique Reverse", "Part 04 · C++"]
tags: [reverse-engineering, cpp]
render_with_liquid: false
---
Real C++ code almost never uses bare C arrays alone. It's full of `std::string`, `std::vector`, `std::map`. The good news: each of these containers has a fixed layout that repeats over and over. Once you recognize their mold, a pile of `[rax]`, `[rax+8]`, `[rax+10h]` in pseudocode suddenly means something, and you can read "ah this is a string, that's a vector" without the decompiler telling you.

This lesson focuses on the two containers you meet most (`string` and `vector`), then quickly covers the rest. Every layout number below is from libstdc++ on x64 (the g++ toolchain), checked with the lab program. MSVC differs a little, with notes at the end.

## std::string, and the trick called SSO

Beginners often think `std::string` is just a pointer to a string. Wrong, and that very mistake makes them misread binaries.

On libstdc++, `std::string` is a 32-byte object made of:

```
offset 0  : char*   pointer to the data (_M_p)
offset 8  : size_t  string length (_M_string_length)
offset 16 : 16-byte union {
              char   internal buffer [16]   // used when the string is short
              size_t capacity               // used when the string is long
            }
```

The key point is Small String Optimization (SSO): if the string is short enough (at most 15 characters on libstdc++), it doesn't allocate on the heap but stuffs the characters into the 16-byte buffer right inside the object. The pointer at offset 0 then points into the object itself (object address + 16).

The lab prints exactly this:

```
--- short std::string (SSO) ---
addr object  = 0x7ffec62d5060
data()       = 0x7ffec62d5070   (= object + 16, points INTO itself)
size         = 2
capacity     = 15

--- long std::string (heap) ---
addr object  = 0x7ffec62d5080
data()       = 0x6306a1464eb0   (points to the heap, far from the object)
size         = 39
capacity     = 39
```

How to recognize a `std::string` while debugging: find an object where offset 0 is a pointer, offset 8 is a sensible small number (the length), and if that pointer points back into the object itself then you're looking at a short SSO string. Seeing a capacity of 15 is also a very characteristic sign of an empty or short string on libstdc++.

In asm, getting the string length is usually:

```asm
mov  rax, [rbx+8]      ; rax = string length (the _M_string_length field)
```

and getting the data pointer to read characters:

```asm
mov  rax, [rbx]       ; rax = data pointer
movzx eax, byte [rax] ; read the first character
```

Seeing the pair "read [obj] as a pointer, read [obj+8] as a length" is almost certainly a `std::string`.

## std::vector, three pointers say it all

![Layout of std::string with SSO and the three-pointer std::vector](/assets/img/technique-reverse/assets/phan-04/stl-layout.svg)

`std::vector` is even easier to recognize. On libstdc++ it's just three pointers, 24 bytes:

```
offset 0  : T* _M_start            pointer to the first element
offset 8  : T* _M_finish           pointer to just past the last element
offset 16 : T* _M_end_of_storage   pointer to the end of the allocated region
```

Everything follows from these three pointers:

```
size()     = (_M_finish - _M_start) / sizeof(T)
capacity() = (_M_end_of_storage - _M_start) / sizeof(T)
```

So in pseudocode, when you see the compiler compute `(v[8] - v[0]) >> 2` that's the `size()` of a `vector<int>` (divide by 4 because an int is 4 bytes, `>>2` is divide by 4). Recognizing the pattern "difference of two pointers then divide by element size" is recognizing a vector.

The lab confirms it:

```
sizeof(std::vector<int>) = 24    (exactly 3 pointers)
begin (data) = 0x...ee0          (points to the heap)
size = 4, capacity = 4
```

A loop walking a vector in asm usually looks like: load `_M_start` into one register, load `_M_finish` into another, and loop incrementing the pointer until they're equal. Seeing the mold "run a pointer from [obj] to [obj+8]" is a `for (auto& x : v)` loop.

## The other containers, quick tour

You'll meet them less, but you should know their faces. std::map and std::set are implemented with a red-black tree. Each node has parent, left and right pointers, a color bit, and then the key/value. In the binary you see a lot of pointer operations rotating the tree and comparisons. The `sizeof` of the map itself is small (48 bytes in the lab, mostly the header node and a counter), and you recognize a map by its calls to very long library function names involving `_Rb_tree`.

std::unique_ptr is usually just a bare pointer (8 bytes), almost vanishing after optimization. It differs from a plain pointer only in that the destructor calls `delete` automatically. std::shared_ptr is two pointers (16 bytes), one to the object and one to a control block holding the reference count. Seeing an atomic (lock-prefixed) integer increment/decrement next to a pointer is a sign of shared_ptr.

## How MSVC differs

If the binary was built with MSVC (common on Windows), the numbers change but the ideas stay the same. MSVC's `std::string` also has SSO but with a 16-byte buffer and a 15-character threshold, the field layout is in a different order, and `sizeof` is usually 32 (x64) but the union is placed at the start. MSVC's `std::vector` is still three pointers (first, last, end), the same in essence. Library function names differ (MSVC-style mangling `?...@@`), but once IDA/Ghidra demangle them you recognize them right away.

Practical rule: don't memorize the offsets for every toolchain. Learn the mental mold: string = pointer + size + (buffer or capacity), vector = three pointers. When you meet an unfamiliar binary, build a small program with exactly that compiler, print the offsets, and apply them. That's exactly what the lab is.

## Tips when using a decompiler

Both IDA and Ghidra let you declare the types `std::string` / `std::vector` and assign them to variables, after which the pseudocode shows `.size()`, `.data()` instead of bare offsets. With IDA Pro, plugins like HexRaysPyTools (see [Lesson 4.5](/posts/re-4-5-plugins-that-rebuild-c-classes-let/)) even recognize many containers automatically. But even without a plugin, recognizing the mold by eye is a foundational skill, because the decompiler doesn't always guess right.

## Lab

The folder [labs/4.3/](https://github.com/Haind03/Technique-Reverse/blob/main/labs/4.3). You'll build `containers.cpp`, run it to see the real layout numbers on your own machine, then open it in a debugger and observe SSO and the vector's three pointers with your own eyes. Details in the lab's README, the solution in `solution.md`.

## Key takeaways
`std::string` (libstdc++, 32 bytes) is [0]=data pointer, [8]=size, [16]=buffer/capacity union. With SSO, strings up to 15 characters live right inside the object, and the data pointer points into the object itself (object+16). `std::vector` is three pointers (24 bytes): start, finish, end_of_storage, and size = (finish-start)/sizeof(T). Seeing "difference of two pointers then divide by element size" means it's computing a vector's size.

map/set are red-black trees (_Rb_tree), and shared_ptr has a control block with an atomic refcount. MSVC has different numbers but the same ideas, so test-build with exactly that compiler to get the right offsets.
