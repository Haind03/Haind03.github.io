---
title: "Lesson 7.3: When pycdc gives up, who else is there"
date: 2023-10-20 21:11:00 +0700
categories: ["Technique Reverse", "Part 07 · Python"]
tags: [reverse-engineering, python]
render_with_liquid: false
---
In the last lesson you got used to pycdc. But one day pycdc will return a mess, or leave a whole function blank with a note like "unsupported opcode". It's not your fault. Python bytecode changes almost every version, and no decompiler keeps up with all of them. The craft is knowing how many knives you have in hand and which one fits which cut.

This lesson goes over the remaining decompilers, and more importantly: how to pick the right knife based on the Python version, plus the last option that never betrays you, reading the bytecode directly.

## Why no decompiler wins outright

The root is that CPython keeps changing the opcode set. Python 3.10 added pattern matching, 3.11 redid the whole function calling mechanism (`PRECALL`, `CALL`, `LOAD_METHOD` changed behavior), 3.12 kept cleaning up. Each time, a decompiler has to have its handling of the new opcodes rewritten.

The decompilers split into two schools. The runtime-dependent ones (uncompyle6, decompyle3) understand bytecode through the Python that's actually running, so they only work well with the versions the author supported, and they're strong on Python 2 and older 3.x. The runtime-independent one (pycdc) parses the bytecode itself in C++ and can run on a .pyc of a different version than the Python on your machine. It's more flexible but support for 3.9+ still has holes.

In practice: try a few tools on the same file and take whichever gives the best result. Don't be loyal to one tool.

## uncompyle6 and decompyle3

This is the classic decompiler pair for older Python. uncompyle6 has the widest historical coverage, from Python 1.x and 2.x up to around 3.8. If you meet a `.pyc` from Python 2.7 (still plenty in malware and old software), this is almost the number one choice. decompyle3 comes from the same author line and focuses on better patching for 3.7, 3.8 and part of 3.9.

Install with pip and run directly:

```
pip install uncompyle6
uncompyle6 target.pyc > target.py
```

But this is when you have to stay alert. Try running uncompyle6 (latest version 3.9.3) on a `.pyc` compiled with Python 3.11, and the result is:

```
# Unsupported bytecode in file secret.pyc
# Unsupported Python version, 3.11, for decompilation
# Can't uncompile secret.pyc
```

It doesn't even try. This is a living illustration of the principle above: uncompyle6 wasn't written to understand 3.11 bytecode, so it flatly refuses. When you see this line, don't panic, you just picked the wrong knife for the cut. For that 3.11 file, pycdc or PyLingual is where you should go.

The plus is that uncompyle6 still prints the useful header before giving up: the bytecode version, compile time, original source file name, size. Free triage info.

## PyLingual, the new player for newer Python

When your file is Python 3.9, 3.10, 3.11, 3.12 and pycdc gives a broken result, PyLingual (pylingual.io) is often the savior. It's a decompiler that runs on the web, using a machine learning approach (a model learned from pairs of bytecode and source) instead of hard rules, so it catches up with new versions faster.

You go to the site, upload the `.pyc` file, and get back Python source. Since it runs on the web, don't upload sensitive files or malware samples with private data, because you're sending it to an outside service (see [Lesson 0.2](/posts/re-0-2-legal-ethics-part-everyone-wants-skip/) again about sending data outside). For crackmes and CTFs, no worries.

## xdis, the Swiss army knife for inspecting

When you only need to know which Python version a file belongs to, or want to read bytecode without the right runtime, xdis (the foundation of uncompyle6) is very handy:

```
pip install xdis
pydisasm target.pyc
```

`pydisasm` can disassemble bytecode of far more versions than the `dis` module of the Python you're running, so it's a good way to read the bytecode of a 3.8 file when your machine runs 3.11.

## The option that never betrays you: dis and marshal

When every decompiler surrenders, you still have one road: read the bytecode directly. Bytecode is always readable, just more work. And if your machine has the exact Python version that created the file, the standard `dis` module does this perfectly.

Open a `.pyc` with `marshal` and then `dis` (skip the header first):

```python
import marshal, dis
with open('target.pyc', 'rb') as f:
    f.read(16)                 # skip the 16-byte header (Python 3.7+)
    code = marshal.load(f)     # get the module's code object
dis.dis(code)                  # print the bytecode
```

With a check function like this:

```python
def check(pw):
    key = "r3v3rs3"
    if len(pw) != 10:
        return False
    total = 0
    for c in pw:
        total += ord(c)
    return total == 1000 and pw.startswith(key[:3])
```

`dis` (on Python 3.11) gives the real bytecode, excerpting the core:

```
  2   LOAD_CONST    1 ('r3v3rs3')
      STORE_FAST    1 (key)
  3   LOAD_GLOBAL   1 (NULL + len)
      LOAD_FAST     0 (pw)
      CALL          1
      LOAD_CONST    2 (10)
      COMPARE_OP    3 (!=)
      POP_JUMP_FORWARD_IF_FALSE  (to 48)
  4   LOAD_CONST    3 (False)
      RETURN_VALUE
  5   LOAD_CONST    4 (0)
      STORE_FAST    2 (total)
  6   LOAD_FAST     0 (pw)
      GET_ITER
      FOR_ITER      (to 98)
  ...
  8   LOAD_FAST     2 (total)
      LOAD_CONST    5 (1000)
      COMPARE_OP    2 (==)
```

Reading it isn't as hard as you'd think. `co_consts` immediately exposes the two important constants: the string `'r3v3rs3'` and the number `1000`. `COMPARE_OP 3 (!=)` compares the length with `10`, `FOR_ITER` is the accumulating loop, `COMPARE_OP 2 (==)` compares the total with `1000`. Just by looking at `co_consts` and a few `COMPARE_OP` instructions, you've worked out the checking rule without any decompiler. This is why Python bytecode is considered the easiest appetizer in the trade.

One more tip: print `code.co_consts` and `code.co_names` before dis. Constants and function/variable names often reveal the answer faster than reading all the bytecode.

## Decompiler choice table by version

First determine the version from the magic number ([Lesson 7.1](/posts/re-7-1-python-bytecode-pyc-files/)), then look up the table:

| .pyc version | Try first | If it fails |
|---|---|---|
| Python 2.x | uncompyle6 | read bytecode (xdis) |
| Python 3.0 to 3.8 | uncompyle6 / decompyle3 | pycdc |
| Python 3.9 | decompyle3 / pycdc | PyLingual |
| Python 3.10 to 3.12 | pycdc / PyLingual | manual dis/marshal |
| Very new (3.13+) | PyLingual | pydisasm / dis |

This table will go stale, since new tools keep coming out. The principle doesn't change: know the version, try a few tools, read the bytecode when stuck.

## Lab

See [labs/7.3/](https://github.com/Haind03/Technique-Reverse/blob/main/labs/7.3). You'll take a `.pyc` file, try several decompilers in turn, see with your own eyes which one refuses which version, then read the bytecode yourself with `dis`/`marshal` to get the answer when tools give up.

## Key takeaways
No decompiler wins on every version, because Python bytecode keeps changing. uncompyle6 is strong on Python 2.x through 3.8 and decompyle3 patches 3.7 through 3.9 further, but both flatly refuse bytecode that's too new (we saw it drop the 3.11 file). pycdc is runtime-independent, and PyLingual (web, ML) fits newer Python.

The last option always works: `marshal` reads the code object and `dis` prints the bytecode, and `co_consts` and `co_names` often expose the answer. Determine the version from the magic number first, then choose the tool.
