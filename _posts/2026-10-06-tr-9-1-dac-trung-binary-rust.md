---
title: "Lesson 9.1: What Rust binaries look like, recognizing them before reading"
date: 2026-10-06 09:03:00 +0700
categories: ["Technique Reverse", "Part 09 · Rust"]
tags: [reverse-engineering, rust]
render_with_liquid: false
---
Rust is spreading fast, from command-line tools to malware, so sooner or later you'll trip over a Rust binary. The bad news: Rust is one of the hardest things to read at the native level, harder than C++ and much harder than Go. The good news: it leaves a few very characteristic traces, and there's a gift called the panic string that helps you locate code quickly. This lesson teaches how to recognize a Rust binary and know in advance what you're up against.

## Why Rust is hard to read

Three reasons, and understanding them means less shock when you open the decompiler:

1. **Monomorphization.** Generics in Rust don't share a single copy like shared templates. Each concrete type generates its own copy of the function. A `Vec<T>` used with five types is five nearly identical copies of the functions, so the binary bloats and fills with duplicate functions.
2. **Aggressive inlining.** Rust's optimizer (through LLVM) inlines very heavily. A nice iterator chain like `.iter().map().filter().collect()` turns into a flat loop, with no function boundaries left to hold on to.
3. **Static linking by default.** Like Go, Rust binaries usually bundle the whole standard library, so the file is big and the author's code is mixed with a lot of library code.

One important difference from Go: Rust **has no GC runtime**, no goroutine scheduler. Structurally it's closer to C++, so the C++ reading experience from Part 4 (especially vtables, structs, STL) carries over a lot.

## Recognizing a Rust binary

![Rust binary: panic strings, v0 mangling, inlined iterators](/assets/img/technique-reverse/assets/phan-09/rust-binary.svg)

A few signs, using DIE or `strings`:

- **Source path strings** like `src/main.rs`, `library/std/src/...`, `/rustc/<hash>/...`. Rust embeds file paths in the panic info, which shows right away.
- **Version string** `rustc 1.xx.x`.
- **Crate names** in symbols: `core::`, `alloc::`, `std::`, and third-party crate names.
- **Mangled symbols** starting with `_ZN` (legacy) or `_R` (v0), see the section below.
- **Panic strings** like `called \`Option::unwrap()\` on a \`None\` value`, `index out of bounds`, `attempt to add with overflow`.

## Name mangling: two kinds

Rust has two kinds of mangling, and you'll meet both depending on the version and build flags:

- **Legacy** (the old default): looks like C++ Itanium, starts with `_ZN`, for example `_ZN4core3fmt9Formatter3pad17h...E`. There's a hash at the end (`17h...`) to distinguish the monomorphized copies.
- **v0** (new, enabled with `-C symbol-mangling-version=v0`): starts with `_R`, and can encode generics too, for example `_RNvNtCs...`. Raw it's messier to read but carries more information.

To read the names back, demangle:
- **rustfilt**: `cat symbols.txt | rustfilt`, or `nm binary | rustfilt`.
- Recent **IDA/Ghidra** can demangle both kinds on their own, turn it on in the demangler config.
- `c++filt` handles the legacy `_ZN` part at a basic level since it resembles Itanium.

The `h...` hash at the end of a legacy name often confuses beginners. It's only an identifier to avoid name collisions between monomorphized copies, and you can ignore it when reading.

## Panic strings: your best friend

This is the most valuable tip of the whole lesson. When Rust code can panic (unwrapping a None, out-of-bounds array access, division by zero, overflow in a debug build), the compiler inserts a call into the panic machinery together with **a string holding the file name and line number of the original source**.

That means in a Rust binary you'll often see strings like:

```
src/validator.rs
called `Result::unwrap()` on an `Err` value
```

Going backwards from that string (xref, like the technique in [Lesson 0.4](/posts/tr-0-4-quy-trinh-reverse/)) takes you straight to the right function in the author's code, skipping the sea of library code. With a heavily optimized Rust binary, the panic string is sometimes the only trustworthy anchor to orient yourself.

## How Option, Result, and enums are represented

Rust uses `Option<T>` and `Result<T, E>` everywhere, so recognizing them helps you read the logic:

- `Option<T>` and `Result<T, E>` are enums with a tag (discriminant) that says which variant it is (Some/None, Ok/Err), plus a payload. In assembly you see code reading a tag and then branching, like a tagged union.
- **Niche optimization**: for some types, Rust doesn't need a separate tag. For example `Option<&T>` uses the value 0 (null) itself to represent `None`, so it's as compact as a pointer. Seeing a pointer checked `== 0` and then a branch is often an `Option` being matched.
- A `match` on an enum becomes a tag comparison followed by a jump table or a chain of `cmp`/`je`, like the switch-case in [Lesson 1.5](/posts/tr-1-5-assembly-3-cau-truc-dieu-khien/).

## Approach strategy

Put together as a working rhythm:

1. Triage with DIE, confirm it's Rust, note the rustc version if you see it.
2. Turn on the demangler in IDA/Ghidra, or run rustfilt on the symbol table.
3. Use panic strings to go backwards to the author's functions, ignoring `core`/`alloc`/`std`.
4. Accept that iterator chains are flattened, read by logic and don't try to find the original function boundaries again.
5. Use your C++ experience (Part 4) for structs and parameter passing.

## Lab

See [labs/9.1/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/9.1). If your machine has `rustc`, build a small program in both debug and release modes, observe the mangling and panic strings, then demangle with rustfilt.

## Key takeaways
- Rust is hard to read because of monomorphization, heavy inlining, static linking. Structurally it's closer to C++ than Go (no GC runtime).
- Recognize Rust by `src/*.rs` paths, `rustc` strings, `core::`/`alloc::`/`std::` symbols, panic strings.
- Two mangling kinds: legacy `_ZN...` (with an `h...` hash) and v0 `_R...`. Demangle with rustfilt or IDA/Ghidra.
- Panic strings hold the file name and source line, use them to go backwards to the author's code. This is the most valuable anchor.
- Option/Result are tagged enums, watch for niche optimization (None becomes null).
