---
title: "Lesson 7.4: Python packaged as an .exe"
image:
  path: /assets/img/covers/re-7-4-when-python-turns-into-exe-open.webp
  alt: "Lesson 7.4: Python packaged as an .exe"
date: 2022-11-12 09:21:00 +0700
categories: ["Technique Reverse", "Part 07 · Python"]
tags: [reverse-engineering, python]
render_with_liquid: false
---
You download a program, DIE says it's a normal Windows PE, but IDA shows only bootloader code that has nothing to do with the logic. Looking closer at the strings you see `python311.dll`, `_MEIPASS`, `pyi-`. This isn't a C program, it's a Python script packaged into an exe. The real logic is still Python bytecode inside. You just have to dig it out and decompile it like in Lesson 7.2.

Three packaging tools you'll commonly meet are PyInstaller (the most common), py2exe, and cx_Freeze. The handling is similar: identify, extract, decompile.

## PyInstaller: structure and how to recognize it

PyInstaller doesn't compile Python to machine code. It puts a whole runtime into the exe: a bootloader written in C (the part you see in IDA), the Python interpreter (`python3xx.dll` or `libpython`), and an archive with all the program's `.pyc` files, compressed in a block called PYZ. At runtime, the bootloader unpacks into a temp folder (the `_MEIPASS` environment variable) and then calls the interpreter to run the main script.

The tells, `strings` is enough:

```
_MEIPASS
pyi-contents-directory
pyimod01_archive
PYZ-00.pyz
python3.11.so.1.0        (or python311.dll on Windows)
```

`_MEIPASS` and `pyi` almost certainly mean PyInstaller. DIE also recognizes it and says so directly.

## Extracting with pyinstxtractor

The classic tool is `pyinstxtractor` (and the newer `pyinstxtractor-ng`, which handles recent PyInstaller versions better). Run it straight on the exe:

```
python3 pyinstxtractor.py secretapp
```

This is the real output when extracting a binary built with PyInstaller 6.20, Python 3.11:

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

Two lines matter here. The first is "Python version: 3.11". You need it to pick the right decompiler. From Lesson 7.2, pycdc doesn't depend on the runtime, but you still need the version to decompile properly. The second is "Possible entry point: secretapp.pyc". PyInstaller generates a lot of `.pyc` files, most of them its own support code (`pyiboot`, `pyimod`, `pyi_rth`). Skip the `pyi*` files. The entry point file named after the original script (`secretapp.pyc`) is the one to read.

After extraction you have a `secretapp_extracted/` folder with all the `.pyc` files and accompanying libraries.

## The magic header trap

Beginners often trip here. A proper `.pyc` file starts with a 16-byte header (magic number + flags + timestamp/hash + size), as Lesson 7.1 said. Many PyInstaller versions strip the magic header of the entry point file when packaging, so the extracted `.pyc` is missing the first 8 or 16 bytes. A decompiler opening it will report an error or read it wrong.

The fix is to copy the header from a healthy `.pyc` (for example a standard module like `struct.pyc` in the same extracted folder) and paste it onto the start of the broken file. For the binary above, the headers of `struct.pyc` and `secretapp.pyc` both start with the same magic:

```
secretapp.pyc : a7 0d 0d 0a 00 00 00 00 ...
struct.pyc    : a7 0d 0d 0a 00 00 00 00 ...
```

`a70d0d0a` is Python 3.11's magic number. Newer PyInstaller and pyinstxtractor-ng keep the header intact, so a lot of the time you don't have to patch anything. But with an old binary, remember the header patch, otherwise you'll think the file is corrupt.

## Decompile

With a `.pyc` that has a complete header, run pycdc like in Lesson 7.2. To show the real logic is still intact, here's the result of reading `co_consts` of the `secretapp.pyc` extracted above (no full decompiler needed, just marshal-load and walk through the constants):

```
 [function] check
  const: 'PyInst@ller_2024'
 [function] main
  const: 'License key: '
  const: 'Licensed!'
  const: 'Wrong key.'
```

The license key `PyInst@ller_2024` sits in the constants of the `check` function. No encryption, nothing. Packaging Python into an exe barely protects secrets. It hides them, it doesn't lock them. To really lock it you need something like PyArmor or Nuitka (Lesson 7.5).

## py2exe and cx_Freeze

Two older tools, same principle. py2exe puts the `.pyc` files into a resource or a `library.zip` file next to the exe. Use `unpy2exe`, or often just unzip `library.zip` with a regular zip tool and then decompile. cx_Freeze usually keeps the `.pyc` files in `library.zip` or the `lib/` folder, so unzip and then decompile.

Neither resists reversing. Find the `.pyc`, patch the header if needed, decompile.

## The workflow

Start with triage. `strings`/DIE showing `_MEIPASS`, `pyi`, `python3xx` means PyInstaller, while a `library.zip` next to the exe means py2exe/cx_Freeze. Then extract with `pyinstxtractor(-ng)` for PyInstaller, or unzip for the other two, and note the Python version the tool reports. Find the right file by skipping `pyi*` and taking the entry point file named after the original script. Patch the magic header if the `.pyc` is missing it (copy from a standard module in the same folder). Finally decompile with pycdc (Lesson 7.2), or a decompiler matching the version (Lesson 7.3).

## Lab

