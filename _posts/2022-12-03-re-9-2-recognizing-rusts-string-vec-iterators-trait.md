---
title: "Lesson 9.2: Rust's String, Vec, iterators and trait objects"
image:
  path: /assets/img/covers/re-9-2-recognizing-rusts-string-vec-iterators-trait.webp
  alt: "Lesson 9.2: Rust's String, Vec, iterators and trait objects"
date: 2022-12-03 09:21:00 +0700
categories: ["Technique Reverse", "Part 09 · Rust"]
tags: [reverse-engineering, rust]
render_with_liquid: false
---
Last lesson you learned how to recognize a Rust binary and demangle its function names. Now the harder part, reading the code inside. Rust follows "zero-cost abstraction", which means the nice things you write in source, iterators, closures, Option, get flattened by the compiler into plain loops and branches with no trace of their original shape. The code runs fast, but the disassembly is hard to read.

This lesson covers a few of Rust's core data structures, so you can still tell what you're looking at in a lot of inlined code.

## String and str: pointer plus length, not null-terminated

This is the first thing that trips up people used to C. In C a string ends with a `0` byte, so you read until you hit `0`. Rust doesn't do that. A `String` or `&str` is a pointer to the data plus a length field, like Go (see [Lesson 8.3](/posts/re-8-3-gos-string-slice-interface-goroutine-assembly/)).

In the data section this means strings are glued together into one long block with no separators. For example you might see `"errorinvalid inputpassword"` in one run. That's three strings, `"error"`, `"invalid input"` and `"password"`, joined together. The boundaries are in the code. Each time a string is used, the compiler loads both the pointer (pointing into the middle of the block) and a length constant. To find where a string stops, look for the length, usually a constant `mov` right next to the instruction that loads the pointer.

A full `String` has three fields: pointer, length and capacity (the allocated space), 24 bytes on a 64-bit system. A `&str` is just pointer plus length, 16 bytes, because it only borrows the data.

```asm
; load a &str: lea the pointer, then load the length as a constant
lea  rax, [rip+0x...]   ; pointer to "password" in the string block
mov  esi, 8             ; length = 8, this is what tells you how long the string is
```

A pointer into the string block followed right away by a small constant is almost certainly a `&str`, and the constant is its length.

## Vec

`Vec<T>` is also three fields, pointer, length and capacity, exactly like the data part of `String` (`String` is internally a `Vec<u8>`). The only difference is the elements aren't necessarily bytes. Accessing `v[i]` becomes `[ptr + i * sizeof(T)]`, the same array formula as in [Lesson 3.2](/posts/re-3-2-variables-pointers-arrays-strings-assembly/).

A three-field struct where the second and third fields look like length and capacity (two integers, the latter greater than or equal to the former) is a `Vec` or `String`.

## Iterators

Here Rust differs from the languages before it. You write nice source like:

```rust
let sum: u32 = data.iter().map(|x| x * 2).filter(|x| x > &10).sum();
```

You'd expect the binary to have separate functions for `map`, `filter` and `sum`. It doesn't. The compiler inlines the whole iterator chain into one flat loop, where each element is doubled, compared to 10 and accumulated in the same loop body. The `map`/`filter`/`sum` structure is gone.

So don't look for a `map` or `filter` function, they don't exist as separate functions. Read the loop body and work out the steps yourself: each iteration it doubles (the `map`), then a branch skips if less than 10 (the `filter`), then it adds into an accumulator (the `sum`). The decompiler (Ghidra, Hex-Rays) usually gives a big `for` loop with many nested `if`s, and you translate that back to the original iterator idea.

With Rust you reverse at the level of what the loop does, not which function is called, because there are almost no function calls left.

## Option and Result

Rust has no `null`. It uses `Option<T>` (`Some` or `None`) and `Result<T, E>` (`Ok` or `Err`). In the binary these usually become a small tag (an integer saying which variant it is) plus the data. For types that can be optimized (like `Option<&T>`), the compiler uses the value `0`/null itself as `None`, so an `Option` is often just a check whether the pointer equals 0. A `panic` call after a check branch is usually where `unwrap()` hit a `None` or `Err`.

## Trait objects: vtable in a fat pointer

If you read [Lesson 4.2](/posts/re-4-2-classes-vtables-inheritance-rtti-rebuilding-class/) on C++ vtables, Rust's trait objects are similar with one difference. C++ puts the vtable pointer at the start of the object. Rust keeps it separate: a trait object (`&dyn Trait`, `Box<dyn Trait>`) is a fat pointer, two pointers traveling together, one to the data and one to the vtable.

A method call through a trait looks like:

```asm
; rax = data pointer, rdx = vtable pointer (travel as a pair)
mov  rcx, rax            ; pass data as self
call [rdx+0x18]          ; call the method at the slot in the vtable
```

Two pointers always together, with one used for `call [reg+offset]`, is a trait object dispatching dynamically.

## Identifying crates through strings and symbols

Even when heavily inlined, a Rust binary still leaks plenty about the libraries (crates) it uses. Path strings in panic messages often show crate names and even source file paths, for example `src/main.rs` or `.cargo/registry/.../serde-1.0.x/src/...`, which tells you which crates the code uses. Symbols (if not stripped) contain the crate name in the mangled part, for example `_ZN4core`, `_ZN5alloc`, `_ZN5serde`. Common crates to watch for are `std`/`core`/`alloc` (always present), `serde` (serialization), `tokio` (async), `reqwest`/`hyper` (HTTP) and `clap` (argument parsing).

Knowing the crates helps you guess what the program does before you read the code in detail.

