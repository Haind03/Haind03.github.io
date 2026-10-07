---
title: "Lesson 7.4: When Python turns into an .exe, how to open it back up"
date: 2026-10-06 08:56:00 +0700
categories: ["Technique Reverse", "Part 07 · Python"]
tags: [reverse-engineering, python]
render_with_liquid: false
---
You download a program, DIE says it's a normal Windows PE, but opening it in IDA shows nothing but bootloader code that has nothing to do with the logic. Looking closer at the strings you see `python311.dll`, `_MEIPASS`, `pyi-`. This isn't a C program, it's a Python script packaged into an exe. And the good news: the real logic is still Python bytecode inside, you just need to dig it out and decompile it like in Lesson 7.2.

Three packaging tools you'll commonly meet are PyInstaller (the most common), py2exe, and cx_Freeze. The handling is similar: identify, extract, then decompile.

## PyInstaller: structure and how to recognize it

PyInstaller doesn't compile Python to machine code. It stuffs a whole runtime into the exe: a bootloader written in C (the part you see in IDA), the Python interpreter (`python3xx.dll` or `libpython`), and an archive containing all the program's `.pyc` files, compressed in a block called PYZ. At runtime, the bootloader unpacks into a temp folder (the `_MEIPASS` environment variable) and then calls the interpreter to run the main script.

Tells, just `strings` is enough:

```
_MEIPASS
pyi-contents-directory
pyimod01_archive
PYZ-00.pyz
python3.11.so.1.0        (or python311.dll on Windows)
```

Seeing `_MEIPASS` and `pyi` is almost certainly PyInstaller. DIE also recognizes it and says so directly.

## Extracting with pyinstxtractor

The classic tool is `pyinstxtractor` (and the newer `pyinstxtractor-ng`, which handles recent PyInstaller versions better). Run it straight on the exe:

```
python3 pyinstxtractor.py secretapp
```

Here's the real output when extracting a binary built with PyInstaller 6.20, Python 3.11:

```
[+] Processing dist/secretapp
[+] Pyinstaller version: 2.1+
[+] Python version: 3.11
[+] Length of package: 16432443 bytes
[+] Found 54 files in CArchive
[+] Beginning extraction...please standby
[+] Possible entry point: pyiboot01_bootstrap.pyc
[+] Possible entry point: pyi_rth_inspect.pyc
[+] Possible entry point: secretapp.pyc
[+] Found 99 files in PYZ archive
[+] Successfully extracted pyinstaller archive: dist/secretapp
```

Two golden pieces of information here:

- **Python version: 3.11.** This is the version you need to pick the right decompiler. Remember Lesson 7.2, pycdc doesn't depend on the runtime but you still need to know the version to decompile properly.
- **Possible entry point: secretapp.pyc.** PyInstaller generates a forest of `.pyc` files, most of them its own support code (`pyiboot`, `pyimod`, `pyi_rth`). Skip those `pyi*` files. The entry point file named after the original script (`secretapp.pyc`) is what you want to read.

After extraction, you have a `secretapp_extracted/` folder with all the `.pyc` files and accompanying libraries.

## The magic header trap

This is where beginners often trip. A proper `.pyc` file starts with a 16-byte header (magic number + flags + timestamp/hash + size), as Lesson 7.1 said. The problem: many PyInstaller versions **strip the magic header** of the entry point file when packaging, so the extracted `.pyc` is missing the first 8 or 16 bytes. A decompiler opening it will report an error or read it wrong.

The fix: copy the header from a healthy `.pyc` (for example a standard module like `struct.pyc` in the same extracted folder) and paste it onto the start of the broken file. For the binary above, the headers of `struct.pyc` and `secretapp.pyc` both start with the same magic:

```
secretapp.pyc : a7 0d 0d 0a 00 00 00 00 ...
struct.pyc    : a7 0d 0d 0a 00 00 00 00 ...
```

`a70d0d0a` is exactly Python 3.11's magic number. The good news is that newer PyInstaller and pyinstxtractor-ng keep the header intact, so a lot of the time you don't have to patch anything. But when you meet an old binary, remember this header patching trick, otherwise you'll think the file is corrupt.

## Decompile: the logic is fully exposed

With a `.pyc` that has a complete header, run pycdc like in Lesson 7.2. To show that the real logic is still intact, here's the result of reading `co_consts` of the `secretapp.pyc` extracted above (no full decompiler needed, just marshal-load and walk through the constants):

```
 [function] check
  const: 'PyInst@ller_2024'
 [function] main
  const: 'License key: '
  const: 'Licensed!'
  const: 'Wrong key.'
```

The license key `PyInst@ller_2024` sits naked in the constants of the `check` function. No encryption, nothing. This is why packaging Python into an exe barely protects secrets: it only hides, it doesn't lock. To really lock it you need things like PyArmor or Nuitka (Lesson 7.5).

## py2exe and cx_Freeze

Two older tools, same principle.

- **py2exe**: stuffs the `.pyc` files into a resource or a `library.zip` file next to the exe. Use `unpy2exe`, or often just unzip `library.zip` with a regular zip tool and then decompile.
- **cx_Freeze**: usually keeps the `.pyc` files in `library.zip` or the `lib/` folder. Unzip and then decompile.

Neither resists reversing: find the `.pyc`, patch the header if needed, decompile.

## The short workflow

1. Triage: `strings`/DIE showing `_MEIPASS`, `pyi`, `python3xx` means PyInstaller. A `library.zip` next to the exe means py2exe/cx_Freeze.
2. Extract: `pyinstxtractor(-ng)` for PyInstaller, unzip for the other two. Note the **Python version** the tool reports.
3. Find the right file: skip `pyi*`, take the entry point file named after the original script.
4. Patch the magic header if the `.pyc` is missing it (copy from a standard module in the same folder).
5. Decompile with pycdc (Lesson 7.2), or a decompiler matching the version (Lesson 7.3).

## Lab

The folder [labs/7.4/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/7.4) has instructions for building a PyInstaller exe from a small script and then extracting it back yourself, including how to handle the magic header. The whole workflow in this lesson was actually run on PyInstaller 6.20 / Python 3.11, and the output in [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/7.4/solution.md) is real.

## Key takeaways
- PyInstaller packs the interpreter + compressed `.pyc` into the exe, the logic is still Python bytecode.
- Recognize it by `_MEIPASS`, `pyi`, `python3xx` in the strings.
- `pyinstxtractor(-ng)` extracts it, read the Python version and Possible entry point lines.
- Skip the `.pyc` files named `pyi*`, take the file named after the original script.
- The extracted `.pyc` may be missing the magic header, copy one from a healthy `.pyc` onto the start to patch it.
- py2exe/cx_Freeze usually keep `.pyc` files in `library.zip`, unzip then decompile.
- Packaging isn't encryption: secrets in the code are fully exposed.
