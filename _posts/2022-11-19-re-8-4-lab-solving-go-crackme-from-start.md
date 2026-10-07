---
title: "Lesson 8.4: Lab, solving a Go crackme from start to finish"
date: 2022-11-19 16:19:00 +0700
categories: ["Technique Reverse", "Part 08 · Go"]
tags: [reverse-engineering, golang]
render_with_liquid: false
---
The previous three lessons gave you the theory: Go binaries are big because they carry the whole runtime, pclntab keeps the function names, Go strings go by length and don't end in null. This lesson puts it all together on a real crackme that I built with Go 1.22 while writing, then walks you through finding the password as if you'd never seen the source.

Every number below is real output, not something I made up to look nice.

## Step 0: triage, know what you're holding

Always start with `file` and look at the size:

```
$ file crackme
crackme: ELF 64-bit LSB executable, x86-64, statically linked,
         Go BuildID=HFE5KTdi..., with debug_info, not stripped
$ ls -la crackme
1895284 bytes
```

Two details give away right away that it's Go: **statically linked** (almost 1.9 MB for a program that prints one line) and the **Go BuildID** string in the header. If you're still unsure, `go version` can read the embedded build info:

```
$ go version crackme
crackme: go1.22.0
```

On Windows, DIE will say "Compiler: Go" outright. Triage done: this is a Go binary, built with Go 1.22, not stripped.

## Step 1: get the function names back

Since it isn't stripped, pclntab is intact and the function names show up even in `strings`:

```
$ strings crackme | grep "main\."
main.main
main.checkKey
```

`main.main` is the author's real entry point (unlike `main` in C, Go has the runtime run first and then call `main.main`). `main.checkKey` sounds like the check function. We have a target.

In Ghidra/IDA, if the names don't show up on their own (or the binary is stripped), run GoReSym to recover them and import them, as in Lesson 8.2. Here it isn't stripped so we jump straight into `main.checkKey`.

One thing worth remembering: I tried fully stripping with `-ldflags "-s -w"`, and the file dropped from 1.9 MB to 1.23 MB, **but `main.checkKey` was still in strings and `go version` still read out go1.22.0.** That's because pclntab isn't a normal symbol table, and `-s -w` doesn't touch it. For a reverser, this is good news: a stripped Go binary still gives up its function names.

## Step 2: read the logic of checkKey

Decompile `main.checkKey` (or read the pseudocode in Ghidra once you have symbols). Skip the Go boilerplate, and the core boils down to this:

```go
func checkKey(input string) bool {
    want := []byte{0x50, 0x79, 0x56, 0x68, 0x7a, 0x79, 0x82, 0x61, 0x7a, 0x2e, 0x2d}
    if len(input) != len(want) {      // compare len first, len(want) = 11
        return false
    }
    for i := 0; i < len(input); i++ {
        if (input[i]^0x17)+byte(i) != want[i] {
            return false
        }
    }
    return true
}
```

When reading at the assembly level, there are a few Go signs you'll run into. The length comparison comes first: a Go string is a struct of a data pointer and a length, and the function takes the input's length and compares it with 11 (a constant). Seeing a `cmp` with a constant right at the start of a check function means it's blocking wrong lengths, which tells you the password is exactly 11 characters. Then there's a loop over each byte, with a `movzx` taking one byte of the input, `xor` with 0x17, `add` the loop index, then `cmp` with a byte in the constant array, and the `want` array sits in `.rodata`. Finally, there's no plaintext password: I checked `strings crackme | grep GoCrackMe24` and got 0 results. The password is transformed so it doesn't show, and you have to reverse the algorithm.

## Step 3: invert it to get the password

The relation is `want[i] = (input[i] XOR 0x17) + i`. Inverted:

```
input[i] = (want[i] - i) XOR 0x17
```

A few lines of Python to be sure:

```python
want = [0x50,0x79,0x56,0x68,0x7a,0x79,0x82,0x61,0x7a,0x2e,0x2d]
pw = ''.join(chr(((w - i) & 0xff) ^ 0x17) for i, w in enumerate(want))
print(pw)   # GoCrackMe24
```

Out comes `GoCrackMe24`. Try it on the real binary:

```
$ ./crackme GoCrackMe24
Correct! Flag: GO{GoCrackMe24}
$ ./crackme GoCrackMe25
Wrong password.
```

Correct. You just reversed a Go crackme end to end: triaged it as Go, used pclntab to get function names, read `checkKey`, inverted the algorithm, got the password.

## Lab

The files are in `labs/8.4/`. `src/crackme.go` has the build commands (including the normal build, the `-s -w` build, and the Windows build), `README.md` gives the task, and `solution.md` is the full writeup, with real build and run results.

Do it yourself before opening the solution: build both the normal and stripped versions, confirm `main.checkKey` is still there in the stripped one, then invert the algorithm to get the password without running it.

## Key takeaways
A Go binary is statically linked, unusually big, and has a Go BuildID, and `go version <file>` or DIE confirms it quickly. The author's entry point is `main.main`, not the first `main` function the runtime calls. pclntab keeps the function names and survives even `-s -w` stripping, and GoReSym recovers them when IDA/Ghidra doesn't recognize them itself.

Go check functions often compare the string length first, then loop over each byte, with the constant comparison array in .rodata. A transformed password isn't in strings, so you have to read the algorithm and invert it.
