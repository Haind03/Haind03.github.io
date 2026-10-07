---
title: "Lesson 7.6: Lab, decompiling sample .pyc files with pycdc"
image:
  path: /assets/img/covers/re-7-6-lab-decompiling-sample-pyc-files-pycdc.webp
  alt: "Lesson 7.6: Lab, decompiling sample .pyc files with pycdc"
date: 2022-11-14 21:48:00 +0700
categories: ["Technique Reverse", "Part 07 · Python"]
tags: [reverse-engineering, python]
render_with_liquid: false
---
Time to use the theory from Part 7. The pycdc project ships with sample `.pyc` files, and three of them (attached in the Lab section below) cover the three situations you'll hit in the wild: a broken file, a file with no header, and a file written for a newer Python version than pycdc supports. Each one teaches something different, so don't skip any.

All the output in this lesson comes from real runs on my machine. If you rerun it you'll get the same.

## Setup: build pycdc

A prebuilt pycdc binary may not run on your machine (for example a GLIBC version mismatch). Rebuild from source to be safe:

```bash
cd pycdc-master/pycdc-master
cmake . -DCMAKE_BUILD_TYPE=Release
make -j4
```

When it's done you have two binaries: `pycdc` (decompiles to Python source) and `pycdas` (disassembles to readable bytecode). Remember the principle from [Lesson 7.2](/posts/re-7-2-pycdc-pycdas-two-scalpels-pyc-files/): pycdc gives nice source when it works, and pycdas always runs, so it's what you use when pycdc can't do it.

## File 1: ok.pyc, the empty file

Try running it:

```
$ ./pycdc ok.pyc
Bad MAGIC!
Could not load file .../ok.pyc
```

Before blaming the tool, check the file. `ls -l` shows `ok.pyc` is exactly 0 bytes. It's empty, so there's nothing to decompile.

Sounds silly, but you'll hit this for real: a half-finished download, a broken extraction, or an accidental overwrite. "Bad MAGIC!" doesn't always mean the wrong version. Sometimes the file doesn't even have 4 magic bytes to read. It's a cheap lesson and saves you an hour of wrongly suspecting pycdc.

## File 2: apple_collector_game.pyc, a file with no header

```
$ ./pycdc apple_collector_game.pyc
Bad MAGIC!
```

"Bad MAGIC!" again, but this file is 11KB, it's not empty. Look at the first bytes:

```
$ xxd apple_collector_game.pyc | head -1
00000000: e300 0000 0000 0000 0000 0000 0005 0000
```

A standard `.pyc` file must start with 4 magic bytes (see [Lesson 7.1](/posts/re-7-1-python-bytecode-pyc-files/)). This one starts with `e3`. The byte `0xe3` is the marshal code for a code object (`TYPE_CODE` = `0x63` = `'c'`, plus the ref flag `0x80`). So this isn't a complete `.pyc`, it's a bare marshaled code object with the 16-byte header stripped off.

