---
title: "Lesson 3.4: FLIRT and recognizing library functions, don't read code the author didn't write"
date: 2023-09-21 22:57:00 +0700
categories: ["Technique Reverse", "Part 03 · C"]
tags: [reverse-engineering, c]
render_with_liquid: false
---
Open a tiny C binary in IDA and see the Functions table has over 1500 functions, and you'll panic. But calm down: the author only wrote a handful of functions, and the other 1490 are `printf`, `malloc`, `strlen` and the whole guts of libc stuffed straight into the file. The job of this lesson is to quickly separate those two groups, so you only read what someone actually wrote.

## Why the binary bloats: static linking

When you `gcc hello.c -o hello`, the linker has two ways to attach library code. With dynamic linking, which is the default, the binary only keeps a list of "I need `printf` from `libc.so`", while the `printf` code lives in the system library and is loaded at runtime. The file is compact and the function table clean. With static linking (`gcc -static`), all the libc code is copied straight into the file. The binary runs on its own without external libraries, but it bloats to hundreds of KB up to a few MB, and the Functions table floods with thousands of library functions.

Malware and CTF binaries very often link statically, partly to run on any machine, partly to make life hard for the analyst by burying the real code in a sea of library code. Telling which code is libc is the biggest time saver at this stage.

## FLIRT, when IDA names the familiar functions itself

![FLIRT signature: before and after applying](/assets/img/technique-reverse/assets/phan-03/flirt.svg)

FLIRT (Fast Library Identification and Recognition Technology) is IDA's mechanism for recognizing a known library function and renaming it automatically. The idea is simple: each compiled libc function has a characteristic byte "fingerprint" (the pattern of the first bytes of the function, ignoring the address parts that change on relocation). IDA keeps a store of signatures for many compiler and libc versions. During analysis, it compares each function against the store, and where one matches it changes `sub_401A20` to `strlen` and colors it differently.

The result: instead of 1500 anonymous functions, you see most already carry real names, leaving a small handful of `sub_xxxx` that are the author's code. You've narrowed it down in a few seconds.

### Applying signatures in IDA

IDA auto-loads some signatures when opening a file, but not always the right set. To apply them manually, open the menu `View > Open subviews > Signatures` (or press `Shift+F5`), then press `Ins` (Insert) to open the list of available signatures. Pick the set matching the file's compiler. For example GCC libc on Linux is usually the sets named `libc_*`, and for MSVC it's `vc32*` / `vc64*` / `vcseh`. IDA then rescans and names the matching functions, and the "Applied" column tells you how many matched.

A practical tip: if after scanning there are still many `sub_`, try the signature set of a different compiler version. A wrong set matches no function at all, which does no harm, so just try another.

### Making your own signatures with FLAIR

When you meet an unfamiliar static library (for example a game SDK, a crypto library packaged as `.lib` / `.a`), IDA has no ready signatures. Hex-Rays' FLAIR toolkit lets you generate them yourself:

```text
pelf / pcf / plb / pmsvc   -> create a pattern file (.pat) from .a / .lib / .obj
sigmake                    -> turn the .pat into a .sig usable in IDA
```

The short workflow is to run the parser tool (`plb` for `.lib`, `pelf` for `.a`) to output a `.pat`, then `sigmake name.pat name.sig`. If there's a collision (two functions with the same fingerprint), sigmake outputs an `.exc` file so you decide which to keep. Copy the `.sig` into IDA's `sig/` folder and it can be applied. With a signature for the very library the target uses, you save hours.

## On the Ghidra side: FunctionID

Ghidra has an equivalent mechanism called FunctionID. It also relies on a characteristic function hash to recognize known libraries. Ghidra ships a few FID sets for common runtimes (Visual Studio, some libc). You turn it on via `Tools > Function ID`, and you can build your own FID database from a known library binary. The coverage of the default FID isn't as wide as FLIRT, so on Ghidra you'll rely a bit more on recognizing by eye.

## When there's no signature: recognizing standard functions by eye

Often you have no matching signature set. Then a few common libc functions still have a very recognizable shape.

A hand-rolled `strlen` is a scan loop to the 0 byte:

```asm
    xor  eax, eax           ; i = 0
loop:
    cmp  byte [rdi+rax], 0  ; s[i] == 0 ?
    je   done
    inc  rax                ; i++
    jmp  loop
done:
    ret                     ; returns the length in rax
```

Translated to C:

```c
size_t strlen(const char *s) {
    size_t i = 0;
    while (s[i] != 0) i++;
    return i;
}
```

See a loop scanning byte by byte until it hits 0 and then returning the count, and it's almost certainly `strlen` or one of its relatives.

`strcmp` is a parallel comparison of two pointers, stopping when they differ or when it hits 0:

```asm
loop:
    mov  al, [rdi]
    cmp  al, [rsi]
    jne  diff
    test al, al          ; reached the end of the string?
    je   equal
    inc  rdi
    inc  rsi
    jmp  loop
```

Two pointers running in parallel, comparing byte by byte, with a check for the 0 byte: that's the geometric signature of `strcmp`/`memcmp`. `memcpy` is a loop copying in big blocks (often using wide registers, movups/rep movsb). Getting familiar with these few functions is enough to not get lost.

Another free clue is the format string. A function that takes a string with `%d`, `%s` and then calls around is almost certainly related to the `printf` family.

## The working rhythm that follows

Open a C binary, and before reading any function, check whether the file is static or dynamic (DIE, or file size, number of imports). If it's static, brace yourself for many functions. Then apply FLIRT (IDA) or FID (Ghidra) right away and let the tool name the libc part for you. The functions that remain as `sub_` after applying signatures are what's worth reading. Start there, combining going from strings and from main (Lesson 3.1).

## Lab

See [labs/3.4/](https://github.com/Haind03/Technique-Reverse/blob/main/labs/3.4). You'll build the same program in static and dynamic forms, open the static one in IDA to see the forest of functions, then apply the libc FLIRT and count how many functions get named, compared to the tidy dynamic version.

## Key takeaways
Static linking stuffs libc code into the file and bloats the function table to thousands, most of which isn't the author's code. FLIRT in IDA recognizes and names library functions by byte fingerprint; apply it via `Shift+F5` and pick the set matching the compiler. A wrong set names nothing, which is harmless, so just try another. For unfamiliar libraries you can make your own signatures with FLAIR (`pelf`/`plb` + `sigmake`), while Ghidra uses FunctionID with narrower coverage, so practice recognizing by eye.

Remember the shapes of `strlen` (scan to the 0 byte), `strcmp` (two parallel pointers), `memcpy` (block copy), and the `printf` family (has a format string).
