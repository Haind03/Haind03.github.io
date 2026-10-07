---
title: "Lesson 14.5: Code virtualization"
image:
  path: /assets/img/covers/re-14-5-code-virtualization-highest-wall.webp
  alt: "Lesson 14.5: Code virtualization"
date: 2023-05-03 23:42:00 +0700
categories: ["Technique Reverse", "Part 14 · Packers and Obfuscation"]
tags: [reverse-engineering, packer, obfuscation]
render_with_liquid: false
---
By now you can unpack packers and strip ordinary obfuscation. Code virtualization is the hardest kind of software protection. When a function has been virtualized by VMProtect, Themida or Code Virtualizer, you open it in IDA and don't see any of the original logic in x86. There's only a strange loop that keeps running. This lesson doesn't teach you to fully solve a VMProtect binary, that takes weeks and several dedicated lessons. It explains how it works so you know which way to go.

## What virtualization is and how it differs

A packer hides code and expands it at runtime, and once you reach the OEP you have the original x86 back. Obfuscation makes code messy but it's still x86: read carefully, run it dynamically, simplify, and you get it. Virtualization is different.

It takes the original x86 code of a function and translates it into bytecode for a virtual machine (VM) that the protector invents. This VM isn't x86. It has its own instruction set, different for each protector and even for each build. The binary carries a block of bytecode (the original program translated into the VM's language), a dispatcher (a loop that reads each bytecode and calls the right piece of code), and a table of handlers (each handler executes one VM opcode, for example add, read memory, jump).

When execution reaches a virtualized function, it enters the VM entry and the dispatcher starts reading bytecode and running it. The original logic still executes, but through an interpretation layer. You no longer have the original x86 to read. You have to understand the whole virtual machine first and only then trace out the logic.

It's like having to read a book written in a language the author made up, where you first have to rebuild the dictionary yourself.

## The dispatcher loop

Every VM is built around a fetch, decode, execute loop:

```asm
vm_dispatcher:
    movzx  eax, byte ptr [vip]    ; fetch: read 1 opcode from the bytecode pointer (VIP)
    inc    vip                    ; advance the pointer
    jmp    [handler_table + rax*8] ; decode+execute: jump to the matching handler
    ; ... each handler does its job then jumps back to vm_dispatcher
```

A few terms are named after a real CPU. VIP (virtual instruction pointer) is the pointer to the VM bytecode being run, like rip on a real CPU. VSP (virtual stack pointer) exists because most protector VMs are stack-based, with their own virtual stack. The VM context is a memory region that plays the role of the virtual registers.

A loop that reads a byte, jumps through a table of pointers to dozens of similar small pieces of code, and keeps coming back to the start is almost certainly a VM dispatcher. That tells you you're facing virtualization.

## Why it's so hard

There's no original x86. What you read is the VM's handlers, not the program logic, and a simple `a + b` in the original code can become dozens of VM instructions spread across many handlers. Each build also gets a different VM. The opcodes aren't fixed and the handler table is shuffled, so there's no universal dictionary, and solving one binary doesn't carry over to another.

The handlers are obfuscated too. Each one is often covered with junk, MBA and opaque predicates (see [Lesson 14.4](/posts/re-14-4-code-level-obfuscation-when-program-flow/)), so it isn't easy to see what it does. And there are multiple layers, since Themida/WinLicense also add anti-debug, anti-VM and mutation on top.

That's why VMProtect and Themida are used on software that wants the strongest resistance to cracking, and why solving them is a research topic, not an evening's job.

## Four directions

Nobody reads a whole VM by eye. You pick the level of abstraction that suits the goal.

The first piece of advice is don't solve the VM, solve the problem. Often you don't need to understand the entire VM, you only need to know what the function takes and what it returns. If the virtualized function is the serial check, treat it as a black box. Feed it input and watch the output, or set a breakpoint where it returns its result and patch that result, instead of reversing the whole virtual machine. A lot of "cracking VMProtect" is just bypassing the VM part by attacking input and output.

The second direction is dynamic trace. Run the binary and record every instruction executed (using Pin, DynamoRIO, or the x64dbg trace, see [Lesson 17.7](/technique-reverse/)). The trace shows the real execution flow across the handlers, and you infer behavior from it without understanding each handler statically.

The third is rebuilding the VM dictionary (devirtualization). When you really have to understand it, you analyze the dispatcher, list the handler table, then map each VM opcode to a meaning (this handler pushes a constant, that one adds two values on the virtual stack). With the dictionary you translate the VM bytecode back into a readable form. Tools for this are VTIL (VMProtect devirtualization), IL frameworks like Miasm and Triton, and dedicated lifters for each protector.

The fourth is symbolic execution. Use angr or Triton (see [Lesson 18.3](/technique-reverse/)) to express the output as a formula of the input, then let a solver find an input that satisfies the condition. This ignores how the VM works and only cares about the mathematical relationship between input and output.

In general, pick the lowest level of abstraction that gets you to the goal. Understanding the whole VM is the most expensive job, so do it only when you really need to.

## Recognize it early