The task is to package a Python script into an exe yourself and then extract it back, to see that the logic is still intact in bytecode form. You need Python 3 and PyInstaller (`pip install pyinstaller`), plus pyinstxtractor or pyinstxtractor-ng. For the first, download the single file with `curl -LO https://raw.githubusercontent.com/extremecoders-re/pyinstxtractor/master/pyinstxtractor.py`. For the ng version run `pip install pyinstxtractor-ng` and use the `pyinstxtractor-ng` command. You also need a .pyc decompiler, either pycdc from Lesson 7.2 or a version-matched decompiler from Lesson 7.3. The sample file is `secretapp.py`, a simple license key checker.

First, package it into an exe:

```
pyinstaller --onefile secretapp.py
```

The result lands in `dist/secretapp` (Linux/macOS) or `dist\secretapp.exe` (Windows). Next triage the new file by running `strings dist/secretapp | grep -iE "_MEIPASS|pyi|python3"` and confirm the PyInstaller signs. Then extract it back:

```
python3 pyinstxtractor.py dist/secretapp
```

Read the output: which Python version does the tool report, and which file is the Possible entry point? Go into the `secretapp_extracted/` folder. Among the many `.pyc` files, which one is the original script and which are PyInstaller's support files (hint: names starting with `pyi`)? Check the magic header of `secretapp.pyc` (the first 16 bytes). Is the header complete? If it's missing, copy the header from a standard module such as `struct.pyc` in the same folder. Finally decompile `secretapp.pyc`, find the license key, and see whether anything hides it.

Two questions to think about. Why does packaging into an exe barely protect secrets in the code? And if the author really wanted to hide the license key, what would they have to use (hint: Lesson 7.5)? Do it yourself before opening the solution.

<div class="lab-box">
<div class="lab-head"><b>LAB 7.4</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/7.4/src/secretapp.py" download><i class="fa-solid fa-file-code"></i>src/secretapp.py</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

All the output below is real, from Python 3.11.9 and PyInstaller 6.20.0 (on Linux, so the exe is an ELF; on Windows the steps are identical apart from the .exe extension).

### 1. Packaging

```
pyinstaller --onefile secretapp.py
```

This produces `dist/secretapp`, about 16 MB because the Python interpreter is bundled inside.

### 2. Triage

```
$ strings -n 5 dist/secretapp | grep -iE "_MEIPASS|pyi|python3" | sort -u
_MEIPASS
_pyinstaller_pyz
libpython3.11.so.1.0
pyi-contents-directory
pyimod01_archive
PYZ-00.pyz
```

`_MEIPASS` and `pyi` confirm PyInstaller, and `libpython3.11` tells you it's Python 3.11.

### 3. Extracting

```
$ python3 pyinstxtractor.py dist/secretapp
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

The Python version is 3.11. The real entry point is `secretapp.pyc`, while the two `pyiboot` and `pyi_rth` files belong to PyInstaller.

### 4. Filtering the files

In `secretapp_extracted/`:

```
pyi_rth_inspect.pyc     <- PyInstaller's, skip
pyiboot01_bootstrap.pyc <- PyInstaller's, skip
pyimod01_archive.pyc    <- PyInstaller's, skip
pyimod02_importers.pyc  <- PyInstaller's, skip
pyimod03_ctypes.pyc     <- PyInstaller's, skip
secretapp.pyc           <- THIS ONE, the original script
struct.pyc              <- a standard module (to borrow a header from if needed)
```

### 5. The magic header

```
$ xxd secretapp.pyc | head -1
00000000: a70d 0d0a 0000 0000 0000 0000 0000 0000
$ xxd struct.pyc | head -1
00000000: a70d 0d0a 0000 0000 0000 0000 0000 0000
```

With PyInstaller 6.x the header is kept intact (`a70d0d0a` is the Python 3.11 magic), so there's nothing to patch. If you meet an older binary where `secretapp.pyc` lacks the header, copy the first 16 bytes of `struct.pyc` and paste them at the start of `secretapp.pyc`.

### 6. Getting the secret

You don't even need a full decompiler. Just marshal-load the file and walk the constants:

```python
import marshal
with open("secretapp.pyc","rb") as f:
    f.read(16)                 # skip the header
    code = marshal.load(f)
# walk co_consts recursively...
```

The real result:

```
 [function] check
  const: 'PyInst@ller_2024'
 [function] main
  const: 'License key: '
  const: 'Licensed!'
  const: 'Wrong key.'
```

The license key is `PyInst@ller_2024`, in plain sight in the constants of the `check` function. Using pycdc would rebuild both `check` and `main` almost verbatim.

### Answers to the questions

Packaging only gathers the files together and doesn't encrypt the bytecode. Every string constant, function name and piece of logic is still in the `.pyc`, so once extracted it can all be read. To really hide something, the bytecode must stop being in the standard form: PyArmor (encrypting and wrapping the bytecode), or Nuitka and Cython (compiling to C and then native, at which point you reverse it like C). See Lesson 7.5.

</details>

## Key takeaways
PyInstaller packs the interpreter and compressed `.pyc` files into the exe, so the logic is still Python bytecode. You recognize it by `_MEIPASS`, `pyi`, `python3xx` in the strings. `pyinstxtractor(-ng)` extracts it, and you read the Python version and Possible entry point lines. Skip the `.pyc` files named `pyi*` and take the file named after the original script. The extracted `.pyc` may be missing the magic header, so copy one from a healthy `.pyc` onto the start to patch it. py2exe/cx_Freeze usually keep `.pyc` files in `library.zip`, so unzip then decompile. Packaging isn't encryption, and secrets in the code are fully exposed.
