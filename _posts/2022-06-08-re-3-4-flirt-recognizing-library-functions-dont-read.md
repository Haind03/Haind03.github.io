---
title: "Lesson 3.4: FLIRT and recognizing library functions, don't read code the author didn't write"
image:
  path: /assets/img/covers/re-3-4-flirt-recognizing-library-functions-dont-read.webp
  alt: "Lesson 3.4: FLIRT and recognizing library functions, don't read code the author didn't write"
date: 2022-06-08 21:00:00 +0700
categories: ["Technique Reverse", "Part 03 · C"]
tags: [reverse-engineering, c]
render_with_liquid: false
---
Open a tiny C binary in IDA and see the Functions table has over 1500 functions, and you'll panic. But calm down: the author only wrote a handful of functions, and the other 1490 are `printf`, `malloc`, `strlen` and the whole guts of libc stuffed straight into the file. The job of this lesson is to quickly separate those two groups, so you only read what someone actually wrote.

## Why the binary bloats: static linking

When you `gcc hello.c -o hello`, the linker has two ways to attach library code. With dynamic linking, which is the default, the binary only keeps a list of "I need `printf` from `libc.so`", while the `printf` code lives in the system library and is loaded at runtime. The file is compact and the function table clean. With static linking (`gcc -static`), all the libc code is copied straight into the file. The binary runs on its own without external libraries, but it bloats to hundreds of KB up to a few MB, and the Functions table floods with thousands of library functions.

Malware and CTF binaries very often link statically, partly to run on any machine, partly to make life hard for the analyst by burying the real code in a sea of library code. Telling which code is libc is the biggest time saver at this stage.

## FLIRT, when IDA names the familiar functions itself

![FLIRT signature: before and after applying](/assets/img/re/part-03/flirt.svg)

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

In this lab you see the forest of functions in a static binary with your own eyes, then use FLIRT to clear it away so only the author's code is left. The source is `greet.c`. The program has only two functions written by the author (`make_tag` and `main`), and everything else in a static binary is libc and CRT.

Build two variants on Linux:

```sh
gcc -O0 -no-pie greet.c -o greet_dyn
gcc -O0 -no-pie -static greet.c -o greet_static
ls -l greet_dyn greet_static
```

Notice right away that `greet_static` is many times larger than `greet_dyn`. Open `greet_dyn` in IDA (or Ghidra) and look at how many functions the Functions table has. `main` and `make_tag` sit in a fairly tidy list. Then open `greet_static` and compare the function count. Scroll through it and you will see countless unfamiliar `sub_` entries, which is libc.

Now apply FLIRT. In IDA, press `Shift+F5` (Signatures), press `Ins`, and pick the libc set matching the GCC on your machine. When the scan finishes, count how many functions got real names (`strlen`, `snprintf`, `printf`, `malloc` and so on). The "Applied" column gives the number. Filter the Functions table to drop the functions that already have library names. The remaining `sub_` entries are the author's code, so confirm that `main` and `make_tag` are in that small group. Optionally, open the same `greet_static` in Ghidra, try `Tools > Function ID`, and compare its coverage with IDA's FLIRT.

Two questions to think about. Why is the static build harder for an analyst even though it is more convenient to run? And if FLIRT names no function at all, what does that say about the signature set you chose?

<div class="lab-box">
<div class="lab-head"><b>LAB 3.4</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/3.4/src/greet.c" download><i class="fa-solid fa-file-code"></i>src/greet.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

After building and comparing sizes with `ls -l greet_dyn greet_static`, a typical result (exact numbers depend on the glibc version) is:

```
-rwxr-xr-x  greet_dyn      ~16 KB
-rwxr-xr-x  greet_static   ~900 KB to over 2 MB
```

The static one is dozens of times larger because the entire libc is stuffed in.

For the function counts, `greet_dyn` has just a handful of author functions plus a few PLT stubs (`printf`, `snprintf`, `strlen`, `__libc_start_main` and so on). It is very tidy, usually under 20 rows, and `main` and `make_tag` are found immediately. In `greet_static` the Functions table jumps to thousands of functions (typically 1500 to 2500 depending on glibc). You can scroll forever, and most are unnamed `sub_` entries. `main` and `make_tag` are buried in that sea and hard to find by eye. This is exactly why static linking makes life harder for the analyst: not because the author's code is harder, but because it is diluted among the whole libc.

To apply FLIRT in IDA, press `Shift+F5` to open the Signatures window, press `Ins` to see the available signatures, and pick the GCC libc set. The usual names are the entries starting with `libc` for 64-bit ELF. If you are unsure, try the newest libc set first and try another if it is wrong. IDA rescans, and the "Applied" column shows the number of matches. You should expect hundreds to over a thousand functions renamed to `strlen`, `snprintf`, `vfprintf`, `malloc`, `memcpy`, `__libc_start_main` and so on, so most of the Functions table now carries real names. If "Applied = 0" after the scan, the signature set does not match the glibc version. That does no harm, so choose another set and rescan.

To isolate the author's code, filter the Functions table (type into the filter box) to hide the known library names. The remaining group of unnamed `sub_` entries is very small, and in it you find `main`, which takes `argc` and `argv`, calls `make_tag`, and then calls `printf` twice, and `make_tag`, which calls `strlen` and then `snprintf` with the format string `"[user:%s len=%zu]"`. A cross-checking trick is to go from the string. Find `"Hello, %s"` in the Strings window and follow the xref, and it leads straight to `main`. Combining FLIRT (clearing libc) with going from strings (Lessons 3.1 and 2.2) is the fastest way to locate the author's code in a static binary.

For Ghidra, open `greet_static`, go to `Tools > Function ID` and enable the bundled FID databases. Ghidra usually recognizes part of it (the CRT and some common glibc functions) but with clearly lower coverage than FLIRT, and many functions stay `FUN_`. This is where your eye for the shapes of `strlen`, `strcmp` and `memcpy` pays off.

The takeaways are that the first thing to do when opening a C binary is to decide whether it is static or dynamic and apply signatures before reading, that FLIRT turns a table of 2000 functions into a handful worth reading and saves most of your time, and that when the tool can't help, the familiar shapes of libc functions are still your lifeline.

</details>

## Key takeaways
Static linking stuffs libc code into the file and bloats the function table to thousands, most of which isn't the author's code. FLIRT in IDA recognizes and names library functions by byte fingerprint; apply it via `Shift+F5` and pick the set matching the compiler. A wrong set names nothing, which is harmless, so just try another. For unfamiliar libraries you can make your own signatures with FLAIR (`pelf`/`plb` + `sigmake`), while Ghidra uses FunctionID with narrower coverage, so practice recognizing by eye.

Remember the shapes of `strlen` (scan to the 0 byte), `strcmp` (two parallel pointers), `memcpy` (block copy), and the `printf` family (has a format string).
