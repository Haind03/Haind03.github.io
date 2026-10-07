---
title: "Lesson 7.6: Lab, decompiling sample .pyc files with pycdc"
date: 2026-10-06 08:58:00 +0700
categories: ["Technique Reverse", "Part 07 · Python"]
tags: [reverse-engineering, python]
render_with_liquid: false
---
Time to put the theory of Part 7 to real use. This repo has a `pycdc-master` folder with three sample `.pyc` files, and those three happen to cover exactly the three situations you'll hit in the wild: a broken file, a file with no header, and a file written in a newer Python version than pycdc supports. Each file teaches a different lesson, so don't skip any.

All the output in this lesson is the result of real runs on my machine, not made-up illustrations. If you rerun it you'll get exactly the same.

## Setup: build pycdc

The prebuilt binary in the repo may not run on your machine (a GLIBC version mismatch, exactly the problem I hit while writing this lesson). Rebuild from source to be safe:

```bash
cd pycdc-master/pycdc-master
cmake . -DCMAKE_BUILD_TYPE=Release
make -j4
```

When done you have two binaries: `pycdc` (decompiles to Python source) and `pycdas` (disassembles to readable bytecode). Remember the principle from [Lesson 7.2](/posts/tr-7-2-pycdc-pycdas/): pycdc gives nice source when it succeeds, pycdas always runs and is the lifeline when pycdc is helpless.

## File 1: ok.pyc, the lesson of the empty file

Try running it:

```
$ ./pycdc ok.pyc
Bad MAGIC!
Could not load file .../ok.pyc
```

Before blaming the tool, check the file. `ls -l` shows `ok.pyc` weighs exactly 0 bytes. It's empty. There's nothing to decompile.

Sounds silly but this is a real error you'll hit: a half-finished download, a broken extraction, or an accidental overwrite. "Bad MAGIC!" doesn't always mean the wrong version, sometimes the file just doesn't even have 4 magic bytes to read. A cheap lesson but it saves you an hour of wrongly suspecting pycdc.

## File 2: apple_collector_game.pyc, a file with no header

```
$ ./pycdc apple_collector_game.pyc
Bad MAGIC!
```

"Bad MAGIC!" again. But this file weighs 11KB, it's not empty. Look at the first bytes:

```
$ xxd apple_collector_game.pyc | head -1
00000000: e300 0000 0000 0000 0000 0000 0005 0000
```

A standard `.pyc` file must start with 4 magic bytes (see [Lesson 7.1](/posts/tr-7-1-bytecode-python-pyc-magic/)). This one starts with `e3`. The byte `0xe3` is the marshal code for a code object (`TYPE_CODE` = `0x63` = `'c'`, plus the ref flag `0x80`). In other words, this isn't a complete `.pyc`, it's a **bare marshaled code object**, with the 16-byte header stripped off.

This is very common when you extract `.pyc` files from PyInstaller: many versions cut the header off. pycdc has flags for exactly this case: `-c` (load a bare code object) plus `-v` (specify the Python version, since there's no magic left to guess from).

The problem: which version? When there's no magic, the fastest way is to try. Run pycdas with a few versions until it loads:

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

3.10 and below blow up, 3.11 loads cleanly and even reveals the original file name `apple_collector_game.py`. So it's Python 3.11. Now decompile:

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

Reading it you understand right away: this is a pygame game "Apple Collector", and it's a CTF challenge. The `R0` function checks `sys._MEIPASS`, a sure sign the program was packaged with **PyInstaller** (see [Lesson 7.4](/posts/tr-7-4-unpack-pyinstaller-py2exe/)). The flag is in the environment variable `CTF_FLAG`, loaded from the accompanying `flag.env` file. So for this challenge, "solving" isn't reading code but finding the `flag.env` file in the PyInstaller bundle.

Notice pycdc prints a few lines of `Unsupported opcode: BEFORE_WITH` and `JUMP_BACKWARD`, and some functions end with `# WARNING: Decompyle incomplete`. This is a real limit of pycdc on Python 3.11: it stumbles on `with` blocks and some loop forms. But the part it decompiled is more than enough to understand the program. Wherever it's incomplete, open pycdas and read the bytecode of just that function.

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

Almost a total failure. Python 3.13 is too new for pycdc, the opcode `LOAD_FROM_DICT_OR_GLOBALS` isn't supported yet, and the result is junk. This is exactly the situation [Lesson 7.3](/posts/tr-7-3-decompiler-python-khac/) warns about: no decompiler keeps up with every version.

But don't give up. Switch to pycdas to read the bytecode, it always runs:

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

Even though the bytecode disassembly for 3.13 is a bit off too (pycdc hasn't mapped all the 3.13 opcodes correctly), the `[Names]` and `[Constants]` parts are still readable, and they tell the whole story. Looking at the name list you can rebuild the logic: take `encoded_catalyst_strand` (the base85 blob), `base64.b85decode`, then `zlib.decompress`, then `marshal.loads` into a code object, then `types.FunctionType` to turn it into a function and run it. This is a **self-decoding loader**: it hides the real payload under three layers of encoding.

## When the tool is helpless, do it by hand

pycdc can't read 3.13, but Python itself can read its marshal (with a bit of flexibility). We peel off each layer ourselves, exactly like the loader does. Write a script (run it with `python3 -I` to be safe, see the note at the start of the course about the folder holding unfamiliar files):

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

Now it's clear: this is the "Project Chimera" challenge. The real payload encrypts a "secret formula" with RC4, with the key generated from `os.getlogin()` (the username, playing the role of the "biometric scan"). pycdc never revealed a single line, but by peeling off the three layers of base85, zlib, marshal ourselves, we recovered the whole structure and even the algorithm. This is exactly the spirit of [Lesson 0.4](/posts/tr-0-4-quy-trinh-reverse/): the tool is only leverage, understanding the mechanism is what saves you when the tool breaks.

## Three files, three lessons

- **ok.pyc**: check the file before suspecting the tool. "Bad MAGIC!" on a 0-byte file means the file is empty.
- **apple_collector_game.pyc**: a bare code object (first byte `e3`, no magic). Use `pycdc -c -v <ver>`, find the version by trying. It turns out to be a PyInstaller game hiding the flag in `flag.env`.
- **out_sequencer.pyc**: Python 3.13 is too new, pycdc fails. pycdas can still read names/consts, and peeling off the base85 + zlib + marshal layers yourself recovers the RC4 payload inside.

## Key takeaways
- Build pycdc from source if the prebuilt binary doesn't run (GLIBC/GLIBCXX mismatch).
- "Bad MAGIC!" has three common causes: an empty/broken file, a bare code object with no header, or an unfamiliar version.
- A first byte of `e3` (or `63`) means a bare code object, use `-c -v`, find the version with pycdas.
- When pycdc fails, pycdas can almost always still read the names and consts, enough to rebuild the logic.
- Python loaders often hide payloads via base64/base85 + zlib + marshal. Peel in that order and it comes out.
- When every tool breaks, use Python's own `marshal` to peel off the layers by hand.
