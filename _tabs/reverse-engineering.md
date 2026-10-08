---
title: Reverse Engineering
icon: fas fa-microchip
order: 1
render_with_liquid: false
---

My reverse engineering notes, written as a series. It starts with the basics (assembly, PE/ELF, tools), then goes through each language, then packers, anti-debug, hooking and malware. 

For learning, CTFs, crackmes and software you own or are allowed to analyse.
{: .prompt-warning }

## Resources

| Post |
|---|
| [Cheatsheet: shortcuts and quick reference](/posts/re-resources-cheatsheet-shortcuts-quick-reference/) |
| [Reading list: the books behind these notes](/posts/re-resources-reading-list-windows-internals-books/) |
| [Reverse Engineering technique repository (map)](/posts/re-resources-reverse-engineering-technique-repository-map/) |
| [Reverse Engineering tool repository (roundup)](/posts/re-resources-reverse-engineering-tool-repository-roundup/) |
| [Study materials and places to practice](/posts/re-resources-study-materials-places-practice/) |

## The series

### Part 00 · Getting Started

| # | Lesson |
|---|---|
| 0.1 | [What is reverse engineering](/posts/re-0-1-reverse-engineering-why-its-not-as/) |
| 0.2 | [Legal and ethics](/posts/re-0-2-legal-ethics-part-everyone-wants-skip/) |
| 0.3 | [Setting up a safe lab](/posts/re-0-3-set-up-safe-lab-before-touching/) |
| 0.4 | [The reverse engineering workflow](/posts/re-0-4-reverse-engineering-workflow-not-get-lost/) |

### Part 01 · Computer Fundamentals for RE

| # | Lesson |
|---|---|
| 1.1 | [Reading a hexdump like text](/posts/re-1-1-reading-hexdump-like-text/) |
| 1.2 | [Process memory map](/posts/re-1-2-process-memory-map-where-everything-happens/) |
| 1.3 | [x86/x64 Assembly (1), registers and common instructions](/posts/re-1-3-x86-x64-assembly-1-registers-instructions/) |
| 1.4 | [x86/x64 assembly (2), stack frames and calling conventions](/posts/re-1-4-x86-x64-assembly-2-stack-frames/) |
| 1.5 | [x86/x64 Assembly (3), if, loops, switch, arrays and structs](/posts/re-1-5-x86-x64-assembly-3-recognizing-if/) |
| 1.6 | [From source code to binary](/posts/re-1-6-from-source-binary-why-same-code/) |
| 1.7 | [The PE format](/posts/re-1-7-pe-format-anatomy-windows-exe/) |
| 1.8 | [ELF and Mach-O](/posts/re-1-8-elf-mach-o-two-formats-outside/) |
| 1.9 | [ARM/ARM64 basics for people who know x86](/posts/re-1-9-arm-arm64-basics-people-who-already/) |
| 1.10 | [Windows internals (1), Win32 API and DLLs](/posts/re-1-10-windows-internals-1-win32-api-dlls/) |
| 1.11 | [Windows internals (2), PEB, TEB, handles and tokens](/posts/re-1-11-windows-internals-2-peb-teb-handles/) |
| 1.12 | [Windows internals for RE (3): SEH, TLS callbacks and syscalls](/posts/re-1-12-windows-internals-re-3-seh-tls/) |
| 1.13 | [Recognizing Windows APIs when reversing](/posts/re-1-13-recognizing-windows-apis-when-reversing-reading/) |

### Part 02 · The Toolkit

| # | Lesson |
|---|---|
| 2.1 | [Five-minute triage with DIE, strings and PE-bear](/posts/re-2-1-five-minute-triage-die-strings-pe/) |
| 2.2 | [IDA for beginners](/posts/re-2-2-ida-beginners-master-tool-before-binary/) |
| 2.3 | [Ghidra basics](/posts/re-2-3-ghidra-basics-free-knife-thats-worth/) |
| 2.4 | [Binary Ninja, Cutter and radare2](/posts/re-2-4-binary-ninja-cutter-radare2-when-ida/) |
| 2.5 | [x64dbg basics](/posts/re-2-5-x64dbg-reversers-dynamic-scalpel-windows/) |
| 2.6 | [GDB, pwndbg and WinDbg](/posts/re-2-6-gdb-pwndbg-windbg-debugging-from-command/) |
| 2.7 | [Hex editors and templates](/posts/re-2-7-hex-editors-templates-when-you-need/) |
| 2.8 | [System monitoring](/posts/re-2-8-system-monitoring-watching-behavior-without-opening/) |

### Part 03 · C

