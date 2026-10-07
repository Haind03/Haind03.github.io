---
title: "Lesson 9.3: Rust crackme lab, taking apart a not-so-friendly binary"
image:
  path: /assets/img/covers/re-9-3-rust-crackme-lab-taking-apart-not.webp
  alt: "Lesson 9.3: Rust crackme lab, taking apart a not-so-friendly binary"
date: 2022-12-18 15:51:00 +0700
categories: ["Technique Reverse", "Part 09 · Rust"]
tags: [reverse-engineering, rust]
render_with_liquid: false
---
Rust isn't hard because it's mysterious, it's hard because the compiler is overly enthusiastic: it inlines a ton, flattens iterator chains into flat loops, and sprinkles panic machinery everywhere. But that very panic machinery is a reverser's friend. This lesson combines 9.1 and 9.2 into a real case: getting the password out of a Rust crackme.

The lab for this lesson is at the end of the post. Try it yourself first, the walkthrough below is the path.

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

Remember from [lesson 9.2](/posts/re-9-2-recognizing-rusts-string-vec-iterators-trait/): a Rust `String`/`str` is a pointer plus a length, not null-terminated. The constant array is also just a contiguous block of bytes. Don't expect a `00` separator like in C strings.

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

Done. The algorithm checks out in Python: encrypting forward gives exactly the constant array, and inverting gives exactly the password. The full details are in the "Show solution" block.

## Why Rust is worth practicing

Most beginners avoid Rust because the decompiler gives a confusing pile of inlining. But there are actually few tricks: latch onto panic strings and strings to locate things, look at the length of the constant block to know the input length, and prefer inverting the check over reading every line of the optimized assembly. Those three habits solve most beginner to intermediate Rust crackmes.

## Lab

The goal is to recognize a Rust binary, work your way to the check function through panic strings and symbols, read the algorithm that transforms the password, and then reverse it to find a valid key. You don't patch anything, you understand and keygen. The source is `main.rs`, and the optimized build, which looks more like a real binary (inlined iterators, merged functions), is:

```
rustc -O main.rs -o crackme
```

If you don't have Rust yet, install it through rustup (https://rustup.rs). While you are still learning, you can build without optimization to make it easier to read:

```
rustc main.rs -o crackme_debug
```

Try a wrong password first with `./crackme WRONG_PASSWORD`, which prints `Nope.`.

Use Detect It Easy or `strings` to confirm it is a Rust binary (look for strings related to rustc, panic, and `.rs` paths). Open it in Ghidra or IDA and use the panic strings and symbol names (if not stripped) to find the `check` function. Find the 12-byte constant array in `.rodata` (the `EXPECTED` array), then read the transformation applied to each input character before the comparison. Write a snippet of Python (or Rust) that reverses it to recover the password from the constant array, run `./crackme <password>`, and confirm you get the `Correct!` line.

Some hints. A Rust `String`/`&str` stores a pointer plus a length and is not null-terminated, and the constant array is also a contiguous block of bytes in `.rodata`. The password length is exactly the length of the `EXPECTED` array, which is the first thing to find. And the transformation is reversible (add the index, then XOR), so reversing it means XOR first, then subtract the index. Do it yourself before opening the solution.

<div class="lab-box">
<div class="lab-head"><b>LAB 9.3</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/9.3/src/main.rs" download><i class="fa-solid fa-file-code"></i>src/main.rs</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

To recognize a Rust binary, run `strings crackme | grep -iE "rustc|\.rs|panicked"`. A Rust binary always leaves behind a compiler version string (for example `rustc 1.xx`), the `.rs` source file paths inside panic messages, and symbol mangling of the `_ZN...` (legacy) or `_R...` (v0) style. Seeing these signs is enough to know you are holding Rust and not C/C++.

There are two good landmarks for finding the check function. One is panic strings: if the code has `unwrap`/`expect` or formatting, the `.rs` path and line numbers show up in `.rodata`, and an xref back leads near the relevant function. The other is symbols: if the binary isn't stripped, look for a symbol containing `check` or `main`. If it is stripped, use the panic strings and the strings `Usage:`, `Nope.` and `Correct!` as landmarks and xref them. In this crackme, an xref from the `Nope.` string leads straight to the failure branch of `check`, and right above it is the comparison loop.

The 12-byte constant array in `.rodata` is:

```
6e 4a 49 4b 5f 0a 45 5a 72 42 44 10
```

After you strip away the inlined iterator, the loop does exactly one thing for each character at position `i`:

```
enc = (input[i] + i) & 0xFF
enc = enc ^ 0x3C
compare enc with EXPECTED[i]
```

The length must be exactly 12 (the array length), checked right at the start of the function.

The transformation is reversible. Inverting it gives `input[i] = (EXPECTED[i] ^ 0x3C) - i`:

```python
EXPECTED = [0x6e,0x4a,0x49,0x4b,0x5f,0x0a,0x45,0x5a,0x72,0x42,0x44,0x10]
pw = "".join(chr(((b ^ 0x3C) - i) & 0xFF) for i, b in enumerate(EXPECTED))
print(pw)
```

The result is:

```
Rust_1s_Fun!
```

To confirm:

```
./crackme 'Rust_1s_Fun!'
Correct! Flag: RE{Rust_1s_Fun!}
```

As a check on the algorithm in `main.rs`: encoding the password `Rust_1s_Fun!` gives exactly the `EXPECTED` array above, and reversing the `EXPECTED` array gives back exactly `Rust_1s_Fun!`.

Three takeaways. With Rust, panic strings and `.rs` paths are the best locating landmarks, so use them before diving into assembly. The length of the constant block tells you the length of the password you are looking for. And when the check is reversible, always prefer a keygen (reversing) over brute force or patching.

</details>

## Key takeaways
Confirm Rust with `strings`: the rustc version, `.rs` paths, and `_ZN`/`_R` mangling. Go from strings (`Nope.`, `Correct!`) and panic strings backwards into the check function, and don't wrestle with the wrapped `main`. The length of the constant block in `.rodata` is often exactly the password length.

Iterator chains get inlined into flat loops, so read what they do instead of rebuilding the syntax. If the check is reversible, write a keygen and don't brute force.
