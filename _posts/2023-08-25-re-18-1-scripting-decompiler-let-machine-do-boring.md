---
title: "Lesson 18.1: Scripting the decompiler, let the machine do the boring work"
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

See `labs/18.1/`. The task: write a script that automatically decrypts strings for a binary whose strings are XORed, and put the result as a comment at each location. The `src/` folder has sample IDAPython and Ghidra scripts for you to reference and adapt to your own binary.

## Key takeaways

Script when an operation repeats more than a dozen times or applies to many locations, and otherwise do it by hand. In IDAPython, five operations are enough: walk functions, read bytes, set comment, rename, get xrefs. The automatic deobfuscation mold is to find an anchor, walk every location, apply the transformation, and write the result back.

Ghidra headless processes binaries in bulk without opening the GUI, and the Binary Ninja API works on BNIL so scripts are architecture-independent.

---
Previous: [17.7 DBI](/posts/re-17-7-dynamic-binary-instrumentation-letting-binary-tell/) · [Back to index](/technique-reverse/) · Next: 18.2 Emulation (Unicorn, Qiling, Speakeasy)
