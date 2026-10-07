---
title: "Lesson 17.3: Hooking on Windows, IAT hooks and inline hooks"
image:
  path: /assets/img/covers/re-17-3-hooking-windows-iat-hooks-inline-hooks.webp
  alt: "Lesson 17.3: Hooking on Windows, IAT hooks and inline hooks"
date: 2023-07-29 22:22:00 +0700
categories: ["Technique Reverse", "Part 17 · Patching, Hooking, Injection"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
A hook puts your code into a function call so the call runs through your code first. It sounds like a malware thing, but a lot of legitimate software uses it, since EDRs monitor behavior with hooks, Frida instruments with hooks, compatibility tools patch old APIs with hooks, and you'll hook to see parameters when analyzing. If you understand how hooking works you can use it and spot it when someone else does.

There are two families of hooks on Windows that you'll meet all the time, IAT hooks and inline hooks. They differ in where they sit.

## IAT hook: change the address in the import table

Recall [Lesson 1.7](/posts/re-1-7-pe-format-anatomy-windows-exe/). When a program calls `MessageBoxW`, it doesn't jump straight to the function in user32.dll. It reads the address from a slot in the Import Address Table (IAT), then `call`s through that slot. The loader fills in the real address when it loads the program.

An IAT hook uses exactly that. You find the IAT slot of the function you want to intercept and overwrite the real address with the address of your function. From then on every call through the IAT runs into your function. Your function does its thing (log, modify parameters) and then calls the saved real address.

```
Before hook:   call [IAT_MessageBoxW]  ->  user32!MessageBoxW
After hook:    call [IAT_MessageBoxW]  ->  my_hook  ->  (calls on to) user32!MessageBoxW
```

The upside is that it's clean, doesn't modify the target function's code, and is easy to remove. The big downside is that it only catches calls that go through the IAT. If the program gets the function address with `GetProcAddress` and calls it directly, or calls an internal function that isn't in the IAT, the IAT hook sees nothing. So IAT hooks suit coarse monitoring, not full coverage.

## Inline hook: overwrite the start of the function with a jump

An inline hook (also called a trampoline hook or detour) goes into the body of the target function itself, so it catches every call no matter which route it takes.

The idea is to overwrite the first few bytes of the target function with a `jmp` to your hook. That destroys those original bytes, and you can no longer call the real function. So before overwriting, you copy those first bytes into a separate area called a trampoline, then append a `jmp` back to the rest of the target function. To call the real function, you call the trampoline.

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

The annoying details are that x86 instructions have varying lengths, so you have to copy whole overwritten instructions and never cut in the middle of one (you need a small length disassembler). If those bytes contain an instruction that uses a relative address (`rip`-relative, `call rel32`), copying it raw to another place will be wrong, and you have to fix the offset. The libraries below handle all of this.

## Ready-made libraries

Nobody patches bytes by hand in practice. Microsoft Detours is the classic, with a compact API (`DetourAttach`/`DetourDetach`) that handles trampolines and relocation automatically. MinHook is small, open source, has good x86 and x64 support, and is very popular, with the API `MH_CreateHook` and `MH_EnableHook`. PolyHook2 is a modern C++ library with many hook types (inline, IAT, VMT for C++ vtables).

When you reverse a binary and see it linking or embedding one of these, it's almost certainly hooking something, and it's worth looking at what.

## EDRs and detection

Endpoint security software (EDR) often inline-hooks sensitive APIs in ntdll (like `NtAllocateVirtualMemory`, `NtWriteVirtualMemory`) to observe suspicious behavior. That's why, when you open ntdll in a debugger on a machine with an EDR, the start of many `Nt*` functions is a strange `jmp` instead of the standard prologue.

That's also how you detect a hook, tying back to [Lesson 15.7](/posts/re-15-7-anti-attach-anti-dump-anti-hook/). Compare the first bytes of the function in memory with the original bytes read from the DLL file on disk. A difference in the prologue, especially a `jmp` (`E9` or `FF 25`) right at the start, means the function has been hooked.

```
Clean function start:   mov [rsp+8], rcx   (48 89 4C 24 08 ...)
Hooked function start:  jmp <somewhere>    (E9 xx xx xx xx ...)
```

Sophisticated malware detects EDR hooks this way and then restores the original bytes itself (unhooking) to dodge monitoring. When analyzing, you use the same comparison to see which functions are being tampered with.

## Telling the two apart during analysis

If an IAT slot points to a region that doesn't belong to the original DLL (for example into a strange module or a dynamically allocated region), suspect an IAT hook. If the start of an API is an unusual `jmp`/`push+ret` instead of the familiar prologue, suspect an inline hook. Both lead to the hook function, so follow it to see what it does.

## Lab

The goal is to recognize a function that has been inline hooked, by reading its prologue in memory and comparing it with the original bytes on disk. It applies this lesson and connects back to [Lesson 15.7](/posts/re-15-7-anti-attach-anti-dump-anti-hook/). This lab is about observation and recognition, and you don't have to write a hook yourself. You need Windows and x64dbg, and any running process (notepad is enough), or a machine with an EDR or antivirus installed so you can see a real hook in ntdll.

Open x64dbg and attach to a process. Go to the Symbols tab, pick the `ntdll.dll` module and find the function `NtAllocateVirtualMemory`. Jump to the start of that function (double click) and read the first few prologue bytes. The standard prologue of an `Nt*` function on Win64 usually begins with `mov r10, rcx` (`4C 8B D1`) followed by `mov eax, <syscall number>`. If the machine has an EDR, the start of the function may instead be a `jmp` (`E9 ...` or `FF 25 ...`) in place of the standard prologue. That's an inline hook, so follow the jmp to see where it leads (usually a module of the EDR).

Then compare. Open the actual file `C:\Windows\System32\ntdll.dll` in another x64dbg window or in PE-bear, find the same function and read the original bytes on disk. Bytes in memory that differ from the bytes on disk at the prologue are the evidence of a hook. To finish, think about why an inline hook catches more calls than an IAT hook, and where malware that wants to dodge an EDR hook would restore the original bytes from.

If you have no EDR to observe, you can still practice the pattern recognition. Remember that a clean function opens with a valid prologue (building a stack frame, or for `Nt*` functions `mov r10, rcx`), while a hooked function opens with a jump instruction. In every later debugging session, glancing at the prologue of the sensitive APIs becomes a habit. As for the opcodes, `E9` is `jmp rel32` (5 bytes), `FF 25` is `jmp [rip+disp]` (6 bytes, an indirect jump through a 64-bit pointer), and `68 ... C3` is `push addr; ret`. All three are common ways of redirecting at the start of a hooked function. Try it yourself before opening the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

An unhooked `Nt*` function in ntdll on Win64 typically opens like this:

```
4C 8B D1              mov r10, rcx
B8 18 00 00 00        mov eax, 18h        ; syscall number (changes with the Windows version)
F6 04 25 ...          test byte ...       ; flag check
0F 05                 syscall
C3                    ret
```

The tell is `mov r10, rcx` (`4C 8B D1`) followed by `mov eax, <number>`, which is the standard shape of every syscall stub in ntdll. If you see exactly this, the function hasn't been tampered with.

On a machine with an EDR, the same function may become:

```
E9 2B 00 1A 00        jmp <address in the EDR module>
```

or

```
FF 25 00 00 00 00     jmp qword [rip]
XX XX XX XX XX XX XX XX   ; 64-bit pointer to the monitoring function
```

The first byte is no longer `4C 8B D1`. Following the jmp (press Enter on the jmp instruction in x64dbg) lands in a region belonging to the security product's DLL. That monitoring function logs the call and then usually continues to the real syscall through a trampoline.

To compare disk with memory, open `ntdll.dll` on disk in PE-bear, or in an x64dbg instance that loads the file statically. Compute the function's RVA and read the bytes there. On disk it's always the clean prologue (`4C 8B D1 ...`), while in the memory of a process hooked by an EDR it's a `jmp`. That difference is the evidence of an inline hook. PE-sieve and anti-malware tools scan for hooks the same way, since they diff the .text in RAM against the .text on disk.

Why does an inline hook catch more than an IAT hook? An IAT hook only changes a pointer in one module's import table, so it only intercepts calls that go through that table. Calls that get the address with `GetProcAddress`, make the syscall directly, or come from another module that doesn't use that IAT slip through. An inline hook modifies the function body itself, so every path that reaches the function has to run through the hook's jmp. In exchange, an inline hook is more complex (copying whole instructions, fixing relocations).

Where does malware restore the original bytes from? It rereads a clean `ntdll.dll` from disk (or maps a fresh copy from `\KnownDlls`, or keeps a pre-hook copy at hand), then overwrites the prologue in memory with the original bytes to erase the EDR's hook before making its call. This technique is called unhooking. It explains why an EDR sometimes doesn't see behavior even though it placed a hook.

One caveat is that the prologue bytes and syscall number above are the standard ntdll Win64 shape, and the specific syscall number differs between Windows versions. The x64dbg procedure is described the standard way, and the details differ from machine to machine.

</details>

## Key takeaways
A hook puts itself into a function call, and it's the basis of EDRs, Frida, compatibility tools, and analysis. An IAT hook changes a pointer in the Import Address Table, so it only catches calls through the IAT, which is clean but not comprehensive. An inline hook overwrites the start of a function with `jmp`, and a trampoline keeps the original bytes to call the real function, so it catches every call.

Inline hooks have to copy whole instructions and fix relative addresses, which is why people use Detours/MinHook/PolyHook2. To detect hooks, compare the prologue in memory with the original bytes on disk, and treat a `jmp` (E9 / FF 25) at the function start as suspicious.
