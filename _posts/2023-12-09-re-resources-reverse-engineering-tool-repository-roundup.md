---
title: "Reverse Engineering tool repository (roundup)"
date: 2023-12-09 22:22:00 +0700
categories: ["Technique Reverse", "Resources"]
tags: [reverse-engineering, resources]
render_with_liquid: false
---
> A catalog of the tools used throughout the series. In the Platform column, W is Windows, L is Linux, M is macOS and X is cross-platform. In the Price column, `free` means free/open source, `paid` means commercial, and `free+paid` means there's both a free and a pro version. The mark (priority) means install these first.

Table of contents: [1. Triage & file identification](#1-triage--file-identification), [2. General-purpose disassemblers / decompilers](#2-general-purpose-disassemblers--decompilers), [3. Debuggers](#3-debuggers), [4. Hex editors & binary viewers](#4-hex-editors--binary-viewers), [5. System & runtime monitoring](#5-system--runtime-monitoring), [6. .NET](#6-net), [7. Java / Android](#7-java--android), [8. Python](#8-python), [9. Go & Rust](#9-go--rust), [10. Delphi / VB / script-compiled](#10-delphi--vb--script-compiled), [11. JavaScript / Electron / WASM](#11-javascript--electron--wasm), [12. Apple: macOS / iOS](#12-apple-macos--ios), [13. Games](#13-games), [14. Unpacking & import rebuild](#14-unpacking--import-rebuild), [15. Anti-anti-debug & stealth](#15-anti-anti-debug--stealth), [16. Hook, injection, instrumentation](#16-hook-injection-instrumentation), [17. Emulation & symbolic execution](#17-emulation--symbolic-execution), [18. Crypto & pattern](#18-crypto--pattern), [19. Binary diffing](#19-binary-diffing), [20. Firmware & embedded](#20-firmware--embedded), [21. Malware analysis](#21-malware-analysis), [22. Prepackaged distros](#22-prepackaged-distros), [23. AI assistance for RE](#23-ai-assistance-for-re).

---

## 1. Triage & file identification

| Tool | Platform | Price | Use |
|---|---|---|---|
| **Detect It Easy (DIE)** (priority) | X | free | Identifies packers/compilers/protectors, entropy, signatures, YARA. *(Already in the repo: `die_win64_portable_3.08_x64`)* |
| `file` | L/M | free | Quick file type identification by magic |
| `strings` / **FLOSS** | X | free | Extracts strings; FLOSS (Mandiant) also decodes encrypted strings/stack strings |
| **PE-bear** | W | free | View & edit PE structure visually |
| **PEiD** / **Exeinfo PE** | W | free | Packer identification (old but still useful) |
| **CFF Explorer** (Explorer Suite) | W | free | View/edit PE, rebuild, dependencies |
| **TrID** | X | free | Identifies file type by statistical signatures |
| **capa** (Mandiant) | X | free | Infers a binary's *capabilities* (e.g. "encrypts with RC4", "injects into a process") |
| **Manalyze** | W/L | free | Static PE analysis + plugins |

## 2. General-purpose disassemblers / decompilers

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **Ghidra** (NSA) (priority) | X | free | The strongest free C decompiler, supports a huge number of architectures, scriptable (Java/Python) |
| **IDA Free / IDA Pro** (priority) | X | free+paid | Industry standard; Hex-Rays decompiler (Pro); IDAPython. Free is enough for learning x86/x64 |
| **Binary Ninja** | X | free+paid | Modern UI, multi-level IL (BNIL), good Python API; has a free cloud version |
| **radare2** / **rizin** | X | free | Powerful CLI, fully open; rizin is the cleaner fork |
| **Cutter** | X | free | GUI for rizin, integrates the Ghidra decompiler (jsdec) |
| **Hopper** | M/L | paid | Popular on macOS, has a decompiler |
| **RetDec** (Avast) | X | free | Command-line decompiler |
| **Relyze** | W | paid | Analysis & diffing |
| **objdump** / **llvm-objdump** | X | free | Quick disassembly from the command line |

## 3. Debuggers

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **x64dbg / x32dbg** (priority) | W | free | The main ring-3 debugger for Windows; many plugins (ScyllaHide, xAnalyzer...) |
| **WinDbg** (+ WinDbg Preview / TTD) | W | free | Kernel + user, Time Travel Debugging records and rewinds |
| **OllyDbg** / **Immunity Debugger** | W | free | Classic (32-bit); Immunity is for exploit dev |
| **GDB** + **pwndbg** / **GEF** / **peda** (priority) | L | free | Linux debugger; plugins add heap/stack/register views |
| **LLDB** | X | free | Default on macOS; iOS debugging |
| **radare2 / rizin** | X | free | Debugging integrated with the disassembler |
| **edb-debugger** | L | free | Olly-style GUI for Linux |

## 4. Hex editors & binary viewers

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **HxD** | W | free | Light, fast |
| **010 Editor** | X | paid | **Binary Templates** give very powerful file structure analysis |
| **ImHex** | X | free | Hex editor for reversers: pattern language, data inspector, disasm |
| **wxHexEditor** | X | free | Opens large files |

## 5. System & runtime monitoring

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **Process Monitor (Procmon)** (priority) | W | free | Real-time file/registry/process/network tracking |
| **Process Hacker / System Informer** (priority) | W | free | Process management, view memory/handles/threads, dump |
| **Process Explorer** | W | free | Process tree, DLLs, handles |
| **API Monitor** | W | free | Captures Win32 API calls with parameters |
| **Autoruns** | W | free | Autostart points (persistence) |
| **Wireshark** | X | free | Network packet analysis |
| **Fiddler** / **mitmproxy** / **Burp Suite** | X | free+paid | Intercept/modify HTTP(S) |
| **PE-sieve / HollowsHunter** | W | free | Detects code injection/hollowing in running processes |
| **ltrace / strace** | L | free | Trace library calls / syscalls |
| **frida-trace** | X | free | Trace any function (see section 16) |

## 6. .NET

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **dnSpy / dnSpyEx** (priority) | W | free | Decompile + **debug + edit** .NET. *(Already in the repo: `dnSpy-net-win64`)* |
| **ILSpy** (priority) | X | free | .NET decompiler; `ilspycmd` CLI version; AvaloniaILSpy is cross-platform. *(Already in the repo: `ILSpy_binaries_9.0.0...`)* |
| **dotPeek** (JetBrains) | W | free | Decompiler, supports symbol servers |
| **de4dot / de4dot-cex** | W | free | Removes .NET obfuscation (many protectors) |
| **.NET Reactor Slayer** | W | free | Unpacks .NET Reactor |
| **dnlib** | X | free | Library for reading/writing assemblies (automating patches) |
| **Mono.Cecil** | X | free | Another IL read/write library |
| **monodis** | X | free | Mono disassembler |

## 7. Java / Android

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **JADX / jadx-gui** (priority) | X | free | APK/DEX/JAR -> Java; basic deobfuscation, generates Frida snippets. *(Already in the repo: `jadx-gui-1.5.1-win`)* |
| **CFR** | X | free | Java decompiler, very good with new syntax |
| **Procyon** | X | free | Java decompiler |
| **Vineflower** (successor of Fernflower/Quiltflower) | X | free | High-quality decompiler |
| **Recaf** | X | free | View + **edit** Java bytecode, recompile |
| **Bytecode Viewer** | X | free | Combines several decompilers in one GUI |
| **apktool** | X | free | Unpack/repack APKs, smali |
| **smali/baksmali** | X | free | Assembler/disassembler for DEX |
| **dex2jar** | X | free | DEX -> JAR |
| **apksigner / uber-apk-signer** | X | free | Re-sign APKs |
| **Androguard** | X | free | APK analysis in Python |
| **frida / objection** | X | free | Runtime hooking (see section 16) |
| **MobSF** | X | free | Automated mobile analysis framework (static+dynamic) |

## 8. Python

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **pycdc / pycdas** (Decompyle++) (priority) | X | free | Decompile/disassemble .pyc without depending on the runtime. *(Already in the repo: `pycdc-master`)* |
| **uncompyle6 / decompyle3** | X | free | Decompilers for Python <=3.8 (decompyle3 up to ~3.9) |
| **PyLingual** | web | free | Modern .pyc decompiler (supports newer Python 3.x), runs on the web |
| **pyinstxtractor / pyinstxtractor-ng** | X | free | Extracts EXEs built by PyInstaller |
| **unpy2exe** | X | free | Extracts py2exe |
| **xdis** | X | free | Reads marshal/magic across many versions |
| **pydumpck** | X | free | Automates unpack + decompile |

## 9. Go & Rust

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **GoReSym** (Mandiant) | X | free | Recovers symbols, types, pclntab of Go binaries |
| **IDAGolangHelper / golang_loader_assist** | X | free | IDA scripts recovering Go function names |
| **GolangAnalyzerExtension** | X | free | Ghidra plugin for Go |
| **redress** | X | free | Go build information |
| **rustfilt** | X | free | Demangles Rust symbols |
| **Ghidra/IDA + rust demangler** | X | free | Demangles v0/legacy |

## 10. Delphi / VB / script-compiled

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **IDR (Interactive Delphi Reconstructor)** | W | free | Recovers Delphi/C++Builder |
| **DeDe** | W | free | Old Delphi |
| **VB Decompiler** | W | free+paid | VB6 P-Code & Native |
| **Exe2Aut / AutoIt-Ripper** | W/X | free | Extracts compiled AutoIt scripts |
| **NSIS extractor (7-Zip) / innounp / UniExtract2** | W | free | Extracts NSIS/Inno installers |

## 11. JavaScript / Electron / WASM

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **js-beautify / Prettier** | X | free | Prettify code |
| **de4js** | web | free | Removes common JS obfuscation |
| **webcrack** | X | free | Unminify + removes modern bundlers/obfuscators |
| **synchrony** (deobfuscator.io) | X | free | Removes javascript-obfuscator |
| **AST Explorer + Babel** | web/X | free | Write automatic transforms |
| **asar** | X | free | Extracts Electron's `app.asar` |
| **bytenode tools** | X | free | Handles V8 bytecode `.jsc` |
| **wabt** (wasm2wat, wasm2c, wasm-objdump) | X | free | WebAssembly toolkit |
| **Ghidra wasm plugin / wasmdec** | X | free | Reverse WASM |

## 12. Apple: macOS / iOS

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **Hopper** | M/L | paid | Very strong for Mach-O/ObjC/Swift |
| **class-dump / class-dump-swift** | M | free | Extracts ObjC/Swift declarations |
| **otool / nm / lipo / codesign** | M | free | System toolset |
| **swift demangle** | M | free | Demangles Swift names |
| **frida / objection** | X | free | iOS hooking |
| **Clutch / frida-ios-dump / bagbak** | iOS | free | Decrypts IPAs (jailbreak) |
| **Ghidra / IDA** + Mach-O loader | X | free+paid | Static analysis |

## 13. Games

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **Cheat Engine** (priority) | W | free | Scan/freeze values, pointers, code injection, AA scripts (offline games) |
| **Il2CppDumper** | X | free | Unity IL2CPP -> headers + metadata |
| **Cpp2IL** | X | free | Rebuilds IL2CPP (modern replacement) |
| **AssetStudio / AssetRipper** | W/X | free | Extract & rebuild Unity assets |
| **UABE / UABEA** | W | free | Edit Unity asset bundles |
| **UE4SS / FModel / UModel** | W | free | Unreal: scripting, view/extract assets, pak |
| **unluac / luadec / ljd / luajit-decompiler** | X | free | Lua / LuaJIT bytecode |
| **ReClass.NET** | W | free | Rebuilds structs in a running game's memory |

## 14. Unpacking & import rebuild

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **UPX** | X | free | `upx -d` for stock UPX files |
| **Scylla / Scylla x64** (priority) | W | free | Dump process + rebuild IAT (after reaching the OEP) |
| **PE-sieve** | W | free | Dumps unpacked/injected modules from a process |
| **MegaDumper** | W | free | Dumps .NET + native from memory |
| **ImpREC** | W | free | Rebuilds IAT (old) |
| **unipacker** | X | free | Automatic unpacking with Unicorn (some packers) |
| **CAPE sandbox** | L | free | Automatic unpacking + dumps malware configs |

## 15. Anti-anti-debug & stealth

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **ScyllaHide** (priority) | W | free | Hides the debugger in user-mode (x64dbg/IDA/Olly plugin) |
| **TitanHide** | W | free | Hides the debugger in kernel-mode (driver) |
| **HyperHide** | W | free | Hides at the hypervisor/DBVM level |
| **SharpOD** | W | free | Anti-anti-debug plugin for x64dbg |
| **strace/ltrace + seccomp** | L | free | Observe anti-debug on Linux (ptrace checks) |

## 16. Hook, injection, instrumentation

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **Frida** (priority) | X | free | Dynamic instrumentation: Interceptor, Stalker, JS/Python scripting. The foundation for many lessons |
| **objection** | X | free | Automation layer on top of Frida (mobile) |
| **frida-gum / frida-tools** | X | free | Library + CLI (frida-trace, frida-ps...) |
| **Microsoft Detours** | W | free | The classic API hooking library |
| **MinHook / PolyHook2** | W | free | Lightweight x86/x64 inline hooks |
| **EasyHook** | W | free | Hook + inject managed/native |
| **Intel Pin** | X | free | Powerful DBI for analysis/taint/coverage |
| **DynamoRIO** | X | free | Open-source DBI |
| **TinyInst** | X | free | Light instrumentation for fuzzing/coverage |
| **QBDI** (QuarksLab) | X | free | Embeddable DBI, nice API |

> Injection techniques (CreateRemoteThread, APC, manual mapping, process hollowing, reflective loading...) are covered in [Lessons 17.4 & 17.5](/technique-reverse/) from the angle of **mechanism + how to detect/defend**. LD_PRELOAD / DYLD_INSERT_LIBRARIES are built-in OS mechanisms, not tools.

## 17. Emulation & symbolic execution

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **Unicorn Engine** | X | free | CPU emulation (x86/ARM/MIPS...), runs individual pieces of code |
| **Qiling** | X | free | Framework emulating the whole OS/syscalls on top of Unicorn |
| **Speakeasy** (Mandiant) | X | free | Emulates Windows shellcode/malware |
| **angr** | X | free | Symbolic/concolic execution, CFG, constraint solving |
| **Triton** | X | free | DBA + symbolic execution + SMT |
| **Miasm** | X | free | IL, emulation, deobfuscation |
| **Z3** | X | free | SMT solver, solves serial/flag check conditions |
| **manticore / maat** | X | free | Alternative symbolic execution |

## 18. Crypto & pattern

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **findcrypt2 / FindCrypt-Ghidra** | X | free | Finds crypto algorithm constants |
| **signsrch** | X | free | Finds algorithm signatures |
| **capa** | X | free | Identifies capabilities including crypto |
| **PortEx / Kaitai Struct** | X | free | Describe & parse binary formats |
| **CyberChef** | web/X | free | The "Swiss army knife" for encode/decode/crypto |

## 19. Binary diffing

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **BinDiff** (Google) | X | free | Matches functions between 2 binaries (patch diffing) |
| **Diaphora** | X | free | Diff for IDA, powerful & open |
| **ghidriff** | X | free | Ghidra-based diff, outputs markdown |
| **radiff2** (radare2) | X | free | Diff from the command line |

## 20. Firmware & embedded

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **binwalk** | X | free | Scans & extracts components inside firmware |
| **unblob** | X | free | Recursively extracts many formats, modern |
| **firmware-mod-kit** | L | free | Unpack & rebuild firmware |
| **QEMU** | X | free | Emulates other architectures (ARM/MIPS) to run/debug firmware |
| **FACT** | L | free | Firmware analysis & comparison platform |
| **flashrom / chipsec** | X | free | Read flash / check platform firmware |
| **OpenOCD / JTAGulator** | X | free | Hardware debugging over JTAG/SWD |

## 21. Malware analysis

| Tool | Platform | Price | Notes |
|---|---|---|---|
| **YARA / yarGen** | X | free | Write & generate detection rules |
| **capa + capa-rules** | X | free | Capability profiling |
| **CAPE / CAPEv2** | L | free | Sandbox with automatic unpacking + config extraction |
| **Cuckoo3 / Drakvuf** | L | free | Dynamic sandboxes |
| **ANY.RUN / Triage / Joe Sandbox / Hybrid Analysis** | web | free+paid | Online sandboxes |
| **oletools (olevba, oleid)** | X | free | Office macro analysis |
| **pdf-parser / peepdf** | X | free | Malicious PDF analysis |
| **lnkparse / LECmd** | X | free | .lnk file analysis |
| **pestudio** | W | free | PE triage focused on suspicious indicators |
| **INetSim / FakeNet-NG** | L/W | free | Fake network services for dynamic analysis |

## 22. Prepackaged distros

| Set | Platform | Notes |
|---|---|---|
| **FLARE-VM** (Mandiant) | W | Script that turns a Windows VM into a full RE/malware machine with all the tools |
| **REMnux** | L | Linux distro for malware analysis |
| **Kali / Parrot** | L | Leans toward pentesting but has many RE tools |
| **Tsurugi Linux** | L | DFIR + RE |

## 23. AI assistance for RE

### 23a. LLM plugins in decompilers

| Tool | Platform | Notes |
|---|---|---|
| **Gepetto** | X | IDA plugin using an LLM to explain functions & rename variables |
| **aiDAPal / Sidekick (Binary Ninja)** | X | AI assistants inside the decompiler |
| **GhidrAssist / G-3PO / GhidraMCP-lite** | X | LLMs for Ghidra |
| **LLM4Decompile / DeGPT** | X | Research on improving decompiler output |

### 23b. MCP servers for RE (connecting decompilers/tools to Cursor, LLM agents)
MCP (Model Context Protocol) lets an LLM drive RE tools directly: read pseudocode, rename, set comments, run debugger commands... Configure it in your LLM client (Cline, Cursor, or any MCP-capable client) and then ask in natural language.

| MCP server | Connects to | Notes |
|---|---|---|
| **ida-pro-mcp** (mrexodia) | IDA Pro | The most popular for IDA: get decompiled output, xrefs, rename, comment, read/write through Hex-Rays |
| **IDA-MCP / ida_mcp (community)** | IDA Pro | Other variants, similar features |
| **GhidraMCP** (LaurieWired) | Ghidra | Control Ghidra over MCP: list functions, decompile, rename, data types |
| **ghidra-mcp (forks)** | Ghidra | Variants adding scripts/headless |
| **Binary Ninja MCP** | Binary Ninja | Use BNIL/HLIL through MCP |
| **radare2 MCP / r2mcp** | radare2/rizin | Run r2 commands, analyze conversationally |
| **x64dbg MCP** | x64dbg | Drive dynamic debugging (breakpoints, read memory, registers) |
| **frida-mcp** | Frida | Let an agent write & load Frida scripts, read hook results |
| **pwndbg / GDB MCP** | GDB | Linux debugging through conversation |
| **angr-mcp** | angr | Hand symbolic execution to an orchestrating agent |
| **capa-mcp / YARA MCP** | capa, YARA | Classify capabilities & scan rules on demand |
| **unblob / binwalk MCP** | firmware tools | Extract firmware conversationally |

> Safety note: MCP gives an LLM permission to run tools on your machine. When analyzing malware, run the client + MCP in an **isolated VM** (see [Lesson 0.3](/posts/re-0-3-set-up-safe-lab-before-touching/)), and don't let the agent execute samples on its own. A separate lesson on setting up MCP for RE is at [Lesson 18.8](/technique-reverse/).

---

### Suggested minimum kit to get started (Windows)
Detect It Easy, x64dbg, IDA Free or Ghidra, dnSpyEx, JADX, HxD or ImHex, Process Hacker plus Procmon, Python plus Frida, PE-bear, and CyberChef (offline).

All of them are free. When you need to go professional: IDA Pro + Hex-Rays, Binary Ninja, 010 Editor.
