---
title: "Lesson 18.1: Scripting the decompiler, let the machine do the boring work"
image:
  path: /assets/img/covers/re-18-1-scripting-decompiler-let-machine-do-boring.webp
  alt: "Lesson 18.1: Scripting the decompiler, let the machine do the boring work"
date: 2023-08-25 21:24:00 +0700
categories: ["Technique Reverse", "Part 18 · Advanced Topics"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
Some jobs in reverse engineering repeat until they're boring: decrypting the same kind of string encryption for three hundred strings, mass-renaming functions by some rule, marking every call to an API. Doing it by hand is both slow and error-prone. That's when you write a script and let the decompiler do it. Knowing scripting is the line between someone who uses tools and someone who drives them.

All three big platforms have an API: IDA has IDAPython, Ghidra has Java/Python scripting, Binary Ninja has a Python API. The idea is the same, only the syntax differs. This lesson focuses on IDAPython because it's the most common, then touches on the other two.

## When it's worth writing a script

Don't script everything. A pragmatic rule: if an operation is something you're about to do more than a dozen times the same way, or a transformation applied at many locations, script it. Classic cases are decrypting encrypted strings in bulk and putting a comment right next to each, renaming functions by pattern (for example every function that calls `print_error` with a fixed error code), finding all the places that call a suspicious API and listing the parameters, marking crypto constants, bulk patching, and extracting data tables.

If you only do it once or twice, doing it by hand is faster than writing a script.

## IDAPython: three groups of functions to remember

IDAPython is packaged into a few modules. The three used most are `idautils`, which has convenient iterators (`Functions()` walks every function, `XrefsTo(ea)` lists xrefs), `idc`, which has the old script-style functions (read/write bytes, set comments, rename) and is easy to use, and `idaapi` / `ida_*`, which is the full low-level API.

A few basic operations:

```python
import idautils, idc, ida_bytes, ida_name

# walk every function and print its name
for ea in idautils.Functions():
    print(hex(ea), idc.get_func_name(ea))

# read n bytes at an address
data = ida_bytes.get_bytes(ea, n)

# set a repeatable comment at an address
idc.set_cmt(ea, "decrypted string: hello", 1)

# rename an address
ida_name.set_name(ea, "decrypt_string", ida_name.SN_CHECK)

# find every place that calls a function
for xref in idautils.XrefsTo(target_ea):
    print(hex(xref.frm))
```

It looks like a lot of function names, but you only need to remember a few: walk, read bytes, set comment, rename, get xrefs. Look up the rest when needed.

## A real example: bulk XOR string decryption

Suppose you've reversed a binary that encrypts all its strings with a one-byte XOR key `0x5A`, and the encrypted strings sit in a data section. Doing three hundred strings by hand would make you quit. A script takes thirty seconds:

```python
import idautils, idc, ida_bytes

KEY = 0x5A

def xor_decrypt(data, key):
    return bytes(b ^ key for b in data)

# suppose each encrypted string is referenced through a call decrypt_string(ptr, len)
# we find every xref to decrypt_string and then read the arguments
decrypt_ea = idc.get_name_ea_simple("decrypt_string")

for xref in idautils.XrefsTo(decrypt_ea):
    call_ea = xref.frm
    # (depends on the binary) trace back up to get the pointer and length passed in
    # for illustration here: assume ptr and length are already known
    ptr = idc.get_operand_value(idc.prev_head(call_ea), 1)
    length = 16
    enc = ida_bytes.get_bytes(ptr, length)
    if enc:
        dec = xor_decrypt(enc, KEY).split(b"\x00")[0].decode("latin1")
        # put the comment right at the call site, so the pseudocode shows it directly
        idc.set_cmt(call_ea, f"str: {dec}", 1)
        print(hex(call_ea), dec)
```

The nice part isn't the specific code (every binary is different), it's the mold of thinking: **find an anchor (the decrypt function, a constant, a byte pattern), walk every location, apply the transformation, write the result back as a comment or a name.** After running it, open the pseudocode again and every call has its real string annotated, and you read it like source code.

## Finding byte patterns

Often you need to find a byte sequence (for example the prologue of a type of function, or a crypto constant):

```python
import ida_search, ida_bytes

# find the byte string "48 8B 05" starting from the start of the program
ea = ida_bytes.find_bytes("48 8B 05", idc.get_inf_attr(idc.INF_MIN_EA))
while ea != idc.BADADDR:
    print(hex(ea))
    ea = ida_bytes.find_bytes("48 8B 05", ea + 1)
```

## Ghidra scripting

Ghidra lets you write scripts in Java or Python (Jython). The central API is `FlatProgramAPI` (the functions `getFunctionManager`, `getInstructionAt`, `setComment`, `createLabel`). A Python example in Ghidra:

```python
# Ghidra Python (Jython)
fm = currentProgram.getFunctionManager()
for func in fm.getFunctions(True):
    print(func.getName(), func.getEntryPoint())
```

What makes Ghidra strong for automation is the **headless analyzer**: run the analysis and scripts from the command line, without opening the GUI, good for processing binaries in bulk:

```
analyzeHeadless /path/to/project MyProject -import target.exe -postScript MyScript.py
```

Use headless when you have a hundred malware samples and need to extract the same thing from each (for example config, IOCs). Write one script, run it as a batch, done.

## Binary Ninja API

Binary Ninja has a Python API praised as the cleanest, and it can access the IL layers (BNIL: LLIL, MLIL, HLIL). Example:

```python
# Binary Ninja
import binaryninja as bn
with bn.load("target.exe") as bv:
    for func in bv.functions:
        print(func.name, hex(func.start))
```

Working on the IL instead of raw assembly lets you write architecture-independent analyses (the same script runs for both x86 and ARM), very good for automatic deobfuscation.

## Which one to choose

There's no single answer. In practice: if you live in IDA, use IDAPython; if you need free and batch, Ghidra headless; if you need nice architecture-independent analysis on IL, Binary Ninja. The three don't exclude each other, and many people use all three depending on the job.

## Lab

The task is to practice writing a script that makes the decompiler decrypt a batch of encrypted strings automatically instead of by hand. Three files go with it. `strcrypt_demo.c` is a sample program with 3 strings XORed with a single byte (key `0x5A`) and decrypted at run time, which you build into a real binary to dissect. `decrypt_strings_ida.py` is a sample IDAPython script that decrypts the XOR and sets a comment at each call, and `decrypt_strings_ghidra.py` is the sample Ghidra (Jython) script. Build and run the program:

```
gcc -O0 -o strcrypt_demo strcrypt_demo.c
./strcrypt_demo        # prints the 3 decrypted strings
```

Open `strcrypt_demo` in IDA or Ghidra and find the `decrypt` function and the arrays `enc_1`, `enc_2` and `enc_3`. Work out the XOR key and the structure of the encrypted strings, in particular which byte terminates them. Then write (or adapt from the samples) a script that decrypts every string and puts the result as a comment right next to where it is used, and reopen the pseudocode to check that the string comments appear. For a harder variant, change the key to a multi-byte one and generalize the script.

One hint is that every real binary differs in how it passes the pointer into the decryption function, so the part of the sample script that fetches `ptr` needs adjusting to your binary. The way of thinking stays the same: find an anchor, walk the locations, apply the transform, write the comment. Try it yourself before opening the solution.

<div class="lab-box">
<div class="lab-head"><b>LAB 18.1</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/18.1/src/decrypt_strings_ghidra.py" download><i class="fa-solid fa-file-code"></i>src/decrypt_strings_ghidra.py</a>
<a class="lab-file" href="/assets/labs/18.1/src/decrypt_strings_ida.py" download><i class="fa-solid fa-file-code"></i>src/decrypt_strings_ida.py</a>
<a class="lab-file" href="/assets/labs/18.1/src/strcrypt_demo.c" download><i class="fa-solid fa-file-code"></i>src/strcrypt_demo.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

### Observing the binary

`strcrypt_demo` contains a function `decrypt(enc, out)` with a loop that XORs each byte with `0x5A` and stops when it meets the byte `0x5A` (because the original terminating byte `0x00` becomes `0x5A` after XOR with 0x5A). The three arrays `enc_1`, `enc_2` and `enc_3` are the encrypted strings. The key is `0x5A`, and the terminator in encrypted form is `0x5A`.

### Quick decryption in Python (no IDA needed)

```python
KEY = 0x5A
def dec(e):
    out = ""
    for b in e:
        if b == KEY: break
        out += chr(b ^ KEY)
    return out
```

### Real result (built and run)

Running `./strcrypt_demo` prints:

```
Hello, reverser!
secret_flag_42
api: VirtualAlloc
```

These three strings are also exactly what you get by applying XOR 0x5A to the three `enc_*` arrays. The string-decryption scripts (IDAPython and Ghidra) reproduce them and then set a comment at each `decrypt` call, so when you reopen the pseudocode you see the real strings immediately without chasing them by hand.

The string `api: VirtualAlloc` is a typical example of malware hiding API names with XOR to avoid being caught through Imports or strings, and a string-decryption script is a fast way to expose it. The general template repeats in every binary: determine the key and the terminator, walk every string or call location, apply the XOR, and write the comment. With a multi-byte key, you only need to change `b ^ KEY` to `b ^ KEY[i % len(KEY)]`.

The C part (`strcrypt_demo.c`) builds with gcc and gives exactly the three strings above. The IDAPython and Ghidra scripts are reference samples meant to be run in the matching tool, so run them there. The XOR decryption logic gives the correct result when checked independently in Python.

</details>

## Key takeaways

Script when an operation repeats more than a dozen times or applies to many locations, and otherwise do it by hand. In IDAPython, five operations are enough: walk functions, read bytes, set comment, rename, get xrefs. The automatic deobfuscation mold is to find an anchor, walk every location, apply the transformation, and write the result back.

Ghidra headless processes binaries in bulk without opening the GUI, and the Binary Ninja API works on BNIL so scripts are architecture-independent.

---
Previous: [17.7 DBI](/posts/re-17-7-dynamic-binary-instrumentation-letting-binary-tell/) · [Back to index](/technique-reverse/) · Next: 18.2 Emulation (Unicorn, Qiling, Speakeasy)
