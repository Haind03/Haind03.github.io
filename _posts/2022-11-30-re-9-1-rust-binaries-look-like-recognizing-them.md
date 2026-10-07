---
title: "Lesson 9.1: What Rust binaries look like, recognizing them before reading"
date: 2022-11-30 16:18:00 +0700
categories: ["Technique Reverse", "Part 09 · Rust"]
tags: [reverse-engineering, rust]
render_with_liquid: false
---
Rust is spreading fast, from command-line tools to malware, so sooner or later you'll trip over a Rust binary. The bad news: Rust is one of the hardest things to read at the native level, harder than C++ and much harder than Go. The good news: it leaves a few very characteristic traces, and there's a gift called the panic string that helps you locate code quickly. This lesson teaches how to recognize a Rust binary and know in advance what you're up against.

## Why Rust is hard to read

Three reasons, and understanding them means less shock when you open the decompiler. The first is monomorphization. Generics in Rust don't share a single copy like shared templates, and each concrete type generates its own copy of the function. A `Vec<T>` used with five types is five nearly identical copies of the functions, so the binary bloats and fills with duplicate functions. The second is aggressive inlining. Rust's optimizer (through LLVM) inlines very heavily, so a nice iterator chain like `.iter().map().filter().collect()` turns into a flat loop, with no function boundaries left to hold on to. The third is static linking by default. Like Go, Rust binaries usually bundle the whole standard library, so the file is big and the author's code is mixed with a lot of library code.

One important difference from Go: Rust **has no GC runtime**, no goroutine scheduler. Structurally it's closer to C++, so the C++ reading experience from Part 4 (especially vtables, structs, STL) carries over a lot.

## Recognizing a Rust binary

![Rust binary: panic strings, v0 mangling, inlined iterators](/assets/img/technique-reverse/assets/phan-09/rust-binary.svg)

A few signs, using DIE or `strings`. Source path strings like `src/main.rs`, `library/std/src/...` and `/rustc/<hash>/...` show up because Rust embeds file paths in the panic info. There's also the version string `rustc 1.xx.x`, and crate names in symbols such as `core::`, `alloc::`, `std::` and third-party crates. Mangled symbols start with `_ZN` (legacy) or `_R` (v0), see the section below. Finally there are panic strings like `called \`Option::unwrap()\` on a \`None\` value`, `index out of bounds` and `attempt to add with overflow`.

## Name mangling: two kinds

Rust has two kinds of mangling, and you'll meet both depending on the version and build flags. Legacy (the old default) looks like C++ Itanium and starts with `_ZN`, for example `_ZN4core3fmt9Formatter3pad17h...E`, with a hash at the end (`17h...`) to distinguish the monomorphized copies. v0 (new, enabled with `-C symbol-mangling-version=v0`) starts with `_R` and can encode generics too, for example `_RNvNtCs...`. Raw it's messier to read but carries more information.

To read the names back, demangle them. rustfilt works with `cat symbols.txt | rustfilt` or `nm binary | rustfilt`, recent IDA/Ghidra can demangle both kinds on their own if you turn it on in the demangler config, and `c++filt` handles the legacy `_ZN` part at a basic level since it resembles Itanium.

The `h...` hash at the end of a legacy name often confuses beginners. It's only an identifier to avoid name collisions between monomorphized copies, and you can ignore it when reading.

## Panic strings: your best friend

This is the most valuable tip of the whole lesson. When Rust code can panic (unwrapping a None, out-of-bounds array access, division by zero, overflow in a debug build), the compiler inserts a call into the panic machinery together with **a string holding the file name and line number of the original source**.

That means in a Rust binary you'll often see strings like:

```
src/validator.rs
called `Result::unwrap()` on an `Err` value
```

Going backwards from that string (xref, like the technique in [Lesson 0.4](/posts/re-0-4-reverse-engineering-workflow-not-get-lost/)) takes you straight to the right function in the author's code, skipping the sea of library code. With a heavily optimized Rust binary, the panic string is sometimes the only trustworthy anchor to orient yourself.

## How Option, Result, and enums are represented

Rust uses `Option<T>` and `Result<T, E>` everywhere, so recognizing them helps you read the logic. They are enums with a tag (discriminant) that says which variant it is (Some/None, Ok/Err), plus a payload, and in assembly you see code reading a tag and then branching, like a tagged union. With niche optimization, for some types Rust doesn't need a separate tag. For example `Option<&T>` uses the value 0 (null) itself to represent `None`, so it's as compact as a pointer, and seeing a pointer checked `== 0` and then a branch is often an `Option` being matched. A `match` on an enum becomes a tag comparison followed by a jump table or a chain of `cmp`/`je`, like the switch-case in [Lesson 1.5](/posts/re-1-5-x86-x64-assembly-3-recognizing-if/).

## Approach strategy

Put together as a working rhythm: triage with DIE, confirm it's Rust, and note the rustc version if you see it. Turn on the demangler in IDA/Ghidra, or run rustfilt on the symbol table. Use panic strings to go backwards to the author's functions, ignoring `core`/`alloc`/`std`. Accept that iterator chains are flattened, and read by logic instead of trying to find the original function boundaries again. Use your C++ experience (Part 4) for structs and parameter passing.

## Lab

See [labs/9.1/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/9.1). If your machine has `rustc`, build a small program in both debug and release modes, observe the mangling and panic strings, then demangle with rustfilt.

## Key takeaways
Rust is hard to read because of monomorphization, heavy inlining and static linking, though structurally it's closer to C++ than Go (no GC runtime). Recognize Rust by `src/*.rs` paths, `rustc` strings, `core::`/`alloc::`/`std::` symbols and panic strings.

There are two mangling kinds, legacy `_ZN...` (with an `h...` hash) and v0 `_R...`, and you demangle with rustfilt or IDA/Ghidra. Panic strings hold the file name and source line, so use them to go backwards to the author's code, which makes them the most valuable anchor. Option/Result are tagged enums, so watch for niche optimization (None becomes null).
