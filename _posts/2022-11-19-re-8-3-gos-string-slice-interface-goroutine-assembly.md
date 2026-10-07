---
title: "Lesson 8.3: Go's string, slice, interface and goroutine in assembly"
image:
  path: /assets/img/covers/re-8-3-gos-string-slice-interface-goroutine-assembly.webp
  alt: "Lesson 8.3: Go's string, slice, interface and goroutine in assembly"
date: 2022-11-19 11:53:00 +0700
categories: ["Technique Reverse", "Part 08 · Go"]
tags: [reverse-engineering, golang]
render_with_liquid: false
---
In the last lesson you learned how to recover Go function names thanks to pclntab. But reading function names is only half of it. The other half is understanding Go's characteristic data types, because they're nothing like C. A Go string doesn't end with a 0 byte, a slice is a triple, an interface hides the type pointer somewhere, and every `go func` turns into a runtime call. Without a grip on these, you look at Go disassembly and keep thinking you're reading something broken.

Every asm snippet and number in this lesson is real output, built with Go 1.22 on Linux x64, taken out with `go tool objdump` and `go tool nm`.

## Go string: pointer plus length, no 0 byte

This is the difference that trips up C people right away. In C, a string is a run of bytes ending in `\x00`, so you read until you hit 0 and you're done. Go is different: a string value is a struct with two fields:

```
type string struct {
    data *byte   // pointer to the first byte
    len  int     // length, in bytes
}
```

No terminator. The length sits in its own field. A hugely important consequence for reversing is that string literals in a Go binary are merged into one long run stuck together, with nothing separating them. The compiler stuffs everything into one blob, and each use site only keeps a pointer and length pointing into its own piece.

See that blob with your own eyes in this lesson's demo binary:

```
secret length:1907348632812595367431640625unexpected EOFunsafe...
sum:true3125-Inf+Inffileboolint8uintchanfunccall...
```

See it? The string `"secret length:"` runs straight into `"1907348..."` and then `"unexpected EOF"` with no 0 byte between them. If you open this in IDA and let it detect strings the C way, it will merge the whole cluster into one giant meaningless string, or cut in the wrong place.

How to handle it: don't trust the string boundaries IDA guesses. Instead follow the code that loads the string, because there the compiler always loads both the pointer and the length. Look at the real asm that loads the string `"GopherReverse"` (13 characters):

```asm
LEAQ 0x78bd(IP), CX        ; CX = pointer to the string's data
MOVQ CX, 0x98(SP)          ; save the pointer
MOVL $0xd, AX              ; AX = 0xd = 13 = length of "GopherReverse"
```

`0xd` is 13, exactly the length of `"GopherReverse"`. Golden tip: if you see a `LEAQ` loading a pointer into the string blob, with a small constant loaded into another register right next to it, that constant is almost certainly the string length. Take the pointer, add the length, and you cut the string cleanly out of the blob.

## Slice: pointer, len, cap

A Go slice is a three-field struct, 24 bytes on x64:

```
type slice struct {
    data *T   // pointer to the backing array
    len  int  // number of elements in use
    cap  int  // capacity
}
```

When you create a slice literal, the compiler builds the backing array and stuffs the values in. Look at the real asm that `[]int{3, 8, 15, 16, 23, 42}` builds:

```asm
MOVQ $0x3,  0x30(SP)       ; element 0 = 3
MOVQ $0x8,  0x38(SP)       ; element 1 = 8
MOVQ $0xf,  0x40(SP)       ; element 2 = 15 (0xf)
MOVQ $0x10, 0x48(SP)       ; element 3 = 16
MOVQ $0x17, 0x50(SP)       ; element 4 = 23 (0x17)
MOVQ $0x2a, 0x58(SP)       ; element 5 = 42 (0x2a)
```

Six int elements, 8 bytes each, laid out back to back on the stack exactly 8 apart. This is how you recognize a slice literal: a series of `MOVQ` writing values to consecutive stack positions. When the slice is passed into a function, you'll see three things travelling together: pointer, len, cap.

