---
title: "Cheatsheet: phím tắt và tra cứu nhanh"
date: 2026-10-06 14:00:00 +0700
categories: ["Technique Reverse", "Tài nguyên"]
tags: [reverse-engineering, resources]
render_with_liquid: false
---
> Để cạnh màn hình lúc làm. Phần cuối là bảng tra lệnh x86 hay gặp, dùng khi đọc disassembly mà quên lệnh nào đó.

## IDA (Free/Pro)

| Phím | Tác dụng |
|---|---|
| `F5` | Decompile hàm hiện tại (Hex-Rays, bản Pro) |
| `Space` | Chuyển graph view / text view |
| `N` | Đổi tên (rename) hàm, biến, nhãn |
| `X` | Xem cross-reference tới đối tượng dưới con trỏ |
| `;` | Thêm comment lặp lại (repeatable) |
| `:` | Thêm comment thường |
| `G` | Nhảy tới địa chỉ |
| `D` | Chuyển đổi giữa data / code; đổi kiểu dữ liệu |
| `C` | Ép thành code (convert to code) |
| `U` | Hủy định nghĩa (undefine) |
| `Y` | Đặt/sửa kiểu (type) của biến hoặc hàm |
| `Alt+T` | Tìm text |
| `Esc` / `Ctrl+Enter` | Quay lại / tiến tới (như back/forward trình duyệt) |
| `Shift+F12` | Mở cửa sổ Strings |

## Ghidra

| Phím | Tác dụng |
|---|---|
| `Ctrl+E` hoặc double-click | Mở decompiler cho hàm |
| `L` | Đổi tên (rename) |
| `Ctrl+L` | Đổi kiểu (retype) |
| `Ctrl+Shift+F` | Xem references tới |
| `G` | Go to địa chỉ/label |
| `;` | Thêm comment |
| `C` | Clear code bytes |
| `D` | Disassemble |
| `T` | Đặt data type |
| `Ctrl+Shift+E` | Equate (đặt tên hằng số) |
| Window > Defined Strings | Danh sách strings |

## x64dbg

| Phím | Tác dụng |
|---|---|
| `F2` | Đặt/bỏ breakpoint tại dòng hiện tại |
| `F7` | Step into (vào trong hàm) |
| `F8` | Step over (bước qua hàm) |
| `F9` | Run / continue |
| `Ctrl+F9` | Execute till return (chạy tới khi hàm return) |
| `F4` | Run to selection (chạy tới dòng đang chọn) |
| `Space` | Sửa lệnh (assemble) tại chỗ |
| `Ctrl+G` | Go to biểu thức/địa chỉ |
| `Ctrl+B` | Tìm chuỗi byte (binary search) |
| Right-click > Search for > String references | Tìm tham chiếu chuỗi |
| Right-click > Follow in Dump | Theo con trỏ vào cửa sổ dump |
| `Ctrl+P` | Patches (xem/lưu các patch đã làm) |

Breakpoint hữu ích đặt bằng lệnh trong ô Command:
```
bp VirtualAlloc        ; dừng khi gọi VirtualAlloc
bp CreateFileW
bp strcmp
```

## GDB + pwndbg/GEF

| Lệnh | Tác dụng |
|---|---|
| `b *0x401000` / `b main` | Breakpoint tại địa chỉ / hàm |
| `r` | Run |
| `c` | Continue |
| `si` / `ni` | Step into / step over (một lệnh) |
| `info registers` | Xem thanh ghi |
| `x/20i $pc` | Xem 20 lệnh tại con trỏ lệnh |
| `x/16xg $rsp` | Xem 16 giá trị 8 byte tại đỉnh stack |
| `p $rax` | In giá trị thanh ghi rax |
| `set $rax=1` | Gán giá trị thanh ghi |
| `finish` | Chạy tới khi hàm hiện tại return |
| `telescope $rsp` (pwndbg) | Xem stack có giải nghĩa con trỏ |
| `vmmap` (pwndbg/GEF) | Bản đồ bộ nhớ tiến trình |

## dnSpy (.NET)

