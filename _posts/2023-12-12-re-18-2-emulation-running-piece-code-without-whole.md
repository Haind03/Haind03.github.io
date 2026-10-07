---
title: "Lesson 18.2: Emulation, running a piece of code without the whole program"
date: 2023-12-12 22:41:00 +0700
categories: ["Technique Reverse", "Part 18 · Advanced Topics"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
Sometimes you only need to know what a function returns, but to run it you'd have to get through a whole forest of anti-debug, or the function sits deep inside a binary that can't run on your machine (wrong architecture, missing libraries, needs special hardware). Debugging gets in the way, reading statically costs a whole afternoon. Emulation is the third path: build a virtual CPU, load that exact piece of byte code into it, set the registers and memory as they were when it was called, hit run, then read the result. There's no real debugger here, so most anti-debug becomes meaningless.

## Unicorn: a CPU in 20 lines of Python

Unicorn Engine is a CPU emulation engine split out of QEMU, supporting x86, ARM, ARM64, MIPS and many other architectures. It knows nothing about the operating system, files, or syscalls. It does exactly one thing: given a sequence of bytes that are machine instructions, it executes each instruction and updates registers and memory. That alone is enough to run a pure-computation function like a string decryption routine.

Using Unicorn always follows the same four steps. You create the virtual machine with an architecture and mode (`Uc(UC_ARCH_X86, UC_MODE_64)`), then allocate memory (`mem_map`) and write the code and data in (`mem_write`). Next you set the input registers (`reg_write`): parameters, stack pointer, buffer pointer. Finally you run (`emu_start`) and read the result out (`reg_read`, `mem_read`).

Here's the XOR decryption snippet, which really runs (see lab 18.2):

```python
from unicorn import *
from unicorn.x86_const import *

# xor byte [rdi],0x5A ; inc rdi ; dec rsi ; jnz loop ; ret
CODE = bytes.fromhex("80375A48ffc748ffce75f5c3")
BASE, DATA, STACK = 0x1000000, 0x2000000, 0x3000000

enc = bytes(c ^ 0x5A for c in b"emulation_wins!")

mu = Uc(UC_ARCH_X86, UC_MODE_64)
for addr in (BASE, DATA, STACK):
    mu.mem_map(addr, 0x1000)
mu.mem_write(BASE, CODE)
mu.mem_write(DATA, enc)
mu.reg_write(UC_X86_REG_RDI, DATA)         # buffer pointer
mu.reg_write(UC_X86_REG_RSI, len(enc))     # length
mu.reg_write(UC_X86_REG_RSP, STACK + 0x800)

mu.emu_start(BASE, BASE + len(CODE))
print(bytes(mu.mem_read(DATA, len(enc))).decode())  # -> emulation_wins!
```

The nice thing is you don't need to understand every detail of the function. You only need to know it takes a pointer in `rdi` and a length in `rsi`, copy the exact byte code of the loop out of IDA, and let Unicorn do the rest. This is a quick way to solve the string-deobfuscation functions that malware loves: instead of sitting there computing XOR by hand, you let the virtual CPU run the malware's own code.

## Three traps when using Unicorn

A `ret` instruction needs a valid return address on the stack, otherwise the VM jumps into an unmapped region and throws an error. The tip is to write a known address onto the top of the stack beforehand and stop `emu_start` at exactly that address.

Calls out to an API or a syscall will break because Unicorn has no operating system. You either avoid the stretch with the call, or set a hook to fake that call.

You also have to map enough memory: code, data, stack, and any region the function touches. Forgetting to map one region gives a `UC_ERR_READ_UNMAPPED` error right away.

## Qiling: Unicorn plus a whole operating system

When the function you need to run calls Windows APIs or Linux syscalls, bare Unicorn isn't enough. Qiling is a framework built on Unicorn that adds an OS emulation layer: it can load a whole PE or ELF file, emulating the loader, syscalls, and part of the Win32 API, and lets you hook any API. That means you can run a whole malware binary in a Python sandbox, intercepting and modifying all its calls, without real Windows.

Qiling fits when you want to run a binary of a different architecture than your machine, catch the APIs the malware calls, or automate config extraction by running to a point and then reading memory.

## Speakeasy: specialized for shellcode and Windows malware

Mandiant's Speakeasy is an emulator aimed straight at Windows malware and shellcode analysis. It emulates a lot of Win32 APIs and the kernel out of the box and logs every call, so you throw a piece of shellcode at it and it tells you what that shellcode does (which APIs it calls, where it connects) without running it for real on your machine. Very good for quick triage.

## When emulation beats debugging and static analysis

Choose emulation when the target function is pure computation (decrypt, hash, transform) and you only need input to output, which is the sweet spot. It also fits a binary full of anti-debug, since without a real debugger the IsDebuggerPresent, timing, and trap checks are all useless (tying back to Part 15). A binary of the wrong architecture for your machine works too: an ARM64 function runs fine on Unicorn even if you're sitting on an x86 machine. And when you want to automate, you can run the same function with thousands of inputs to find a pattern.

Emulation doesn't fit when the code is so tied to the OS/API/hardware that faking it costs more effort than running it for real, or when it's virtualized (then the VM bytecode is the thing you need to understand, see lesson 14.5). And remember: emulating exactly one piece is easy, emulating a whole large program makes the effort grow fast. Cut the target down small.

## Lab

See [labs/18.2/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/18.2): run `emu_xor.py` to use Unicorn yourself to decrypt a string without rewriting the algorithm, then try changing the key and length. The solution and how to extend it to functions with multiple parameters are in `solution.md`.

## Key takeaways
Emulation means building a virtual CPU, loading byte code, setting registers and memory, running, and reading the result. Unicorn is pure CPU emulation with no OS, so it fits self-contained computation functions, and its model is always the same four steps: create the machine, map and write memory, set registers, run and read. The traps are that `ret` needs a return address, calls out will break, and you have to map enough memory.

Qiling adds an OS/syscall layer to run whole binaries, and Speakeasy specializes in shellcode and Windows malware. Since there's no real debugger, emulation gets past most anti-debug.