## When the decompiler gives a mess

This is how I deal with real Rust binaries. Demangle and recover symbols first (Lesson 9.1), so you have function names to hold on to. Read the panic strings to learn the crates and source paths and infer the project structure. For each function, don't try to map every line back to the source. Work out what it takes, what it returns and how it transforms things, at the loop level. Accept that iterator chains are flat and read the loop by behavior. If you need a concrete value at runtime (for example a decrypted string), switch to dynamic like usual.

## Lab

In this lab you see how Rust represents familiar structures in a binary, and why iterator chains disappear. You build a small Rust program that uses `String`, `Vec`, an iterator chain and a trait object, then look at it in Ghidra or IDA to see the glued-together strings, the three-field structure of `Vec`, and the iterator inlined into a flat loop. Install Rust through rustup (https://rustup.rs) and check it with `rustc --version`. The program is `main.rs`. Build an optimized copy and a plain copy, and compare them to see the effect of optimization.

```
rustc -O main.rs -o rust_demo            # optimized build
rustc main.rs -o rust_demo_debug         # plain build, easier to read
```

Open `rust_demo` in Ghidra and run auto-analysis. In Defined Strings, look for `"ReverseEngineer"`, `"Xin chao"` and `"Hello"`, and check whether they're stuck to other strings and whether there's a terminating `0` byte. Find where `"ReverseEngineer"` is used and locate the length constant `15` loaded nearby. Then find the function `sum_even_doubled`. In the `-O` build, confirm that `filter`, `map` and `sum` aren't three separate functions but one flat loop, and point out which part of the loop does the even filtering, which does the doubling and which does the accumulation.

Next find the place where `greet()` is called through the trait object. Identify the data and vtable pointer pair and the `call [reg+offset]` instruction. Compare `rust_demo` with `rust_demo_debug` and decide in which one the iterators are easier to recognize. If there's a panic path string, find it to see the source path leaking.

Two questions to think about. Why can't you find a single string ending in a `0` byte for the literals above? And if a large program used the `serde` crate, where would you look for its traces? Try it yourself before opening the solution.

<div class="lab-box">
<div class="lab-head"><b>LAB 9.2</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/9.2/src/main.rs" download><i class="fa-solid fa-file-code"></i>src/main.rs</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The figures below follow the standard behavior of the Rust compiler (rustc and LLVM). When you build it yourself, the addresses will differ but the patterns are as described.

In Defined Strings, the three literals `"ReverseEngineer"`, `"Xin chao"` and `"Hello"` (along with format strings such as `"Name: "` and `", length: "`) live in a read-only section (`.rodata` on ELF, `.rdata` on PE). They're usually glued together into one block with no `0` byte separating them, because Rust stores a string as a pointer plus a length and needs no terminator.

The boundary of `"ReverseEngineer"` (15 characters) is set in the code, not in the data. Where the `String` is created you will see this.

```asm
lea  rax, [rip + OFFSET_to_string]   ; pointer
mov  edx, 15                         ; length, which is the string length
```

The constant `15` is the clue. Without it you wouldn't know where the string stops.

In the `-O` build, `sum_even_doubled` doesn't contain calls to `filter`, `map` or `sum`. Everything is a single loop, roughly like this.

```
acc = 0
for i in 0..len:
    x = data[i]            ; iter()
    if (x & 1) != 0:       ; filter: skip odd numbers
        continue
    acc += x * 2           ; map (double) and sum (accumulate) merged
return acc
```

The three original iterator layers become three operations in the same loop body: the parity check (`filter`), the doubling (`map`) and the addition to `acc` (`sum`). That's zero-cost abstraction: a nice abstraction in the source, zero cost in the binary, and no trace left for the reverser either. For the array `[1..8]` the even numbers 2, 4, 6, 8 double to 4, 8, 12, 16 and the sum is 40.

Trait objects are fat pointers. `Vec<Box<dyn Greeter>>` holds fat pointers, each element being two pointers: one to the object data and one to the vtable of the matching impl (`Vietnamese` or `English`). The call `g.greet()` becomes this.

```asm
mov  rdi, [data_ptr]       ; self
call [vtable_ptr + OFFSET] ; dynamic dispatch through the greet slot in the vtable
```

The difference from C++ is that the vtable pointer isn't inside the object but travels next to the data pointer as a pair.

The `rust_demo_debug` build (no `-O`) keeps more iterator functions as separate calls and inlines less, so the shape of `map` and `filter` is easier to spot. The `-O` build is much faster but flat and harder to read. When you have both, read the debug build to understand the logic and then compare with the optimized one.

If the program has a panic branch (for example an out-of-bounds array access), you'll see a string like `src/main.rs` with a line number. For external crates, the path even shows the crate name and version under `.cargo/registry/...`.

On the questions: there's no string ending in `0` because Rust uses an explicit length rather than a null terminator like C. And traces of `serde` live in the mangled symbols (`_ZN5serde...` if the binary isn't stripped) and in panic or registry paths if present.

</details>

## Key takeaways
String/str and Vec are pointer plus length (Vec/String add capacity) and not null-terminated. Strings are glued together, and the boundaries are in the length constants in the code. An iterator chain (map/filter/sum) is inlined into a flat loop with no separate functions, so read by behavior and don't look for function names.

Option/Result become a tag plus data, `None` is often just null, and a `panic` after a branch is usually an `unwrap`. A trait object is a fat pointer, a data pointer and vtable pointer pair, dispatching through `call [vtable+offset]`. Panic strings expose crate names and source paths, which helps you guess what the program does.
