---
title: "Lesson 14.2: Unpacking UPX, automatic and manual"
image:
  path: /assets/img/covers/re-14-2-unpacking-upx-automatic-manual.webp
  alt: "Lesson 14.2: Unpacking UPX, automatic and manual"
date: 2022-07-03 07:24:00 +0700
categories: ["Reverse Engineering", "Part 14 · Packers and Obfuscation"]
tags: [reverse-engineering, packer, obfuscation]
render_with_liquid: false
---
UPX is the packer you'll meet most, and a good place to learn manual unpacking because it's simple, open source, and has no anti-debug. The structure of every packer is the same. A small piece of code (the stub) decompresses the real code into memory and then jumps to the original entry point. This lesson goes from the laziest way (one command) to what you do by hand when the packer resists.

![The UPX stub and the ESP trick](/assets/img/re/re-14-2-unpacking-upx-automatic-manual.svg)
_The stub runs pushad, unpacks, runs popad and jumps to the OEP, which the ESP trick catches._

## What a packer does

A packed file has two parts, which are compressed data (your original code, compressed so it can't be read) and a decompression stub placed at the entry point. When it runs, the stub expands the compressed part into memory, rebuilds the import table, then jumps to the OEP (Original Entry Point, the real entry point of the original program). From the OEP onward the original program runs.

To unpack, you catch the moment the stub has just finished expanding and is about to jump to the OEP, then dump the memory at that moment. That dump is the original code.

## The lazy way: upx -d

If the file was packed with standard UPX and nobody touched it, all you need is:

```
upx -d -o output.exe packed.exe
```

UPX recognizes its own format and expands it back. This is the best case, and it's why UPX alone isn't real protection, since anyone can remove it in a second.

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

Compressed to 39% of the size, and the unpacked version runs like the original.

## When upx -d refuses

Whoever packs the file knows about `upx -d`. The most common countermeasure is editing a few bytes in the header so UPX no longer recognizes its own file. UPX marks its blocks with a four-byte magic `UPX!`. Change these markers and `upx -d` gives up, but the stub still runs fine because it doesn't rely on that magic to decompress.

Same session as above, after changing all four `UPX!` markers to junk:

```
$ upx -d -o out hello_s.broken
upx: hello_s.broken: NotPackedException: not packed by UPX
Unpacked 0 files.
$ ./hello_s.broken UPX_s3cr3t
Correct!
```

UPX says "not packed by UPX", but the file still runs and prints "Correct!". Now you have to unpack it yourself. Even though the header was edited, the decompression mechanism is unchanged, so the manual technique still works.

## The UPX stub

The UPX stub on Windows starts by saving all the registers, does the decompression, then restores the registers before jumping to the OEP.

```asm
pushad                    ; save all registers on the stack
mov  esi, <source address> ; source: compressed data
mov  edi, <dest address>   ; destination: where the decompressed code goes
...                       ; decompression loop
popad                     ; restore all registers
jmp  <OEP>                ; tail jump: jump to the original entry point
```

Two details matter. `pushad` pushes 8 registers onto the stack at once, so right after `pushad` the stack pointer (ESP) points to the block it just saved. And at the end of the stub is `popad` and then a far `jmp`, called the tail jump, which goes straight to the OEP. These two give us two ways to find the OEP.

## Method 1: the ESP trick

This is the classic technique, fast and almost always works on UPX.

`pushad` writes 8 registers onto the stack, and `popad` will read back exactly that region. If you set a hardware breakpoint watching reads of the stack region `pushad` just wrote, it fires when `popad` runs, which is right before the tail jump to the OEP.

In x64dbg (x32dbg for 32-bit), open the file in the debugger and it stops at the entry point, the start of the stub. Step over the first `pushad` instruction (F8 once). Look at the ESP register, which just decreased after the pushad, then right-click ESP and choose "Follow in Dump". In the Dump window, select the first 4 bytes, right-click, Breakpoint, Hardware, Access. Press F9 (Run), and the debugger will stop when `popad` reads that region back.

Now you're right before the tail jump. Step a few instructions (F8) until you see a `jmp` to a far address, completely different from the stub region. That's the tail jump. Step over it and you're at the OEP.

At the OEP the code looks clean, with a normal function prologue (or for a real program the CRT startup, see [Lesson 3.1](/posts/re-3-1-hello-world-under-microscope-finding-real/)), no longer like a compression stub.

## Method 2: find the tail jump directly

If you have a trained eye, you can scroll to the end of the stub and look for the `popad` + far `jmp` pair. Set a breakpoint at that tail jump, run to it, then step over. This is quick but you need to know what the stub looks like. The ESP trick is safer for beginners.

## Method 3: breakpoint on the original section

Another approach relies on the fact that the section that holds the original code is empty at the start (because the code is still compressed). Set an "execute" memory breakpoint on that section. When the stub finishes decompressing and the CPU starts running code in the original section, the breakpoint fires, and you're close to the OEP. This helps when a complicated stub makes the ESP trick hard.

## At the OEP, dump

Reaching the OEP is only half the job. The decompressed code is in memory, but you need to save it as a runnable file. That's Scylla's job (usually shipped with x64dbg as a plugin). Open Scylla, pick the process you're debugging, and put the OEP you just found in the OEP field. Click "IAT Autosearch" then "Get Imports", and Scylla rebuilds the import table (the stub resolved the imports in memory, but a raw dump doesn't have the right import table yet). Then "Dump" saves the memory to a file, and "Fix Dump" patches the import table into the file you just dumped.

