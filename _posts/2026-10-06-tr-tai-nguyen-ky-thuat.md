---
title: "Reverse Engineering technique repository (map)"
date: 2026-10-06 14:02:00 +0700
categories: ["Technique Reverse", "Resources"]
tags: [reverse-engineering, resources]
render_with_liquid: false
---
> Every technique in the series, grouped by topic. Each technique lists *when to use it* and the *matching lesson*.
> Lesson notation: for example `15.5` = Part 15, Lesson 5 (see the [README](/technique-reverse/)).

## A. Static analysis
Don't run the file, just read.

| Technique | Use when | Lesson |
|---|---|---|
| Triage / fingerprinting | Always the first step: know the file type, compiler, packer | 2.1, 14.1 |
| Reading strings & stacked/encoded strings | Quick clues: URLs, paths, error messages, flags | 2.1 |
| Import/export analysis | Infer functionality from the APIs called | 1.7, 1.13 |
| Reading disassembly | Understand each machine instruction | 1.3,1.5 |
| Reading decompiler output | Quick understanding at the C/pseudocode level | 2.2, 2.3 |
| Recovering data types & structs | Make pseudocode readable | 3.3, 4.2 |
| Cross-reference (xref) | Trace where a function/variable/string is used | 2.2 |
| Identifying the calling convention | Read parameters correctly | 1.4 |
| Identifying control structures (if/loop/switch) | Translate assembly back to logic | 1.5 |
| FLIRT / library signatures | Skip library code, focus on the author's code | 3.4 |
| Control Flow Graph (CFG) | See the overall flow of a function | 2.2, 2.3 |

## B. Dynamic analysis
Run the file in a controlled environment.

| Technique | Use when | Lesson |
|---|---|---|
| Debugging (breakpoint, step, watch) | Observe real values at runtime | 2.5, 2.6 |
| API breakpoints | Stop at GetProcAddress, CreateFile... | 2.5, 15.9 |
| Memory breakpoint / hardware breakpoint | Catch accesses to a memory region | 2.5 |
| Memory dump | Get code that has been decrypted/unpacked | 14.2, 14.3 |
| Tracing (API/syscall/library) | Understand overall behavior | 2.8, 17.2 |
| System monitoring (Procmon...) | See file/registry/network effects | 2.8, 19.1 |
| Time Travel Debugging | Rewind to find where a value came from | 2.6 |
| Network monitoring | Understand the C2/API protocol | 2.8, 18.7 |

## C. By language / platform
| Platform | Specific techniques | Lesson |
|---|---|---|
| C/C++ native | Recovering structs, vtables, RTTI, name mangling | 3.x, 4.x |
| .NET | Decompile IL to C#, debug without source, patch IL | 5.x |
| Java/Android | DEX to Java, smali patching, re-signing APKs, hooking Java | 6.x |
| Python | .pyc to source, unpacking PyInstaller | 7.x |
| Go | Recovering symbols from pclntab | 8.x |
| Rust | Demangling, recognizing Result/Option patterns | 9.x |
| JS/Electron/WASM | Deobfuscating, unpacking asar, wasm2wat | 11.x |
| Apple | ObjC runtime, Swift demangling | 12.x |
| Games | IL2CPP dump, Cheat Engine, Lua decompiling | 13.x |

## D. Unpacking & deobfuscation
| Technique | Description | Lesson |
|---|---|---|
| Identifying packers & entropy | Tell packed from unpacked | 14.1 |
| Automatic unpacking (UPX -d, unipacker) | Fast when the packer is standard | 14.2 |
| Manual unpacking (finding the OEP) | For custom packers; follow the tail jump/ESP trick | 14.2 |
| Dump + rebuild IAT (Scylla) | Recreate a runnable file after unpacking | 14.3 |
| Removing string encryption | Decrypt statically encrypted strings | 14.4, 18.2 |
| Removing control-flow flattening | Recover the original flow | 14.4, 14.6 |
| Removing opaque predicates / MBA | Simplify junk expressions | 14.4, 18.3 |
| Dealing with virtualization (VMProtect/Themida) | Understand the bytecode handlers | 14.5 |
| Deobfuscating with emulation/symbolic execution | Automation | 14.6, 18.2, 18.3 |

## E. Anti-reverse (recognizing & getting past)
Presented from the angle of **understanding the mechanism to analyze and defend**.

