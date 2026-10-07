---
title: "Lesson 8.2: Recovering function names and types in Go binaries"
image:
  path: /assets/img/covers/re-8-2-recovering-function-names-types-go-binaries.webp
  alt: "Lesson 8.2: Recovering function names and types in Go binaries"
date: 2022-11-18 15:57:00 +0700
categories: ["Technique Reverse", "Part 08 · Go"]
tags: [reverse-engineering, golang]
render_with_liquid: false
---
Open a Go binary in IDA for the first time and you get many `sub_xxxxxx` functions and that familiar feeling of being lost. But even when a Go binary is stripped, most function names are still inside it. The tools just don't read them by default. This lesson shows how to pull them out.

## Why stripped Go can still be recovered

The Go runtime needs function names itself at runtime, to print a stack trace on panic. So the compiler embeds a mapping table from addresses to function names in the binary, whether or not you strip it. That table is called the pclntab (program counter line table).

Go also stores type information for reflection and the garbage collector in a structure called moduledata. Together, a Go binary carries far more metadata than a stripped C binary. Strip only removes the standard ELF/PE symbol table and doesn't touch pclntab and moduledata. That's why specialized tools can recover so much.

So with Go, don't get discouraged when you see it's stripped. Run the right tool first.

## GoReSym

GoReSym (from Mandiant) is the tool I run first. It parses pclntab and moduledata to recover function names (both the author's functions and standard library ones), type information, and build info such as the Go version, the list of modules/packages, and sometimes even source paths.

Basic run:

```
GoReSym.exe -t -d -p target_go.exe > symbols.json
```

The `-t` flag extracts types, `-d` also gets the default Go packages, and `-p` gets path/build info. The result is JSON with function names and addresses, which you load back into IDA/Ghidra with a script to rename in bulk.

Just knowing the Go version is useful. Go's calling convention changed at Go 1.17 (from passing parameters on the stack to passing through registers, ABIInternal), so the version tells you how to read the parameters. This was covered in an earlier lesson of this part.

## Plugins for IDA and Ghidra

If you'd rather keep everything in one tool instead of going through intermediate JSON, there are a few options. IDAGolangHelper and golang_loader_assist are IDA scripts (IDAPython) that find pclntab inside IDA and rename functions in place, which is handy when you're already in IDA. GolangAnalyzerExtension (GOA) is an extension for Ghidra. After installing, it recognizes Go binaries on its own, recovers function names, rebuilds types, and recognizes Go strings (which are not null-terminated but a pointer plus a length, so the default tools often read them wrong). redress is a command-line tool for the build info and package structure of a Go binary, useful for quick triage.

In practice I often run GoReSym to get the JSON (stable, doesn't depend on the IDA version), then load it into my tool of choice. Plugins are fast but sometimes struggle with newer Go versions.

## Strings in Go

Even after you have the function names, strings still trip you up. A Go string doesn't end with a 0 byte like in C. It's a two-field struct: a pointer to the data and a length. Constant strings also get merged into one big contiguous block in `.rodata`, with no separators.

So the default Strings window of IDA/Ghidra shows the whole stuck-together block as one huge meaningless string. GolangAnalyzerExtension and Go scripts handle this, cutting each string correctly by its length. Without a tool, you have to look at how the code loads the (pointer, length) pair to find the real string boundaries.

## The workflow

First recognize that it's a Go binary (DIE, or the `go:buildid` string, the `.gopclntab` section, Go runtime patterns). Run GoReSym to get symbols.json, and read the Go version and package list too. Load the symbols into IDA/Ghidra with a JSON import script, or run the corresponding plugin, and add Go string handling (GOA or a script) so strings display properly. Only then start reading code, focusing on the author's package (usually `main.*`) and skipping the runtime and standard library.

The last step saves the most time. After recovering names, `main.main` and `main.validateLicense` show up clearly among thousands of runtime functions, and you go straight to what you need.

## Lab

The goal is to see how pclntab turns a stripped Go binary from many `sub_xxx` names into a list of named functions. You need Ghidra (or IDA), GoReSym (download a release from the Mandiant GoReSym repository, or build it with `go build`), and a Go binary to try on. To be sure of what you have, build one yourself from this program:

```go
// main.go
package main

import "fmt"

func validateLicense(key string) bool {
    return len(key) == 16 && key[0] == 'G'
}

func main() {
    var k string
    fmt.Print("Key: ")
    fmt.Scanln(&k)
    if validateLicense(k) {
        fmt.Println("Correct!")
    } else {
        fmt.Println("Nope.")
    }
}
```

Build two versions, one with symbols and one stripped, so you can compare. The flags `-s -w` drop the symbol table and the debug info, imitating a real stripped binary.

```
go build -o demo_go main.go
go build -ldflags="-s -w" -o demo_go_stripped main.go
```

Open `demo_go_stripped` in Ghidra, run auto-analysis and open the Functions window. Note how many functions got a proper name and how many are `FUN_xxxxxx`, and try searching for `main.main` to see whether it's there. Then run GoReSym to pull out the symbols:

```
GoReSym -t -d -p demo_go_stripped > syms.json
```

Open `syms.json` and look for `validateLicense` and `main.main`. Did GoReSym recover them even though the binary is stripped? Read the build info part of the JSON too: what Go version is it, and is it above or below 1.17 (the point where the calling convention changed)? Then load the symbols into Ghidra, either with a script that imports the JSON and renames by address, or with GolangAnalyzerExtension. Reopen the Functions window and check whether `main.validateLicense` shows up now. Finally compare how long it took you to find the license check function before and after having the symbols.

Two questions to think about. Why does stripping with `-s -w` still fail to hide function names from GoReSym? And if an attacker really wanted to hide Go function names, what would they have to break, and why is that risky (hint: panics and stack traces)?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This writeup describes the procedure and the typical results. The exact numbers (the function count) will differ with the Go version you use, but the shape of the result is as described.

After auto-analysis, the Functions window of a stripped Go binary looks messy: thousands of entries, most of them `FUN_00xxxxxx`. Ghidra can't recover the names because the ELF/PE symbol table was wiped by `-s -w`. Searching for `main.main` by name finds nothing, so you're left feeling your way by strings or from the entry point, which is very slow. The binary appears to have lost all its information, but it didn't. The information is still in pclntab, and Ghidra just doesn't read it for Go by default.

Then GoReSym gets the names back:

```
GoReSym -t -d -p demo_go_stripped > syms.json
```

In `syms.json` you find both `main.validateLicense` and `main.main` with their addresses, even though the binary is stripped. GoReSym reads pclntab and moduledata directly, and `-s -w` doesn't touch either. The JSON looks like this (shortened):

```json
{
  "UserFunctions": [
    {"Start": 4983808, "End": 4983900, "FullName": "main.validateLicense"},
    {"Start": 4983904, "End": 4984100, "FullName": "main.main"}
  ]
}
```

The build info section of the JSON states the Go version, for example `"Version": "go1.21.3"`. That's above 1.17, so the binary uses the register-based calling convention (ABIInternal): arguments go into rax, rbx, rcx, rdi, rsi and so on instead of sitting on the stack. You need to know this to read the parameters of `validateLicense` correctly.

To load the symbols into Ghidra there are two routes. You can install GolangAnalyzerExtension and re-analyze, and it applies names and builds types by itself. Or you can write a Ghidra script that reads `syms.json` and, for each entry, calls `createFunction` and `setName` at the `Start` address. After loading, reopen the Functions window and `main.validateLicense` and `main.main` have their names. Double-click `main.validateLicense` and the decompiler gives clear logic: it checks `len(key) == 16` and that the first character is `G`.

For the comparison, before the symbols you have to trace from the entry point through the runtime init, which is easy to get lost in and takes minutes or even a whole session. After the symbols, you type `main.` into the Functions filter, see every function the author wrote, and go straight to `validateLicense` in seconds.

On the reflection questions, `-s -w` doesn't hide names from GoReSym because it only removes the standard symbol table and the DWARF debug info. pclntab is a structure of the Go runtime itself, not a symbol table, and the runtime needs it to print stack traces on a panic, so the compiler always embeds it. GoReSym reads pclntab directly and isn't affected. To really hide Go function names you have to delete or corrupt pclntab and moduledata (some Go packers and obfuscators do this, garble partly). The risk is that when the program panics the runtime reads pclntab to build the stack trace, so a broken pclntab can cause unpredictable crashes or give away the tampering. garble renames functions to hashed strings instead of deleting them, which keeps pclntab valid but the names meaningless, and that's the safer tradeoff.

With a Go binary, run GoReSym (or a plugin) before anything else. The hard part of Go isn't the lost function names, it's the register-based calling convention and how strings, slices and interfaces are represented, which Lesson 8.3 deals with.

</details>

## Key takeaways
A stripped Go binary can still recover many function names thanks to pclntab, since the runtime needs it to print stack traces. GoReSym is the first tool to run, giving function names, types, build info and the Go version. The alternatives are IDAGolangHelper for IDA, GolangAnalyzerExtension for Ghidra, and redress on the command line.

Know the Go version to read the calling convention right, since it changed at Go 1.17. A Go string is (pointer, length) and not null-terminated, so you need a tool to cut them correctly or you'll read them wrong. After recovery, focus on the `main.*` packages and skip the runtime.
