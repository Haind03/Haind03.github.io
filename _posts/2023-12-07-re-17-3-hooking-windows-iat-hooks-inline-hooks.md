---
title: "Lesson 17.3: Hooking on Windows, IAT hooks and inline hooks"
date: 2023-12-07 09:49:00 +0700
categories: ["Technique Reverse", "Part 17 · Patching, Hooking, Injection"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
A hook means wedging yourself into a function call so the call runs through your code first. It sounds like a malware thing, but it's actually the foundation of a lot of legitimate stuff: EDRs monitor behavior with hooks, Frida instruments with hooks, compatibility tools patch old APIs with hooks, and you yourself will hook to see parameters when analyzing. Understanding how hooking works lets you both use it and spot it when someone else does.

There are two families of hooks on Windows that you'll meet all the time: IAT hooks and inline hooks. They differ in where they wedge in.

## IAT hook: change the address in the import table

Recall [Lesson 1.7](/posts/re-1-7-pe-format-anatomy-windows-exe/): when a program calls `MessageBoxW`, it doesn't jump straight to the function in user32.dll. It reads the address from a slot in the Import Address Table (IAT), then `call`s through that slot. The loader fills in the real address when it loads the program.

An IAT hook takes advantage of exactly that spot: find the IAT slot of the function you want to intercept and overwrite the real address with the address of your function. From then on every call through the IAT runs into your function. Your function does its thing (log, modify parameters) and then calls the saved real address.

```
Before hook:   call [IAT_MessageBoxW]  ->  user32!MessageBoxW
After hook:    call [IAT_MessageBoxW]  ->  my_hook  ->  (calls on to) user32!MessageBoxW
```

The upside is that it's clean, doesn't modify the target function's code, and is easy to remove. The deciding downside is that it only catches calls that go through the IAT. If the program gets the function address with `GetProcAddress` and calls it directly, or calls an internal function that isn't in the IAT, the IAT hook sees nothing. That's why IAT hooks suit coarse monitoring, not full coverage.

## Inline hook: overwrite the start of the function with a jump

An inline hook (also called a trampoline hook or detour) wedges into the body of the target function itself, so it catches every call no matter which route it takes.

The idea: overwrite the first few bytes of the target function with a `jmp` that jumps to your hook. But doing that destroys those original bytes, and you can no longer call the real function. So before overwriting, you copy those first bytes into a separate area called a trampoline, and then append a `jmp` back to the rest of the target function. To call the real function, you call the trampoline.

```
Original function (typical Win64 prologue):
    mov  [rsp+8], rcx      ; 4 bytes
    push rdi               ; ...

After the inline hook, the function start is replaced with:
    jmp  my_hook           ; usually E9 + 32-bit offset, or FF25 jmp [addr] on 64-bit

Trampoline (separate area) keeps the lost work and then returns:
    mov  [rsp+8], rcx      ; the original bytes that were copied out
    jmp  func+N            ; jump back to the original function after the overwritten part
```

The annoying details: x86 instructions have varying lengths, so you have to copy whole overwritten instructions and never cut in the middle of one (you need a small length disassembler). If those bytes contain an instruction that uses a relative address (`rip`-relative, `call rel32`), copying it raw to another place will be wrong, and you have to fix the offset. The libraries below handle all of this for you.

## Ready-made libraries

Nobody patches bytes by hand in practice. Microsoft Detours is the classic, from Microsoft itself, with a compact API (`DetourAttach`/`DetourDetach`) that handles trampolines and relocation automatically. MinHook is small, light, open source, and has good x86 and x64 support, and it's very popular in the community, with the API `MH_CreateHook` and `MH_EnableHook`. PolyHook2 is a modern C++ library with many hook types (inline, IAT, VMT for C++ vtables).

When you reverse a binary and see it linking or embedding one of these, it's almost certainly hooking something, and it's worth looking at what.

## EDRs and the detection angle

Endpoint security software (EDR) often inline-hooks sensitive APIs in ntdll (like `NtAllocateVirtualMemory`, `NtWriteVirtualMemory`) to observe suspicious behavior. That's why, when you open ntdll on a machine with an EDR in a debugger, the start of many `Nt*` functions is a strange `jmp` instead of the standard prologue.

And that's also exactly how to detect a hook, tying back to [Lesson 15.7](/posts/re-15-7-anti-attach-anti-dump-anti-hook/): compare the first bytes of the function in memory with the original bytes read from the DLL file on disk. A difference in the prologue, especially a `jmp` (`E9` or `FF 25`) right at the start, is the sign the function has been hooked.

```
Clean function start:   mov [rsp+8], rcx   (48 89 4C 24 08 ...)
Hooked function start:  jmp <somewhere>    (E9 xx xx xx xx ...)
```

Sophisticated malware detects EDR hooks this way and then restores the original bytes itself (unhooking) to dodge monitoring. When analyzing, you use the same comparison technique to know which functions are being tampered with.

## Telling the two apart quickly during analysis

If you see an IAT slot pointing to a region that doesn't belong to the original DLL (for example pointing into a strange module or a dynamically allocated region), suspect an IAT hook. If you see the start of an API as an unusual `jmp`/`push+ret` instead of the familiar prologue, suspect an inline hook. Both lead you to the hook function, so just follow it to see what it does.

## Lab

See [labs/17.3/](https://github.com/Haind03/Technique-Reverse/blob/main/labs/17.3): observe an inline hook in memory, recognize the `jmp` at the start of a function, and compare prologues to tell a hooked function from a clean one.

## Key takeaways
A hook wedges into a function call, and it's the foundation of EDRs, Frida, compatibility tools, and analysis. An IAT hook changes a pointer in the Import Address Table, so it only catches calls through the IAT: clean but not comprehensive. An inline hook overwrites the start of a function with `jmp`, and a trampoline keeps the original bytes to call the real function, so it catches every call.

Inline hooks have to copy whole instructions and fix relative addresses, which is why people use Detours/MinHook/PolyHook2. To detect hooks, compare the prologue in memory with the original bytes on disk, and treat a `jmp` (E9 / FF 25) at the function start as a red flag.
