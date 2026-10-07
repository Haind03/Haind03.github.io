---
title: "Lesson 7.2: pycdc and pycdas, two scalpels for .pyc files"
date: 2026-10-06 08:54:00 +0700
categories: ["Technique Reverse", "Part 07 · Python"]
tags: [reverse-engineering, python]
render_with_liquid: false
---
In the last lesson you learned what a `.pyc` file is and how to read its magic number. Now it's time to open it up. The main toolset is Decompyle++ (the repo is called `pycdc`), made of two programs: `pycdc` tries to rebuild the Python source, and `pycdas` dumps the bytecode in a human-readable form. Both are already in this repo at `pycdc-master/pycdc-master`, along with a few sample `.pyc` files to play with.

What makes this set worth it: it's written in C++ and **doesn't depend on a Python runtime**. Other decompilers like uncompyle6 run on Python itself and can usually only decompile a `.pyc` from the same version line as the interpreter running them. pycdc reads the file structure directly, so on a machine with only Python 3.11 you can still try a `.pyc` from 2.7 or 3.6. In return, it has to implement its own knowledge of each bytecode version, so the newest versions (3.12, 3.13) aren't fully supported. Below you'll see both the strength and the weakness clearly, with real run results.

## Build in five minutes

pycdc uses CMake. On Linux/WSL:

```sh
cd pycdc-master/pycdc-master
cmake . -DCMAKE_BUILD_TYPE=Release
make -j4
```

When done you have two executables, `pycdc` and `pycdas`, right in the folder. This repo includes a prebuilt version, but if it complains about a missing `GLIBC`/`GLIBCXX` (built on another machine with an older glibc), just rebuild as above and that goes away. On Windows use Visual Studio or MinGW, with a similar CMake process.

## pycdc: try to rebuild the source

The simplest syntax:

```sh
./pycdc path_to_file.pyc
```

It prints the rebuilt source straight to stdout. With a clean 3.8 bytecode file from the repo's test suite, the result is nearly perfect:

```
$ ./pycdc tests/compiled/test_calls.3.8.pyc
# Source Generated with Decompyle++
# File: test_calls.3.8.pyc (Python 3.8)

import sys
import os
sys.stdout.write('Test\n')
sys.stdout.write(os.path.join('foo', 'bar'))
print('\n')
print(eval('4 * 13'))
print()
```

It reads like the original source. This is the ideal case: a well-supported version and code that isn't obfuscated.

## When pycdc gives up: the weakness with new Python

The repo comes with a file `out_sequencer.pyc`. Run pycdc:

```
$ ./pycdc out_sequencer.pyc
Unsupported opcode: LOAD_FROM_DICT_OR_GLOBALS
# Source Generated with Decompyle++
# File: out_sequencer.pyc (Python 3.13)

if not None + None:
    pass
# WARNING: Decompyle incomplete
```

This is the most important practical lesson of the whole post. This file is Python 3.13 (magic `f3 0d 0d 0a`), and pycdc hit the opcode `LOAD_FROM_DICT_OR_GLOBALS` which it doesn't understand yet, so it surrendered and printed nonsense (`if not None + None`). Don't trust output like this. When you see the line `Unsupported opcode` or `WARNING: Decompyle incomplete`, it means you can't rely on the source it printed. At that point switch to `pycdas` to read the raw bytecode.

## pycdas: dump the bytecode when decompiling fails

`pycdas` doesn't try to rebuild source, it just lists everything in the file: variable names, constants, strings, and bytecode. When pycdc fails, this is a lifeline because it almost always can read the metadata part.

```
$ ./pycdas out_sequencer.pyc
out_sequencer.pyc (Python 3.13)
[Code]
    File Name: <genetic_sequencer>
    Object Name: <module>
    ...
    [Names]
        'base64'
        'zlib'
        'marshal'
        'types'
        'encoded_catalyst_strand'
        'b85decode'
        'compressed_catalyst'
        'decompress'
        'marshalled_genetic_code'
        'loads'
        'catalyst_code_object'
        'FunctionType'
```