| Phím | Tác dụng |
|---|---|
| `F5` | Chạy / debug |
| `F9` | Toggle breakpoint |
| `F10` / `F11` | Step over / step into |
| Right-click > Analyze | Xem ai gọi method này (used by) |
| Right-click > Edit Method (C#) | Sửa code C# rồi biên dịch lại |
| Right-click > Edit IL Instructions | Sửa trực tiếp IL |
| `Ctrl+Shift+K` | Tìm trong assembly |
| File > Save Module | Lưu assembly đã sửa |

## JADX-GUI (Android)

| Phím | Tác dụng |
|---|---|
| Double-click | Nhảy tới định nghĩa |
| `x` | Find usage (xref) |
| `n` | Rename |
| `Ctrl+Shift+F` | Tìm text toàn dự án |
| Right-click > Copy as Frida snippet | Sinh sẵn đoạn hook Frida cho method |
| `Ctrl+Shift+S` | Save all (xuất source) |

## Bảng tra lệnh x86/x64 hay gặp

Khi đọc disassembly mà quên lệnh nào làm gì.

### Di chuyển dữ liệu
| Lệnh | Ý nghĩa |
|---|---|
| `mov dst, src` | Gán: dst = src |
| `lea dst, [expr]` | Nạp địa chỉ, dst = địa chỉ của expr (không truy cập bộ nhớ). Hay bị dùng để tính toán số học |
| `push` / `pop` | Đẩy vào / lấy ra khỏi stack |
| `xchg a, b` | Hoán đổi a và b |
| `movzx` / `movsx` | Mở rộng, zero-extend / sign-extend khi chép sang thanh ghi lớn hơn |

### Số học và logic
| Lệnh | Ý nghĩa |
|---|---|
| `add` / `sub` | Cộng / trừ |
| `inc` / `dec` | Tăng / giảm 1 |
| `imul` / `mul`, `idiv` / `div` | Nhân / chia (i = có dấu) |
| `and` / `or` / `xor` / `not` | Logic bit. `xor eax, eax` là cách gọn để gán eax = 0 |
| `shl` / `shr` / `sar` | Dịch bit trái/phải (sar giữ dấu) |
| `test a, b` | AND nhưng chỉ đặt cờ, không lưu kết quả. `test eax, eax` để kiểm tra eax có bằng 0 |
| `cmp a, b` | So sánh (trừ thử a, b) rồi đặt cờ, không lưu kết quả |

### Rẽ nhánh (sau cmp/test)
| Lệnh | Nhảy khi |
|---|---|
| `jmp` | Luôn nhảy (vô điều kiện) |
| `je` / `jz` | Bằng nhau / kết quả bằng 0 |
| `jne` / `jnz` | Khác / khác 0 |
| `jg` / `jl` | Lớn hơn / nhỏ hơn (có dấu) |
| `jge` / `jle` | Lớn hơn hoặc bằng / nhỏ hơn hoặc bằng (có dấu) |
| `ja` / `jb` | Trên / dưới (không dấu) |
| `js` / `jns` | Dấu âm / không âm |

Mẹo đọc: `cmp` hoặc `test` đi ngay trước một lệnh `j*` chính là một câu `if` trong source. Nhận ra cặp này là bạn đọc được logic rẽ nhánh.

### Gọi hàm
| Lệnh | Ý nghĩa |
|---|---|
| `call func` | Gọi hàm (đẩy địa chỉ trở về rồi nhảy) |
| `ret` | Trả về hàm gọi |
| `leave` | Dọn stack frame (tương đương `mov rsp,rbp; pop rbp`) |
| `nop` | Không làm gì. Dân RE hay dùng để "xoá" lệnh khi patch |

### Thanh ghi hay gặp (x64)
| Thanh ghi | Vai trò thường thấy |
|---|---|
| `rax` / `eax` | Giá trị trả về của hàm nằm ở đây |
| `rcx, rdx, r8, r9` | 4 tham số đầu trên Windows x64 (thứ tự này) |
| `rdi, rsi, rdx, rcx, r8, r9` | 6 tham số đầu trên Linux/macOS x64 (System V) |
| `rsp` | Con trỏ đỉnh stack |
| `rbp` | Con trỏ base của stack frame |
| `rip` | Con trỏ lệnh (lệnh sắp chạy) |

Biết nơi để tham số và nơi trả về giá trị là đủ đọc hiểu phần lớn lời gọi hàm. Chi tiết calling convention ở [Bài 1.4](https://github.com/Haind03/Technique-Reverse/tree/main/phan-01-nen-tang-may-tinh).