Don't read a virtualized function statically for hours before realizing it's a VM. Early signs: Detect It Easy reports VMProtect, Themida, WinLicense or Code Virtualizer, and there are odd section names like `.vmp0`, `.vmp1`, `.themida`, `.winlice`. Other signs are a function that jumps into another region and disappears into a huge dispatcher loop, lots of `push`/`pop` with accesses to a context through fixed registers, and an IDA decompiler that gives up or produces endless meaningless pseudocode.

When you see these, switch to black-box or dynamic thinking right away and don't try to read it statically.

## Lab

The goal is to recognize a binary (or a function) that has been virtualized and observe the dispatcher loop, instead of trying to read the original logic, which no longer exists as x86. You need Detect It Easy, IDA Free or Ghidra, and x64dbg. For a sample, the best option is a binary you build yourself and then protect with a trial version of VMProtect or Themida on your own machine. If you don't have that, use a public CTF sample labeled VMProtect (many Flare-On challenges over the years have a VM part).

First triage. Open the sample in DIE and note the protector name and any odd sections (`.vmp0`, `.themida` and so on). What's the entropy of the bytecode section? Then look for the VM entry. In x64dbg, set a breakpoint at a suspicious function (for example a license check), run to it, and watch the flow jump into a different region and then disappear into a loop.

Inside that loop, recognize the dispatcher by the fetch, decode, execute pattern: an instruction that reads a byte from a pointer (the VIP), advances the pointer, and then jumps indirectly through a table (`jmp [table + reg*8]`). That's the dispatcher. Look at the table of pointers the dispatcher jumps to and estimate how many handlers there are. Open a few handlers and see whether they're covered in junk or MBA.

Finally choose an attack. Suppose the goal is to get past the license check. Instead of translating the entire VM, find where the function returns its result (right or wrong) and think about how to patch it or read the result. Write two sentences: what black box approach would you try, and why shouldn't you translate the whole VM?

Two questions to think about. Why doesn't solving the VM of this binary help you solve another VMProtect binary? And when are you forced into real devirtualization, where the black box approach won't do?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This writeup describes the signs and the standard procedure you'll meet on a real VMProtect or Themida sample. The mechanism follows public documentation and common VM structures.

For triage, DIE often reports `VMProtect`, `Themida/WinLicense` or `Code Virtualizer` straight on the protector line. Sections you commonly see are `.vmp0` and `.vmp1` (VMProtect) and `.themida` and `.winlice` (Themida). The section holding the VM bytecode has high entropy because the data has been mixed up, though not necessarily close to 8.0 the way pure compression is. If DIE isn't sure, indirect signs are a poor import table, many executable sections and a size that's unusually large for the functionality.

For the VM entry, set a breakpoint at the suspicious function and run. The flow doesn't go linearly but jumps into a `.vmp` section, usually through a chain of `push` instructions that push a "handler key" followed by a `jmp` or `ret` into the VM. That's `vmenter`: it saves the real CPU context into the VM context and starts the dispatcher.

You recognize the core by the fetch, decode, execute pattern:

```asm
movzx  eax, byte ptr [rsi]   ; rsi plays the VIP, reads the VM opcode
add    rsi, 1                 ; advance the VIP
jmp    qword ptr [rbx+rax*8]  ; jump to the handler through the table
```

The registers playing VIP, VSP and context differ per build, but the shape "read a byte, advance the pointer, jump indirectly through a table, then come back" doesn't change. When you see it, you've confirmed it's a VM.

The table the dispatcher jumps to holds pointers to the handlers. VMProtect usually has a few dozen to over a hundred handlers (including duplicate variants to cause noise). Open a few and you see they're short, each doing one primitive thing (push a constant, add, xor, read or write memory), and are usually covered with extra junk, redundant instructions and MBA. Because the handlers are obfuscated, mapping the opcodes takes effort.

For the attack, the black box approach to try first is this: even a virtualized license check still has to return a right or wrong value to the code that calls it (the calling code is usually not virtualized). Set a breakpoint right after the VM returns, look at the return value and patch it, or patch the `jz` or `jnz` branch on the caller's side. You get past the check without understanding a single VM opcode. You shouldn't translate the whole VM because it takes dozens of hours, the result only works for this one binary, and it's usually unnecessary for the real goal.

On the questions, the work can't be reused because every build VMProtect generates a different opcode table and different handlers (it's polymorphic), so the dictionary you built for binary A is useless for binary B. You're forced into real devirtualization when the goal is to understand the hidden algorithm itself (for example pulling out the key computation formula to write a keygen, or extracting a proprietary encryption algorithm) and not just to get past a right or wrong check. Then the black box isn't enough and you have to rebuild the logic through devirtualization (VTIL, Triton, dedicated lifters) or symbolic execution.

</details>

## Key takeaways
Virtualization translates the original code into bytecode for a custom VM, so there's no original x86 left to read. It's built around a fetch, decode, execute dispatcher loop with a handler table and the virtual pointers VIP/VSP. It's hard because each build has a different VM, handlers are obfuscated, and layers stack up.

The directions are to first attack input and output as a black box, then dynamic trace, then devirtualization (VTIL/Miasm/Triton), then symbolic execution. Pick the lowest level of abstraction that's enough. Fully understanding the VM is the last option, not the default.
