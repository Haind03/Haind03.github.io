---
title: "Lesson 18.2: Emulation, running a piece of code without the whole program"
image:
  path: /assets/img/covers/re-18-2-emulation-running-piece-code-without-whole.webp
  alt: "Lesson 18.2: Emulation, running a piece of code without the whole program"
date: 2023-09-01 15:06:00 +0700
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

The goal is to use Unicorn Engine to run the actual bytes of a decryption routine, rather than sitting down and translating the algorithm by hand. This is exactly the skill for quickly solving the string-deobfuscation functions that show up constantly in malware and crackmes. Install Unicorn with `pip install unicorn`. The reference environment this was checked against is unicorn 2.1.2 with Python 3.11.

Read `emu_xor.py` and work out where the code sits, where the encrypted data sits, and which registers hold the parameters. Run `python3 emu_xor.py` and watch the encrypted string go in and the decrypted string come out. Change the key from `0x5A` to a different value, in both the part that builds `enc` and in the byte code itself (`80 37 XX`), run it again, and confirm it still matches. Explain why a return address has to be written onto the stack before running, and why `emu_start` stops exactly at `BASE + len(CODE)`. As an extension, replace the XOR loop with a simple addition function (`add byte [rdi], 7`) and emulate that instead.

Two questions worth thinking through. If the code snippet had a `call printf` in the middle, what happens when you emulate it, and how would you handle that? And why does emulation get past anti-debug checks that trip up a real debugger?

<div class="lab-box">
<div class="lab-head"><b>LAB 18.2</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/18.2/src/emu_xor.py" download><i class="fa-solid fa-file-code"></i>src/emu_xor.py</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Results from an actual run. Running `python3 emu_xor.py` in the reference environment (unicorn 2.1.2, Python 3.11) gives:

```
Input (encrypted): 3f372f363b2e333534052d3334297b
Output (decrypted): emulation_wins!
```

Unicorn executed the actual XOR loop over virtual memory and reversed the string, with no need to rewrite the algorithm in Python.

Walking through the pieces. The byte code `80 37 5A 48 ff c7 48 ff ce 75 f5 c3` is:

```
80 37 5A      xor byte ptr [rdi], 0x5A   ; decrypt one byte
48 ff c7      inc rdi                     ; move to the next byte
48 ff ce      dec rsi                     ; decrement the counter
75 f5         jnz -11                     ; loop while bytes remain
c3            ret                         ; done
```

Following the System V calling convention, the input registers are `rdi`, the buffer pointer, and `rsi`, the length. We load the encrypted buffer into the `DATA` region, point `rdi` at it, set `rsi` to its length, and run. After running, reading the `DATA` region back gives the original string.

On the return address and the stop point: a `ret` instruction takes 8 bytes off the top of the stack as the address to jump to. If the stack holds garbage, the emulated CPU jumps into unmapped memory and throws `UC_ERR_FETCH_UNMAPPED`. So we write `BASE + len(CODE)` onto the top of the stack ahead of time, and tell `emu_start` to stop exactly at that address. When `ret` runs, it jumps to that stop point, Unicorn sees it has reached the target, and it finishes cleanly. This is the standard trick for emulating a function that ends in `ret`.

On switching to an addition function, `CODE` becomes:

```python
# add byte [rdi],7 ; inc rdi ; dec rsi ; jnz loop ; ret
CODE = bytes.fromhex("80070748ffc748ffce75f5c3")
```

and the data is built with `bytes((c - 7) & 0xFF for c in b"...")`. The rest of the emulation logic stays the same.

On a call leading outside the snippet: if there's a `call printf` in the middle, Unicorn jumps to printf's address, which isn't mapped, and the emulation breaks. There are two ways to handle it. One is to only emulate the portion without the call, narrowing the target down. The other is to set a `UC_HOOK_CODE` hook, or a hook on that specific address range, to simulate printf yourself (logging the arguments, then resuming execution by setting `rip` past the call). When you need to simulate many APIs, it's worth switching to Qiling instead, since it already has that layer built in.

On getting past anti-debug: anti-debug checks rely on detecting that a real debugger is attached (IsDebuggerPresent, PEB.BeingDebugged, RDTSC timing, INT3 traps). Inside Unicorn there's no real process, no standard PEB, and no debugger attached at all, so these checks either have nothing to read or read back a clean value. We run exactly the piece of logic we need and skip the entire defensive layer, because we're not playing by the program's rules, we're building our own playground instead.

</details>

## Key takeaways
Emulation means building a virtual CPU, loading byte code, setting registers and memory, running, and reading the result. Unicorn is pure CPU emulation with no OS, so it fits self-contained computation functions, and its model is always the same four steps: create the machine, map and write memory, set registers, run and read. The traps are that `ret` needs a return address, calls out will break, and you have to map enough memory.

Qiling adds an OS/syscall layer to run whole binaries, and Speakeasy specializes in shellcode and Windows malware. Since there's no real debugger, emulation gets past most anti-debug.
