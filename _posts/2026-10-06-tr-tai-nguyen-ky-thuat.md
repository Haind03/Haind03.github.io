---
title: "Kho kỹ thuật Reverse Engineering (bản đồ)"
date: 2026-10-06 14:02:00 +0700
categories: ["Technique Reverse", "Tài nguyên"]
tags: [reverse-engineering, resources]
render_with_liquid: false
---
> Toàn bộ kỹ thuật trong series, nhóm theo chủ đề. Mỗi kỹ thuật ghi: *dùng khi nào* và *bài học tương ứng*.
> Ký hiệu bài: ví dụ `15.5` = Phần 15, Bài 5 (xem [README](/technique-reverse/)).

## A. Phân tích tĩnh (Static analysis)
Không chạy file, chỉ đọc.

| Kỹ thuật | Dùng khi | Bài |
|---|---|---|
| Triage / fingerprinting | Bước đầu luôn làm: biết loại file, compiler, packer | 2.1, 14.1 |
| Đọc chuỗi (strings) & stacked/encoded string | Tìm manh mối nhanh: URL, path, thông báo lỗi, flag | 2.1 |
| Phân tích import/export | Suy chức năng từ API được gọi | 1.7, 1.13 |
| Đọc disassembly | Hiểu từng lệnh máy | 1.3,1.5 |
| Đọc decompiler output | Hiểu nhanh ở mức C/pseudocode | 2.2, 2.3 |
| Khôi phục kiểu dữ liệu & struct | Làm pseudocode dễ đọc | 3.3, 4.2 |
| Cross-reference (xref) | Lần theo nơi dùng hàm/biến/chuỗi | 2.2 |
| Nhận diện calling convention | Đọc đúng tham số | 1.4 |
| Nhận diện cấu trúc điều khiển (if/loop/switch) | Dịch assembly ngược về logic | 1.5 |
| FLIRT / library signature | Bỏ qua code thư viện, tập trung code người viết | 3.4 |
| Control Flow Graph (CFG) | Nhìn tổng thể luồng hàm | 2.2, 2.3 |

## B. Phân tích động (Dynamic analysis)
Chạy file trong môi trường kiểm soát.

| Kỹ thuật | Dùng khi | Bài |
|---|---|---|
| Debugging (breakpoint, step, watch) | Quan sát giá trị thật lúc chạy | 2.5, 2.6 |
| Breakpoint theo API | Dừng tại GetProcAddress, CreateFile… | 2.5, 15.9 |
| Memory breakpoint / hardware breakpoint | Bắt truy cập vùng nhớ | 2.5 |
| Dump bộ nhớ | Lấy code đã giải mã/unpack | 14.2, 14.3 |
| Trace (API/syscall/thư viện) | Hiểu hành vi tổng thể | 2.8, 17.2 |
| Giám sát hệ thống (Procmon…) | Thấy tác động file/registry/network | 2.8, 19.1 |
| Time Travel Debugging | Tua ngược để tìm nguồn giá trị | 2.6 |
| Giám sát mạng | Hiểu giao thức C2/API | 2.8, 18.7 |

## C. Theo ngôn ngữ / nền tảng
| Nền tảng | Kỹ thuật đặc thù | Bài |
|---|---|---|
| C/C++ native | Khôi phục struct, vtable, RTTI, name mangling | 3.x, 4.x |
| .NET | Decompile ILC#, debug không source, patch IL | 5.x |
| Java/Android | DEXJava, smali patch, ký lại APK, hook Java | 6.x |
| Python | .pycsource, unpack PyInstaller | 7.x |
| Go | Phục hồi symbol từ pclntab | 8.x |
| Rust | Demangle, nhận diện pattern Result/Option | 9.x |
| JS/Electron/WASM | Deobfuscate, giải asar, wasm2wat | 11.x |
| Apple | ObjC runtime, Swift demangle | 12.x |
| Game | IL2CPP dump, Cheat Engine, Lua decompile | 13.x |

## D. Unpacking & deobfuscation
| Kỹ thuật | Mô tả | Bài |
|---|---|---|
| Nhận diện packer & entropy | Phân biệt packed/không | 14.1 |
| Unpack tự động (UPX -d, unipacker) | Nhanh khi packer chuẩn | 14.2 |
| Unpack thủ công (tìm OEP) | Khi packer tuỳ biến; theo tail jump/ESP trick | 14.2 |
| Dump + rebuild IAT (Scylla) | Tái tạo file chạy được sau unpack | 14.3 |
| Gỡ string encryption | Giải chuỗi bị mã hoá tĩnh | 14.4, 18.2 |
| Gỡ control-flow flattening | Phục hồi luồng gốc | 14.4, 14.6 |
| Gỡ opaque predicate / MBA | Đơn giản hoá biểu thức rác | 14.4, 18.3 |
| Đối phó virtualization (VMProtect/Themida) | Hiểu bytecode handler | 14.5 |
| Deobfuscate bằng emulation/symbolic | Tự động hoá | 14.6, 18.2, 18.3 |

## E. Anti-reverse (nhận diện & vượt qua)
Trình bày theo hướng **hiểu cơ chế để phân tích và phòng thủ**.

