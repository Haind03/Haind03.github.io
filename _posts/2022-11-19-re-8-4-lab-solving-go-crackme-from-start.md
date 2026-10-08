---
title: "Lesson 8.4: Lab, solving a Go crackme"
image:
  path: /assets/img/covers/re-8-4-lab-solving-go-crackme-from-start.webp
  alt: "Lesson 8.4: Lab, solving a Go crackme"
date: 2022-11-19 16:19:00 +0700
categories: ["Reverse Engineering", "Part 08 · Go"]
tags: [reverse-engineering, golang]
render_with_liquid: false
---
The previous three lessons covered the theory. Go binaries are big because they carry the whole runtime, pclntab keeps the function names, and Go strings carry a length and don't end in null. This lesson puts it together on a real crackme that I built with Go 1.22, and finds the password as if I'd never seen the source.

Every number below is real output.

## Step 0: triage

I always start with `file` and the size:

```
$ file crackme
crackme: ELF 64-bit LSB executable, x86-64, statically linked,
         Go BuildID=HFE5KTdi..., with debug_info, not stripped
$ ls -la crackme
1895284 bytes
```

Two details say it's Go, namely statically linked (almost 1.9 MB for a program that prints one line) and the Go BuildID string in the header. If you're still unsure, `go version` can read the embedded build info:

```
$ go version crackme
crackme: go1.22.0
```

On Windows, DIE will say "Compiler: Go" directly. So this is a Go binary, built with Go 1.22, not stripped.

## Step 1: get the function names back

Since it isn't stripped, pclntab is intact and the function names show up even in `strings`:

```
$ strings crackme | grep "main\."
main.main
main.checkKey
```

`main.main` is the author's real entry point (unlike `main` in C, Go runs the runtime first and then calls `main.main`). `main.checkKey` sounds like the check function, so that's the target.

In Ghidra/IDA, if the names don't show up on their own (or the binary is stripped), run GoReSym to recover them and import them, as in Lesson 8.2. Here it isn't stripped, so we go straight into `main.checkKey`.

I also tried fully stripping with `-ldflags "-s -w"`. The file dropped from 1.9 MB to 1.23 MB, but `main.checkKey` was still in strings and `go version` still read out go1.22.0. pclntab isn't a normal symbol table, and `-s -w` doesn't touch it. So a stripped Go binary still gives up its function names.

## Step 2: read the logic of checkKey

Decompile `main.checkKey` (or read the pseudocode in Ghidra once you have symbols). Skip the Go boilerplate and the core is this:

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

At the assembly level there are a few Go signs. The length comparison comes first. A Go string is a struct of a data pointer and a length, and the function takes the input's length and compares it with 11 (a constant). A `cmp` with a constant right at the start of a check function means it's rejecting wrong lengths, so the password is exactly 11 characters. Then there's a loop over each byte, with a `movzx` taking one byte of the input, `xor` with 0x17, `add` the loop index, then `cmp` with a byte in the constant array. The `want` array sits in `.rodata`. And there's no plaintext password, as I checked `strings crackme | grep GoCrackMe24` and got 0 results. The password is transformed, so you have to reverse the algorithm.

## Step 3: invert it to get the password

The relation is `want[i] = (input[i] XOR 0x17) + i`. Inverted:

```
input[i] = (want[i] - i) XOR 0x17
```

A few lines of Python to check:

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

That's a Go crackme done end to end, where you triaged as Go, used pclntab to get function names, read `checkKey`, inverted the algorithm, got the password.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 8.4</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/8.4.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/8.4/src/crackme.go" download><i class="fa-solid fa-download"></i>src/crackme.go</a>
</div>
</div>

The crackme is written in Go, and the task is to find the password without brute force. You need Go installed (check with `go version`), and the lab was built and verified with Go 1.22.0. Build the crackme from `crackme.go` in the three ways below, namely the full build that keeps pclntab, a stripped build for comparison, and an optional Windows build.

```
go build -o crackme crackme.go                        # full build, keeps pclntab
go build -ldflags "-s -w" -o crackme_strip crackme.go # stripped build, for comparison
GOOS=windows go build -o crackme.exe crackme.go       # Windows build (optional)
```

