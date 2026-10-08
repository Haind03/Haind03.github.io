---
title: "Lesson 7.2: pycdc and pycdas"
image:
  path: /assets/img/covers/re-7-2-pycdc-pycdas-two-scalpels-pyc-files.webp
  alt: "Lesson 7.2: pycdc and pycdas"
date: 2022-11-04 23:28:00 +0700
categories: ["Reverse Engineering", "Part 07 · Python"]
tags: [reverse-engineering, python]
render_with_liquid: false
---
In the last lesson you learned what a `.pyc` file is and how to read its magic number. Now we open it up. The main toolset is Decompyle++ (the repo is called `pycdc`), made of two programs, where `pycdc` tries to rebuild the Python source, and `pycdas` dumps the bytecode in a readable form.

It's written in C++ and doesn't depend on a Python runtime. Other decompilers like uncompyle6 run on Python itself and can usually only decompile a `.pyc` from the same version line as the interpreter running them. pycdc reads the file structure directly, so on a machine with only Python 3.11 you can still try a `.pyc` from 2.7 or 3.6. The downside is that it has to implement its own knowledge of each bytecode version, so the newest versions (3.12, 3.13) aren't fully supported. Below are real run results showing both sides.

## Build in five minutes

pycdc uses CMake. On Linux/WSL:

```sh
cd pycdc-master/pycdc-master
cmake . -DCMAKE_BUILD_TYPE=Release
make -j4
```

When it's done you have two executables, `pycdc` and `pycdas`, right in the folder. A prebuilt version may exist for your platform, but if it complains about a missing `GLIBC`/`GLIBCXX` (built on another machine with an older glibc), rebuild as above and that goes away. On Windows use Visual Studio or MinGW, with a similar CMake process.

## pycdc: rebuild the source

The simplest syntax:

```sh
./pycdc path_to_file.pyc
```

It prints the rebuilt source straight to stdout. With a clean 3.8 bytecode file from the pycdc test suite, the result is nearly perfect:

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

It reads like the original source. That's the ideal case, a well-supported version and code that isn't obfuscated.

## When pycdc gives up

The pycdc test suite has a file `out_sequencer.pyc`. Run pycdc:

```
$ ./pycdc out_sequencer.pyc
Unsupported opcode: LOAD_FROM_DICT_OR_GLOBALS
# Source Generated with Decompyle++
# File: out_sequencer.pyc (Python 3.13)

if not None + None:
    pass
# WARNING: Decompyle incomplete
```

This file is Python 3.13 (magic `f3 0d 0d 0a`), and pycdc hit the opcode `LOAD_FROM_DICT_OR_GLOBALS` which it doesn't understand yet, so it gave up and printed nonsense (`if not None + None`). Don't trust output like this. When you see `Unsupported opcode` or `WARNING: Decompyle incomplete`, you can't rely on the source it printed. Switch to `pycdas` and read the raw bytecode.

## pycdas: dump the bytecode when decompiling fails

`pycdas` doesn't try to rebuild source, it just lists everything in the file, including variable names, constants, strings, and bytecode. When pycdc fails, it's a lifeline because it can almost always read the metadata part.

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

From the `[Names]` list you can guess the whole scenario without reading any logic. The file does `b85decode` on a string, `zlib.decompress`, then `marshal.loads` to rebuild a code object and turn it into a function with `types.FunctionType`. This is a classic self-decoding loader. The outer layer is just a shell, and the real code is compressed and marshaled in a base85 blob (you also see that blob in the `[Constants]` section of pycdas). To go further, extract the blob and do `b85decode` + `zlib.decompress` + `marshal.loads` yourself in a Python session to get the code object inside, then bring that back into pycdc. The same unwrapping comes up again in the post on unpacking ([7.4](/posts/re-7-4-when-python-turns-into-exe-open/)).

