---
title: "Lesson 7.5: When Python is no longer an easy-to-swallow .pyc"
date: 2022-11-13 14:45:00 +0700
categories: ["Technique Reverse", "Part 07 · Python"]
tags: [reverse-engineering, python]
render_with_liquid: false
---
The last few lessons gave you the feeling that Python is easy prey: drag a .pyc into pycdc and you almost have the source back. True, but only when the author leaves the bytecode as is. Once they use Nuitka, Cython or PyArmor, the party's over. pycdc returns nothing, uncompyle6 throws errors, and you realize you're no longer reversing Python.

This is the same turning point as NativeAOT on the .NET side (Lesson 5.6): the language-specific tools are useless, you have to fall back to native reversing with IDA/Ghidra, or switch to attacking the runtime. This lesson teaches you to recognize which kind you're facing, because picking the wrong direction costs a whole session.

## Three spoilers, three different natures

![Python packaging: PyInstaller is easy to decompile, Nuitka/Cython/PyArmor are hard](/assets/img/technique-reverse/assets/phan-07/python-packaging.svg)

The most important thing to grasp is that these three are different in nature, so the handling is completely different too. Nuitka compiles Python to C and then compiles on to native machine code, so the Python bytecode disappears completely. Cython also translates Python (or Cython syntax) to C and then to a C extension (`.pyd` on Windows, `.so` on Linux), so it's native too. PyArmor is different: it still runs Python bytecode, but encrypts and wraps it, only decrypting in memory at runtime, so at its core it's still Python, just locked.

In other words, Nuitka and Cython push you into the native world, while PyArmor keeps you in the Python world but builds a wall.

## Nuitka: Python in a C coat

Nuitka takes your Python program, generates C code calling into the CPython API, then compiles it to an exe (or a folder holding an exe and DLLs). The result is a genuine native binary, no co_code, no PYZ archive, and pycdc is dead on arrival.

But Nuitka can't hide its fingerprint. The binary is still full of calls to the CPython runtime: names like `PyObject_`, `PyTuple_New`, `Py_INCREF`, `PyImport_`. And more importantly, Nuitka embeds a module table along with lots of strings that leak the original Python function, variable and module names. That means even though you have to read assembly, you still have more anchors than when reversing a pure C program.

The strategy with Nuitka is to treat it like a C/C++ binary. Open it in IDA/Ghidra, and rely on the CPython API calls to understand which Python object is being manipulated at each step. For example, seeing `PyObject_RichCompare` right after loading the input means a comparison is happening, very much like the familiar password check logic. Reuse everything you learned in Parts 3 and 4.

## Cython: the same story, a smaller package

Cython usually doesn't produce a whole exe but a compiled module (`.pyd`/`.so`) imported from a thin Python script. The sensitive code lives in that native module, and the rest may still be readable .pyc.

You recognize Cython by symbols in the module like `__pyx_`, `__Pyx_`, and wrapper function names like `__pyx_pf_...`. It's also full of CPython API like Nuitka. The strategy is exactly the same: open the `.pyd`/`.so` in Ghidra/IDA, and follow `__pyx_` and the CPython API. Don't waste time looking for a Python decompiler, there isn't one.

## PyArmor: still Python, but locked

PyArmor takes a different road. It doesn't compile to native. It encrypts the bytecode and adds a runtime layer (an accompanying C module, you often see the name `pytransform` in old versions or `pyarmor_runtime` in new ones) to decrypt and load the code in memory right before running. On disk you only see junk, and the real code only exists in RAM during execution.

You recognize PyArmor by a script line like `from pytransform import pyarmor` or `from pyarmor_runtime...`, along with encrypted data blobs and a native runtime library. pycdc is of course helpless.

The strategy with PyArmor revolves around one idea: let it decrypt itself and then grab the code from memory. Since CPython ultimately still needs a code object to run, you can intervene at that layer. For old versions (PyArmor 5/6), the community once had unpack scripts that hook into `pytransform` to intercept the code object after decryption, so look for the exact version. New versions (PyArmor 7/8+) are much tougher, with RFT mode and multiple layers. The general direction there is to hook CPython's code-loading functions (for example intercepting `PyEval_EvalCodeEx`/`PyEval_EvalFrame` or using a patched CPython to dump every executed code object), then marshal the collected code objects out to .pyc to decompile. This requires understanding the runtime and usually running the sample, so do it in an isolated VM if the origin is suspicious (Lesson 0.3).

## Recognizing which kind in a minute

Before digging, always triage to know what you're holding. Drag the file into Detect It Easy and run `strings`, then look for the tells. If you see `python3x.dll`/`libpython`, the strings `PyInstaller`, `MEI`, or a PYZ archive, this is plain PyInstaller (Lesson 7.4), which you extract then decompile, the easiest case. If you see lots of `Py_`, `PyObject_`, with a table of Python module name strings but no PYZ, suspect Nuitka. If you see `__pyx_`, `__Pyx_` in a `.pyd`/`.so`, it's Cython. If you see `pytransform`, `pyarmor_runtime`, encrypted blobs, it's PyArmor. Then pick a direction using the table in the lab below.

A common mix-up is thinking a Nuitka binary is PyInstaller and then fumbling around looking for a PYZ that isn't there. A quick way to tell: PyInstaller has an archive attached at the end of the file and the bootloader leaves very characteristic strings, while Nuitka has no archive, only native code with the CPython API scattered throughout.

## Why this is a turning point

All of Part 7 so far taught you one narrow skill: reading and decompiling Python bytecode. Nuitka and Cython wipe that skill out and force you back to the native foundation of Parts 1 to 4. That's exactly why the curriculum puts assembly and C/C++ first: when the high-level language shell is stripped away, you always fall back to native, and anyone solid on native has no dead end. PyArmor teaches a different lesson: when the code only exists in memory at runtime, the answer lies in dynamic analysis, not static.

## Key takeaways
Nuitka and Cython compile Python to native, so there's no more bytecode and you have to use IDA/Ghidra like with C. The traces to hold onto are the CPython API (`Py_`, `PyObject_`) with Nuitka and `__pyx_`/`__Pyx_` with Cython. PyArmor is still Python but encrypts the bytecode and decrypts it in RAM at runtime, so the approach is dumping code objects from memory. Always triage with DIE and strings first to know which kind you're facing, and don't look for a PYZ on a Nuitka binary. When the language shell is stripped, you always fall back to native, and the foundation of Parts 1 to 4 is the lifesaver.