| Kỹ thuật phía phần mềm | Cách reverser xử lý | Bài |
|---|---|---|
| Anti-debug qua API (IsDebuggerPresent…) | Hook/patch trả về giả, ScyllaHide | 15.1, 15.9 |
| Anti-debug qua PEB/NtGlobalFlag | Sửa cờ trong bộ nhớ | 15.2 |
| Anti-debug timing (RDTSC) | Bỏ qua/điều chỉnh delta, patch | 15.3 |
| Trap (INT3/INT2D/ICEBP), hardware BP detect | Nhận ra & tránh | 15.3 |
| Self-debug, debug object, thread hiding | HyperHide/TitanHide | 15.4, 15.9 |
| TLS callback chạy trước main | Đặt BP ở TLS callback | 15.4 |
| Anti-VM/sandbox | Làm VM giống thật, patch check | 15.5 |
| Anti-disassembly (junk/overlap/SMC) | Sửa định dạng, chạy động, force code | 15.6 |
| Anti-attach / anti-dump / anti-hook | Attach sớm, dựng lại header, so prologue | 15.7 |
| Integrity check (CRC/checksum) | Vô hiệu hoá check thay vì sửa code bị kiểm | 15.8 |

## F. Crypto & thuật toán
| Kỹ thuật | Mô tả | Bài |
|---|---|---|
| Nhận diện hằng số crypto | findcrypt/capa/signsrch | 16.1 |
| Nhận diện XOR/RC4/Base64 custom | Pattern phổ biến nhất trong malware/crackme | 16.2 |
| Nhận diện AES/DES/TEA/ChaCha/hash | Qua S-box, hằng số, cấu trúc vòng | 16.3 |
| Viết lại thuật toán bằng Python | Để tự giải/keygen | 16.4 |
| Giải điều kiện bằng Z3/angr | Khi logic check phức tạp | 16.4, 18.3 |

## G. Patch, hook, injection, instrumentation
| Kỹ thuật | Mô tả | Bài |
|---|---|---|
| Patch tĩnh (đổi jump, NOP, code cave) | Sửa hành vi vĩnh viễn trên file | 17.1 |
| Patch runtime | Sửa trong bộ nhớ lúc chạy | 17.1 |
| IAT hook | Thay con trỏ trong bảng import | 17.3 |
| Inline/trampoline hook (Detours/MinHook) | Chèn jump đầu hàm | 17.3 |
| Frida Interceptor/Stalker | Hook & trace linh hoạt mọi nền tảng | 17.2 |
| DLL injection (LoadLibrary+CreateRemoteThread, SetWindowsHookEx, AppInit) | Nạp code vào tiến trình khác | 17.4 |
| Manual mapping / reflective DLL | Nạp không qua loader chuẩn | 17.4 |
| Shellcode injection, APC, thread hijacking, process hollowing | Cơ chế & dấu hiệu phát hiện (PE-sieve, EDR) | 17.5 |
| LD_PRELOAD / ptrace / DYLD_INSERT_LIBRARIES | Tương đương trên Linux/macOS | 17.6 |
| DBI (Pin/DynamoRIO/QBDI/TinyInst) | Taint, coverage, tracing quy mô lớn | 17.7 |

## H. Nâng cao & tự động hoá
| Kỹ thuật | Mô tả | Bài |
|---|---|---|
| Scripting decompiler (IDAPython/Ghidra/BN API) | Tự động hoá phân tích lặp lại | 18.1 |
| Emulation (Unicorn/Qiling/Speakeasy) | Chạy đoạn code tách biệt | 18.2 |
| Symbolic execution (angr/Triton) | Tự tìm input thoả điều kiện | 18.3 |
| Binary/patch diffing | Tìm lỗ hổng từ bản vá, so sánh biến thể | 18.4 |
| Firmware/IoT (binwalk/QEMU) | Reverse thiết bị nhúng | 18.5 |
| Kernel driver / LKM | Reverse code ring-0 | 18.6 |
| Reverse giao thức/định dạng file | Dựng lại spec từ mẫu | 18.7 |
| AI hỗ trợ (LLM plugin/MCP) | Tăng tốc đặt tên, giải thích | 18.8 |

## I. Malware analysis (phòng thủ)
| Kỹ thuật | Mô tả | Bài |
|---|---|---|
| Quy trình an toàn + sandbox | Chạy mẫu không lây lan | 19.1 |
| Viết IOC/YARA/capa/sigma | Phát hiện & săn mối đe doạ | 19.2 |
| Maldoc analysis (macro/PDF/LNK) | Khâu lây nhiễm ban đầu | 19.3 |
| Trích config & C2 | Hiểu hạ tầng kẻ tấn công | 19.4 |

---

### Lộ trình kỹ năng gợi ý
1. **Static cơ bản** (A) -> đọc được disassembly/pseudocode.
2. **Dynamic cơ bản** (B) -> debug thành thạo x64dbg/GDB.
3. **Một ngôn ngữ managed** (.NET hoặc Java) để thấy "thành quả" nhanh.
4. **C/C++ native**, xương sống.
5. **Unpacking + anti-reverse** (D, E), nơi tách người mới và người giỏi.
6. **Tự động hoá** (H), scripting, emulation, symbolic.
7. Chuyên sâu theo hướng: malware, exploit/vuln research, hoặc game/mobile.
