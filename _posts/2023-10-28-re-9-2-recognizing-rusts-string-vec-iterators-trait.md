---
title: "Lesson 9.2: Recognizing Rust's String, Vec, iterators and trait objects"
date: 2023-10-28 21:43:00 +0700
categories: ["Technique Reverse", "Part 09 · Rust"]
tags: [reverse-engineering, rust]
render_with_liquid: false
---
Last lesson you learned how to recognize a binary as Rust and strip function names with demangling. Now comes the more headache-inducing part: reading the code inside. Rust has a philosophy that makes reversers suffer, "zero-cost abstraction". It means all the pretty things you write in the source, iterators, closures, Option, get ground flat by the compiler into bare loops and branches in the binary, with no trace of their original shape. In return the code runs fast, but whoever reads the disassembly cries.

This lesson teaches you to recognize a few of Rust's core data structures, so in a sea of inlined code you still know what you're looking at.

## String and str: pointer plus length, not null-terminated

This is the first thing that trips up people used to C. In C, a string ends with a `0` byte, so you read until you hit `0` and that's the end. Rust doesn't. A `String` or `&str` is represented by a pointer to the data plus a length field, just like Go (see [Lesson 8.3](/posts/re-8-3-gos-string-slice-interface-goroutine-assembly/)).

The practical consequence when you look at the data section is that strings are glued together into one long block with no separators. For example you see `"errorinvalid inputpassword"` sitting in one run. That's not one string, it's three strings `"error"`, `"invalid input"`, `"password"` joined together. The boundaries are elsewhere: in the code, each time a string is used, the compiler loads both the pointer (pointing into the middle of the block) and a length constant. To know where a string stops, you have to find the accompanying length, usually a constant `mov` right next to the instruction that loads the pointer.

Concretely, a full `String` has three fields: pointer, length, and capacity (the allocated space), 24 bytes in total on a 64-bit system. A `&str` is just pointer plus length, 16 bytes, because it only borrows the data and doesn't own it.

```asm
; load a &str: lea the pointer, then load the length as a constant
lea  rax, [rip+0x...]   ; pointer to "password" in the string block
mov  esi, 8             ; length = 8, this is what tells you how long the string is
```

Tip: seeing a pair of "load a pointer into the string block, then immediately load a small constant" is almost certainly a `&str` with the constant being its length.

## Vec: like String but holding any element

`Vec<T>` is also three fields pointer, length, capacity, exactly like the data part of `String` (in fact `String` is internally a `Vec<u8>`). The only difference is the elements aren't necessarily bytes. Accessing `v[i]` becomes `[ptr + i * sizeof(T)]`, the same array formula you're used to from [Lesson 3.2](/posts/re-3-2-variables-pointers-arrays-strings-assembly/).

When you see a three-field struct where the second and third fields look like length and capacity (two integers, the latter greater than or equal to the former), you're looking at a `Vec` or `String`.

## Iterators: where all the beauty disappears

This is where Rust differs from every language above. You write very elegant source:

```rust
let sum: u32 = data.iter().map(|x| x * 2).filter(|x| x > &10).sum();
```

You expect the binary to have three separate functions for `map`, `filter`, `sum`. No. The Rust compiler inlines that whole iterator chain into a single flat loop, in which each element is doubled, compared to 10, then accumulated, all in the same loop body. The `map`/`filter`/`sum` structure evaporates completely.

The consequence for the reader is that you shouldn't go looking for a `map` or `filter` function, because they don't exist as separate functions. Instead, read the loop body and recognize the steps yourself: "ah, each iteration it doubles (the `map`), then there's a branch that skips if less than 10 (the `filter`), then it adds into an accumulator variable (the `sum`)". The decompiler (Ghidra, Hex-Rays) usually gives a big `for` loop with many nested `if`s, and your job is to translate that loop back to the original iterator intent.

In other words, with Rust you reverse at the level of "what the loop does", not "which function is called", because there are almost no function calls left to hold on to.

## Option and Result: two familiar branches

Rust has no `null`, replacing it with `Option<T>` (holding `Some` or `None`) and `Result<T, E>` (holding `Ok` or `Err`). In the binary, they usually become a small tag (an integer telling which variant it is) plus the data. For types that can be optimized (like `Option<&T>`), the compiler uses the value `0`/null itself as `None`, so often an `Option` is just a check "is the pointer equal to 0". Seeing `panic` called after a check branch is usually where `unwrap()` hit a `None` or `Err`.

## Trait objects: vtable as a fat pointer

If you've read [Lesson 4.2](/posts/re-4-2-classes-vtables-inheritance-rtti-rebuilding-class/) on C++ vtables, Rust's trait objects are similar with one important difference. C++ hides the vtable pointer at the start of the object. Rust separates it: a trait object (`&dyn Trait`, `Box<dyn Trait>`) is a fat pointer, two pointers traveling together, one pointing to the data and one to the vtable.

So a method call through a trait looks like:

```asm
; rax = data pointer, rdx = vtable pointer (travel as a pair)
mov  rcx, rax            ; pass data as self
call [rdx+0x18]          ; call the method at the slot in the vtable
```

Seeing two pointers always together, with one of them used for `call [reg+offset]`, that's a trait object dispatching dynamically.

## Identifying crates through strings and symbols

Even when heavily inlined, a Rust binary still leaks plenty of clues about the libraries (crates) it uses. Path strings in panic messages often expose crate names and even source file paths, for example `src/main.rs` or `.cargo/registry/.../serde-1.0.x/src/...`, which is a gold mine for knowing which crates the code uses. Symbols (if not stripped) contain the crate name in the mangled part, for example `_ZN4core`, `_ZN5alloc`, `_ZN5serde`. The common crates to watch for are `std`/`core`/`alloc` (always present), `serde` (serialization), `tokio` (async), `reqwest`/`hyper` (HTTP), and `clap` (argument parsing).

Knowing which crates are in use helps you guess what the program does even before reading the code in detail.

## When the decompiler gives a mess, what to do

In real Rust reversing, this is the least discouraging way to work. Demangle and recover symbols first (Lesson 9.1), so you have function names to hold on to. Read the panic strings to learn the crates and source paths, and infer the project structure. For each function, don't try to map every line back to the source, and instead understand "what this function takes, what it returns, how it transforms" at the loop level. Accept that the iterator chain is flat, and read the loop by behavior and not by its original shape. If you need a concrete value at runtime (for example a decrypted string), switch to dynamic like always.

## Lab

See [labs/9.2/](https://github.com/Haind03/Technique-Reverse/blob/main/labs/9.2). You build a small Rust program using `String`, `Vec` and an iterator chain, then observe it in Ghidra to see with your own eyes the glued strings, the three-field structure of `Vec`, and the iterator inlined into a flat loop.

## Key takeaways
String/str and Vec are all pointer plus length (Vec/String add capacity) and not null-terminated. Strings are glued together, and the boundaries are in the length constants in the code. An iterator chain (map/filter/sum) is inlined into a flat loop with no separate functions, so read by behavior and don't look for function names.

Option/Result become a tag plus data, often `None` is just null, and a `panic` after a branch is usually an `unwrap`. A trait object is a fat pointer, a data pointer and vtable pointer pair, dispatching through `call [vtable+offset]`. Panic strings expose crate names and source paths, so use them to guess what the program does.