| # | Lesson |
|---|---|
| 3.1 | [Hello world and finding the real main](/posts/re-3-1-hello-world-under-microscope-finding-real/) |
| 3.2 | [Variables, pointers, arrays and strings in assembly](/posts/re-3-2-variables-pointers-arrays-strings-assembly/) |
| 3.3 | [Structs in assembly and how to recover them](/posts/re-3-3-structs-assembly-art-recovering-them/) |
| 3.4 | [FLIRT and recognizing library functions](/posts/re-3-4-flirt-recognizing-library-functions-dont-read/) |
| 3.5 | [Lab, solving your first C crackme](/posts/re-3-5-lab-solving-first-c-crackme-from/) |
| 3.6 | [Writing a keygen](/posts/re-3-6-writing-keygen-when-fishing-out-serial/) |

### Part 04 · C++

| # | Lesson |
|---|---|
| 4.1 | [C++ for reversers, name mangling and the this pointer](/posts/re-4-1-c-through-reversers-eyes-name-mangling/) |
| 4.2 | [Classes, vtables, inheritance and RTTI](/posts/re-4-2-classes-vtables-inheritance-rtti-rebuilding-class/) |
| 4.3 | [STL in binaries, std::string and std::vector](/posts/re-4-3-stl-binaries-reading-std-string-std/) |
| 4.4 | [Exceptions, templates and lambdas](/posts/re-4-4-exceptions-templates-lambdas-three-modern-c/) |
| 4.5 | [Plugins that rebuild C++ classes](/posts/re-4-5-plugins-that-rebuild-c-classes-let/) |
| 4.6 | [Lab, a C++ crackme with a vtable](/posts/re-4-6-lab-c-crackme-vtable-going-through/) |

### Part 05 · C# and .NET

| # | Lesson |
|---|---|
| 5.1 | [.NET internals](/posts/re-5-1-net-internals-why-decompiling-gives-back/) |
| 5.2 | [ILSpy and dnSpy](/posts/re-5-2-ilspy-dnspy-when-decompiling-gives-back/) |
| 5.3 | [Debugging .NET without source using dnSpy](/posts/re-5-3-debugging-net-without-source-using-dnspy/) |
| 5.4 | [Editing a .NET assembly and saving it](/posts/re-5-4-editing-net-assembly-saving-where-dnspy/) |
| 5.5 | [.NET obfuscators and how to strip them](/posts/re-5-5-net-obfuscators-strip-them/) |
| 5.6 | [Modern .NET publish modes](/posts/re-5-6-modern-net-when-decompile-gift-gets/) |
| 5.7 | [Combined lab, solving .NET crackmes](/posts/re-5-7-combined-lab-solving-net-crackmes-from/) |

### Part 06 · Java, Kotlin and Android

| # | Lesson |
|---|---|
| 6.1 | [JVM bytecode and Java decompilers](/posts/re-6-1-jvm-bytecode-java-decompiler-lineup/) |
| 6.2 | [Anatomy of an APK file](/posts/re-6-2-anatomy-apk-file/) |
| 6.3 | [JADX-GUI in depth](/posts/re-6-3-jadx-gui-depth-number-one-tool/) |
| 6.4 | [Smali and apktool, patching and repacking an Android app](/posts/re-6-4-smali-apktool-modifying-android-app-repacking/) |
| 6.5 | [Kotlin in bytecode](/posts/re-6-5-kotlin-bytecode-why-jadx-gives-you/) |
| 6.6 | [Frida on Android](/posts/re-6-6-frida-android-changing-app-behavior-while/) |
| 6.7 | [Native .so libraries and JNI](/posts/re-6-7-native-so-libraries-jni-where-logic/) |
| 6.8 | [Obfuscation and packers on Android](/posts/re-6-8-obfuscation-packers-android/) |
| 6.9 | [Big lab, solving OWASP UnCrackable Level 1 to 3](/posts/re-6-9-big-lab-solving-owasp-uncrackable-level/) |

### Part 07 · Python

| # | Lesson |
|---|---|
| 7.1 | [Python bytecode and .pyc files](/posts/re-7-1-python-bytecode-pyc-files/) |
| 7.2 | [pycdc and pycdas](/posts/re-7-2-pycdc-pycdas-two-scalpels-pyc-files/) |
| 7.3 | [Python decompilers other than pycdc](/posts/re-7-3-when-pycdc-gives-up-who-else/) |
| 7.4 | [Python packaged as an .exe](/posts/re-7-4-when-python-turns-into-exe-open/) |
| 7.5 | [Nuitka, Cython and PyArmor](/posts/re-7-5-when-python-no-longer-easy-swallow/) |
| 7.6 | [Lab, decompiling sample .pyc files with pycdc](/posts/re-7-6-lab-decompiling-sample-pyc-files-pycdc/) |

### Part 08 · Go