This is common when you extract `.pyc` files from PyInstaller, since many versions cut the header off. pycdc has flags for this case: `-c` (load a bare code object) plus `-v` (specify the Python version, since there's no magic left to guess from).

Which version? With no magic, the fastest way is to try. Run pycdas with a few versions until it loads:

```
$ ./pycdas -c -v 3.10 apple_collector_game.pyc
CreateObject: Got unsupported type 0x0
terminate called ... std::bad_cast

$ ./pycdas -c -v 3.11 apple_collector_game.pyc
apple_collector_game.pyc (Python 3.11)
[Code]
    File Name: apple_collector_game.py
    ...
```

3.10 and below blow up, 3.11 loads cleanly and even shows the original file name `apple_collector_game.py`. So it's Python 3.11. Now decompile:

```
$ ./pycdc -c -v 3.11 apple_collector_game.pyc
```

The result comes out almost complete:

```python
import os
import sys
from dotenv import load_dotenv
_BASE = os.path.dirname(os.path.abspath(__file__))

def R0(p):
    return os.path.join(sys._MEIPASS, p) if hasattr(sys, '_MEIPASS') else os.path.join(_BASE, p)

load_dotenv(R0('flag.env'))
...
class G:
    def __init__(self):
        self.s = pygame.display.set_mode(_W)
        pygame.display.set_caption('Apple Collector Game')
        ...
        self.fl = os.getenv('CTF_FLAG')
```

You can read it right away: it's a pygame game, "Apple Collector", and a CTF challenge. The `R0` function checks `sys._MEIPASS`, a sure sign the program was packaged with PyInstaller (see [Lesson 7.4](/posts/re-7-4-when-python-turns-into-exe-open/)). The flag is in the environment variable `CTF_FLAG`, loaded from the accompanying `flag.env` file. So "solving" this challenge isn't about reading code, it's about finding the `flag.env` file in the PyInstaller bundle.

pycdc prints a few lines of `Unsupported opcode: BEFORE_WITH` and `JUMP_BACKWARD`, and some functions end with `# WARNING: Decompyle incomplete`. That's a real limit of pycdc on Python 3.11: it stumbles on `with` blocks and some loop forms. The part it decompiled is still plenty to understand the program. Where it's incomplete, open pycdas and read the bytecode of just that function.

## File 3: out_sequencer.pyc, a version newer than pycdc

This file has a proper header:

```
$ xxd out_sequencer.pyc | head -1
00000000: f30d 0d0a 0000 0000 240e d668 ...
```

The magic `f3 0d 0d 0a`, i.e. `0x0df3` = 3571, is Python 3.13. Try decompiling:

```
$ ./pycdc out_sequencer.pyc
Unsupported opcode: LOAD_FROM_DICT_OR_GLOBALS
# Source Generated with Decompyle++
# File: out_sequencer.pyc (Python 3.13)

if not None + None:
    pass
# WARNING: Decompyle incomplete
```

Almost a total failure. Python 3.13 is too new for pycdc, the opcode `LOAD_FROM_DICT_OR_GLOBALS` isn't supported yet, and the result is junk. This is the situation [Lesson 7.3](/posts/re-7-3-when-pycdc-gives-up-who-else/) warns about: no decompiler keeps up with every version.

Don't give up though. Switch to pycdas to read the bytecode, it always runs:

```
$ ./pycdas out_sequencer.pyc
out_sequencer.pyc (Python 3.13)
[Code]
    File Name: <genetic_sequencer>
    [Names]
        'base64'  'zlib'  'marshal'  'types'
        'encoded_catalyst_strand'  'print'  'b85decode'
        'compressed_catalyst'  'decompress'
        'marshalled_genetic_code'  'loads'
        'catalyst_code_object'  'FunctionType'  'globals'
    [Constants]
        b'c$|e+O>7&-6`m!Rzak~llE|2<...'   (a very long base85 blob)
        '--- Calibrating Genetic Sequencer ---'
        'Decoding catalyst DNA strand...'
```

The bytecode disassembly for 3.13 is a bit off too (pycdc hasn't mapped all the 3.13 opcodes correctly), but the `[Names]` and `[Constants]` parts are still readable, and they tell the story. From the name list you can rebuild the logic: take `encoded_catalyst_strand` (the base85 blob), `base64.b85decode`, then `zlib.decompress`, then `marshal.loads` into a code object, then `types.FunctionType` to turn it into a function and run it. It's a self-decoding loader that hides the real payload under three layers of encoding.

## When the tool can't do it, do it by hand

pycdc can't read 3.13, but Python itself can read its marshal (with a bit of flexibility). So we decode each layer ourselves, the same way the loader does. Write a script (run it with `python3 -I` to be safe, see the note at the start of the course about the folder holding unfamiliar files):

```python
import sys, base64, zlib, marshal
data = open('out_sequencer.pyc','rb').read()
code = marshal.loads(data[16:])          # drop the 16-byte .pyc header then unmarshal the module
blob = [c for c in code.co_consts if isinstance(c, bytes)][0]
inner = marshal.loads(zlib.decompress(base64.b85decode(blob)))
print(inner.co_names)
```

The real result:

```
('os', 'sys', 'emoji', 'random', 'asyncio', 'cowsay', 'pyjokes',
 'art', 'arc4', 'ARC4', 'activate_catalyst', 'run')
```

The inner layer is another code object, importing `arc4.ARC4` (the RC4 algorithm) and with a function `activate_catalyst`. Digging into its constants:

```
fn: activate_catalyst
  bytes: b'm\x1b@I\x1dAoe@\x07ZF[BL\rN\n\x0cS'   (ciphertext)
  bytes: b'r2b-\r\x9e\xf2\x1f...'                 (ciphertext)
  str: '--- Catalyst Serum Injected ---'
  str: "Verifying Lead Researcher's credentials via biometric scan..."
  str: 'AUTHENTICATION   SUCCESS'
  str: 'I am alive! The secret formula is:\n'
  str: 'AUTHENTICATION   FAILED'
```

This is the "Project Chimera" challenge. The real payload encrypts a "secret formula" with RC4, with the key generated from `os.getlogin()` (the username, playing the role of the "biometric scan"). pycdc never showed a single line, but by peeling off the three layers of base85, zlib and marshal ourselves, we recovered the whole structure and even the algorithm. This is the idea from [Lesson 0.4](/posts/re-0-4-reverse-engineering-workflow-not-get-lost/): the tool only helps, and understanding the mechanism is what saves you when the tool breaks.

## Three files, three lessons

The first file, ok.pyc, teaches you to check the file before suspecting the tool, since "Bad MAGIC!" on a 0-byte file means the file is empty. The second, apple_collector_game.pyc, is a bare code object (first byte `e3`, no magic), so you use `pycdc -c -v <ver>` and find the version by trying. It turns out to be a PyInstaller game hiding the flag in `flag.env`. The third, out_sequencer.pyc, is Python 3.13 and too new, so pycdc fails, but pycdas can still read names and consts, and peeling off the base85 + zlib + marshal layers yourself recovers the RC4 payload inside.

## Lab

The lab uses three ready-made `.pyc` files from the pycdc source tree, `ok.pyc`, `apple_collector_game.pyc` and `out_sequencer.pyc`. Each is a different situation, so try them yourself first and only open the solution below if you get stuck. Build pycdc from source first, because a prebuilt binary may not match the GLIBC version on your machine:

```bash
cd pycdc-master/pycdc-master
cmake . -DCMAKE_BUILD_TYPE=Release
make -j4
```

You end up with `pycdc` and `pycdas`.

For `ok.pyc`, run `pycdc` on it, explain the error message, check the file size and decide what that tells you. For `apple_collector_game.pyc`, run `pycdc` directly and ask why you get "Bad MAGIC!" even though the file isn't empty. Look at the first bytes with `xxd ... | head -1` and think about what they say about the file format. Use `pycdas -c -v <ver>` to probe for the right Python version (try 3.8 through 3.12), then decompile with `pycdc -c -v <ver>`. What does the program do, which tool packaged it (look for clues in the code), and where is the flag?

For `out_sequencer.pyc`, look at the first bytes and work out the Python version from the magic. Run `pycdc` and find out why it fails. Run `pycdas` and read the `[Names]` and `[Constants]` sections: what does this program do with the base85 blob in the constants? The harder challenge is to decode the encoding layers yourself with a short Python script. As a hint, drop the 16 byte header, call `marshal.loads`, take the bytes constant, then `base64.b85decode`, `zlib.decompress` and `marshal.loads` once more. Which crypto algorithm does the inner payload use?

A few questions to think about afterwards. Why doesn't "Bad MAGIC!" always mean a wrong version? When pycdc doesn't support the file's Python version, what other ways do you have to get information? And why would a loader hide its payload behind several layers of base85, zlib and marshal instead of leaving the code in the open?

A safety note. These files are harmless to read and disassemble, but the third one contains a payload that decodes itself and then runs, so analyze it statically only (decode by hand) and never `exec` it. If you want to run it, do it in a VM following [Lesson 0.3](/posts/re-0-3-set-up-safe-lab-before-touching/). When you write the layer-peeling script, run it with `python3 -I` and keep the unknown files in a folder of their own.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

All the output below comes from real runs on my machine while writing the lesson (pycdc built from source, Python 3.11 as the host for the layer-peeling script). If you rerun it you'll get something similar.

For `ok.pyc`:

```
$ ./pycdc ok.pyc
Bad MAGIC!
Could not load file .../ok.pyc

$ ls -l ok.pyc
-rwxrwxrwx 1 ... 0 ... ok.pyc
```

The file is 0 bytes. There is no magic and nothing to read, so "Bad MAGIC!" here just means the file is empty. Always check that the file exists and isn't empty before suspecting the tool or the version.

For `apple_collector_game.pyc`, the first bytes are:

```
$ xxd apple_collector_game.pyc | head -1
00000000: e300 0000 0000 0000 0000 0000 0005 0000
```

It starts with `e3`, not a 4 byte magic. `0xe3` is `TYPE_CODE` (`0x63`) plus the ref flag (`0x80`), so this is a marshaled code object with the `.pyc` header stripped. That's why you need `-c` and `-v`. Probing the version with pycdas:

```
$ ./pycdas -c -v 3.10 apple_collector_game.pyc
CreateObject: Got unsupported type 0x0
terminate called ... std::bad_cast        # wrong version

$ ./pycdas -c -v 3.11 apple_collector_game.pyc
apple_collector_game.pyc (Python 3.11)
[Code]
    File Name: apple_collector_game.py    # loads cleanly, reveals the original file name
```

The right version is 3.11. Then decompile:

```
$ ./pycdc -c -v 3.11 apple_collector_game.pyc
```

An excerpt of the real result:

```python
import os, sys
from dotenv import load_dotenv
_BASE = os.path.dirname(os.path.abspath(__file__))

def R0(p):
    return os.path.join(sys._MEIPASS, p) if hasattr(sys, '_MEIPASS') else os.path.join(_BASE, p)

load_dotenv(R0('flag.env'))
...
class G:
    def __init__(self):
        self.s = pygame.display.set_mode(_W)
        pygame.display.set_caption('Apple Collector Game')
        ...
        self.fl = os.getenv('CTF_FLAG')
```

This is a pygame game, "Apple Collector", from a CTF challenge, and `hasattr(sys, '_MEIPASS')` is a sure sign of PyInstaller, so this `.pyc` was extracted from a PyInstaller bundle. The flag sits in the environment variable `CTF_FLAG`, loaded from `flag.env`. "Solving" this challenge means finding `flag.env` in the original PyInstaller bundle, not reading the game logic. pycdc prints a few `Unsupported opcode: BEFORE_WITH` and `JUMP_BACKWARD` messages and some functions end with `# WARNING: Decompyle incomplete`. That's a real limit of pycdc on 3.11 (`with` blocks, some loop shapes). The part that does decompile is still enough to understand the program, and for an incomplete function you read its bytecode with pycdas.

For `out_sequencer.pyc`:

```
$ xxd out_sequencer.pyc | head -1
00000000: f30d 0d0a 0000 0000 240e d668 ...
```

The magic `f3 0d 0d 0a` is `0x0df3` = 3571 = Python 3.13.

```
$ ./pycdc out_sequencer.pyc
Unsupported opcode: LOAD_FROM_DICT_OR_GLOBALS
...
if not None + None:
    pass
# WARNING: Decompyle incomplete
```

pycdc fails because 3.13 is too new. Switch to pycdas and read the names and constants:

```
[Names]  base64, zlib, marshal, types, encoded_catalyst_strand,
         b85decode, compressed_catalyst, decompress,
         marshalled_genetic_code, loads, catalyst_code_object,
         FunctionType, globals
[Constants]  b'c$|e+O>7&-...'  (a long base85 blob),
             '--- Calibrating Genetic Sequencer ---', ...
```

The names give away the loader logic: `base64.b85decode(blob)`, then `zlib.decompress`, then `marshal.loads` into a code object, then `types.FunctionType` to run it. It's a loader that decodes itself through three layers. To decode it by hand (run with `python3 -I`):

```python
import base64, zlib, marshal
data = open('out_sequencer.pyc','rb').read()
code = marshal.loads(data[16:])                       # drop the 16 byte header
blob = [c for c in code.co_consts if isinstance(c, bytes)][0]
inner = marshal.loads(zlib.decompress(base64.b85decode(blob)))
print(inner.co_names)
```

The real result:

```
('os', 'sys', 'emoji', 'random', 'asyncio', 'cowsay', 'pyjokes',
 'art', 'arc4', 'ARC4', 'activate_catalyst', 'run')
```

Digging into the constants of the function `activate_catalyst`:

```
bytes: b'm\x1b@I\x1dAoe@\x07ZF[BL\rN\n\x0cS'   (ciphertext)
bytes: b'r2b-\r\x9e\xf2\x1f...'                 (ciphertext)
str: "Verifying Lead Researcher's credentials via biometric scan..."
str: 'AUTHENTICATION   SUCCESS'
str: 'I am alive! The secret formula is:\n'
str: 'AUTHENTICATION   FAILED'
```

This is the "Project Chimera" challenge. The real payload encrypts the "secret formula" with RC4 (`arc4.ARC4`), with a key derived from `os.getlogin()` (the user name playing the role of a "biometric scan"). pycdc couldn't show a single line, yet peeling base85, zlib and marshal by hand recovers the whole structure and the algorithm. Getting the real flag needs the exact username the author used as the key, which is the puzzle part of the challenge. The goal of this lab is to recover the logic, and we did that even though the main tool failed.

The three files gave three different causes of "Bad MAGIC!" or a failed decompile: an empty file, a stripped header and a version that is too new. `-c -v` rescues a bare code object file, and you find the version by trying it with pycdas. pycdas can almost always still read names and constants even when pycdc breaks. And when the tools can't keep up with the version, Python's own `marshal` plus an understanding of the encoding flow lets you decode the payload by hand.

</details>

## Key takeaways
Build pycdc from source if the prebuilt binary doesn't run (GLIBC/GLIBCXX mismatch). "Bad MAGIC!" has three common causes: an empty or broken file, a bare code object with no header, or an unfamiliar version. A first byte of `e3` (or `63`) means a bare code object, so use `-c -v` and find the version with pycdas. When pycdc fails, pycdas can almost always still read the names and consts, enough to rebuild the logic. Python loaders often hide payloads via base64/base85 + zlib + marshal, and decoding in that order recovers it. When every tool breaks, use Python's own `marshal` to decode the layers by hand.