First use `file` and `go version crackme` to confirm it's a Go binary and see which version built it. Compare the size of the normal and the `-s -w` builds, check with `strings` whether `main.checkKey` is still there in the stripped one, and draw your conclusion about pclntab. Then find the function `main.checkKey` and read its logic. How many characters is the password, and how do you know? How does the algorithm transform each character? Write a snippet that reverses it to compute the password, then run `./crackme <password>` and confirm you get "Correct!".

Two questions to think about. Why does `strings` not find the password directly while it still shows function names? And if the binary were fully stripped and IDA didn't recognize the Go function names, which tool would you use (see Lesson 8.2)? Do it yourself before opening the solution. Build both the normal and stripped versions, confirm `main.checkKey` is still there in the stripped one, then invert the algorithm to get the password without running it.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The password is `GoCrackMe24`. I built it with Go 1.22.0 and verified it with real runs.

For triage:

```
$ file crackme
crackme: ELF 64-bit LSB executable, x86-64, statically linked,
         Go BuildID=HFE5KTdi..., with debug_info, not stripped
$ ls -la crackme
1895284 bytes
$ go version crackme
crackme: go1.22.0
```

Statically linked, close to 1.9 MB, with a Go BuildID, so it is definitely Go.

For pclntab and stripping:

```
$ go build -ldflags "-s -w" -o crackme_strip crackme.go
$ ls -la crackme_strip
1233048 bytes
$ go version crackme_strip
crackme_strip: go1.22.0
$ strings crackme_strip | grep -c "main.checkKey"
1
```

Stripping with `-s -w` shrinks the file from 1.9 MB to 1.23 MB, but the function name `main.checkKey` and the build info are still there, because they live in pclntab and not in the ordinary symbol table. For a Go binary, this kind of strip does not hide function names.

The logic of `checkKey` is:

```go
func checkKey(input string) bool {
    want := []byte{0x50,0x79,0x56,0x68,0x7a,0x79,0x82,0x61,0x7a,0x2e,0x2d}
    if len(input) != len(want) { return false }   // len = 11
    for i := 0; i < len(input); i++ {
        if (input[i]^0x17)+byte(i) != want[i] { return false }
    }
    return true
}
```

The password is 11 characters long (the `len` is compared against 11 right at the start of the function). Each character is XORed with 0x17, then the index is added, and the result is compared with a constant array in .rodata. There's no plaintext password (`strings crackme | grep -c GoCrackMe24` gives 0).

To invert it, start from `want[i] = (input[i] ^ 0x17) + i`, which gives `input[i] = (want[i] - i) ^ 0x17`:

```python
want = [0x50,0x79,0x56,0x68,0x7a,0x79,0x82,0x61,0x7a,0x2e,0x2d]
print(''.join(chr(((w - i) & 0xff) ^ 0x17) for i, w in enumerate(want)))
# GoCrackMe24
```

Confirming with real runs:

```
$ ./crackme GoCrackMe24
Correct! Flag: GO{GoCrackMe24}
$ ./crackme GoCrackMe25
Wrong password.
$ ./crackme short
Wrong password.
```

As for the questions, `strings` doesn't see the password because it's transformed (XOR plus index) before the comparison, and only the resulting array is in the binary. The function name is visible because pclntab stores it separately so the runtime can build stack traces. If a Go binary is stripped and IDA doesn't recognize it, run GoReSym (Lesson 8.2) to parse pclntab, export the symbols and import them into IDA/Ghidra, or use GolangAnalyzerExtension for Ghidra.

</details>

## Key takeaways
A Go binary is statically linked, unusually big, and has a Go BuildID, and `go version <file>` or DIE confirms it quickly. The author's entry point is `main.main`, not the first `main` function the runtime calls. pclntab keeps the function names and survives even `-s -w` stripping, and GoReSym recovers them when IDA/Ghidra doesn't recognize them itself.

Go check functions often compare the string length first, then loop over each byte, with the constant comparison array in .rodata. A transformed password isn't in strings, so you have to read the algorithm and invert it.