| # | Lesson |
|---|---|
| 8.1 | [What Go binaries look like](/posts/re-8-1-go-binaries-look-like-why-pclntab/) |
| 8.2 | [Recovering function names and types in Go binaries](/posts/re-8-2-recovering-function-names-types-go-binaries/) |
| 8.3 | [Go's string, slice, interface and goroutine in assembly](/posts/re-8-3-gos-string-slice-interface-goroutine-assembly/) |
| 8.4 | [Lab, solving a Go crackme](/posts/re-8-4-lab-solving-go-crackme-from-start/) |

### Part 09 · Rust

| # | Lesson |
|---|---|
| 9.1 | [What Rust binaries look like](/posts/re-9-1-rust-binaries-look-like-recognizing-them/) |
| 9.2 | [Rust's String, Vec, iterators and trait objects](/posts/re-9-2-recognizing-rusts-string-vec-iterators-trait/) |
| 9.3 | [Rust crackme lab](/posts/re-9-3-rust-crackme-lab-taking-apart-not/) |

### Part 10 · Legacy: Delphi, VB6, AutoIt, AHK

| # | Lesson |
|---|---|
| 10.1 | [Reversing Delphi and C++Builder programs](/posts/re-10-1-reversing-delphi-c-builder-programs/) |
| 10.2 | [Visual Basic 6](/posts/re-10-2-visual-basic-6-two-worlds-inside/) |
| 10.3 | [Scripts packed into exes](/posts/re-10-3-scripts-packed-into-exes-easier-open/) |

### Part 11 · JavaScript, Electron, WebAssembly

| # | Lesson |
|---|---|
| 11.1 | [Deobfuscating JavaScript](/posts/re-11-1-deobfuscating-javascript-peeling-layer-by-layer/) |
| 11.2 | [Dissecting an Electron app](/posts/re-11-2-dissecting-electron-app-from-app-asar/) |
| 11.3 | [WebAssembly](/posts/re-11-3-webassembly-reading-bytecode-that-runs-browser/) |

### Part 12 · Swift and Objective-C

| # | Lesson |
|---|---|
| 12.1 | [Objective-C and objc_msgSend](/posts/re-12-1-objective-c-where-every-call-goes/) |
| 12.2 | [Swift reverse engineering](/posts/re-12-2-swift-where-apple-makes-things-harder/) |
| 12.3 | [Reversing an iOS app from the IPA file](/posts/re-12-3-reversing-ios-app-from-ipa-file/) |

### Part 13 · Games: Unity, Unreal, Lua

| # | Lesson |
|---|---|
| 13.1 | [Unity with the Mono backend](/posts/re-13-1-unity-mono-backend-gift-beginners/) |
| 13.2 | [Unity IL2CPP](/posts/re-13-2-unity-il2cpp-when-assembly-csharp-disappears/) |
| 13.3 | [Reversing Unreal Engine games](/posts/re-13-3-reversing-unreal-engine-games/) |
| 13.4 | [Lua and LuaJIT bytecode](/posts/re-13-4-lua-luajit-bytecode-taking-apart-game/) |
| 13.5 | [Cheat Engine and runtime memory](/posts/re-13-5-cheat-engine-learning-runtime-memory-through/) |

### Part 14 · Packers and Obfuscation

| # | Lesson |
|---|---|
| 14.1 | [How packers work and how to spot one](/posts/re-14-1-packers-work-spot-one/) |
| 14.2 | [Unpacking UPX, automatic and manual](/posts/re-14-2-unpacking-upx-automatic-manual/) |
| 14.3 | [Dumping a process and rebuilding the IAT with Scylla](/posts/re-14-3-dumping-process-rebuilding-iat-scylla/) |
| 14.4 | [Code-level obfuscation](/posts/re-14-4-code-level-obfuscation-when-program-flow/) |
| 14.5 | [Code virtualization](/posts/re-14-5-code-virtualization-highest-wall/) |
| 14.6 | [Automatic deobfuscation](/posts/re-14-6-automatic-deobfuscation-let-machine-unpick-instead/) |

### Part 15 · Anti-Reversing and Bypasses

| # | Lesson |
|---|---|
| 15.1 | [Anti-debug via Windows APIs](/posts/re-15-1-anti-debug-via-windows-apis-group/) |
| 15.2 | [Anti-debug by reading the PEB](/posts/re-15-2-anti-debug-reading-peb-directly-when/) |
| 15.3 | [Anti-debug group 3, timing and traps](/posts/re-15-3-anti-debug-group-3-timing-traps/) |
| 15.4 | [Advanced anti-debug, self-debug and TLS callbacks](/posts/re-15-4-advanced-anti-debug-self-debug-tls/) |
| 15.5 | [Anti-VM and anti-sandbox](/posts/re-15-5-anti-vm-anti-sandbox-when-sample/) |
| 15.6 | [Anti-disassembly](/posts/re-15-6-anti-disassembly-when-disassembler-itself-gets/) |
| 15.7 | [Anti-attach, anti-dump and anti-hook](/posts/re-15-7-anti-attach-anti-dump-anti-hook/) |
| 15.8 | [Integrity checks and anti-tamper](/posts/re-15-8-integrity-checks-anti-tamper-when-program/) |
| 15.9 | [Bypassing anti-debug](/posts/re-15-9-bypassing-anti-debug-from-mouse-click/) |
| 15.10 | [Handling stacked anti-analysis layers](/posts/re-15-10-when-several-anti-layers-are-stacked/) |

### Part 16 · Crypto and Algorithms

| # | Lesson |
|---|---|
| 16.1 | [Identifying crypto algorithms by their constants](/posts/re-16-1-identifying-crypto-algorithms-by-their-constants/) |
| 16.2 | [XOR, RC4 and custom Base64](/posts/re-16-2-xor-rc4-custom-base64-three-youll/) |
| 16.3 | [Recognizing AES, DES, TEA, ChaCha and hash functions](/posts/re-16-3-recognizing-aes-des-tea-chacha-hash/) |
| 16.4 | [Rewriting the algorithm in Python and solving with Z3](/posts/re-16-4-rewriting-algorithm-python-letting-z3-solve/) |

### Part 17 · Patching, Hooking, Injection

| # | Lesson |
|---|---|
| 17.1 | [Patching binaries](/posts/re-17-1-patching-binaries-changing-one-byte-change/) |
| 17.2 | [Frida, inspecting and modifying a running program](/posts/re-17-2-frida-full-inspecting-modifying-program-while/) |
| 17.3 | [Hooking on Windows, IAT hooks and inline hooks](/posts/re-17-3-hooking-windows-iat-hooks-inline-hooks/) |
| 17.4 | [Recognizing DLL injection techniques](/posts/re-17-4-recognizing-dll-injection-techniques/) |
| 17.5 | [Recognizing process injection in malware](/posts/re-17-5-recognizing-process-injection-when-analyzing-malware/) |
| 17.6 | [LD_PRELOAD, ptrace and DYLD_INSERT_LIBRARIES](/posts/re-17-6-ld-preload-ptrace-dyld-insert-libraries/) |
| 17.7 | [Dynamic Binary Instrumentation](/posts/re-17-7-dynamic-binary-instrumentation-letting-binary-tell/) |

### Part 18 · Advanced Topics

| # | Lesson |
|---|---|
| 18.1 | [Scripting the decompiler](/posts/re-18-1-scripting-decompiler-let-machine-do-boring/) |
| 18.2 | [Emulation, running a piece of code on its own](/posts/re-18-2-emulation-running-piece-code-without-whole/) |
| 18.3 | [Symbolic execution](/posts/re-18-3-symbolic-execution-making-computer-solve-crackme/) |
| 18.4 | [Binary diffing](/posts/re-18-4-binary-diffing-finding-vulnerabilities-from-patch/) |
| 18.5 | [Reversing firmware and IoT devices](/posts/re-18-5-reversing-firmware-iot-devices/) |
| 18.6 | [Reversing Windows drivers and Linux kernel modules](/posts/re-18-6-reversing-ring-0-code-windows-drivers/) |
| 18.7 | [Reversing network protocols and proprietary file formats](/posts/re-18-7-reversing-network-protocols-proprietary-file-formats/) |
| 18.8 | [AI-assisted reverse engineering](/posts/re-18-8-ai-assisted-reverse-engineering-twice-as/) |

### Part 19 · Malware Analysis Basics

| # | Lesson |
|---|---|
| 19.1 | [A safe malware analysis workflow](/posts/re-19-1-safe-malware-analysis-workflow/) |
| 19.2 | [IOC, YARA, capa and Sigma](/posts/re-19-2-ioc-yara-capa-sigma-turning-sample/) |
| 19.3 | [Analyzing maldocs and loaders](/posts/re-19-3-analyzing-maldocs-loaders-where-attack-begins/) |
| 19.4 | [Extracting config and C2](/posts/re-19-4-extracting-config-c2-pulling-out-brain/) |

### Part 20 · Real-World Practice

| # | Lesson |
|---|---|
| 20.1 | [Hands-on with crackmes.one, level 1 to level 4](/posts/re-20-1-hands-crackmes-one-from-level-1/) |
| 20.2 | [Solving RE challenges in CTFs and writing a write-up](/posts/re-20-2-solving-re-challenges-ctfs-writing-decent/) |
| 20.3 | [Final project, reverse a program and write the report](/posts/re-20-3-final-project-fully-reverse-program-write/) |