Looking at the `[Names]` list you can guess the whole scenario right away, even without reading a line of logic: this file does `b85decode` on a string, `zlib.decompress`, then `marshal.loads` to rebuild a code object and turn it into a function with `types.FunctionType`. This is the classic self-decoding loader pattern: the outer layer is just a shell, and the real code is compressed and marshaled, hidden in a base85 blob (you also see that blob in the `[Constants]` section of pycdas). To go further, you extract the blob and do `b85decode` + `zlib.decompress` + `marshal.loads` yourself in a Python session to get the code object inside, then bring that back into pycdc. This layer-peeling technique comes up again in the post on unpacking ([7.4](/posts/tr-7-4-unpack-pyinstaller-py2exe/)).

Note: with this 3.13 file, even the `[Disassembly]` section of pycdas shows skewed opcodes (it assigns wrong opcode names because it hasn't mapped the 3.13 table correctly). But the `[Names]` and `[Constants]` sections are still enough to understand the intent. The lesson: a tool can be wrong at one level and right at another, so don't throw away the whole output just because one part is broken.

## Two header traps, through real sample files

The repo has two more files illustrating two common errors:

`ok.pyc` is 0 bytes. Whatever you run gives:

```
$ ./pycdc ok.pyc
Bad MAGIC!
Could not load file ok.pyc
```

An empty or truncated file has no magic to read. Before blaming the tool, check the file size.

`apple_collector_game.pyc` is more interesting. It also reports `Bad MAGIC!` but the file isn't empty at all (nearly 12 KB). Look at the first four bytes:

```
$ xxd -l 4 apple_collector_game.pyc
00000000: e300 0000
```

A valid `.pyc` must start with a magic number (for example `f3 0d 0d 0a` for 3.13). The byte `e3` here is the marshal opcode for a code object. In other words, this file isn't a complete `.pyc` but a **raw marshaled code object**, with the 16-byte header stripped off. pycdc needs the header to know the version, so it refuses. How to handle it: patch the header back on yourself (prepend the correct magic number for the version plus padding), or read it directly with Python's `marshal` module. This is a simple but effective hiding trick, and now you can recognize it from just the first four bytes.

## A suggested working rhythm

1. `pycdas file.pyc` first to learn the version and look at Names/Constants overall, even when you plan to use pycdc.
2. `pycdc file.pyc` to get the source. If it's clean, done.
3. If you see `Unsupported opcode` or `WARNING: Decompyle incomplete`: go back to reading bytecode with pycdas, or try another decompiler ([7.3](/posts/tr-7-3-decompiler-python-khac/)).
4. If you see `Bad MAGIC!`: check for an empty file, or raw marshal with the header missing, or whether it's been encrypted.

## Lab

The folder [labs/7.2/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/7.2) has instructions to build pycdc and run it on exactly the sample files in the repo (`ok.pyc`, `out_sequencer.pyc`, `apple_collector_game.pyc`) so you can see all three outcomes yourself: a clean decompile, a failed decompile because of a new version, and a header error. `solution.md` comes with the real output.

## Key takeaways
- pycdc rebuilds source, pycdas dumps bytecode. Neither needs a Python runtime of the exact version.
- Build with cmake + make in a few minutes if the prebuilt version has library errors.
- `Unsupported opcode` or `WARNING: Decompyle incomplete` means don't trust the source pycdc printed, switch to pycdas.
- pycdc is weak with Python 3.12/3.13, this is a real limitation, you didn't do anything wrong.
- `Bad MAGIC!` has three common causes: an empty/truncated file, raw marshal with the header missing, or an encrypted file.
- Always read the `[Names]` and `[Constants]` of pycdas: often they reveal the whole scenario (a base64/zlib/marshal loader) before you read the logic.
