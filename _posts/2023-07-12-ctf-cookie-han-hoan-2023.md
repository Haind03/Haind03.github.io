---
title: "Cookie Han Hoan 2023: writeups"
image:
  path: /assets/img/covers/ctf-cookie-han-hoan-2023.webp
  alt: "Cookie Han Hoan 2023 writeups"
date: 2023-07-12 20:00:00 +0700
categories: ["CTF Writeups", "Cookie Han Hoan 2023"]
tags: [ctf, writeup, rev]
render_with_liquid: false
---

Cookie Han Hoan was a Vietnamese CTF held in the summer of 2023. These are my notes for the second batch of reverse engineering challenges (the "arenas2" set). I solved two of them, jump and pyreverser. A third (rev1) shipped in a password protected archive that I could not open, and the fourth is a malicious document challenge that I did not open at all. The other categories are not covered here.

## Rev - jump

The challenge is a 32-bit Windows console program, `jump.exe`. It prints `jump jump jump: ` and reads a number with `scanf`. The binary also contains a function named `_flag` at `0x00401500` that prints `flag: %s`, but nothing in the normal flow calls it.

The input is read into a stack buffer without a length check, so the saved return address can be overwritten. The program treats the number as a target for the jump, and the only useful target is the address of the flag function. The address has to be entered in decimal because it is read with `scanf` as a number, so I converted it first:

```
>>> 0x00401500
4199680
```

Then I fed that value to the program:

```
./jump.exe
jump jump jump: 4199680
flag: CHH{JUMP_T0_TH3_M00N}
```

A quick disassembly confirms the target. `_flag` starts at `0x401500` with a normal function prologue and loads the flag string from `0x404000`.

Flag: `CHH{JUMP_T0_TH3_M00N}`

## Rev - pyreverser

The challenge gives `pyreverser.exe`, which is a Python program packed into an executable (PyInstaller style), plus a `pyreverser.pyc` and a `log.log` from my earlier run.

The plan is to unpack the executable and decompile the embedded bytecode. I used `pydumpck`, which wraps pycdc and uncompyle6:

```
pydumpck pyreverser.exe -p uncompyle6
```

The tool extracts the archive and writes the `.pyc` files into its output folder. Decompilation of the main module was not fully clean, so I opened the extracted `.pyc` in a hex editor (HxD). In the constants of the module there is a Base64 string:

```
Q0hIe3B5dGhvbjJFeGlfUmV2ZXJzZV9FTmdpbmVyaW5nfQ==
```

Decoding it gives the flag:

```
$ echo Q0hIe3B5dGhvbjJFeGlfUmV2ZXJzZV9FTmdpbmVyaW5nfQ== | base64 -d
CHH{python2Exi_Reverse_ENginering}
```

Flag: `CHH{python2Exi_Reverse_ENginering}`

## Rev - rev1

The challenge is a zip archive containing a single Windows executable, `rev.exe` (about 390 KB). The archive is password protected, and the password is not in the files I have, so I could not extract or analyze the executable.

Status: unsolved. I listed the archive contents and tried to extract it, but extraction fails with "unable to get password". Without the password there is nothing to analyze statically, and I did not want to guess a flag.

## Rev - cv-malware

This challenge is a malicious document reversing task. The archive contains a single Word document, `updated-cv-pentester.docx`, that is meant to look like a CV and is expected to carry a malicious payload that the player has to find and analyze. I deliberately did not open or extract it, and I did not run anything from it.

Status: not solved here. I only listed the archive contents, for safety reasons. A proper solve would be done in an isolated analysis machine, inspecting the document structure and any embedded macro or external reference without opening it in Word.
