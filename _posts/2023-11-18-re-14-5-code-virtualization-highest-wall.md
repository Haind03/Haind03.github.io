---
title: "Lesson 14.5: Code virtualization, the highest wall"
date: 2023-11-18 09:02:00 +0700
categories: ["Technique Reverse", "Part 14 · Packers and Obfuscation"]
tags: [reverse-engineering, packer, obfuscation]
render_with_liquid: false
---
By now you can unpack packers and strip ordinary obfuscation. Now comes the hardest thing in software protection: code virtualization. When a function gets "eaten" by VMProtect, Themida or Code Virtualizer, you open it in IDA and don't see a single line of the original logic in x86. There's only a strange loop that runs and runs. This lesson doesn't teach you to fully solve a VMProtect binary, that takes a month and several dedicated lessons, but teaches you how it works so you know which way to go.

## What virtualization is, and why it differs from everything before

A packer hides code and expands it at runtime: once you reach the OEP you have the original x86 back. Obfuscation makes code messy but it's still x86: read carefully, run it dynamically, simplify, and you get it. Virtualization is fundamentally different.

It takes the original x86 code of a function and translates it into bytecode for a virtual machine (VM) that the protector invents itself. This VM isn't x86 but its own instruction set, a different one for each protector, even for each build. The binary carries a block of bytecode (the original program translated into the VM's language), a dispatcher (a loop that reads each bytecode and calls the right piece of handling code), and a table of handlers (each handler executes one VM opcode, for example add, read memory, jump).

When execution reaches a virtualized function, the flow enters the VM entry, the dispatcher starts reading bytecode and running it. The original logic is still executed, but through an interpretation layer. You no longer have the original x86 to read, you have to understand the whole virtual machine first and only then trace out the logic.

A simple picture: instead of reading a book in Vietnamese, you now have to read a book written in an artificial language the author invented, and first you have to rebuild that language's dictionary yourself.

## The dispatcher loop, the sign of a VM

The heart of every VM is the fetch, decode, execute loop:

```asm
vm_dispatcher:
    movzx  eax, byte ptr [vip]    ; fetch: read 1 opcode from the bytecode pointer (VIP)
    inc    vip                    ; advance the pointer
    jmp    [handler_table + rax*8] ; decode+execute: jump to the matching handler
    ; ... each handler does its job then jumps back to vm_dispatcher
```

A few concepts are named after a real CPU. VIP (virtual instruction pointer) is the pointer to the VM bytecode being run, like rip on a real CPU. VSP (virtual stack pointer) exists because most protector VMs are stack-based, with their own virtual stack. The VM context is a memory region playing the role of the virtual registers.

When you see a loop that reads a byte, then jumps through a table of pointers to dozens of similar small pieces of code, and keeps coming back to the start, it's almost certainly a VM's dispatcher. That's the sign you're facing virtualization.

## Why it's so hard

There's no original x86. What you read is the VM's handlers, not the program logic, and a simple `a + b` in the original code can become dozens of VM instructions spread across many handlers. Each build also gets a different VM. The opcodes aren't fixed and the handler table is shuffled, so there's no "universal dictionary", and solving one binary doesn't carry over to another.

The handlers are obfuscated too: each one is often covered with junk, MBA, opaque predicates (see [Lesson 14.4](/posts/re-14-4-code-level-obfuscation-when-program-flow/)), so it isn't easy to see what it does. And there are multiple layers, since Themida/WinLicense also stack anti-debug, anti-VM, and mutation on top.

This is why VMProtect and Themida are used for the software that wants the strongest crack resistance, and also why solving them is a research topic, not an evening's job.

## The mindset, four directions

Nobody reads a whole VM by eye. People pick the level of abstraction that suits the goal.

The most important advice is don't solve the VM, solve the problem. Often you don't need to understand the entire VM, you only need to know what the function takes and what it returns. If the virtualized function is the serial check, treat it as a black box: feed it input and watch the output, or set a breakpoint where it returns its result and patch that result, instead of reversing the whole virtual machine. A lot of "cracking VMProtect" is really just bypassing the VM part by attacking input/output.

The second direction is dynamic trace. Run the binary and record every instruction executed (using Pin, DynamoRIO, or the x64dbg trace, see [Lesson 17.7](https://github.com/Haind03/Technique-Reverse/tree/main/phan-17-patch-hook-frida)). The trace shows the real execution flow across the handlers, from which you infer behavior without statically understanding each handler.

The third is rebuilding the VM dictionary (devirtualization). When you have to understand it deeply, you analyze the dispatcher, list the handler table, then map each VM opcode to a meaning (this handler pushes a constant, that one adds two values on the virtual stack). With the dictionary, you translate the VM bytecode back into a readable form. Tools that help in this direction are VTIL (VMProtect devirtualization), IL frameworks like Miasm and Triton, and dedicated lifters for each protector.

The fourth is symbolic execution. Use angr or Triton (see [Lesson 18.3](https://github.com/Haind03/Technique-Reverse/tree/main/phan-18-nang-cao)) to express the output in terms of the input as a formula, then let a solver find an input that satisfies the condition. This ignores how the VM works and only cares about the mathematical relationship between input and output.

The general principle: pick the lowest level of abstraction that's enough to reach the goal. Understanding the whole VM is the most expensive job, do it only when you really need to.

## Recognize it early to save effort

Don't sit reading a virtualized function statically for hours before realizing it's a VM. The early signs are Detect It Easy reporting VMProtect, Themida, WinLicense or Code Virtualizer, and odd section names like `.vmp0`, `.vmp1`, `.themida`, `.winlice`. Others are a function that jumps into another region and disappears into a huge dispatcher loop, lots of `push`/`pop` with accesses to a "context" through fixed registers, and an IDA decompiler that gives up or produces endless meaningless pseudocode.

When you see these signs, switch right away to black-box or dynamic thinking, don't try to read it statically.

## Key takeaways
Virtualization translates the original code into bytecode for a custom VM, so there's no original x86 left to read. The heart is the fetch, decode, execute dispatcher loop with a handler table and the virtual pointers VIP/VSP. It's hardest because each build has a different VM, handlers are obfuscated, and layers stack up.

The directions are to first prefer attacking input/output as a black box, then dynamic trace, then devirtualization (VTIL/Miasm/Triton), then symbolic execution. Pick the lowest level of abstraction that's enough. Fully understanding the VM is the last option, not the default.
