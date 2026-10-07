---
title: Technique Reverse
icon: fas fa-microchip
order: 1
render_with_liquid: false
---

Ghi chép reverse của mình, bắt đầu từ mấy note anti-debug hồi 2023 rồi viết lại thành một series đầy đủ: nền tảng, từng ngôn ngữ, packer, anti-reverse, Frida, malware.

Code lab và binary mẫu để ở repo [Haind03/Technique-Reverse](https://github.com/Haind03/Technique-Reverse).

Nội dung chỉ để học, chơi CTF, crackme hoặc phân tích phần mềm của chính mình.
{: .prompt-warning }

## Ghi chép 2023

| Bài |
|---|
| [Anti Debug](/posts/re-anti-debug/) |
| [Anti Disassembly](/posts/re-anti-disassembly/) |
| [Chall 18 - Sample 1](/posts/re-chall-18-sample-1/) |
| [Chall 18 - Sample 1 (API)](/posts/re-chall-18-sample-1-api/) |

## Tài nguyên

- [Kho công cụ](/posts/tr-tai-nguyen-cong-cu/)
- [Bản đồ kỹ thuật](/posts/tr-tai-nguyen-ky-thuat/)
- [Tài liệu học và chỗ luyện](/posts/tr-tai-nguyen-tai-lieu-hoc/)
- [Cheatsheet phím tắt, opcode](/posts/tr-tai-nguyen-cheatsheet/)

## Giáo trình


### Chặng 1: Nền tảng

#### Phần 0 · Nhập môn
| # | Bài |
|---|---|
| 0.1 | [Reverse Engineering là gì? Bản đồ toàn cảnh](/posts/tr-0-1-reverse-engineering-la-gi/) |
| 0.2 | [Pháp lý & đạo đức khi làm RE](/posts/tr-0-2-phap-ly-dao-duc/) |
| 0.3 | [Dựng lab an toàn: VM, snapshot, mạng cô lập, FLARE-VM/REMnux](/posts/tr-0-3-dung-lab-an-toan/) |
| 0.4 | [Quy trình RE chuẩn: Triage - Static - Dynamic - Ghi chép](/posts/tr-0-4-quy-trinh-reverse/) |

#### Phần 1 · Nền tảng máy tính cho RE
| # | Bài |
|---|---|
| 1.1 | [Hệ số, hex, endianness, bitwise: đọc hexdump như đọc chữ](/posts/tr-1-1-hex-endian-bitwise/) |
| 1.2 | [Bộ nhớ tiến trình: stack, heap, section, virtual memory](/posts/tr-1-2-bo-nho-tien-trinh/) |
| 1.3 | [Assembly x86/x64 (1): thanh ghi, mov/lea/add/cmp/jmp](/posts/tr-1-3-assembly-1-thanh-ghi-lenh-co-ban/) |
| 1.4 | [Assembly x86/x64 (2): stack frame, call/ret, calling convention (cdecl, stdcall, fastcall, SysV, Win64)](/posts/tr-1-4-assembly-2-stack-calling-convention/) |
| 1.5 | [Assembly x86/x64 (3): nhận diện if/else, loop, switch-case, mảng, struct](/posts/tr-1-5-assembly-3-cau-truc-dieu-khien/) |
| 1.6 | [Từ mã nguồn đến binary: compiler, linker, loader, tối ưu hóa -O0 vs -O2](/posts/tr-1-6-tu-source-den-binary/) |
| 1.7 | [Định dạng PE (Windows): header, section, import/export, relocation, TLS](/posts/tr-1-7-dinh-dang-pe/) |
| 1.8 | [Định dạng ELF (Linux) và Mach-O (macOS)](/posts/tr-1-8-elf-va-mach-o/) |
| 1.9 | [ARM/ARM64 cơ bản (cho Android/iOS/IoT)](/posts/tr-1-9-arm-arm64-co-ban/) |
| 1.10 | [Windows internals cho RE (1): Win32 API, DLL, kernel32/ntdll, ordinals, API set](/posts/tr-1-10-windows-internals-1-win32-api-dll/) |
| 1.11 | [Windows internals cho RE (2): PEB/TEB, handle, object, token, cấu trúc tiến trình](/posts/tr-1-11-windows-internals-2-peb-teb-handle-token/) |
| 1.12 | [Windows internals cho RE (3): SEH/VEH, TLS callback, syscall & chuyển Nt->Zw, Native API](/posts/tr-1-12-windows-internals-3-seh-tls-syscall/) |
| 1.13 | [Nhận diện Windows API trong IDA/x64dbg: tra cứu MSDN, đọc tham số trên stack, Apiscout](/posts/tr-1-13-nhan-dien-windows-api/) |

#### Phần 2 · Làm quen bộ công cụ
| # | Bài |
|---|---|
| 2.1 | [Triage file với Detect It Easy (DIE), file, strings, PE-bear](/posts/tr-2-1-triage-die-strings-pebear/) |
| 2.2 | [IDA Free/Pro: giao diện, navigation, rename, xref, comment](/posts/tr-2-2-ida-co-ban/) |
| 2.3 | [Ghidra: project, CodeBrowser, decompiler, data type manager](/posts/tr-2-3-ghidra-co-ban/) |
| 2.4 | [Binary Ninja / Cutter (rizin) / radare2, lựa chọn thay thế](/posts/tr-2-4-binaryninja-cutter-radare2/) |
| 2.5 | [x64dbg: breakpoint, step, memory map, patch, plugin](/posts/tr-2-5-x64dbg/) |
| 2.6 | [GDB + pwndbg/GEF, WinDbg cơ bản](/posts/tr-2-6-gdb-pwndbg-windbg/) |
| 2.7 | [Hex editor (HxD, 010 Editor, ImHex) và template](/posts/tr-2-7-hex-editor-template/) |
| 2.8 | [Giám sát hệ thống: Procmon, Process Hacker/System Informer, API Monitor, Wireshark](/posts/tr-2-8-giam-sat-he-thong/) |

### Chặng 2: Reverse theo ngôn ngữ

#### Phần 3 · C: ngôn ngữ gốc của mọi thứ
| # | Bài |
|---|---|
| 3.1 | [Hello world dưới kính hiển vi: main, CRT startup, tìm main thật](/posts/tr-3-1-hello-world-tim-main-that/) |
| 3.2 | [Biến, con trỏ, mảng, chuỗi trong assembly](/posts/tr-3-2-bien-con-tro-mang-chuoi/) |
| 3.3 | [Struct & khôi phục struct trong IDA/Ghidra](/posts/tr-3-3-struct-khoi-phuc-struct/) |
| 3.4 | [Hàm thư viện: FLIRT/signature, nhận diện libc tĩnh](/posts/tr-3-4-flirt-nhan-dien-thu-vien/) |
| 3.5 | [Lab: crackme C đầu tiên, tìm password (static + dynamic)](/posts/tr-3-5-lab-crackme-c-dau-tien/) |
| 3.6 | [Lab: viết keygen cho thuật toán serial đơn giản](/posts/tr-3-6-lab-viet-keygen/) |

#### Phần 4 · C++
| # | Bài |
|---|---|
| 4.1 | [Name mangling, this pointer, method call](/posts/tr-4-1-name-mangling-this-method-call/) |
| 4.2 | [Class, vtable, kế thừa, RTTI, khôi phục cây class](/posts/tr-4-2-class-vtable-ke-thua-rtti/) |
| 4.3 | [STL trong binary: std::string, vector, map](/posts/tr-4-3-stl-trong-binary/) |
| 4.4 | [Exception handling (SEH/C++ EH), template, lambda](/posts/tr-4-4-exception-template-lambda/) |
| 4.5 | [Plugin hỗ trợ: ClassInformer, HexRaysPyTools, Ghidra C++ class analyzer](/posts/tr-4-5-plugin-ho-tro-cpp/) |
| 4.6 | [Lab: crackme C++ có vtable](/posts/tr-4-6-lab-crackme-cpp-vtable/) |

#### Phần 5 · C# / .NET (dnSpy, ILSpy)
| # | Bài |
|---|---|
| 5.1 | [.NET bên trong: CLR, IL, metadata, assembly, vì sao decompile gần như ra source](/posts/tr-5-1-net-ben-trong-clr-il-metadata/) |
| 5.2 | [ILSpy & dnSpy: decompile, tìm kiếm, analyze](/posts/tr-5-2-ilspy-dnspy-decompile/) |
| 5.3 | [Debug .NET không cần source với dnSpy](/posts/tr-5-3-debug-net-khong-source-dnspy/) |
| 5.4 | [Sửa IL/C# và lưu lại assembly (patching)](/posts/tr-5-4-patch-il-csharp-dnspy/) |
| 5.5 | [Obfuscator .NET: ConfuserEx, .NET Reactor, Eazfuscator, de4dot](/posts/tr-5-5-obfuscator-net-de4dot/) |
| 5.6 | [.NET Core/5+: single-file bundle, ReadyToRun, NativeAOT](/posts/tr-5-6-net-core-singlefile-r2r-nativeaot/) |
| 5.7 | [Lab: crackme .NET từ dễ đến obfuscated](/posts/tr-5-7-lab-crackme-net/) |

#### Phần 6 · Java / Kotlin / Android (JADX)
| # | Bài |
|---|---|
| 6.1 | [JVM bytecode & .class; decompiler Java: JADX, CFR, Procyon, Vineflower, Recaf](/posts/tr-6-1-jvm-bytecode-decompiler-java/) |
| 6.2 | [Cấu trúc APK: AndroidManifest, DEX, resources, native lib](/posts/tr-6-2-cau-truc-apk/) |
| 6.3 | [JADX-GUI chuyên sâu: tìm kiếm, rename, deobfuscation, Frida snippet](/posts/tr-6-3-jadx-gui-chuyen-sau/) |
| 6.4 | [Smali & apktool: sửa app và đóng gói/ký lại](/posts/tr-6-4-smali-apktool-repack/) |
| 6.5 | [Kotlin trong bytecode: coroutine, data class, metadata](/posts/tr-6-5-kotlin-trong-bytecode/) |
| 6.6 | [Frida trên Android: hook Java method, bypass root detection/SSL pinning](/posts/tr-6-6-frida-android-hook/) |
| 6.7 | [Thư viện native .so (JNI)](/posts/tr-6-7-native-so-jni/) |
| 6.8 | [Obfuscation Android: R8/ProGuard, DexGuard, packer](/posts/tr-6-8-obfuscation-android/) |
| 6.9 | [Lab: UnCrackable (OWASP MASTG) Level 1-3](/posts/tr-6-9-lab-uncrackable-mastg/) |

#### Phần 7 · Python (pycdc)
| # | Bài |
|---|---|
| 7.1 | [Bytecode Python, file .pyc, magic number theo phiên bản](/posts/tr-7-1-bytecode-python-pyc-magic/) |
| 7.2 | [pycdc & pycdas: decompile/disassemble, giới hạn Python 3.9+](/posts/tr-7-2-pycdc-pycdas/) |
| 7.3 | [Các decompiler khác: uncompyle6, decompyle3, PyLingual, dis/marshal](/posts/tr-7-3-decompiler-python-khac/) |
| 7.4 | [Unpack PyInstaller (pyinstxtractor), py2exe, cx_Freeze](/posts/tr-7-4-unpack-pyinstaller-py2exe/) |
| 7.5 | [Nuitka, Cython, PyArmor: khi Python biến thành native](/posts/tr-7-5-nuitka-cython-pyarmor/) |
| 7.6 | [Lab: decompile các file .pyc mẫu trong pycdc-master/](/posts/tr-7-6-lab-decompile-pyc-mau/) |

#### Phần 8 · Go
| # | Bài |
|---|---|
| 8.1 | [Đặc trưng binary Go: runtime, pclntab, calling convention theo register](/posts/tr-8-1-dac-trung-binary-go/) |
| 8.2 | [Khôi phục tên hàm & kiểu: GoReSym, IDA Go plugin, Ghidra GolangAnalyzer](/posts/tr-8-2-khoi-phuc-symbol-type-go/) |
| 8.3 | [String, slice, interface, goroutine trong assembly](/posts/tr-8-3-string-slice-interface-goroutine/) |
| 8.4 | [Lab: crackme Go](/posts/tr-8-4-lab-crackme-go/) |

#### Phần 9 · Rust
| # | Bài |
|---|---|
| 9.1 | [Đặc trưng binary Rust: mangling v0/legacy, panic, Option/Result](/posts/tr-9-1-dac-trung-binary-rust/) |
| 9.2 | [Nhận diện crate, String/Vec/iterator đã inline](/posts/tr-9-2-nhan-dien-crate-string-vec-iterator/) |
| 9.3 | [Lab: crackme Rust](/posts/tr-9-3-lab-crackme-rust/) |

#### Phần 10 · Ngôn ngữ legacy: Delphi, VB6, AutoIt, AHK
| # | Bài |
|---|---|
| 10.1 | [Delphi/C++Builder: IDR, DeDe, form DFM](/posts/tr-10-1-delphi-cpp-builder/) |
| 10.2 | [Visual Basic 6: P-Code vs Native, VB Decompiler](/posts/tr-10-2-visual-basic-6/) |
| 10.3 | [Script compiled: AutoIt, AutoHotkey, NSIS/Inno Setup](/posts/tr-10-3-script-compiled-autoit-ahk-installer/) |

#### Phần 11 · JavaScript, Electron, WebAssembly
| # | Bài |
|---|---|
| 11.1 | [Deobfuscate JavaScript: beautify, de4js, webcrack, synchrony, AST transform](/posts/tr-11-1-deobfuscate-javascript/) |
| 11.2 | [Ứng dụng Electron: giải nén app.asar, V8 bytecode (bytenode)](/posts/tr-11-2-electron-asar-v8-bytecode/) |
| 11.3 | [WebAssembly: wabt (wasm2wat/wasm2c), Ghidra wasm plugin](/posts/tr-11-3-webassembly/) |

#### Phần 12 · Swift / Objective-C (macOS, iOS)
| # | Bài |
|---|---|
| 12.1 | [Objective-C runtime: objc_msgSend, class-dump](/posts/tr-12-1-objc-runtime-class-dump/) |
| 12.2 | [Swift: metadata, demangle, Hopper/IDA](/posts/tr-12-2-swift/) |
| 12.3 | [iOS app: IPA, decrypt, Frida/objection trên iOS](/posts/tr-12-3-ios-app-ipa-frida/) |

#### Phần 13 · Game: Unity, Unreal, Lua
| # | Bài |
|---|---|
| 13.1 | [Unity Mono: Assembly-CSharp.dll + dnSpy](/posts/tr-13-1-unity-mono/) |
| 13.2 | [Unity IL2CPP: Il2CppDumper, Cpp2IL, global-metadata.dat](/posts/tr-13-2-unity-il2cpp/) |
| 13.3 | [Unreal Engine: UE4SS, SDK dump, pak file](/posts/tr-13-3-unreal-engine/) |
| 13.4 | [Lua/LuaJIT bytecode: unluac, luadec, ljd](/posts/tr-13-4-lua-luajit-bytecode/) |
| 13.5 | [Cheat Engine: scan bộ nhớ, pointer, code injection (game offline)](/posts/tr-13-5-cheat-engine/) |

### Chặng 3: Kỹ thuật chuyên sâu

#### Phần 14 · Packer & Obfuscation
| # | Bài |
|---|---|
| 14.1 | [Packer hoạt động thế nào; entropy; nhận diện bằng DIE](/posts/tr-14-1-packer-entropy-nhan-dien/) |
| 14.2 | [Unpack UPX: tự động và thủ công (tìm OEP)](/posts/tr-14-2-unpack-upx-oep/) |
| 14.3 | [Dump & rebuild IAT với Scylla](/posts/tr-14-3-dump-rebuild-iat-scylla/) |
| 14.4 | [Obfuscation: control-flow flattening, opaque predicate, MBA, string encryption](/posts/tr-14-4-obfuscation-ky-thuat/) |
| 14.5 | [Virtualization (VMProtect/Themida/Code Virtualizer): tư duy tiếp cận](/posts/tr-14-5-virtualization-vmprotect-themida/) |
| 14.6 | [Deobfuscation: D-810, HexRaysDeob, Miasm, symbolic lifting](/posts/tr-14-6-deobfuscation-tu-dong/) |

#### Phần 15 · Anti-Reverse chuyên sâu và cách vượt qua
| # | Bài |
|---|---|
| 15.1 | [Anti-debug (1) API-based: IsDebuggerPresent, NtQueryInformationProcess, OutputDebugString](/posts/tr-15-1-anti-debug-api/) |
| 15.2 | [Anti-debug (2) PEB/struct: BeingDebugged, NtGlobalFlag, heap flags](/posts/tr-15-2-anti-debug-peb/) |
| 15.3 | [Anti-debug (3) timing & trap: RDTSC, INT3/INT2D/ICEBP, hardware breakpoint](/posts/tr-15-3-anti-debug-timing-trap/) |
| 15.4 | [Anti-debug (4): self-debugging, parent check, debug object, TLS callback](/posts/tr-15-4-anti-debug-selfdebug-tls/) |
| 15.5 | [Anti-VM / anti-sandbox: CPUID hypervisor bit, artefact, timing](/posts/tr-15-5-anti-vm-sandbox/) |
| 15.6 | [Anti-disassembly: junk byte, overlapping instruction, opaque predicate, SMC](/posts/tr-15-6-anti-disassembly/) |
| 15.7 | [Anti-attach, anti-dump, anti-hook](/posts/tr-15-7-anti-attach-dump-hook/) |
| 15.8 | [Kiểm tra toàn vẹn: checksum/CRC code section, anti-tamper](/posts/tr-15-8-integrity-check-anti-tamper/) |
| 15.9 | [Vượt qua: ScyllaHide, TitanHide, HyperHide, conditional breakpoint & script](/posts/tr-15-9-bypass-scyllahide-titanhide/) |
| 15.10 | [Chiến lược khi gặp nhiều lớp anti kết hợp](/posts/tr-15-10-chien-luoc-nhieu-lop-anti/) |

#### Phần 16 · Crypto & thuật toán
| # | Bài |
|---|---|
| 16.1 | [Nhận diện hằng số crypto: findcrypt, capa, signsrch](/posts/tr-16-1-nhan-dien-hang-so-crypto/) |
| 16.2 | [XOR, RC4, Base64 custom: những gì hay gặp nhất](/posts/tr-16-2-xor-rc4-base64-custom/) |
| 16.3 | [AES/DES/TEA/ChaCha, hash MD5/SHA/CRC trong assembly](/posts/tr-16-3-aes-des-tea-hash/) |
| 16.4 | [Viết lại thuật toán bằng Python & giải bằng Z3](/posts/tr-16-4-viet-lai-python-z3/) |

#### Phần 17 · Patch, Hook, Injection & Instrumentation
| # | Bài |
|---|---|
| 17.1 | [Patch binary: đổi jump, NOP, code cave, patch trên đĩa vs runtime](/posts/tr-17-1-patch-binary-jump-nop-codecave/) |
| 17.2 | [Frida toàn tập: Interceptor, Stalker, frida-trace, script Windows/Linux/Android](/posts/tr-17-2-frida-toan-tap/) |
| 17.3 | [Hooking trên Windows: IAT hook, inline/trampoline hook, Detours, MinHook](/posts/tr-17-3-hooking-windows-iat-inline-detours/) |
| 17.4 | [DLL injection: cơ chế & cách phát hiện (LoadLibrary+CreateRemoteThread, manual mapping, reflective)](/posts/tr-17-4-dll-injection-ky-thuat/) |
| 17.5 | [Shellcode injection, APC, thread hijacking, process hollowing: nhận diện & phát hiện](/posts/tr-17-5-shellcode-injection-hollowing-phat-hien/) |
| 17.6 | [LD_PRELOAD, ptrace trên Linux; DYLD_INSERT_LIBRARIES trên macOS](/posts/tr-17-6-ld-preload-ptrace-dyld/) |
| 17.7 | [Pin, DynamoRIO, QBDI, TinyInst: dynamic binary instrumentation](/posts/tr-17-7-dbi-pin-dynamorio-tinyinst/) |

#### Phần 18 · Nâng cao
| # | Bài |
|---|---|
| 18.1 | [Scripting decompiler: IDAPython, Ghidra script (Java/Python), Binary Ninja API](/posts/tr-18-1-scripting-decompiler/) |
| 18.2 | [Emulation: Unicorn, Qiling, Speakeasy](/posts/tr-18-2-emulation-unicorn-qiling/) |
| 18.3 | [Symbolic execution: angr, Triton, Z3](/posts/tr-18-3-symbolic-execution-angr-triton/) |
| 18.4 | [Binary diffing & patch diffing: BinDiff, Diaphora, ghidriff](/posts/tr-18-4-binary-diffing/) |
| 18.5 | [Firmware & IoT: binwalk, unblob, MIPS/ARM, QEMU, emulate firmware](/posts/tr-18-5-firmware-iot/) |
| 18.6 | [Kernel driver Windows & Linux kernel module](/posts/tr-18-6-kernel-driver-lkm/) |
| 18.7 | [Reverse giao thức mạng và định dạng file](/posts/tr-18-7-reverse-giao-thuc-dinh-dang-file/) |
| 18.8 | [AI hỗ trợ RE: LLM plugin cho IDA/Ghidra, MCP server cho decompiler](/posts/tr-18-8-ai-ho-tro-re-mcp/) |

#### Phần 19 · Phân tích mã độc cơ bản (phòng thủ)
| # | Bài |
|---|---|
| 19.1 | [Quy trình phân tích malware an toàn; sandbox (ANY.RUN, CAPE, Triage)](/posts/tr-19-1-quy-trinh-phan-tich-malware-sandbox/) |
| 19.2 | [IOC, YARA rule, capa, sigma](/posts/tr-19-2-ioc-yara-capa-sigma/) |
| 19.3 | [Phân tích maldoc: Office macro (olevba), PDF, LNK, script loader](/posts/tr-19-3-maldoc-macro-pdf-lnk/) |
| 19.4 | [Trích xuất config & C2](/posts/tr-19-4-trich-config-c2/) |

#### Phần 20 · Thực chiến
| # | Bài |
|---|---|
| 20.1 | [Giải crackmes.one từ cấp 1 đến 4](/posts/tr-20-1-giai-crackmes-one/) |
| 20.2 | [Write-up RE challenge CTF (Flare-On, picoCTF, HTB)](/posts/tr-20-2-writeup-ctf-flareon/) |
| 20.3 | [Đồ án cuối: reverse toàn bộ một chương trình và viết báo cáo](/posts/tr-20-3-do-an-cuoi-bao-cao/) |
