---
title: "Lesson 8.2: Recovering function names and types in Go binaries"
date: 2026-10-06 09:00:00 +0700
categories: ["Technique Reverse", "Part 08 · Go"]
tags: [reverse-engineering, golang]
render_with_liquid: false
---
Open a Go binary in IDA for the first time and you'll see a sea of `sub_xxxxxx` functions and that familiar feeling of despair. But Go has a pleasant secret: even when the binary is stripped, most function names are still somewhere inside, the tools just don't know how to read them. This lesson shows you how to pull them out.

## Why stripped Go can still be recovered

The Go runtime needs to know function names itself at runtime, to print a stack trace on panic. That means the compiler has to embed a mapping table from addresses to function names right in the binary, whether or not you strip it. That table is called the **pclntab** (program counter line table).

On top of that, Go also stores type information for reflection and the garbage collector in a structure called **moduledata**. Put together, a Go binary carries far more metadata than a stripped C binary. Strip only removes the standard ELF/PE symbol table, and doesn't touch pclntab and moduledata. That's why specialized tools can recover so much.

The key point to remember: with Go, don't rush to feel discouraged when you see it's stripped. Run the right tool first.

## GoReSym, the main knife

GoReSym (from Mandiant) is the tool worth running first. It parses pclntab and moduledata to recover function names (both the author's functions and standard library ones), type information, and build info such as the Go version, the list of modules/packages, and sometimes even source paths.

Basic run:

```
GoReSym.exe -t -d -p target_go.exe > symbols.json
```

The `-t` flag extracts types, `-d` also gets the default Go packages, and `-p` gets path/build info. The result is JSON containing function names with addresses, which you then load back into IDA/Ghidra with a script to rename in bulk.

Just knowing the Go version is valuable: Go's calling convention changed at Go 1.17 (from passing parameters on the stack to passing through registers, ABIInternal), so knowing the version helps you read the parameters right. This was covered in an earlier lesson of this part.

## Plugins for IDA and Ghidra

If you'd rather keep it tidy in one tool instead of going through intermediate JSON, there are a few options. IDAGolangHelper and golang_loader_assist are IDA scripts (IDAPython) that find pclntab right inside IDA and rename functions in place, which is handy when you're already in IDA. GolangAnalyzerExtension (GOA) is an extension for Ghidra: after installing, it recognizes Go binaries on its own, recovers function names, rebuilds types, and recognizes Go strings (which are not null-terminated but a pointer plus a length, so the default tools often read them wrong). redress is a command-line tool for the build info and package structure of a Go binary, useful for quick triage.

In practice many people run GoReSym to get the JSON (stable, doesn't depend on the IDA version), then load it into their favorite tool. Plugins are fast but are sometimes picky about newer Go versions.

## Strings in Go, a trap of their own

Even after you have the function names, strings still trip you up. A Go string doesn't end with a 0 byte like in C. It's a two-field struct: a pointer to the data and a length. Constant strings also get merged into one big contiguous block in `.rodata`, with no separators.

The consequence is that the default Strings window of IDA/Ghidra shows the whole stuck-together block as one huge meaningless string. GolangAnalyzerExtension and Go scripts handle this, cutting each string correctly by its length. Without a tool, you have to look at how the code loads the (pointer, length) pair to know the real string boundaries.

## The short workflow

First recognize that it's a Go binary (DIE, or see the `go:buildid` string, the `.gopclntab` section, Go runtime patterns). Run GoReSym to get symbols.json, and read the Go version and package list too. Load the symbols into IDA/Ghidra with a JSON import script, or run the corresponding plugin, and install extra Go string handling (GOA or a script) so strings display properly. Only then start reading code, focusing on the author's package (usually `main.*`) and skipping the runtime and standard library.

That last step is where you save the most time: after recovering names, `main.main` and `main.validateLicense` show up clearly among thousands of runtime functions, and you go straight to where you need.

## Lab

See [labs/8.2/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/8.2). You'll run GoReSym on a Go binary and compare the function window in Ghidra before and after having the symbols, to see with your own eyes the difference pclntab makes.

## Key takeaways
A stripped Go binary can still recover many function names thanks to pclntab, since the runtime needs it to print stack traces. GoReSym is the first tool to run, giving function names, types, build info and the Go version. The alternatives are IDAGolangHelper for IDA, GolangAnalyzerExtension for Ghidra, and redress on the command line.

Know the Go version to read the calling convention right, since it changed at Go 1.17. A Go string is (pointer, length) and not null-terminated, so you need a tool to cut them correctly or you'll read them wrong. After recovery, focus on the `main.*` packages and skip the runtime.
