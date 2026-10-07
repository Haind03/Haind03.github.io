---
title: "Lesson 18.4: Binary diffing, finding vulnerabilities from the patch itself"
date: 2023-12-14 15:21:00 +0700
categories: ["Technique Reverse", "Part 18 · Advanced Topics"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
There's an interesting paradox in security: often the fastest way to learn what vulnerability a piece of software had is to read its patch. The vendor ships an update with a vague changelog line like "fixed some stability issues". But where the binaries before and after the patch differ tells you straight out where the bug is. Comparing two binaries to find what differs is called binary diffing, and when the two binaries are before/after a patch it's specifically called patch diffing.

This lesson shows you that technique with an example that actually ran: two versions of the same program, one with a bug, one patched, and how diffing points straight at the fixed function.

## What it's used for

There are three common situations. The first is patch diffing for vulnerability research: compare the old version and the patched one, find the fixed function, and understand the bug that was fixed. From there you rebuild the vulnerability to write a detection signature, or verify that your own systems are safe. This is legitimate defensive work, and also how people research 1-days (a vulnerability that was just patched but many machines haven't updated).

The second is comparing malware variants. Two malware samples from the same family share most of their code, and a diff shows what the attacker added or changed in the new variant, which helps update rules. The third is recovering already-known functions. You analyzed a binary thoroughly, and now you meet another binary that shares a library. A diff helps transfer function names and comments from the old one to the new one, saving you from starting over.

## Tools

Diffing doesn't compare byte by byte (almost every byte changes just because addresses shifted), it compares function structure: control flow graph (CFG), number of blocks, number of calls, constants. Each pair of functions gets a similarity score from 0 to 1.

| Tool | Notes |
|---|---|
| BinDiff (Google, free) | The industry standard. Export the two analyzed binaries from IDA or Ghidra (in BinExport format) and compare them, and it shows a table of matched/unmatched functions with similarity. A function at 1.00 is identical, a function below 1.00 is worth a look. |
| Diaphora (open source, for IDA) | Very powerful, also compares pseudocode, and imports results back into IDA to port names/comments. |
| ghidriff (Ghidra-based, command line) | Runs headless, outputs a markdown report, handy for automation and CI. |
| radiff2 (radare2) | Quick diff from the command line, `radiff2 -A -C v1 v2` compares by function. |

A few concepts to remember. A matched function is one where a corresponding pair was found between the two sides. An unmatched function exists only on one side, meaning a function that was added or removed. Similarity matters because a matched function that differs is where a real change is. In patch diffing, you dive straight into the matched functions with similarity below 1.00.

## A real example

Lab [18.4](https://github.com/Haind03/Technique-Reverse/tree/main/labs/18.4) has two versions of a small login program. The only difference in the source is in the `copy_name` function: v1 copies the username with `strcpy` into a 16-byte buffer without checking the length (a classic stack buffer overflow), and v2 adds a length check before copying.

Build both with gcc `-O1` and run `objdump -d`. This is `copy_name` from v1 (the vulnerable one):

```asm
<copy_name>:
    push   %rbx
    sub    $0x10,%rsp
    mov    %rdi,%rsi
    mov    %rsp,%rbx
    mov    $0x10,%edx
    mov    %rbx,%rdi
    call   __strcpy_chk       ; copies directly, no length check
    ...
    call   __printf_chk
    ret
```

And `copy_name` from v2 (the patched one):

```asm
<copy_name>:
    push   %rbp
    push   %rbx
    sub    $0x18,%rsp
    mov    %rdi,%rbx
    call   strlen             ; NEW: measure the length first
    cmp    $0xf,%rax          ; NEW: compare with 15
    ja     <copy_name+0x4c>   ; NEW: too long, jump away to report an error
    mov    %rsp,%rbp
    mov    $0xf,%edx
    mov    %rbx,%rsi
    mov    %rbp,%rdi
    call   strncpy            ; changed from strcpy to strncpy, limited to 15
    movb   $0x0,0xf(%rsp)     ; NEW: manually set the NUL at the end
    ...
    call   __printf_chk
    ret
    ; error branch "Name too long"
    lea    ...,%rdi
    call   puts
    jmp    ...
```

The story is obvious at a glance. The patched function has an extra `strlen` + `cmp $0xf` + `ja` group, and `strcpy` became a bounded `strncpy`. The new `cmp` is exactly the bound check the old version lacked, so v1's vulnerability is a buffer overflow when the name is longer than 15 characters. You just found the bug without anyone telling you, only by comparing the two versions.

The other two functions, `main` and `check_pin`, are structurally identical between v1 and v2 (only the addresses are shifted). A diffing tool would score them at similarity close to 1.00 and skip them, while `copy_name` would stand out with a low similarity. That's exactly where you need to read.

## The patch diffing workflow

Start by getting two versions, before and after the patch (usually downloadable from the vendor, or extracted from the update package). Analyze each one in IDA/Ghidra and export in a diffable format (BinExport for BinDiff, or use Diaphora/ghidriff directly). Run the diff and sort the table by similarity ascending.

Skip the 1.00 functions, and focus on matched functions with low similarity and newly appeared unmatched functions. Read where the two functions differ. An added check, a dangerous API swapped for a safe one, a fixed size comparison, all of them are signs of where a bug used to be. Finally, rebuild the scenario that triggers the bug in the old version to understand it and write a signature.

## Common pitfalls

A compiler version or optimization flag change between the two builds drops similarity across the board even though the logic didn't change, which makes noise, so try to compare two builds from the same toolchain when you can. A function inlined in one build and not in the other won't match. In this lab I had to add `__attribute__((noinline))` to keep `copy_name` a separate function, otherwise the compiler inlines it into `main` and the per-function diff isn't clean anymore. And a big patch changes many functions at once, so you have to filter for the ones related to the vulnerability and not every harmless change.

## Key takeaways
Diffing compares function structure (CFG), not raw bytes, so shifted addresses don't throw off the result. In patch diffing, matched functions with low similarity and new unmatched functions are what's worth reading. A new bound check, or an API changed from strcpy to strncpy, is the classic sign of where a bug used to be.

BinDiff and Diaphora give a detailed GUI, while ghidriff and radiff2 are for command line and automation. Use the same toolchain for both builds to avoid similarity noise.