| Software-side technique | How the reverser handles it | Lesson |
|---|---|---|
| Anti-debug via APIs (IsDebuggerPresent...) | Hook/patch to return fake values, ScyllaHide | 15.1, 15.9 |
| Anti-debug via PEB/NtGlobalFlag | Edit the flags in memory | 15.2 |
| Timing anti-debug (RDTSC) | Skip/adjust the delta, patch | 15.3 |
| Traps (INT3/INT2D/ICEBP), hardware BP detection | Recognize and avoid | 15.3 |
| Self-debug, debug object, thread hiding | HyperHide/TitanHide | 15.4, 15.9 |
| TLS callbacks running before main | Set a BP at the TLS callback | 15.4 |
| Anti-VM/sandbox | Make the VM look real, patch the checks | 15.5 |
| Anti-disassembly (junk/overlap/SMC) | Fix the format, run dynamically, force code | 15.6 |
| Anti-attach / anti-dump / anti-hook | Attach early, rebuild headers, compare prologues | 15.7 |
| Integrity check (CRC/checksum) | Disable the check instead of editing the checked code | 15.8 |

## F. Crypto & algorithms
| Technique | Description | Lesson |
|---|---|---|
| Identifying crypto constants | findcrypt/capa/signsrch | 16.1 |
| Identifying XOR/RC4/custom Base64 | The most common patterns in malware/crackmes | 16.2 |
| Identifying AES/DES/TEA/ChaCha/hashes | Through S-boxes, constants, round structure | 16.3 |
| Rewriting the algorithm in Python | To solve it yourself/write a keygen | 16.4 |
| Solving conditions with Z3/angr | When the check logic is complex | 16.4, 18.3 |

## G. Patching, hooking, injection, instrumentation
| Technique | Description | Lesson |
|---|---|---|
| Static patching (change jumps, NOP, code cave) | Permanently change behavior in the file | 17.1 |
| Runtime patching | Edit in memory while running | 17.1 |
| IAT hook | Replace a pointer in the import table | 17.3 |
| Inline/trampoline hook (Detours/MinHook) | Insert a jump at the function start | 17.3 |
| Frida Interceptor/Stalker | Flexible hooking & tracing on any platform | 17.2 |
| DLL injection (LoadLibrary+CreateRemoteThread, SetWindowsHookEx, AppInit) | Load code into another process | 17.4 |
| Manual mapping / reflective DLL | Load without going through the standard loader | 17.4 |
| Shellcode injection, APC, thread hijacking, process hollowing | Mechanisms & detection signs (PE-sieve, EDR) | 17.5 |
| LD_PRELOAD / ptrace / DYLD_INSERT_LIBRARIES | Equivalents on Linux/macOS | 17.6 |
| DBI (Pin/DynamoRIO/QBDI/TinyInst) | Taint, coverage, large-scale tracing | 17.7 |

## H. Advanced & automation
| Technique | Description | Lesson |
|---|---|---|
| Decompiler scripting (IDAPython/Ghidra/BN API) | Automate repetitive analysis | 18.1 |
| Emulation (Unicorn/Qiling/Speakeasy) | Run an isolated piece of code | 18.2 |
| Symbolic execution (angr/Triton) | Automatically find inputs satisfying conditions | 18.3 |
| Binary/patch diffing | Find vulnerabilities from patches, compare variants | 18.4 |
| Firmware/IoT (binwalk/QEMU) | Reverse embedded devices | 18.5 |
| Kernel driver / LKM | Reverse ring-0 code | 18.6 |
| Reversing protocols/file formats | Rebuild the spec from samples | 18.7 |
| AI assistance (LLM plugin/MCP) | Speed up naming and explanation | 18.8 |

## I. Malware analysis (defensive)
| Technique | Description | Lesson |
|---|---|---|
| Safe workflow + sandbox | Run samples without spreading infection | 19.1 |
| Writing IOC/YARA/capa/sigma | Detection & threat hunting | 19.2 |
| Maldoc analysis (macro/PDF/LNK) | The initial infection stage | 19.3 |
| Extracting config & C2 | Understand the attacker's infrastructure | 19.4 |

---

### Suggested skill path
1. **Basic static** (A) -> be able to read disassembly/pseudocode.
2. **Basic dynamic** (B) -> debug fluently with x64dbg/GDB.
3. **One managed language** (.NET or Java) to see "results" quickly.
4. **C/C++ native**, the backbone.
5. **Unpacking + anti-reverse** (D, E), where newcomers and good people split apart.
6. **Automation** (H), scripting, emulation, symbolic.
7. Specialize by direction: malware, exploit/vuln research, or games/mobile.
