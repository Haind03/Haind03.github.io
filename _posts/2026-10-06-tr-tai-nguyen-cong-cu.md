---
title: "Kho công cụ Reverse Engineering (tổng hợp)"
date: 2026-10-06 14:01:00 +0700
categories: ["Technique Reverse", "Tài nguyên"]
tags: [reverse-engineering, resources]
render_with_liquid: false
---
> Danh mục công cụ dùng xuyên suốt series.
> Cột **Nền tảng**: W=Windows, L=Linux, M=macOS, X=đa nền (cross).
> Cột **Giá**: `free` = miễn phí/mã nguồn mở · `paid` = thương mại · `free+paid` = có bản miễn phí lẫn pro.
> Đánh dấu **(ưu tiên)** = nên cài trước tiên.

Mục lục:
- [1. Triage & nhận diện file](#1-triage--nhận-diện-file)
- [2. Disassembler / Decompiler đa năng](#2-disassembler--decompiler-đa-năng)
- [3. Debugger](#3-debugger)
- [4. Hex editor & xem nhị phân](#4-hex-editor--xem-nhị-phân)
- [5. Giám sát hệ thống & runtime](#5-giám-sát-hệ-thống--runtime)
- [6. .NET](#6-net)
- [7. Java / Android](#7-java--android)
- [8. Python](#8-python)
- [9. Go & Rust](#9-go--rust)
- [10. Delphi / VB / script-compiled](#10-delphi--vb--script-compiled)
- [11. JavaScript / Electron / WASM](#11-javascript--electron--wasm)
- [12. Apple: macOS / iOS](#12-apple-macos--ios)
- [13. Game](#13-game)
- [14. Unpacking & import rebuild](#14-unpacking--import-rebuild)
- [15. Anti-anti-debug & stealth](#15-anti-anti-debug--stealth)
- [16. Hook, injection, instrumentation](#16-hook-injection-instrumentation)
- [17. Emulation & symbolic execution](#17-emulation--symbolic-execution)
- [18. Crypto & pattern](#18-crypto--pattern)
- [19. Binary diffing](#19-binary-diffing)
- [20. Firmware & embedded](#20-firmware--embedded)
- [21. Malware analysis](#21-malware-analysis)
- [22. Bộ cài sẵn (distro)](#22-bộ-cài-sẵn-distro)
- [23. AI hỗ trợ RE](#23-ai-hỗ-trợ-re)

---

## 1. Triage & nhận diện file
| Tool | Nền tảng | Giá | Công dụng |
|---|---|---|---|
| **Detect It Easy (DIE)** (ưu tiên) | X | free | Nhận diện packer/compiler/protector, entropy, signature, YARA. *(Có sẵn trong repo: `die_win64_portable_3.08_x64`)* |
| `file` | L/M | free | Nhận diện loại file nhanh theo magic |
| `strings` / **FLOSS** | X | free | Trích chuỗi; FLOSS (Mandiant) còn giải chuỗi bị mã hoá/stack string |
| **PE-bear** | W | free | Xem & sửa cấu trúc PE trực quan |
| **PEiD** / **Exeinfo PE** | W | free | Nhận diện packer (cũ nhưng còn hữu ích) |
| **CFF Explorer** (Explorer Suite) | W | free | Xem/sửa PE, rebuild, dependency |
| **TrID** | X | free | Nhận diện loại file theo chữ ký thống kê |
| **capa** (Mandiant) | X | free | Suy ra *khả năng* của binary (vd: "mã hoá bằng RC4", "inject vào tiến trình") |
| **Manalyze** | W/L | free | Phân tích tĩnh PE + plugin |

## 2. Disassembler / Decompiler đa năng
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **Ghidra** (NSA) (ưu tiên) | X | free | Decompiler C miễn phí mạnh nhất, hỗ trợ cực nhiều kiến trúc, scriptable (Java/Python) |
| **IDA Free / IDA Pro** (ưu tiên) | X | free+paid | Chuẩn công nghiệp; Hex-Rays decompiler (Pro); IDAPython. Free đủ học x86/x64 |
| **Binary Ninja** | X | free+paid | UI hiện đại, IL nhiều tầng (BNIL), API Python tốt; có bản cloud free |
| **radare2** / **rizin** | X | free | CLI mạnh, hoàn toàn mở; rizin là fork sạch hơn |
| **Cutter** | X | free | GUI cho rizin, tích hợp decompiler Ghidra (jsdec) |
| **Hopper** | M/L | paid | Phổ biến trên macOS, có decompiler |
| **RetDec** (Avast) | X | free | Decompiler dòng lệnh |
| **Relyze** | W | paid | Phân tích & diff |
| **objdump** / **llvm-objdump** | X | free | Disassemble nhanh từ dòng lệnh |

## 3. Debugger
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **x64dbg / x32dbg** (ưu tiên) | W | free | Debugger ring-3 chủ lực cho Windows; nhiều plugin (ScyllaHide, xAnalyzer…) |
| **WinDbg** (+ WinDbg Preview / TTD) | W | free | Kernel + user, Time Travel Debugging ghi lại và tua ngược |
| **OllyDbg** / **Immunity Debugger** | W | free | Kinh điển (32-bit); Immunity cho exploit dev |
| **GDB** + **pwndbg** / **GEF** / **peda** (ưu tiên) | L | free | Debugger Linux; plugin thêm view heap/stack/registers |
| **LLDB** | X | free | Mặc định trên macOS; iOS debugging |
| **radare2 / rizin** | X | free | Debug tích hợp disassembler |
| **edb-debugger** | L | free | GUI kiểu Olly cho Linux |

## 4. Hex editor & xem nhị phân
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **HxD** | W | free | Nhẹ, nhanh |
| **010 Editor** | X | paid | **Binary Template** phân tích cấu trúc file cực mạnh |
| **ImHex** | X | free | Hex editor cho reverser: pattern language, data inspector, disasm |
| **wxHexEditor** | X | free | Mở file lớn |

## 5. Giám sát hệ thống & runtime
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **Process Monitor (Procmon)** (ưu tiên) | W | free | Theo dõi file/registry/process/network real-time |
| **Process Hacker / System Informer** (ưu tiên) | W | free | Quản lý tiến trình, xem memory/handle/thread, dump |
| **Process Explorer** | W | free | Cây tiến trình, DLL, handle |
| **API Monitor** | W | free | Bắt lời gọi Win32 API kèm tham số |
| **Autoruns** | W | free | Điểm khởi động tự động (persistence) |
| **Wireshark** | X | free | Phân tích gói mạng |
| **Fiddler** / **mitmproxy** / **Burp Suite** | X | free+paid | Chặn/sửa HTTP(S) |
| **PE-sieve / HollowsHunter** | W | free | Phát hiện code injection/hollowing trong tiến trình đang chạy |
| **ltrace / strace** | L | free | Trace lời gọi thư viện / syscall |
| **frida-trace** | X | free | Trace hàm bất kỳ (xem mục 16) |

## 6. .NET
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **dnSpy / dnSpyEx** (ưu tiên) | W | free | Decompile + **debug + sửa** .NET. *(Có sẵn: `dnSpy-net-win64`)* |
| **ILSpy** (ưu tiên) | X | free | Decompiler .NET; bản CLI `ilspycmd`; AvaloniaILSpy đa nền. *(Có sẵn: `ILSpy_binaries_9.0.0...`)* |
| **dotPeek** (JetBrains) | W | free | Decompiler, hỗ trợ symbol server |
| **de4dot / de4dot-cex** | W | free | Gỡ obfuscation .NET (nhiều protector) |
| **.NET Reactor Slayer** | W | free | Unpack .NET Reactor |
| **dnlib** | X | free | Thư viện đọc/ghi assembly (tự động hoá patch) |
| **Mono.Cecil** | X | free | Thư viện đọc/ghi IL khác |
| **monodis** | X | free | Disassembler Mono |

## 7. Java / Android
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **JADX / jadx-gui** (ưu tiên) | X | free | APK/DEX/JAR -> Java; deobfuscation cơ bản, sinh snippet Frida. *(Có sẵn: `jadx-gui-1.5.1-win`)* |
| **CFR** | X | free | Decompiler Java rất tốt với cú pháp mới |
| **Procyon** | X | free | Decompiler Java |
| **Vineflower** (kế thừa Fernflower/Quiltflower) | X | free | Decompiler chất lượng cao |
| **Recaf** | X | free | Xem + **sửa** bytecode Java, recompile |
| **Bytecode Viewer** | X | free | Gộp nhiều decompiler trong 1 GUI |
| **apktool** | X | free | Giải nén/đóng gói APK, smali |
| **smali/baksmali** | X | free | Assembler/disassembler cho DEX |
| **dex2jar** | X | free | DEX -> JAR |
| **apksigner / uber-apk-signer** | X | free | Ký lại APK |
| **Androguard** | X | free | Phân tích APK bằng Python |
| **frida / objection** | X | free | Hook runtime (xem mục 16) |
| **MobSF** | X | free | Khung phân tích mobile tự động (static+dynamic) |

## 8. Python
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **pycdc / pycdas** (Decompyle++) (ưu tiên) | X | free | Decompile/disassemble .pyc không phụ thuộc runtime. *(Có sẵn: `pycdc-master`)* |
| **uncompyle6 / decompyle3** | X | free | Decompiler cho Python <=3.8 (decompyle3 tới ~3.9) |
| **PyLingual** | web | free | Decompiler .pyc hiện đại (hỗ trợ Python 3.x mới), chạy trên web |
| **pyinstxtractor / pyinstxtractor-ng** | X | free | Giải nén EXE do PyInstaller đóng |
| **unpy2exe** | X | free | Giải nén py2exe |
| **xdis** | X | free | Đọc marshal/magic nhiều phiên bản |
| **pydumpck** | X | free | Tự động hoá unpack + decompile |

## 9. Go & Rust
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **GoReSym** (Mandiant) | X | free | Khôi phục symbol, type, pclntab của binary Go |
| **IDAGolangHelper / golang_loader_assist** | X | free | Script IDA phục hồi tên hàm Go |
| **GolangAnalyzerExtension** | X | free | Plugin Ghidra cho Go |
| **redress** | X | free | Thông tin build Go |
| **rustfilt** | X | free | Demangle symbol Rust |
| **Ghidra/IDA + rust demangler** | X | free | Demangle v0/legacy |

## 10. Delphi / VB / script-compiled
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **IDR (Interactive Delphi Reconstructor)** | W | free | Khôi phục Delphi/C++Builder |
| **DeDe** | W | free | Delphi cũ |
| **VB Decompiler** | W | free+paid | VB6 P-Code & Native |
| **Exe2Aut / AutoIt-Ripper** | W/X | free | Giải script AutoIt đã biên dịch |
| **NSIS extractor (7-Zip) / innounp / UniExtract2** | W | free | Giải installer NSIS/Inno |

## 11. JavaScript / Electron / WASM
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **js-beautify / Prettier** | X | free | Làm đẹp code |
| **de4js** | web | free | Gỡ obfuscation JS phổ biến |
| **webcrack** | X | free | Unminify + gỡ bundle/obfuscator hiện đại |
| **synchrony** (deobfuscator.io) | X | free | Gỡ javascript-obfuscator |
| **AST Explorer + Babel** | web/X | free | Viết transform tự động |
| **asar** | X | free | Giải nén `app.asar` của Electron |
| **bytenode tools** | X | free | Xử lý V8 bytecode `.jsc` |
| **wabt** (wasm2wat, wasm2c, wasm-objdump) | X | free | Bộ công cụ WebAssembly |
| **Ghidra wasm plugin / wasmdec** | X | free | Reverse WASM |

## 12. Apple: macOS / iOS
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **Hopper** | M/L | paid | Rất mạnh cho Mach-O/ObjC/Swift |
| **class-dump / class-dump-swift** | M | free | Trích khai báo ObjC/Swift |
| **otool / nm / lipo / codesign** | M | free | Bộ công cụ hệ thống |
| **swift demangle** | M | free | Giải tên Swift |
| **frida / objection** | X | free | Hook iOS |
| **Clutch / frida-ios-dump / bagbak** | iOS | free | Giải mã IPA (jailbreak) |
| **Ghidra / IDA** + loader Mach-O | X | free+paid | Phân tích tĩnh |

## 13. Game
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **Cheat Engine** (ưu tiên) | W | free | Scan/freeze giá trị, pointer, code injection, AA scripts (game offline) |
| **Il2CppDumper** | X | free | Unity IL2CPP -> header + metadata |
| **Cpp2IL** | X | free | Dựng lại IL2CPP (thay thế hiện đại) |
| **AssetStudio / AssetRipper** | W/X | free | Trích & dựng lại asset Unity |
| **UABE / UABEA** | W | free | Chỉnh sửa asset bundle Unity |
| **UE4SS / FModel / UModel** | W | free | Unreal: scripting, xem/trích asset, pak |
| **unluac / luadec / ljd / luajit-decompiler** | X | free | Lua / LuaJIT bytecode |
| **ReClass.NET** | W | free | Dựng lại struct trong bộ nhớ game đang chạy |

## 14. Unpacking & import rebuild
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **UPX** | X | free | `upx -d` cho file UPX nguyên bản |
| **Scylla / Scylla x64** (ưu tiên) | W | free | Dump tiến trình + rebuild IAT (sau khi tới OEP) |
| **PE-sieve** | W | free | Dump module đã bị unpack/inject từ tiến trình |
| **MegaDumper** | W | free | Dump .NET + native từ bộ nhớ |
| **ImpREC** | W | free | Rebuild IAT (cũ) |
| **unipacker** | X | free | Tự động unpack bằng Unicorn (một số packer) |
| **CAPE sandbox** | L | free | Tự động unpack + dump config malware |

## 15. Anti-anti-debug & stealth
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **ScyllaHide** (ưu tiên) | W | free | Ẩn debugger ở user-mode (plugin x64dbg/IDA/Olly) |
| **TitanHide** | W | free | Ẩn debugger ở kernel-mode (driver) |
| **HyperHide** | W | free | Ẩn ở mức hypervisor/DBVM |
| **SharpOD** | W | free | Plugin anti-anti-debug cho x64dbg |
| **strace/ltrace + seccomp** | L | free | Quan sát anti-debug trên Linux (ptrace check) |

## 16. Hook, injection, instrumentation
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **Frida** (ưu tiên) | X | free | Instrumentation động: Interceptor, Stalker, scripting JS/Python. Nền tảng cho rất nhiều bài |
| **objection** | X | free | Lớp tự động hoá trên Frida (mobile) |
| **frida-gum / frida-tools** | X | free | Thư viện + CLI (frida-trace, frida-ps…) |
| **Microsoft Detours** | W | free | Thư viện hook API kinh điển |
| **MinHook / PolyHook2** | W | free | Inline hook x86/x64 gọn nhẹ |
| **EasyHook** | W | free | Hook + inject managed/native |
| **Intel Pin** | X | free | DBI mạnh cho phân tích/taint/coverage |
| **DynamoRIO** | X | free | DBI mã nguồn mở |
| **TinyInst** | X | free | Instrumentation nhẹ cho fuzzing/coverage |
| **QBDI** (QuarksLab) | X | free | DBI nhúng được, API đẹp |

> Các kỹ thuật injection (CreateRemoteThread, APC, manual mapping, process hollowing, reflective loading…) được trình bày ở [Bài 17.4 & 17.5](https://github.com/Haind03/Technique-Reverse/tree/main/phan-17-patch-hook-frida) dưới góc độ **cơ chế + cách phát hiện/phòng thủ**. LD_PRELOAD / DYLD_INSERT_LIBRARIES là cơ chế sẵn có của OS, không phải tool.

## 17. Emulation & symbolic execution
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **Unicorn Engine** | X | free | Emulate CPU (x86/ARM/MIPS…), chạy từng đoạn code |
| **Qiling** | X | free | Framework emulate cả OS/syscall trên nền Unicorn |
| **Speakeasy** (Mandiant) | X | free | Emulate shellcode/malware Windows |
| **angr** | X | free | Symbolic/concolic execution, CFG, giải constraint |
| **Triton** | X | free | DBA + symbolic execution + SMT |
| **Miasm** | X | free | IL, emulate, deobfuscate |
| **Z3** | X | free | SMT solver, giải điều kiện check serial/flag |
| **manticore / maat** | X | free | Symbolic execution thay thế |

## 18. Crypto & pattern
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **findcrypt2 / FindCrypt-Ghidra** | X | free | Tìm hằng số thuật toán crypto |
| **signsrch** | X | free | Tìm chữ ký thuật toán/áp dụng |
| **capa** | X | free | Nhận diện khả năng gồm crypto |
| **PortEx / Kaitai Struct** | X | free | Mô tả & parse định dạng nhị phân |
| **CyberChef** | web/X | free | "Dao đa năng" encode/decode/crypto |

## 19. Binary diffing
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **BinDiff** (Google) | X | free | So khớp hàm giữa 2 binary (patch diffing) |
| **Diaphora** | X | free | Diff cho IDA, mạnh & mở |
| **ghidriff** | X | free | Diff dựa trên Ghidra, xuất markdown |
| **radiff2** (radare2) | X | free | Diff từ dòng lệnh |

## 20. Firmware & embedded
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **binwalk** | X | free | Quét & trích thành phần trong firmware |
| **unblob** | X | free | Trích đệ quy nhiều định dạng, hiện đại |
| **firmware-mod-kit** | L | free | Mở & dựng lại firmware |
| **QEMU** | X | free | Emulate kiến trúc khác (ARM/MIPS) để chạy/debug firmware |
| **FACT** | L | free | Nền tảng phân tích & so sánh firmware |
| **flashrom / chipsec** | X | free | Đọc flash / kiểm tra firmware nền tảng |
| **OpenOCD / JTAGulator** | X | free | Debug phần cứng qua JTAG/SWD |

## 21. Malware analysis
| Tool | Nền tảng | Giá | Ghi chú |
|---|---|---|---|
| **YARA / yarGen** | X | free | Viết & sinh rule nhận diện |
| **capa + capa-rules** | X | free | Lập hồ sơ khả năng |
| **CAPE / CAPEv2** | L | free | Sandbox tự động unpack + trích config |
| **Cuckoo3 / Drakvuf** | L | free | Sandbox động |
| **ANY.RUN / Triage / Joe Sandbox / Hybrid Analysis** | web | free+paid | Sandbox online |
| **oletools (olevba, oleid)** | X | free | Phân tích macro Office |
| **pdf-parser / peepdf** | X | free | Phân tích PDF độc |
| **lnkparse / LECmd** | X | free | Phân tích file .lnk |
| **pestudio** | W | free | Triage PE hướng dấu hiệu khả nghi |
| **INetSim / FakeNet-NG** | L/W | free | Giả lập dịch vụ mạng cho dynamic analysis |

## 22. Bộ cài sẵn (distro)
| Bộ | Nền tảng | Ghi chú |
|---|---|---|
| **FLARE-VM** (Mandiant) | W | Script biến Windows VM thành máy RE/malware đầy đủ tool |
| **REMnux** | L | Distro Linux cho phân tích malware |
| **Kali / Parrot** | L | Thiên về pentest nhưng có nhiều tool RE |
| **Tsurugi Linux** | L | DFIR + RE |

## 23. AI hỗ trợ RE

### 23a. Plugin LLM trong decompiler
| Tool | Nền tảng | Ghi chú |
|---|---|---|
| **Gepetto** | X | Plugin IDA dùng LLM giải thích hàm & đổi tên biến |
| **aiDAPal / Sidekick (Binary Ninja)** | X | Trợ lý AI trong decompiler |
| **GhidrAssist / G-3PO / GhidraMCP-lite** | X | LLM cho Ghidra |
| **LLM4Decompile / DeGPT** | X | Nghiên cứu cải thiện output decompiler |

### 23b. MCP server cho RE (nối decompiler/tool với Claude, Cursor, LLM agent)
MCP (Model Context Protocol) cho phép LLM điều khiển trực tiếp công cụ RE: đọc pseudocode, đổi tên, đặt comment, chạy lệnh debugger… Cấu hình trong client (Claude Desktop/Code, Cline, Cursor) rồi hỏi bằng ngôn ngữ tự nhiên.

| MCP server | Kết nối tới | Ghi chú |
|---|---|---|
| **ida-pro-mcp** (mrexodia) | IDA Pro | Phổ biến nhất cho IDA: lấy decompile, xref, rename, comment, đọc/ghi qua Hex-Rays |
| **IDA-MCP / ida_mcp (cộng đồng)** | IDA Pro | Các biến thể khác, tính năng tương tự |
| **GhidraMCP** (LaurieWired) | Ghidra | Điều khiển Ghidra qua MCP: liệt kê hàm, decompile, rename, data type |
| **ghidra-mcp (các fork)** | Ghidra | Biến thể bổ sung script/headless |
| **Binary Ninja MCP** | Binary Ninja | Khai thác BNIL/HLIL qua MCP |
| **radare2 MCP / r2mcp** | radare2/rizin | Chạy lệnh r2, phân tích theo hội thoại |
| **x64dbg MCP** | x64dbg | Điều khiển debug động (breakpoint, đọc bộ nhớ, register) |
| **frida-mcp** | Frida | Để agent viết & nạp script Frida, đọc kết quả hook |
| **pwndbg / GDB MCP** | GDB | Debug Linux qua hội thoại |
| **angr-mcp** | angr | Giao symbolic execution cho agent điều phối |
| **capa-mcp / YARA MCP** | capa, YARA | Phân loại khả năng & quét rule theo yêu cầu |
| **unblob / binwalk MCP** | firmware tools | Trích firmware theo hội thoại |

> Lưu ý an toàn: MCP cho LLM quyền chạy công cụ trên máy bạn. Khi phân tích malware, chạy client + MCP trong **VM cô lập** (xem [Bài 0.3](/posts/tr-0-3-dung-lab-an-toan/)), không để agent tự ý thực thi mẫu. Một bài riêng về dựng MCP cho RE ở [Bài 18.8](https://github.com/Haind03/Technique-Reverse/tree/main/phan-18-nang-cao).

---

### Gợi ý bộ cài tối thiểu để bắt đầu (Windows)
1. Detect It Easy · 2. x64dbg · 3. IDA Free **hoặc** Ghidra · 4. dnSpyEx · 5. JADX · 6. HxD/ImHex · 7. Process Hacker + Procmon · 8. Python + Frida · 9. PE-bear · 10. CyberChef (offline).

Tất cả đều miễn phí. Khi cần lên chuyên nghiệp: IDA Pro + Hex-Rays, Binary Ninja, 010 Editor.
