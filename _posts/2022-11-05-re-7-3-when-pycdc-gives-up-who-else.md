---
title: "Lesson 7.3: When pycdc gives up, who else is there"
image:
  path: /assets/img/covers/re-7-3-when-pycdc-gives-up-who-else.webp
  alt: "Lesson 7.3: When pycdc gives up, who else is there"
date: 2022-11-05 22:22:00 +0700
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

In this lab you see why you need several decompilers at hand, and you practice the last resort, which is reading the bytecode directly with `dis` and `marshal`. You take a `.pyc` file, try several decompilers in turn, watch which one refuses which version, and then read the bytecode yourself to get the answer when the tools give up.

You need Python 3 (the lab was checked on 3.11.9) and, optionally, the extra tools from `pip install uncompyle6 decompyle3 xdis`. The sample program is `secret.py`, and you can also use any other `.pyc` files you have lying around. First create a `.pyc` to experiment on by compiling `secret.py`.

```
python3 -c "import py_compile; py_compile.compile('secret.py', cfile='secret.pyc')"
```

Next determine the version by reading the 4 magic bytes at the start of the file (see [Lesson 7.1](/posts/re-7-1-python-bytecode-pyc-files/)) and write down the Python version. Then try `uncompyle6 secret.pyc`. If the file was produced by Python 3.9 or newer, it will most likely refuse with a line saying `Unsupported Python version`, so read carefully the header it still prints (bytecode version, compile time, source name). After that, try pycdc, which you built in Lesson 7.2, on the same file and compare with the uncompyle6 result.

When the tools give up, read the bytecode manually.

```python
import marshal, dis
with open('secret.pyc','rb') as f:
    f.read(16)
    code = marshal.load(f)
print(code.co_consts)
for c in code.co_consts:
    if hasattr(c,'co_code'):
        dis.dis(c)
```

Look in `co_consts` for suspicious constants, and in the bytecode for `COMPARE_OP` instructions. Then work out the rule that the `check` function enforces using the bytecode alone, without looking at the source. What conditions must a valid password satisfy?

Two questions to think about. Why does uncompyle6 refuse outright rather than try and produce something wrong? And if you only had the bytecode and no decompiler worked, could you still solve the task, and why? Try it yourself before opening the solution.

<div class="lab-box">
<div class="lab-head"><b>LAB 7.3</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/7.3/src/secret.py" download><i class="fa-solid fa-file-code"></i>src/secret.py</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

All the output below is real, produced on Python 3.11.9.

To create the `.pyc` and identify the version:

```
python3 -c "import py_compile; py_compile.compile('secret.py', cfile='secret.pyc')"
xxd secret.pyc | head -1
```

The first 4 magic bytes (for example `a7 0d 0d 0a`) correspond to Python 3.11. The full magic table is in [Lesson 7.1](/posts/re-7-1-python-bytecode-pyc-files/).

Now uncompyle6 refuses.

```
pip install uncompyle6
uncompyle6 secret.pyc
```

The real result is this.

```
# Unsupported bytecode in file secret.pyc
# Unsupported Python version, 3.11, for decompilation
# Can't uncompile secret.pyc
# uncompyle6 version 3.9.3
# Python bytecode version base 3.11 (3495)
# Embedded file name: secret.py
# Compiled at: 2026-10-06 15:44:48
# Size of source mod 2**32: 185 bytes
```

uncompyle6 (the latest version, 3.9.3) does not support 3.11 bytecode, so it refuses outright. But notice the header: it still reports the bytecode version, the source file name `secret.py`, the compile time and the source size. That is free triage even when decompilation fails.

With the same file, pycdc (which is independent of the runtime) has a better chance than uncompyle6 on 3.11, although its 3.11 support is still not perfect. If pycdc also gives an incomplete result, move on to PyLingual or read the bytecode.

When the tools give up, `marshal` plus `dis` never betrays you, using the snippet from the task. The module's `co_consts` immediately reveals the `check` code object. Disassembling `check` gives this (excerpt).

```
  2   LOAD_CONST  1 ('r3v3rs3')   STORE_FAST 1 (key)
  3   LOAD_GLOBAL (len) ... LOAD_CONST 2 (10)  COMPARE_OP 3 (!=)
  4   LOAD_CONST  3 (False)  RETURN_VALUE
  5   LOAD_CONST  4 (0)  STORE_FAST 2 (total)
  6   FOR_ITER ...  (loop)
  7   LOAD_GLOBAL (ord) ... BINARY_OP 13 (+=)  STORE_FAST 2 (total)
  8   LOAD_CONST  5 (1000)  COMPARE_OP 2 (==)
      ... startswith(key[:3]) ...
```

Just looking at `co_consts` gives you three clues: the string `'r3v3rs3'`, the number `10` and the number `1000`. Combined with the `COMPARE_OP` instructions, the rule `check` enforces has three parts. The length must be exactly 10 characters (`COMPARE_OP != 10`, and if it is wrong the function returns False). The sum of the ASCII codes of all characters must equal 1000 (the `FOR_ITER` loop adds `ord(c)`, then `COMPARE_OP == 1000`). And the password must start with `key[:3]`, the first three characters of `'r3v3rs3'`, which is `"r3v"`.

There is no single valid password. Any 10-character string that starts with `r3v` and whose ASCII sum is 1000 passes. One example, verified by actually running it, is below.

```
python3 secret.py r3versekz9
Correct!
python3 secret.py wrongpass1
Nope.
```

`r3versekz9` starts with `r3v`, is 10 characters long and has an ASCII sum of 1000, so it is valid.

The lessons are these. A decompiler refusing does not mean you are stuck, because bytecode can always be read. `co_consts` often contains the answer directly (comparison constants, target strings). And when the task asks for a property (an ASCII sum) rather than a fixed string, there are countless correct answers, just like the keygen in Lesson 3.6.

</details>

## Key takeaways
No decompiler wins on every version, because Python bytecode keeps changing. uncompyle6 is strong on Python 2.x through 3.8 and decompyle3 patches 3.7 through 3.9 further, but both flatly refuse bytecode that's too new (we saw it drop the 3.11 file). pycdc is runtime-independent, and PyLingual (web, ML) fits newer Python.

The last option always works: `marshal` reads the code object and `dis` prints the bytecode, and `co_consts` and `co_names` often expose the answer. Determine the version from the magic number first, then choose the tool.