The details of rebuilding the IAT, why it's needed, and the pitfalls are in [Lesson 14.3](/posts/re-14-3-dumping-process-rebuilding-iat-scylla/). Without rebuilding the IAT, the dumped file opens in IDA for static reading but usually won't run.

## When UPX is no longer UPX

Many packers and malware use UPX as an outer layer and add their own protection on top, or modify the stub so heavily that the standard pushad/popad is gone. Then the ESP trick may miss. The principle still holds (run the stub, find the OEP, dump), but how you find the OEP has to be flexible. UPX is the intro exercise for an unpacking approach that applies to every packer.

## Key takeaways
Try `upx -d` first, since often it's done right away. If the header was edited (the `UPX!` magic changed), `upx -d` reports NotPackedException but the file still runs, so you have to unpack manually. The UPX stub has `pushad` at the start and `popad` + tail jump at the end, and those are the two landmarks for finding the OEP.

For the ESP trick, put a hardware breakpoint on the stack right after `pushad`, and it fires again when `popad` runs, near the tail jump. At the OEP, dump with Scylla and rebuild the IAT (Lesson 14.3). UPX is the intro exercise, and the same approach applies to every packer.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 14.2</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/14.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/14.2/src/hello.c" download><i class="fa-solid fa-download"></i>src/hello.c</a>
</div>
</div>

This lab has you take both UPX unpacking routes and understand why `upx -d` fails when the header has been edited. You need `upx` (on Linux `apt install upx-ucl`, or download the official build), `gcc` on Linux or MinGW on Windows, and for the manual part x64dbg or x32dbg with the Scylla plugin on Windows. The target is `hello.c`.

For the automatic route, build it. On Linux use `gcc -O2 -static -o hello hello.c`, and on Windows `x86_64-w64-mingw32-gcc -O2 -o hello.exe hello.c`. Then pack it with `upx --best -o hello.upx hello` and write down the compression ratio UPX prints. Open both files in Detect It Easy and compare the entropy and the import table (see Lesson 14.1). Unpack with `upx -d -o hello.unp hello.upx` and try `./hello.unp UPX_s3cr3t`.

Next, break the header so `upx -d` fails. Copy the packed file and change every `UPX!` magic to junk (the script is in the solution). Run `upx -d` on the broken file and watch the `NotPackedException` error, then confirm the broken file still runs because the stub is intact.

For the manual route on Windows, open the packed file in x32dbg or x64dbg and stop at the entry point, the start of the stub. Step over `pushad` with F8, right-click ESP and choose Follow in Dump, select the first 4 bytes in the Dump and set a hardware access breakpoint on them, then press F9 and stop when `popad` reads that region back. Step to the tail jump (the far `jmp`) and step over it, and you are at the OEP. To finish, open Scylla, set the OEP, then IAT Autosearch, Get Imports, Dump and Fix Dump, as covered in Lesson 14.3.

