---
title: "Lesson 8.1: What Go binaries look like, and why pclntab is a gift"
date: 2022-11-15 22:09:00 +0700
categories: ["Technique Reverse", "Part 08 · Go"]
tags: [reverse-engineering, golang]
render_with_liquid: false
---
The first time you open a Go binary in IDA, it feels like getting lost in a strange city: tens of thousands of functions, most named `runtime.*`, a tiny hello world file that weighs almost 2 MB. But Go is much easier to breathe in than a stripped C++ binary, because Go packs a precious thing into the binary: a table of function names. This lesson shows you how to recognize a Go binary and make use of that table.

All the numbers and asm below come from a binary built for real with Go 1.22.0 on Linux x64, and if you redo it in the lab you'll get something similar.

## Why Go binaries are so big and have so many functions

Build a Go hello world and compare it with C:

```
hello world C   (gcc, dynamic):   ~16 KB
hello world Go  (go build):       ~1.9 MB
```

A difference of more than a hundred times. The reason: Go **statically links by default**, and more importantly, it stuffs the whole **runtime** into every binary. That runtime includes the goroutine scheduler, the garbage collector, memory management, reflection. So you see a forest of `runtime.*`, `fmt.*`, `sync.*` functions even though your program only prints one line.

The practical consequence for a reverser: **don't try to read it all.** 95% of the functions are runtime and the standard library. The author's code is in the functions named `main.*` and their own packages. The first job is always to carve out the `main.*` part and ignore the rest. Sounds familiar, this is the "find the real main" mindset from [Lesson 3.1](/posts/re-3-1-hello-world-under-microscope-finding-real/), just at a larger scale.

## pclntab: why Go is never truly "stripped"

![Go binary: big runtime, pclntab survives strip](/assets/img/re/part-08/go-binary.svg)

This is the most important point of the lesson. Go embeds a structure called **pclntab** (program counter line table) into every binary. Its original purpose is so the runtime can print a stack trace with function names and line numbers on panic. But for a reverser, it's an address-to-function-name mapping table that's already in the file.

The great part: pclntab **survives even stripping**. A real test:

```
go build            -> 1.9 MB, has symbol table
go build -ldflags="-s -w"  -> 1.2 MB, "stripped"
```

The `-s -w` build makes `nm` stop listing the normal symbols. But pclntab is still sitting there intact (in the experiment, its magic was at the same offset `0x4030b` before and after stripping). That means specialized tools can still recover function names from a "stripped" Go binary. This is why RE people joke that Go binaries are never really stripped.

The pclntab magic number by Go version (the first 4 bytes of the table), and recognizing it tells you for sure this is Go:

| Magic | Go version |
|---|---|
| `fb ff ff ff` | Go 1.2 to 1.15 |
| `fa ff ff ff` | Go 1.16, 1.17 |
| `f0 ff ff ff` | Go 1.18 to 1.19 |
| `f1 ff ff ff` | Go 1.20 and up |

Lesson [8.2](/posts/re-8-2-recovering-function-names-types-go-binaries/) will use GoReSym and the IDA/Ghidra plugins to read pclntab and rename thousands of functions in a single run.

## Recognizing that a binary is Go

Before working on it, you have to be sure it's Go. A few signs are checkable in seconds. One is size: a small CLI that weighs 1 to 5 MB is suspicious. Another is the build info string, since Go embeds a version line, and you can run the official command:

```
go version hello        ->  hello: go1.22.0
go version -m hello     ->  with GOARCH, GOOS, build flags, module path
```

Without the Go toolchain, `strings` also shows a string like `go1.22.0`. You can also look for characteristic strings such as `runtime.`, `runtime.gopanic`, `fmt.` and package names, with `strings hello | grep '^go1\.'` or `grep 'runtime\.'`. And DIE (see [Lesson 2.1](/posts/re-2-1-five-minute-triage-die-strings-pe/)) often recognizes "Go build ID" right away.

## Calling convention: the version trap

This is where reversers often trip if they're used to C. Go changed how arguments are passed between versions. Before Go 1.17, all arguments and return values go through the stack, not registers like C. Reading old Go code you'll see it push arguments onto the stack and the callee read them from the stack, very different from the `rcx/rdx` habit of Win64. From Go 1.17 on (ABIInternal), it switched to passing through registers, but the register order is DIFFERENT from C. Go uses `RAX, RBX, RCX, RDI, RSI, R8, R9, R10, R11` for arguments (the first 9 registers), not System V's `RDI, RSI, RDX...`.

Looking at a real `add(a, b int) int` function, built with Go 1.22 (register ABI):

```asm
TEXT main.add(SB)
    PUSHQ BP
    MOVQ  SP, BP
    SUBQ  $0x8, SP
    MOVQ  AX, 0x18(SP)     ; a comes in from AX  (not RDI)
    MOVQ  BX, 0x20(SP)     ; b comes in from BX  (not RSI)
    ADDQ  BX, AX           ; AX = a + b
    MOVQ  AX, 0(SP)
    ...
    RET                    ; returned in AX
```

Translated: `a` arrives in `AX` (that is RAX), `b` in `BX` (RBX), and the result is also returned in `AX`. If you apply the System V rule (`a` in RDI) you'll misread everything. Always ask yourself which Go version this binary was built with, then apply the right ABI. Newer IDA and Ghidra recognize the Go ABI, but with older versions you have to know it yourself.

A syntax note: `go tool objdump` uses the Plan 9 form (`AX`, `MOVQ`), while IDA/Ghidra show Intel (`rax`, `mov`). Same thing, just different names.

## What Go leaves in the code

A few patterns you'll see a lot are covered in detail in [Lesson 8.3](/posts/re-8-3-gos-string-slice-interface-goroutine-assembly/), and I list them here so they don't catch you off guard. Strings aren't null-terminated: a Go string is a (pointer, length) pair, so a string in Go often sits stuck against other strings in one big blob, cut out by length, and seeing a huge block of text glued together is characteristic of Go. Go also inserts bounds checks on array indexes everywhere, so the code has lots of compare instructions followed by a jump to `runtime.panicIndex`. A `go f()` call turns into `runtime.newproc`, and Go functions return multiple values, which in the register ABI means returning through several registers.

## Key takeaways
Go binaries are big because of static linking plus the bundled runtime and GC, so don't read the `runtime.*` forest and focus on `main.*`. pclntab is an embedded function name table that survives strip, so Go is almost never truly stripped, and tools recover names from it (Lesson 8.2). The pclntab magic tells you the Go version: `f1 ff ff ff` is Go 1.20+.

Recognize Go by size, build info (`go version -m`), and `runtime.`/`go1.x` strings. The calling convention changes by version: before 1.17 it goes through the stack, and from 1.17 through registers but in the order `RAX, RBX, RCX, RDI, RSI...`, different from System V, with the return in AX.
