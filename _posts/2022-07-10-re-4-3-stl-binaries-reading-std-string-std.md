---
title: "Lesson 4.3: STL in binaries, std::string and std::vector"
image:
  path: /assets/img/covers/re-4-3-stl-binaries-reading-std-string-std.webp
  alt: "Lesson 4.3: STL in binaries, std::string and std::vector"
date: 2022-07-10 10:42:00 +0700
categories: ["Technique Reverse", "Part 04 · C++"]
tags: [reverse-engineering, cpp]
render_with_liquid: false
---
Real C++ code almost never uses bare C arrays alone. It's full of `std::string`, `std::vector`, `std::map`. Each of these containers has a fixed layout that repeats everywhere. Once you recognize it, a pile of `[rax]`, `[rax+8]`, `[rax+10h]` in pseudocode starts to mean something, and you can tell this is a string and that is a vector without the decompiler telling you.

This lesson focuses on the two containers you meet most (`string` and `vector`), then quickly covers the rest. Every layout number below is from libstdc++ on x64 (the g++ toolchain), checked with the lab program. MSVC differs a little, with notes at the end.

## std::string and SSO

Beginners often think `std::string` is just a pointer to a string. It isn't, and that mistake makes them misread binaries.

On libstdc++, `std::string` is a 32-byte object made of:

```
offset 0  : char*   pointer to the data (_M_p)
offset 8  : size_t  string length (_M_string_length)
offset 16 : 16-byte union {
              char   internal buffer [16]   // used when the string is short
              size_t capacity               // used when the string is long
            }
```

The important part is Small String Optimization (SSO): if the string is short enough (at most 15 characters on libstdc++), it doesn't allocate on the heap and puts the characters into the 16-byte buffer inside the object. The pointer at offset 0 then points into the object itself (object address + 16).

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

To recognize a `std::string` while debugging, find an object where offset 0 is a pointer and offset 8 is a sensible small number (the length). If that pointer points back into the object itself, it's a short SSO string. A capacity of 15 is also typical of an empty or short string on libstdc++.

In asm, getting the string length is usually:

```asm
mov  rax, [rbx+8]      ; rax = string length (the _M_string_length field)
```

and getting the data pointer to read characters:

```asm
mov  rax, [rbx]       ; rax = data pointer
movzx eax, byte [rax] ; read the first character
```

If you see "read [obj] as a pointer, read [obj+8] as a length", it's almost certainly a `std::string`.

## std::vector

![Layout of std::string with SSO and the three-pointer std::vector](/assets/img/re/part-04/stl-layout.svg)

`std::vector` is even easier to recognize. On libstdc++ it's three pointers, 24 bytes:

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

So when you see `(v[8] - v[0]) >> 2` in pseudocode, that's the `size()` of a `vector<int>` (an int is 4 bytes, so `>>2` divides by 4). A difference of two pointers divided by the element size means vector.

The lab confirms it:

```
sizeof(std::vector<int>) = 24    (exactly 3 pointers)
begin (data) = 0x...ee0          (points to the heap)
size = 4, capacity = 4
```

A loop walking a vector in asm usually loads `_M_start` into one register, loads `_M_finish` into another, and increments the pointer until they're equal. A pointer running from [obj] to [obj+8] is a `for (auto& x : v)` loop.

## The other containers

You'll meet them less, but you should know what they look like. std::map and std::set are implemented with a red-black tree. Each node has parent, left and right pointers, a color bit, and then the key/value. In the binary you see a lot of pointer operations rotating the tree and comparisons. The `sizeof` of the map itself is small (48 bytes in the lab, mostly the header node and a counter), and you recognize a map by its calls to very long library function names involving `_Rb_tree`.

std::unique_ptr is usually just a bare pointer (8 bytes), almost gone after optimization. It differs from a plain pointer only in that the destructor calls `delete` automatically. std::shared_ptr is two pointers (16 bytes), one to the object and one to a control block holding the reference count. An atomic (lock-prefixed) integer increment/decrement next to a pointer suggests shared_ptr.

## How MSVC differs

If the binary was built with MSVC (common on Windows), the numbers change but the ideas stay the same. MSVC's `std::string` also has SSO but with a 16-byte buffer and a 15-character threshold, the field layout is in a different order, and `sizeof` is usually 32 (x64) but the union is placed at the start. MSVC's `std::vector` is still three pointers (first, last, end). Library function names differ (MSVC-style mangling `?...@@`), but once IDA/Ghidra demangle them you recognize them right away.

Don't memorize the offsets for every toolchain. Remember the shape: string = pointer + size + (buffer or capacity), vector = three pointers. When you meet an unfamiliar binary, build a small program with that exact compiler, print the offsets, and apply them. The lab does exactly that.

## Tips when using a decompiler

Both IDA and Ghidra let you declare the types `std::string` / `std::vector` and assign them to variables, after which the pseudocode shows `.size()`, `.data()` instead of bare offsets. With IDA Pro, plugins like HexRaysPyTools (see [Lesson 4.5](/posts/re-4-5-plugins-that-rebuild-c-classes-let/)) even recognize many containers automatically. Even without a plugin, learn to recognize the layouts by eye, because the decompiler doesn't always guess right.

## Lab

The goal is to see the layout of `std::string` and `std::vector` yourself, understand SSO (the small string optimization), and practice recognizing them in a debugger. You build `containers.cpp`, run it to see the real layout numbers on your own machine, then open it in a debugger. On Linux with libstdc++:

```
g++ -O0 -g -std=c++17 containers.cpp -o containers
./containers
```

On Windows with the MSVC STL:

```
cl /EHsc /Zi /std:c++17 containers.cpp
containers.exe
```

On Windows with MinGW:

```
g++ -O0 -g -std=c++17 containers.cpp -o containers.exe
containers.exe
```

Run the program and write down `sizeof(std::string)` and `sizeof(std::vector<int>)` on your toolchain. Are they exactly 32 and 24 (libstdc++), and what does MSVC give? Then look at the "std::string short (SSO)" part of the output: how many bytes apart are the `data()` address and the object address, and why does the pointer point into the object itself? In the "std::string long (heap)" part, where does `data()` sit relative to the object this time, and why is that different from the short string? For the short string, what is `capacity()`, and what does that number say about the size of the SSO buffer?

Next, open the binary in Ghidra or IDA and set a breakpoint (x64dbg or gdb) right after `shortStr` and `longStr` are created. Look at the 32 bytes at each object's address and point out which part is the pointer, which is the size, and which is the buffer or capacity. For `std::vector<int> v`, look at the 24 bytes of the object and compute `(second pointer - first pointer) / 4`. Does it give `size()`?

Two questions to think about afterwards. Why does SSO exist (hint: what would a heap allocation for every short string cost)? And if you see a 24-byte object made of consecutive heap pointers, why should you suspect a `std::vector`? Try it all before opening the solution.

<div class="lab-box">
<div class="lab-head"><b>LAB 4.3</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/4.3/src/containers.cpp" download><i class="fa-solid fa-file-code"></i>src/containers.cpp</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The numbers below come from a real run on libstdc++ x64 (g++ 11). MSVC differs a little, but the principle holds. The reference output:

```
sizeof(std::string)      = 32
sizeof(std::vector<int>) = 24
sizeof(std::map<...>)    = 48

--- std::string short (SSO) ---
addr object  = 0x7ffec62d5060
data()       = 0x7ffec62d5070   (= object + 16)
size         = 2
capacity     = 15

--- std::string long (heap) ---
addr object  = 0x7ffec62d5080
data()       = 0x6306a1464eb0   (heap, far from the object)
size         = 39
capacity     = 39

--- std::vector<int> ---
addr object  = 0x7ffec62d5000
begin (data) = 0x6306a1464ee0   (heap)
size         = 4
capacity     = 4
```

On libstdc++, `sizeof(std::string)` is 32 and `sizeof(std::vector<int>)` is 24, which is exactly three 8-byte pointers. MSVC x64 also gives 32 for string but lays out the union at the start of the object, and its vector is still 24.

For the short string, `data()` equals object + 16. Short strings use SSO: the characters live in an internal buffer at offset 16 of the object, so the data pointer points into the object itself, and no heap allocation happens. For the long string, `data()` points to a heap region far from the object (a completely different address range from the object's stack). The 39-character string exceeds the SSO threshold of 15, so the string has to `malloc` a heap buffer and the pointer at offset 0 points there.

The short string's `capacity()` is 15. That is the maximum number of characters the 16-byte SSO buffer holds (15 characters plus 1 byte for the null terminator). A capacity of 15 on libstdc++ almost always means the string is in SSO mode.

The 32-byte layout of a libstdc++ `std::string` is:

```
[object + 0]  : char*  data pointer (_M_p)
[object + 8]  : size_t size (_M_string_length)
[object + 16] : 16-byte union:
                  - if SSO: the string characters live right here
                  - if heap: the first 8 bytes are the capacity (_M_allocated_capacity)
```

For `shortStr = "hi"`, object+0 holds a pointer back to object+16, object+8 holds 2, and object+16 holds the bytes `68 69 00` ("hi\0"). For `longStr`, object+0 is a heap pointer, object+8 is 39, and object+16 is the capacity (39).

The `std::vector<int>` layout is:

```
[object + 0]  : int* _M_start            (begin)
[object + 8]  : int* _M_finish           (end, after the last element)
[object + 16] : int* _M_end_of_storage   (end of capacity)
```

`(_M_finish - _M_start) / sizeof(int)` is `(pointer[8] - pointer[0]) / 4`, which is 4, equal to `size()`. It checks out.

As for the reflection questions: SSO exists to avoid a `malloc` plus `free` for every short string. Short strings are very common (variable names, keys, tokens), and if each one allocated on the heap it would be slow and fragment memory, whereas putting them in the object costs nothing. A 24-byte object made of three increasing heap pointers (start < finish <= end_of_storage) is the typical signature of a `std::vector`, and dividing the difference of the first two pointers by the element size gives the element count, a computation the compiler always generates when you call `.size()`.

You don't need to memorize the offsets of every toolchain. Remember two shapes: a string is (pointer, size, buffer-or-capacity) and a vector is three pointers. When you meet an unfamiliar binary, build a small program with that exact compiler and print the offsets, as this lab does.

</details>

## Key takeaways
`std::string` (libstdc++, 32 bytes) is [0]=data pointer, [8]=size, [16]=buffer/capacity union. With SSO, strings up to 15 characters live inside the object, and the data pointer points into the object itself (object+16). `std::vector` is three pointers (24 bytes): start, finish, end_of_storage, and size = (finish-start)/sizeof(T). A difference of two pointers divided by the element size means it's computing a vector's size.

map/set are red-black trees (_Rb_tree), and shared_ptr has a control block with an atomic refcount. MSVC has different numbers but the same ideas, so test-build with exactly that compiler to get the right offsets.
