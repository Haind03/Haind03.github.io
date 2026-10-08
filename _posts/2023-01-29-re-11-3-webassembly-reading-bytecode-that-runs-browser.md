---
title: "Lesson 11.3: WebAssembly"
image:
  path: /assets/img/covers/re-11-3-webassembly-reading-bytecode-that-runs-browser.webp
  alt: "Lesson 11.3: WebAssembly"
date: 2023-01-29 09:03:00 +0700
categories: ["Reverse Engineering", "Part 11 · JavaScript, Electron, WebAssembly"]
tags: [reverse-engineering, javascript, wasm]
render_with_liquid: false
---
When a web page does heavy work (games, crypto, encryption, image processing) that plain JavaScript can't handle, people move that part to WebAssembly (WASM). For reversers WASM is familiar and a bit strange. It's familiar because it's bytecode for a stack-based VM, like the JVM or CPython from Parts 6 and 7. It's strange because it doesn't keep variable names and often hides the important logic on purpose. This lesson covers opening a `.wasm` file and reading it.

## What WASM is, from a reverse angle

WASM is a compact bytecode format that runs in a sandbox in the browser (or in a runtime like wasmtime or Node). Two things to remember. It's stack-based, so instructions push and pop operands on a stack, like Python bytecode, with no registers like x86. And it comes in two forms, `.wasm` is the binary (what the browser downloads) and `.wat` is the equivalent text that humans can read. Your first job is almost always turning `.wasm` into `.wat`.

Unlike native code, WASM can't access system memory arbitrarily. It has a linear memory region (a flat byte array, growing in 64KB pages), a table (an array of function references, used for indirect calls), and it talks to JavaScript through imports/exports. The exported functions are where you should start reading.

## Getting the .wasm file from the web

If the target is a web page, open the browser's DevTools. In the Network tab, filter by `wasm` or look for a request ending in `.wasm`, then right-click to save. In the Sources tab, Chrome lists the loaded WASM modules, and you can view and save from there. Once you've saved the `.wasm` file you can work offline, no web page needed.

## The wabt toolkit

wabt (WebAssembly Binary Toolkit) is the main set of tools. The most used commands:

```bash
wasm2wat app.wasm -o app.wat      # binary to readable text (first step)
wasm-objdump -x app.wasm          # view headers: import, export, section, type
wasm-decompile app.wasm -o app.dcmp  # generate pseudo-C, much easier to read than WAT
wasm2c app.wasm -o app.c          # to C, to recompile or analyze deeper
```

`wasm2wat` shows every instruction exactly, while `wasm-decompile` gives you pseudo-C close to the high-level logic. I read both, the decompiled version to get the idea, and WAT when I need precision.

If you want heavier tools, Ghidra has a WASM plugin (loads `.wasm` as its own architecture, using the familiar decompiler), and there are tools like wasmdec. For most web and CTF challenges, wabt is enough.

## Reading a piece of WAT

Say a web challenge checks a key using WASM. After `wasm2wat`, you see something like:

```wat
(module
  (func $check (param $p0 i32) (result i32)   ;; takes a pointer to the string, returns 0/1
    (local $i i32)
    ...
    local.get $p0
    i32.load8_u            ;; read 1 byte from linear memory at address $p0
    i32.const 42
    i32.xor                ;; byte XOR 42
    i32.const 0x5b
    i32.eq                 ;; compare with 0x5b
    ...
  )
  (export "check" (func $check))   ;; this is the entry point
  (memory (export "memory") 1)
)
```

It reads like the Python or Java bytecode you already know. `local.get $p0` pushes the parameter onto the stack. `i32.load8_u` takes the address on top of the stack, reads 1 byte from linear memory there, and pushes the value. `i32.const 42` then `i32.xor` XORs the byte just read with 42. `i32.const 0x5b` then `i32.eq` compares it with 0x5b and pushes the 0/1 result.

In plain terms, for each character, `char ^ 42 == 0x5b`, so `char == 0x5b ^ 42 == 0x71 == 'q'`. Reading the WASM and working out the right character at the same time is what reversing looks like. An XOR pattern in a loop is almost always a check or string decode routine, same as in Lesson 1.1.

## When the logic lives in linear memory

Strings and constants are often not in the instructions but in the data section, preloaded into linear memory. `wasm-objdump -x` lists the data segments with their offsets. When the code does an `i32.load` at a fixed offset, look that offset up in the data section to see what it's reading. Beginners often miss this step and get stuck.