## Interface: two pointers

An interface value is also a two-field struct:

```
type iface struct {
    tab  *itab   // pointer to the type table (itab), gives the dynamic type and methods
    data *T      // pointer to the real data
}
```

The `itab` holds type info and the method table, playing a role like the vtable in C++ (see Lesson 4.2 again). When calling a method through an interface, Go reads the function pointer from the itab and calls it indirectly, just like a virtual call. In asm you see a `MOVQ` fetching the function pointer from an offset in the itab and then a `CALL` on it. Seeing `go:itab.*os.File,io.Writer` in the disassembly (which is really in the demo) is a clear sign of an interface: it pairs the concrete type `*os.File` with the interface `io.Writer`.

## Goroutine: go func becomes runtime.newproc

This is where Go looks strangest. When you write `go f(x)`, the compiler doesn't call `f` directly. It packages the function and parameters and calls `runtime.newproc`, and Go's scheduler takes care of running it on a separate goroutine. In the demo, nm confirms:

```
main.main.func1              ; the goroutine body (closure)
main.main.gowrap1            ; wrapper generated by Go
main.main.func1.deferwrap1   ; wrapper for a defer inside
runtime.newproc              ; the function that creates a goroutine
```

So when you see a `CALL runtime.newproc` in code, understand right away: there's a `go func(...)` here. The goroutine's real body sits in a separate function named like `main.xxx.funcN`. To know what the goroutine does, jump into that funcN function.

Similarly, `defer` becomes `deferwrap`/`runtime.deferproc` and runs when the function returns (`runtime.deferreturn`). Channels become calls to `runtime.chansend`/`runtime.chanrecv`. Maps become `runtime.makemap`, `runtime.mapaccess`, `runtime.mapassign`. Recognizing these runtime names lets you read the high-level intent of the code without tracing every instruction.

## Recognizing runtime calls, your compass

What all of the above has in common: Go hands a lot of work to the runtime, and the runtime functions all have clear names (after you recover symbols in Lesson 8.2). Memorize a few common ones and reading Go gets much faster:

| When you see the call | It means |
|---|---|
| `runtime.newproc` | there's a `go func(...)` |
| `runtime.deferproc` / `deferreturn` | there's a `defer` |
| `runtime.makemap` / `mapaccess` / `mapassign` | map operations |
| `runtime.makeslice` / `growslice` | creating/growing a slice |
| `runtime.chansend` / `chanrecv` | sending/receiving on a channel |
| `runtime.convT64` / `convTstring` | boxing a value into an interface |
| `runtime.stringtoslicebyte` | converting string to []byte |
| `runtime.concatstrings` | string concatenation |

## Lab

The goal is to see for yourself that Go strings are glued together in the binary, and to follow how the code loads a string with a pointer plus a length. You need a Go toolchain (`go version`), and the lab was checked with Go 1.22 on Linux x64. The program is `main.go`, and you build it with:

```
go build -o demo83 main.go
```

Look at the size: a program of a few lines comes out near 2 MB, because Go embeds the whole runtime and the garbage collector.

First see the string blob. Run this to find the run of glued strings:

```
strings demo83 | grep "secret length"
```

Notice that `secret length:` runs straight into other strings with nothing separating them. That is the evidence that a Go string doesn't end with a 0 byte. Next measure the secret string. How many characters does `"GopherReverse"` have? Disassemble `main.main` and look for that constant in hex:

```
go tool objdump -s "main.main$" demo83 | grep -iE "LEAQ|MOVL"
```

Find a `MOVL $0x..., AX` whose value equals the string length exactly. The string pointer is loaded with a `LEAQ` right nearby.

Then spot the slice literal. In the same objdump output, look for the run of `MOVQ $0x..., 0x..(SP)` instructions that load the values 3, 8, 15, 16, 23, 42 (hex 0x3, 0x8, 0xf, 0x10, 0x17, 0x2a) into stack slots 8 bytes apart. That is `[]int{...}` being built. Finally find the goroutine. List the symbols and look for the goroutine body:

```
go tool nm demo83 | grep -iE "func1|newproc|gowrap|deferwrap"
```

The function `main.main.func1` is the body of `go func(...)`, and `runtime.newproc` is where the goroutine gets created.

Two questions to think about. Why does letting IDA auto-detect C-style strings on a Go binary give wrong results? And if the binary is stripped, what still lets you find `main.main` (hint: look back at Lesson 8.2)?

<div class="lab-box">
<div class="lab-head"><b>LAB 8.3</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/8.3/src/main.go" download><i class="fa-solid fa-file-code"></i>src/main.go</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

All the output below is real, built with Go 1.22.0 on Linux x64. For the string blob:

```
$ strings demo83 | grep "secret length"
secret length:1907348632812595367431640625unexpected EOFunsafe...
```

The string `"secret length:"` is glued to `"1907348..."` and then to `"unexpected EOF"`, with no 0 byte separating them. Another example from the same binary:

```
sum:true3125-Inf+Inffileboolint8uintchanfunccall...
```

This is the nature of a Go string: the compiler merges every string literal (including those of the runtime) into one shared blob, and each use site keeps only a pointer and a length.

For the length, `"GopherReverse"` has 13 characters. In the disassembly:

```asm
LEAQ 0x78bd(IP), CX        ; CX = pointer to the string data in the blob
MOVQ CX, 0x98(SP)
MOVL $0xd, AX              ; 0xd = 13 = length of "GopherReverse"
```

`0xd` is 13, matching the length exactly. This is the common pattern: `LEAQ` loads the pointer and a small constant loads the length. Taking the pointer plus the length cuts the string cleanly out of the blob.

For the slice literal:

```asm
MOVQ $0x3,  0x30(SP)       ; 3
MOVQ $0x8,  0x38(SP)       ; 8
MOVQ $0xf,  0x40(SP)       ; 15
MOVQ $0x10, 0x48(SP)       ; 16
MOVQ $0x17, 0x50(SP)       ; 23
MOVQ $0x2a, 0x58(SP)       ; 42
```

Six int elements exactly 8 bytes apart on the stack. That is `[]int{3, 8, 15, 16, 23, 42}` being built on the stack before the slice header (data, len, cap) pointing at it is created.

For the goroutine:

```
$ go tool nm demo83 | grep -iE "func1|newproc|gowrap|deferwrap"
  480e60 T main.main.func1
  480e00 T main.main.gowrap1
  480f40 T main.main.func1.deferwrap1
  43f4a0 T runtime.newproc
```

`main.main.func1` is the real body of `go func(id int){...}`, `runtime.newproc` is where the goroutine is created (the compiler turns `go f()` into this call), and `deferwrap1` is the wrapper for `defer wg.Done()` inside the goroutine. One more thing to note is that `sumSlice` doesn't appear in `nm` because the compiler inlined it into `main`. Inlining like this is normal in Go and is one more reason the function tree in the binary doesn't match the source one to one.

On the questions, IDA's C-style string detection goes wrong because it looks for a 0 terminator byte and Go strings don't have one. It will merge the whole blob into one enormous string or cut in the wrong places, so you have to rely on the pointer plus length pair where the code loads the string. A stripped binary still lets you find `main.main` thanks to pclntab (see Lesson 8.2), the table that keeps the mapping from addresses to function names and that GoReSym can read.

</details>

## Key takeaways
A Go string is (pointer, length) and is NOT terminated by a 0 byte, so string literals merge into one stuck-together blob. To cut a string correctly, follow the code that loads it: a `LEAQ` pointer next to a small constant, which is the length. A slice is (data, len, cap), 24 bytes, and a slice literal is a series of MOVQ into consecutive stack slots.

An interface is (itab, data), and calling a method through the itab is like a virtual call. `go func` becomes `runtime.newproc`, and the real body sits in a separate `funcN` function. Learn the runtime function names (newproc, deferproc, makemap, chansend) to read high-level intent quickly.
