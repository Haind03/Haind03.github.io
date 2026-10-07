---
title: "Lesson 11.3: WebAssembly, reading bytecode that runs in the browser"
date: 2026-10-06 09:11:00 +0700
categories: ["Technique Reverse", "Part 11 · JavaScript, Electron, WebAssembly"]
tags: [reverse-engineering, javascript, wasm]
render_with_liquid: false
---
When a web page does heavy work (games, crypto, encryption, image processing) that plain JavaScript can't handle, people push that part down to WebAssembly (WASM). For reversers, WASM is both familiar and strange: familiar because it's bytecode for a stack-based VM, like the JVM or CPython you met in Parts 6 and 7, strange because it doesn't keep variable names and often deliberately hides the important logic. This lesson teaches you to open up a `.wasm` file and read it.

## What WASM is, from a reverse angle

WASM is a compact bytecode format that runs in a sandbox in the browser (or in a runtime like wasmtime or Node). Two things to remember right away. It's stack-based: instructions push and pop operands on a stack, like Python bytecode, with no registers like x86. And it comes in two forms: `.wasm` is the binary (what the browser downloads) and `.wat` is the equivalent text that humans can read. Your first job is almost always turning `.wasm` into `.wat`.

Unlike native code, WASM can't access system memory arbitrarily. It has a linear memory region (a flat byte array, growing in 64KB pages), a table (an array of function references, used for indirect calls), and it talks to JavaScript through imports/exports. The exported functions are the entry points you should start reading from.

## Getting the .wasm file from the web

If the target is a web page, open the browser's DevTools. In the Network tab, filter by `wasm` or look for a request ending in `.wasm`, then right-click to save. In the Sources tab, Chrome lists the loaded WASM modules, and you can view and save from there. Once you've saved the `.wasm` file you can work offline, no web page needed.

## The wabt toolkit, a must-have

wabt (WebAssembly Binary Toolkit) is the main set of knives. The most used commands:

```bash
wasm2wat app.wasm -o app.wat      # binary to readable text (first step)
wasm-objdump -x app.wasm          # view headers: import, export, section, type
wasm-decompile app.wasm -o app.dcmp  # generate pseudo-C, much easier to read than WAT
wasm2c app.wasm -o app.c          # to C, to recompile or analyze deeper
```

`wasm2wat` gives you the truth of every instruction, while `wasm-decompile` gives you pseudo-C close to the high-level logic. Experienced people read both: use the decompiled version to get the idea, drop down to WAT when you need precision.

If you want heavier tools, Ghidra has a WASM plugin (loads `.wasm` as its own architecture, using the familiar decompiler), and there are tools like wasmdec. But for most web and CTF challenges, wabt is enough.

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

Reading it is no different from the Python or Java bytecode you already know. `local.get $p0` pushes the parameter onto the stack. `i32.load8_u` takes the address on top of the stack, reads 1 byte from linear memory there, and pushes the value. `i32.const 42` then `i32.xor` XORs the byte just read with 42. `i32.const 0x5b` then `i32.eq` compares it with 0x5b and pushes the 0/1 result.

Translated into meaning: for each character, `char ^ 42 == 0x5b`, so `char == 0x5b ^ 42 == 0x71 == 'q'`. Reading the WASM and deducing the right character at the same time, that's reversing. Seeing an XOR pattern in a loop is almost certainly a check or string decode routine, just like the experience from Lesson 1.1.

## Tip for when the logic lives in linear memory

Strings and constants are often not in the instructions but in the data section, preloaded into linear memory. `wasm-objdump -x` lists the data segments with their offsets. When the code does an `i32.load` at a fixed offset, look that offset up in the data section to see what string it's reading. This step is often missed and leaves beginners stuck.

## Key takeaways
WASM is stack-based bytecode, read much like Python/JVM bytecode. The first step is `wasm2wat` to get text, then `wasm-decompile` to get pseudo-C, and you can get the `.wasm` from the DevTools Network or Sources tab. Start from the exported functions, since that's the entry point.

Strings and constants are in the data section of linear memory, so look them up with `wasm-objdump -x`. An XOR pattern in a loop is usually a check or string decode.

## Lab
Code and instructions: [labs/11.3/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/11.3). In short: take a `.wasm` file, run `wasm2wat` and read it, find the exported function that checks the key, use `wasm-decompile` to cross-check, then work out the key.