## Key takeaways
WASM is stack-based bytecode, read much like Python/JVM bytecode. The first step is `wasm2wat` to get text, then `wasm-decompile` to get pseudo-C, and you can get the `.wasm` from the DevTools Network or Sources tab. Start from the exported functions, since that's the entry point.

Strings and constants are in the data section of linear memory, so look them up with `wasm-objdump -x`. An XOR pattern in a loop is usually a check or string decode.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 11.3</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/11.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/11.3/src/check.wat" download><i class="fa-solid fa-download"></i>src/check.wat</a>
</div>
</div>

In this lab you take a WASM module, turn it into a readable form, find the function that checks the key, and work out the correct key. The source is `check.wat`, the WAT text of a small keygenme. Its exported function `check(ptr, len)` returns 1 if the key at `ptr` (of length `len`) is valid.

You need wabt (the WebAssembly Binary Toolkit). Download a release from the wabt page, or use `apt install wabt` or `brew install wabt`, and check it with `wasm2wat --version`. First compile the WAT into a binary so you have a `.wasm` file like the real thing.

```bash
wat2wasm check.wat -o check.wasm
```

Then work backwards as if you only had the binary.

```bash
wasm2wat check.wasm -o out.wat
wasm-objdump -x check.wasm      # see exports, memory, data section
wasm-decompile check.wasm -o out.dcmp
```

Find the exported function (the name is `check`) and read its logic in `out.wat` or `out.dcmp`. Find the target constant array in the data section (use `wasm-objdump -x`), placed at offset 256. Work out the transformation applied to each key byte and then reverse it to compute the correct key, which is 8 characters long. For an extra step, write a few lines of Python that rebuild the key from the target array.

Two questions to think about. Why start reading from the exported function rather than the first function? And if the target array isn't in an instruction but in the data section, where do you look it up? Try it yourself before opening the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The algorithm in `check.wat` can be checked with Python, where encoding forward from the correct key gives exactly the target array, and reversing the target array gives back exactly the key. The wabt commands below (`wasm2wat` and `wat2wasm`) are the standard workflow and work on any machine with wabt installed.

Step one is getting a binary to work with.

```bash
wat2wasm check.wat -o check.wasm
```

In practice you'd get `check.wasm` from the Network or Sources tab of DevTools rather than building it yourself. Here we build it to simulate that.

Step two is bringing it to a readable form.

```bash
wasm2wat check.wasm -o out.wat
wasm-objdump -x check.wasm
wasm-decompile check.wasm -o out.dcmp
```

`wasm-objdump -x` shows an exported function named `check`, an exported memory, and a data segment that loads 8 bytes at offset 256.

Step three is reading the logic. Inside `check`, the function requires `len == 8` and otherwise returns 0 immediately. Then a loop runs with i from 0 to 7. In each iteration `c = memory[ptr + i]` (byte i of the key) and `want = memory[256 + i]` (the target byte), and if `((c + i) ^ 0x1F) != want` it returns 0. If it gets through the whole loop it returns 1. So the condition for each character is this.

```
(key[i] + i) ^ 0x1F == TARGET[i]
```

Step four is the target array. The data section at offset 256 holds 8 bytes.

```
48 7d 6a 6f 7c 48 74 62
```

Step five is reversing it into the key.

```
key[i] = (TARGET[i] ^ 0x1F) - i
```

As a script:

```python
target = [0x48,0x7d,0x6a,0x6f,0x7c,0x48,0x74,0x62]
key = ''.join(chr(((t ^ 0x1F) - i) & 0xFF) for i, t in enumerate(target))
print(key)   # Wasm_Rev
```

The correct key is `Wasm_Rev`. As a cross-check (run in Python), encoding `Wasm_Rev` forward gives exactly the array `48 7d 6a 6f 7c 48 74 62`, and reversing that array gives back `Wasm_Rev`.

On the questions, you start from the exported function because it's the entry point JavaScript calls into, so it's the surface of the real logic, while the other internal functions are usually utilities generated by the compiler. The constant array isn't in an instruction but in the data section of the linear memory. Look it up with `wasm-objdump -x` (which lists the data segments with their offsets), then map the offset used by the `i32.load` instruction to that piece of data.

</details>
