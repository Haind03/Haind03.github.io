---
title: "Lesson 1.2: Process memory, the map of where everything happens"
date: 2023-08-30 15:12:00 +0700
categories: ["Technique Reverse", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
When you double-click an `.exe` file, the OS doesn't run it straight from disk. It creates a process, gives that process its own chunk of memory, loads the code in, and only then lets it run. Understanding the layout of that memory is understanding where your debugger will be walking around all day. Without it, you look at an address and can't tell whether it's code, a variable, or junk.

## Every process has its own world

The first thing that surprises people: two processes can both see the address `0x401000`, but they are two completely different physical memory cells. Each process lives in its own isolated virtual address space. Process A can't accidentally read the memory of process B.

The CPU and the OS work together on this: the addresses you see in IDA or a debugger are virtual addresses, and the OS quietly translates them to real physical addresses in RAM. As a reverse engineer you almost always work at the virtual address level, so just treat the process as if it has one continuous range of addresses all to itself.

The practical consequence: to read or write another process's memory (the foundation of every injection technique in Part 17), you have to ask the OS through special APIs like `ReadProcessMemory` and `WriteProcessMemory`. You can't just reach over directly.

## The memory map of a process

![Process memory map: code, data, heap growing up, stack growing down, libraries](/assets/img/technique-reverse/assets/phan-01/bo-nho-tien-trinh.svg)

The address space is split into several regions, each with its own job. From low to high, roughly:

```
low address
  +-------------------------+
  |  Code (.text)           |  machine instructions, read + execute only
  +-------------------------+
  |  Initialized data       |  .data: globals with an initial value
  |  (.data)                |
  +-------------------------+
  |  Uninitialized data     |  .bss: globals = 0
  |  (.bss)                 |
  +-------------------------+
  |  Heap  --->             |  dynamic allocation (malloc/new), grows upward
  |                         |
  |         ...             |
  |                         |
  |              <--- Stack |  locals, function calls, grows downward
  +-------------------------+
  |  Libraries (DLL/.so)    |  kernel32, libc... get loaded here
  +-------------------------+
high address
```

In x64dbg, open the Memory Map tab and you see exactly this map with real addresses, access rights (R/W/X), and which module owns which region. It's one of the windows you'll have open the most.

### The main sections

A PE or ELF file is split into sections, and when it's loaded into memory each section becomes a region. The .text section holds the machine instructions. Its permissions are usually read + execute, no write, so when you see an R-X region it's almost certainly code. (Self-modifying code needs write permission, and that's a suspicious sign, covered in Part 15.) The .data section holds globals that have an initial value, read + write. The .bss section holds globals initialized to 0. It takes no space on disk, the loader just allocates an empty region. The .rdata / .rodata sections hold read-only data like constants and strings, and your "Wrong password" string usually lives there.

## Stack, where functions live and die

The stack is the region you need to understand best, because almost every function uses it. It's a real stack: last in, first out (LIFO), where `push` puts things on and `pop` takes them off. On x86/x64 the stack grows down, so a push makes the top pointer (rsp) decrease. That sounds backwards, but just remember it. Every function call builds a block called a stack frame to hold the return address (pushed by `call`), the function's local variables, and sometimes parameters. When the function does `ret`, that frame is dropped and the stack shrinks back to where it was.

Since local variables sit on the stack, in assembly you see them as `[rbp-4]`, `[rbp-8]` (referenced backwards from the base pointer) or `[rsp+8]` (from the top of the stack). When IDA names things `var_4`, `var_8`, it's naming these locals. Lesson [1.4](/posts/re-1-4-x86-x64-assembly-2-stack-frames/) goes through the stack frame in detail.

The stack is also at the center of a whole class of security bugs (stack buffer overflow): writing past a local variable can overwrite the return address, and controlling the return address means controlling execution flow. That belongs to exploit development, but the root of it is in how the stack works.

## Heap, memory you ask for at runtime

When a program needs memory whose size is only known at runtime (how many bytes a file has, how long a string the user types), it asks the heap through `malloc`, `new`, `HeapAlloc`. It differs from the stack in a few ways. The programmer (or the runtime) manages it, so what you ask for you have to give back (`free`, `delete`), and forgetting to is a memory leak. Heap regions live a long time and aren't cleaned up when the function returns like stack variables. In RE, if you see a pointer pointing into the heap (usually its own address range in the Memory Map), you know it's dynamically allocated data, for example a struct or an array.

## Addresses aren't fixed: ASLR

It used to be that a program always loaded at the same address, for example `0x400000`. Now the OS turns on ASLR (Address Space Layout Randomization): each run, code and libraries are placed at different random addresses, to make things harder to guess for an attacker.

For you this means the address you see in IDA (a static address, based on the default base) will be different from the real address in the debugger at runtime. To match the two sides, you use offsets relative to the module base. x64dbg has a "follow in disassembler" button and a rebase feature to help sync them. Don't panic when the address in IDA is `0x401500` and in the debugger it's `0x7FF6xx401500`, the tail `401500` is the part to compare.

## Access rights, free clues

Each memory region has permissions: R (read), W (write), X (execute). Reading the permissions tells you the intent. R-X is normal code and RW- is normal data. RWX is both writable and executable. It's rare in clean software but very common in malware and packers, because they write decrypted code in there and then jump to run it. Seeing an RWX region in the Memory Map should make your ears prick up.

## Key takeaways
Every process has its own isolated virtual address space, and the addresses you see are virtual addresses. The layout is code (.text), data (.data/.bss/.rdata), heap (grows up), stack (grows down), and libraries. The stack is LIFO, grows down, and holds locals and the return address, with locals showing up as `[rbp-x]`. The heap is allocated dynamically at runtime and you have to free it yourself.

ASLR changes addresses every run, so compare the offset part and not absolute addresses. An RWX region is a red flag, often seen in packers and malware.
