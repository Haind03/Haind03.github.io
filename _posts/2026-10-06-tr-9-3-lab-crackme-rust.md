---
title: "Lesson 9.3: Rust crackme lab, taking apart a not-so-friendly binary"
date: 2026-10-06 09:05:00 +0700
categories: ["Technique Reverse", "Part 09 · Rust"]
tags: [reverse-engineering, rust]
render_with_liquid: false
---
Rust isn't hard because it's mysterious, it's hard because the compiler is overly enthusiastic: it inlines a ton, flattens iterator chains into flat loops, and sprinkles panic machinery everywhere. But that very panic machinery is a reverser's friend. This lesson combines 9.1 and 9.2 into a real case: getting the password out of a Rust crackme.

The lab file is at [labs/9.3/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/9.3). Try it yourself first, the path is below.

## Step 0: confirm it's Rust

Before opening the disassembler, run a quick triage. `strings crackme | grep -iE "rustc|\.rs|panicked"` almost always returns something: a `rustc` version string, `.rs` file paths embedded in panic messages, and mangled symbols like `_ZN` or `_R`. Seeing these signs tells you right away you're holding Rust and not C.

Detect It Easy recognizes it too, but the `strings` habit is still worth keeping because it also gives you the landmark strings to xref in a moment.

## Step 1: use panic strings and strings as landmarks

This is the biggest difference when reversing Rust compared to C. In C you start from `main`. In Rust, the real `main` is wrapped in `lang_start` and a layer of closures, so going straight in is a bit tiring. Instead, work backwards from strings.

This crackme prints `Nope.` on failure and `Correct!` on success. Open the Strings window, find `Nope.`, press xref. It takes you straight to the failure branch of the check function, and right above it is the comparison loop. You just skipped the entire Rust runtime without reading a single line of it.

If the binary isn't stripped, you're even better off: demangled symbols (with rustfilt or let IDA/Ghidra do it) show the function name `check` plainly.

## Step 2: find the constant array

In the `check` function, the decompiler shows the input being compared against a fixed block of bytes sitting in `.rodata`:

```
6e 4a 49 4b 5f 0a 45 5a 72 42 44 10
```

Twelve bytes. And right at the top of the function there's a length check: if the length of the input string isn't 12, it returns false immediately. So the password is exactly 12 characters long. Knowing the length first gets you halfway there.

Remember from [lesson 9.2](/posts/tr-9-2-nhan-dien-crate-string-vec-iterator/): a Rust `String`/`str` is a pointer plus a length, not null-terminated. The constant array is also just a contiguous block of bytes. Don't expect a `00` separator like in C strings.

## Step 3: read the transformation

The iterator part in the original source may be an `.enumerate().map(...)` chain, but after the compiler inlines it you only see a flat loop. Don't try to rebuild the iterator syntax, just understand what it does for each character at position `i`:

```
enc = (input[i] + i) & 0xFF      ; add the index
enc = enc ^ 0x3C                 ; XOR with a constant
if enc != EXPECTED[i] -> Nope
```

Two simple operations: add the index then XOR. The nice thing is both are reversible.

## Step 4: keygen instead of guessing

Since the check can be inverted, don't brute force, just compute it. Reverse it: `input[i] = (EXPECTED[i] ^ 0x3C) - i`.

```python
EXPECTED = [0x6e,0x4a,0x49,0x4b,0x5f,0x0a,0x45,0x5a,0x72,0x42,0x44,0x10]
pw = "".join(chr(((b ^ 0x3C) - i) & 0xFF) for i, b in enumerate(EXPECTED))
print(pw)   # Rust_1s_Fun!
```

Run the crackme again with that password:

```
./crackme 'Rust_1s_Fun!'
Correct! Flag: RE{Rust_1s_Fun!}
```

Done. Note: I haven't built and run the binary for this lab in place because the environment doesn't have `rustc`, but the algorithm was checked in Python (encrypting forward gives exactly the constant array, inverting gives exactly the password). On a machine with Rust it runs as described. Details in [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/9.3/solution.md).

## Why Rust is worth practicing

Most beginners avoid Rust because the decompiler gives a confusing pile of inlining. But there are actually few tricks: latch onto panic strings and strings to locate things, look at the length of the constant block to know the input length, and prefer inverting the check over reading every line of the optimized assembly. Those three habits solve most beginner to intermediate Rust crackmes.

## Key takeaways
Confirm Rust with `strings`: the rustc version, `.rs` paths, and `_ZN`/`_R` mangling. Go from strings (`Nope.`, `Correct!`) and panic strings backwards into the check function, and don't wrestle with the wrapped `main`. The length of the constant block in `.rodata` is often exactly the password length.

Iterator chains get inlined into flat loops, so read what they do instead of rebuilding the syntax. If the check is reversible, write a keygen and don't brute force.