With this 3.13 file, even the `[Disassembly]` section of pycdas shows skewed opcodes (it assigns wrong opcode names because it hasn't mapped the 3.13 table correctly). But `[Names]` and `[Constants]` are still enough to understand the intent. A tool can be wrong at one level and right at another, so don't throw away the whole output because one part is broken.

## Two header traps

The pycdc project has two more files showing two common errors. `ok.pyc` is 0 bytes, and whatever you run gives:

```
$ ./pycdc ok.pyc
Bad MAGIC!
Could not load file ok.pyc
```

An empty or truncated file has no magic to read. Check the file size before blaming the tool.

`apple_collector_game.pyc` is more interesting. It also reports `Bad MAGIC!` but the file isn't empty at all (nearly 12 KB). Look at the first four bytes:

```
$ xxd -l 4 apple_collector_game.pyc
00000000: e300 0000
```

A valid `.pyc` must start with a magic number (for example `f3 0d 0d 0a` for 3.13). The byte `e3` here is the marshal opcode for a code object. So this file isn't a complete `.pyc` but a raw marshaled code object, with the 16-byte header stripped off. pycdc needs the header to know the version, so it refuses. To handle it, patch the header back on yourself (prepend the correct magic number for the version plus padding), or read it directly with Python's `marshal` module. It's a simple hiding trick, and now you can recognize it from the first four bytes.

## My usual rhythm

I run `pycdas file.pyc` first to learn the version and look at Names/Constants, even when I plan to use pycdc. Then I run `pycdc file.pyc` to get the source, and if it's clean, I'm done. If I see `Unsupported opcode` or `WARNING: Decompyle incomplete`, I go back to reading bytecode with pycdas, or try another decompiler ([7.3](/posts/re-7-3-when-pycdc-gives-up-who-else/)). If I see `Bad MAGIC!`, I check whether the file is empty, raw marshal with the header missing, or encrypted.

## Lab

The task is to build Decompyle++ yourself and run it on the sample `.pyc` files `ok.pyc`, `out_sequencer.pyc` and `apple_collector_game.pyc`, so you see all three common outcomes, a clean decompile, a failed decompile because of a new Python version, and a header error. You need `cmake`, `make` and `g++` (or Visual Studio on Windows). If a prebuilt copy complains about a missing GLIBC or GLIBCXX, rebuild it:

```sh
cd pycdc
cmake . -DCMAKE_BUILD_TYPE=Release
make -j4
```

Afterwards the folder holds the two programs `pycdc` and `pycdas`.

Begin by running `./pycdas` and then `./pycdc` on a file from `tests/compiled/`, for example `tests/compiled/test_calls.3.8.pyc`. This is a clean decompile, so use it as the baseline. Then run `./pycdc ok.pyc` and explain the error message by looking at the file size. Run `./pycdc out_sequencer.pyc` and note what it reports, which Python version the file is, and why pycdc can't rebuild the source. For the same file switch to `./pycdas out_sequencer.pyc`, read the `[Names]` and `[Constants]` sections, and describe the scenario the file carries out (the hint is base64, zlib, marshal). Finally run `./pycdc apple_collector_game.pyc`. It reports `Bad MAGIC!` even though the file isn't empty, so look at the first 4 bytes with `xxd -l 4 apple_collector_game.pyc` and explain why.

Two questions to think about. When should you trust the source pycdc prints, and when not? And what does `apple_collector_game.pyc` lack to be a valid `.pyc`, and how can you read its contents? Do it yourself before opening the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

All the output below is real, from a pycdc built from source (CMake + make, g++ on WSL) and run on the sample files.

### Task 1: the clean case

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

The start of pycdas output:

```
$ ./pycdas tests/compiled/test_calls.3.8.pyc
test_calls.3.8.pyc (Python 3.8)
[Code]
    File Name: tests/input/test_calls.py
    Object Name: <module>
    ...
```

Python 3.8 is well supported, so the decompile is nearly verbatim. This is the baseline to compare against.

### Task 2: ok.pyc

```
$ ./pycdc ok.pyc
Bad MAGIC!
Could not load file ok.pyc
```

The file `ok.pyc` is 0 bytes (check with `ls -l`). With no magic number it can't be loaded. On a `Bad MAGIC!` error, first think of an empty or truncated download.

### Task 3: out_sequencer.pyc, where pycdc fails

```
$ ./pycdc out_sequencer.pyc
Unsupported opcode: LOAD_FROM_DICT_OR_GLOBALS
# Source Generated with Decompyle++
# File: out_sequencer.pyc (Python 3.13)

if not None + None:
    pass
# WARNING: Decompyle incomplete
```

The version is Python 3.13 (magic `f3 0d 0d 0a`). pycdc meets the opcode `LOAD_FROM_DICT_OR_GLOBALS` (new in 3.12/3.13), which it doesn't implement yet, so it stops and prints nonsense. The lines `Unsupported opcode` and `WARNING: Decompyle incomplete` are the signal not to trust the output.

### Task 4: out_sequencer.pyc, reading it with pycdas

```
$ ./pycdas out_sequencer.pyc
out_sequencer.pyc (Python 3.13)
[Code]
    File Name: <genetic_sequencer>
    Object Name: <module>
    [Names]
        'base64'
        'zlib'
        'marshal'
        'types'
        'encoded_catalyst_strand'
        'print'
        'b85decode'
        'compressed_catalyst'
        'decompress'
        'marshalled_genetic_code'
        'loads'
        'catalyst_code_object'
        'FunctionType'
        'globals'
```

The `[Constants]` section also holds a long base85 blob and strings like `--- Calibrating Genetic Sequencer ---`. Reading the Names, the file takes a base85 string (`encoded_catalyst_strand`), runs `base64.b85decode` on it, then `zlib.decompress`, then `marshal.loads` to get a code object (`catalyst_code_object`), and finally `types.FunctionType` turns that into a function and runs it. It's a self-decrypting loader, so the real logic is compressed and marshaled in the blob, and the outer `.pyc` layer is just a wrapper.

To go further (not required in this lab), extract the base85 blob and run `marshal.loads(zlib.decompress(base64.b85decode(blob)))` in a Python session to get the inner code object, then bring it into pycdc. Since it's 3.13, pycdc may still stumble, and then you read the bytecode with the `dis` module of Python 3.13. The `[Disassembly]` part of pycdas on this 3.13 file shows wrong opcodes (it maps the 3.13 opcode table incorrectly), so rely only on Names and Constants.

### Task 5: apple_collector_game.pyc

```
$ ./pycdc apple_collector_game.pyc
Bad MAGIC!
Could not load file apple_collector_game.pyc

$ xxd -l 4 apple_collector_game.pyc
00000000: e300 0000
```

The file is nearly 12 KB, so it's not empty. The first four bytes are `e3 00 00 00`. A valid `.pyc` must start with a magic number (for example `f3 0d 0d 0a`). The byte `e3` here is the marshal code for a code object (`TYPE_CODE`), which means this file is a raw marshaled code object with the 16-byte `.pyc` header stripped off. To read it, prepend a header (the correct magic number for the version plus 12 bytes of padding) and open it with pycdc, or read it directly with `marshal.loads(open('apple_collector_game.pyc','rb').read())` in a Python session of the same version that created it.

### Answers to the questions

Trust pycdc's source only when there's no `Unsupported opcode` or `Decompyle incomplete` warning and the code reads meaningfully. With a warning, treat the output as garbage and switch to pycdas or another decompiler. The file `apple_collector_game.pyc` lacks the `.pyc` header (magic + flags/timestamp + size). You can read it by prepending a header or by using the `marshal` module directly.

</details>

## Key takeaways
pycdc rebuilds source and pycdas dumps bytecode, and neither needs a Python runtime of the exact version. Build with cmake + make in a few minutes if the prebuilt version has library errors. `Unsupported opcode` or `WARNING: Decompyle incomplete` means you shouldn't trust the source pycdc printed, so switch to pycdas. pycdc is weak with Python 3.12/3.13. That's a real limitation, not something you did wrong.

`Bad MAGIC!` has three common causes, an empty/truncated file, raw marshal with the header missing, or an encrypted file. Always read the `[Names]` and `[Constants]` of pycdas, since they often reveal the whole scenario (a base64/zlib/marshal loader) before you read the logic.