Three questions to think about. Why does changing the `UPX!` magic make `upx -d` fail while the file still runs? Which property of the `pushad` and `popad` pair does the ESP trick rely on? And why is dumping memory not enough, so that the IAT has to be rebuilt?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This writeup uses real numbers, run on Linux with UPX and gcc (a static ELF binary). On Windows the numbers differ but the mechanism is the same.

For the automatic pack and unpack, build static so the file is big enough for UPX to compress (a file that is too small fails with `NotCompressibleException`):

```
$ gcc -O2 -static -o hello_s hello.c
$ stat -c%s hello_s
900368

$ upx --best -o hello_s.upx hello_s
   900368 ->    352616   39.16%   linux/amd64   hello_s.upx

$ stat -c%s hello_s.upx
352616
```

It compresses to 39.16% of the original size. Unpacking it again:

```
$ upx -d -o hello_s.unp hello_s.upx
Unpacked 1 file.
$ ./hello_s.unp UPX_s3cr3t
Correct!
```

In DIE, the original is recognized as an ordinary gcc ELF with moderate entropy. The packed version has clearly higher entropy (compressed data is nearly random) and sections named like `UPX0` and `UPX1`, a clear sign of a packer.

To break the header, UPX marks its blocks with the four-byte magic `UPX!`. Change all of them:

```python
d = bytearray(open('hello_s.broken', 'rb').read())
n = 0; i = 0
while True:
    j = d.find(b'UPX!', i)
    if j < 0: break
    d[j:j+4] = b'XPU?'   # corrupt the magic
    i = j + 4; n += 1
open('hello_s.broken', 'wb').write(d)
print('corrupted', n, 'UPX! markers')   # -> corrupted 4 UPX! markers
```

The real result:

```
$ upx -d -o out hello_s.broken
upx: hello_s.broken: NotPackedException: not packed by UPX
Unpacked 0 files.

$ ./hello_s.broken UPX_s3cr3t
Correct!
```

This is the main point of the lab. `upx -d` relies on the `UPX!` magic to recognize and parse the file structure, so without the magic it refuses. But the decompression stub does not use that magic. It runs through the decompression from fixed offsets, so the file still runs and prints "Correct!". The real code is still there, and `upx -d` just won't extract it for you any more, so you have to do it yourself.

The manual unpack with the ESP trick is described for Windows with x64dbg, because that is where the ESP trick is most familiar. The steps are the ones from the lesson. Open the packed file and stop at the entry point (the start of the stub, usually showing `pushad`), then press F8 to step over `pushad`, after which ESP has just dropped by 32 (or 64) bytes. Right-click ESP in the Registers panel and choose Follow in Dump, select the first 4 bytes in the Dump, right-click, Breakpoint, Hardware, Access (DWORD), and press F9. The debugger stops when `popad` reads that stack region back, near the end of the stub. Press F8 a few times until you meet a `jmp` to a far address (the tail jump) and step over it. You are at the OEP, where the code is now a normal function prologue or CRT startup and no longer looks like the stub. It works because `pushad` writes 8 registers onto the stack and `popad` reads back exactly that region. A hardware breakpoint watching that stack region fires precisely at `popad`, right before the stub hands control back to the original code.

For the dump and IAT rebuild, at the OEP open Scylla, set the OEP, run IAT Autosearch, Get Imports, Dump, Fix Dump. The details and the reasons are in Lesson 14.3.

On the questions. Changing the magic makes `upx -d` fail but the file still runs because `upx -d` uses the `UPX!` magic to recognize and read the file structure, and without it cannot parse, while the decompression stub runs from the entry point with fixed logic, never looks the magic up, and so still unpacks and runs normally. The ESP trick relies on `pushad` saving all the registers into one stack region and `popad` restoring exactly that region. Reading it back happens once, at the end of the stub, so a hardware breakpoint on that region takes you to near the tail jump. And a raw dump isn't enough because at runtime the stub already resolved the imports and wrote the function addresses into the IAT in memory, but the raw dump has no valid Import Directory pointing at them, so when Windows loads the dumped file again the loader doesn't know how to fill in the IAT. Scylla rebuilds the Import Directory from the addresses present in memory so the dumped file can run.

The ESP trick and Scylla steps describe the standard Windows workflow with x64dbg, so run them on a Windows machine. The automatic pack and unpack and the header corruption work on Linux as well.

</details>

