---
title: "Lesson 14.2: Unpacking UPX, automatic and manual"
date: 2026-10-06 09:21:00 +0700
categories: ["Technique Reverse", "Part 14 · Packers and Obfuscation"]
tags: [reverse-engineering, packer, obfuscation]
render_with_liquid: false
---
UPX is the packer you'll meet the most, and also the best place to learn the manual unpacking workflow because it's simple, open source, and has no anti-debug. Understanding UPX is understanding the skeleton of every packer: a small piece of code (the stub) decompresses the real code into memory and then jumps to the original entry point. This lesson goes from the laziest way (one command) to what you have to do by hand when the packer fights back.

## What a packer does, said briefly again

A packed file has two parts: compressed data (your original code, compressed so it can't be read) and a decompression stub placed at the entry point. When it runs, the stub expands the compressed part into memory, rebuilds the import table, then jumps to the OEP (Original Entry Point, the real entry point of the original program). From the OEP onward it's the original program running.

The goal of unpacking: catch the exact moment the stub has just finished expanding and is about to jump to the OEP, then snapshot (dump) the memory at that moment. That dump is the original code.

## The lazy way: upx -d

If the file was packed with standard UPX and nobody touched it, all you need is:

```
upx -d -o output.exe packed.exe
```

UPX recognizes its own format and expands it back. This is the best case, and also the reason UPX alone isn't a serious protection: anyone can remove it in a second.

A real session on Linux so you can see the numbers:

```
$ gcc -O2 -static -o hello_s hello.c      # 900368 bytes
$ upx --best -o hello_s.upx hello_s
   900368 ->    352616   39.16%   linux/amd64   hello_s.upx
$ upx -d -o hello_s.unp hello_s.upx
Unpacked 1 file.
$ ./hello_s.unp UPX_s3cr3t
Correct!
```

Compressed to 39% of the size, and the unpacked version runs exactly like the original. Done.

## When upx -d refuses

The problem is that whoever packs the file knows about `upx -d`. The most common countermeasure: edit a few bytes in the header so UPX no longer recognizes its own file. UPX marks its blocks with a four-byte magic `UPX!`. Just change these markers and `upx -d` gives up, but the stub still runs fine because it doesn't rely on that magic to decompress.

Same session as above, after changing all four `UPX!` markers to junk:

```
$ upx -d -o out hello_s.broken
upx: hello_s.broken: NotPackedException: not packed by UPX
Unpacked 0 files.
$ ./hello_s.broken UPX_s3cr3t
Correct!
```

UPX says "not packed by UPX", but the file still runs and prints "Correct!". This is the moment you have to unpack it yourself. The good news: even though the header was edited, the decompression mechanism is unchanged, so the manual technique still works.

## Anatomy of the UPX stub

The UPX stub on Windows starts with a very characteristic move: it saves all the registers, does the decompression, then restores the registers before jumping to the OEP.

```asm
pushad                    ; save all registers on the stack
mov  esi, <source address> ; source: compressed data
mov  edi, <dest address>   ; destination: where the decompressed code goes
...                       ; decompression loop
popad                     ; restore all registers
jmp  <OEP>                ; tail jump: jump to the original entry point
```

There are two golden details here. `pushad` pushes 8 registers onto the stack at once, so right after `pushad` the stack pointer (ESP) points to the block it just saved. And at the end of the stub is `popad` and then a far `jmp`, called the tail jump, which goes straight to the OEP. These two details give us two ways to find the OEP.

## Method 1: the ESP trick (stack restore)

This is the classic technique, fast and almost always effective against UPX.

The idea: `pushad` writes 8 registers onto the stack, and `popad` will read back exactly that region. If you set a hardware breakpoint watching reads of the stack region `pushad` just wrote, that breakpoint fires exactly when `popad` runs, which is right before the tail jump to the OEP.

In x64dbg (x32dbg for 32-bit), open the file in the debugger and it stops at the entry point, the start of the stub. Step over the first `pushad` instruction (F8 once). Look at the ESP register, which just decreased after the pushad, then right-click ESP and choose "Follow in Dump". In the Dump window, select the first 4 bytes, right-click, Breakpoint, Hardware, Access. Press F9 (Run), and the debugger will stop when `popad` reads that region back.

Now you're right before the tail jump. Step a few instructions (F8) until you see a `jmp` to a far address, completely different from the stub region. That's the tail jump. Step over it and you're at the OEP.

When you reach the OEP, the code looks "clean": a normal function prologue (or for a real program the CRT startup, see [Lesson 3.1](/posts/tr-3-1-hello-world-tim-main-that/)), no longer like a compression stub.

## Method 2: find the tail jump directly

If you have a trained eye, you can scroll to the end of the stub and look for the `popad` + far `jmp` pair. Set a breakpoint at that tail jump, run to it, then step over. This is quick but requires knowing what the stub looks like. The ESP trick is safer for beginners.

## Method 3: breakpoint on the original section

Another approach: the section that holds the original code is empty at the start (because the code is in compressed form). Set an "execute" memory breakpoint on that section. When the stub finishes decompressing and the CPU starts running code in the original section, the breakpoint fires, and you're close to the OEP. Useful when a complicated stub makes the ESP trick hard.

## At the OEP, now dump

Reaching the OEP is only half the job. The decompressed code is in memory, but you need to save it as a runnable file. That's the job of Scylla (usually shipped with x64dbg as a plugin). Open Scylla, pick the process you're debugging, and put the OEP you just found in the OEP field. Click "IAT Autosearch" then "Get Imports", and Scylla probes and rebuilds the import table (because the stub resolved the imports in memory, but a raw dump doesn't have the right import table yet). Then "Dump" saves the memory to a file, and "Fix Dump" patches the import table into the file you just dumped.

The details of rebuilding the IAT, why it's needed, and the pitfalls are in [Lesson 14.3](/posts/tr-14-3-dump-rebuild-iat-scylla/). Without rebuilding the IAT, the dumped file opens in IDA for static reading but usually won't run.

## When UPX is no longer UPX

Careful: many packers and malware use UPX as an outer layer and wrap their own protection on top, or modify the stub so heavily that the standard pushad/popad is gone. Then the ESP trick may miss. The general principle still holds (run the stub, find the OEP, dump), but how you find the OEP has to be flexible. UPX is just the intro exercise for an unpacking mindset that applies to every packer.

## Key takeaways
Try `upx -d` first, since often it's done right away. If the header was edited (the `UPX!` magic changed), `upx -d` reports NotPackedException but the file still runs, so you have to unpack manually. The UPX stub has `pushad` at the start and `popad` + tail jump at the end, and those are the two landmarks for finding the OEP.

For the ESP trick, put a hardware breakpoint on the stack right after `pushad`, and it fires again when `popad` runs, near the tail jump. At the OEP, dump with Scylla and rebuild the IAT (Lesson 14.3). UPX is the intro exercise, and this mindset applies to every packer.

## Lab
The folder [labs/14.2/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/14.2) has a sample program, the pack command, and how to corrupt the header yourself to practice manual unpacking. The full writeup with real numbers is in [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/14.2/solution.md).
