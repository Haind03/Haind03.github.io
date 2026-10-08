---
title: "Cheatsheet: shortcuts and quick reference"
image:
  path: /assets/img/covers/re-resources-cheatsheet-shortcuts-quick-reference.webp
  alt: "Cheatsheet: shortcuts and quick reference"
date: 2023-11-22 20:17:00 +0700
categories: ["Reverse Engineering", "Resources"]
tags: [reverse-engineering, resources]
render_with_liquid: false
---
> Keep this next to your screen while you work. The last part is a table of common x86 instructions, for when you're reading disassembly and forget one.

## IDA (Free/Pro)

| Key | Action |
|---|---|
| `F5` | Decompile the current function (Hex-Rays, Pro version) |
| `Space` | Switch between graph view / text view |
| `N` | Rename a function, variable, label |
| `X` | Show cross-references to the object under the cursor |
| `;` | Add a repeatable comment |
| `:` | Add a regular comment |
| `G` | Jump to an address |
| `D` | Cycle between data / code; change the data type |
| `C` | Force to code (convert to code) |
| `U` | Undefine |
| `Y` | Set/edit the type of a variable or function |
| `Alt+T` | Search text |
| `Esc` / `Ctrl+Enter` | Go back / forward |
| `Shift+F12` | Open the Strings window |

## Ghidra

| Key | Action |
|---|---|
| `Ctrl+E` or double-click | Open the decompiler for a function |
| `L` | Rename |
| `Ctrl+L` | Retype |
| `Ctrl+Shift+F` | Show references to |
| `G` | Go to address/label |
| `;` | Add a comment |
| `C` | Clear code bytes |
| `D` | Disassemble |
| `T` | Set data type |
| `Ctrl+Shift+E` | Equate (name a constant) |
| Window > Defined Strings | List of strings |

## x64dbg

| Key | Action |
|---|---|
| `F2` | Set/clear a breakpoint at the current line |
| `F7` | Step into (go inside the function) |
| `F8` | Step over (step past the function) |
| `F9` | Run / continue |
| `Ctrl+F9` | Execute till return (run until the function returns) |
| `F4` | Run to selection (run to the selected line) |
| `Space` | Edit the instruction in place (assemble) |
| `Ctrl+G` | Go to expression/address |
| `Ctrl+B` | Find a byte string (binary search) |
| Right-click > Search for > String references | Find string references |
| Right-click > Follow in Dump | Follow a pointer into the dump window |
| `Ctrl+P` | Patches (view/save the patches you made) |

Useful breakpoints can be set with commands in the Command box:
```
bp VirtualAlloc        ; stop when VirtualAlloc is called
bp CreateFileW
bp strcmp
```

## GDB + pwndbg/GEF

| Command | Action |
|---|---|
| `b *0x401000` / `b main` | Breakpoint at an address / function |
| `r` | Run |
| `c` | Continue |
| `si` / `ni` | Step into / step over (one instruction) |
| `info registers` | Show registers |
| `x/20i $pc` | Show 20 instructions at the instruction pointer |
| `x/16xg $rsp` | Show 16 8-byte values at the top of the stack |
| `p $rax` | Print the value of register rax |
| `set $rax=1` | Set a register value |
| `finish` | Run until the current function returns |
| `telescope $rsp` (pwndbg) | Show the stack with pointers dereferenced |
| `vmmap` (pwndbg/GEF) | The process memory map |

## dnSpy (.NET)

| Key | Action |
|---|---|
| `F5` | Run / debug |
| `F9` | Toggle breakpoint |
| `F10` / `F11` | Step over / step into |
| Right-click > Analyze | See who calls this method (used by) |
| Right-click > Edit Method (C#) | Edit the C# code and recompile |
| Right-click > Edit IL Instructions | Edit the IL directly |
| `Ctrl+Shift+K` | Search in the assembly |
| File > Save Module | Save the modified assembly |

## JADX-GUI (Android)

| Key | Action |
|---|---|
| Double-click | Jump to the definition |
| `x` | Find usage (xref) |
| `n` | Rename |
| `Ctrl+Shift+F` | Search text across the whole project |
| Right-click > Copy as Frida snippet | Generate a ready-made Frida hook snippet for the method |
| `Ctrl+Shift+S` | Save all (export source) |

## Common x86/x64 instruction reference

For when you're reading disassembly and forget what an instruction does.

### Data movement

| Instruction | Meaning |
|---|---|
| `mov dst, src` | Assign: dst = src |
| `lea dst, [expr]` | Load address, dst = the address of expr (no memory access). Often used for arithmetic |
| `push` / `pop` | Push onto / pop off the stack |
| `xchg a, b` | Swap a and b |
| `movzx` / `movsx` | Extend, zero-extend / sign-extend when copying into a larger register |

### Arithmetic and logic

| Instruction | Meaning |
|---|---|
| `add` / `sub` | Add / subtract |
| `inc` / `dec` | Increment / decrement by 1 |
| `imul` / `mul`, `idiv` / `div` | Multiply / divide (i = signed) |
| `and` / `or` / `xor` / `not` | Bit logic. `xor eax, eax` is the compact way to set eax = 0 |
| `shl` / `shr` / `sar` | Shift bits left/right (sar keeps the sign) |
| `test a, b` | AND but only sets flags, doesn't store the result. `test eax, eax` checks whether eax is 0 |
| `cmp a, b` | Compare (trial subtraction of a, b) and set flags, doesn't store the result |

### Branching (after cmp/test)

| Instruction | Jumps when |
|---|---|
| `jmp` | Always (unconditional) |
| `je` / `jz` | Equal / result is 0 |
| `jne` / `jnz` | Not equal / not 0 |
| `jg` / `jl` | Greater / less (signed) |
| `jge` / `jle` | Greater or equal / less or equal (signed) |
| `ja` / `jb` | Above / below (unsigned) |
| `js` / `jns` | Negative / non-negative |

A `cmp` or `test` right before a `j*` instruction is an `if` statement in the source. Once you see this pair you can read the branching logic.

### Calling functions

| Instruction | Meaning |
|---|---|
| `call func` | Call a function (push the return address then jump) |
| `ret` | Return to the caller |
| `leave` | Tear down the stack frame (equivalent to `mov rsp,rbp; pop rbp`) |
| `nop` | Does nothing. Often used to "delete" an instruction when patching |

### Common registers (x64)

| Register | Usual role |
|---|---|
| `rax` / `eax` | A function's return value lives here |
| `rcx, rdx, r8, r9` | First 4 parameters on Windows x64 (in this order) |
| `rdi, rsi, rdx, rcx, r8, r9` | First 6 parameters on Linux/macOS x64 (System V) |
| `rsp` | Stack top pointer |
| `rbp` | Stack frame base pointer |
| `rip` | Instruction pointer (the next instruction to run) |

If you know where parameters go and where the return value comes back, you can follow most function calls. Calling conventions are covered in [Lesson 1.4](/reverse-engineering/).
