---
title: "Bài 2.6: GDB, pwndbg và WinDbg, debug ở chế độ dòng lệnh"
date: 2026-10-06 08:22:00 +0700
categories: ["Technique Reverse", "Phần 2 · Làm quen bộ công cụ"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
x64dbg ở bài trước là một GUI đẹp, bấm chuột là xong. Nhưng khi bạn sang Linux, hoặc cần debug nhân Windows, hoặc muốn script hoá cả phiên debug, bạn sẽ quay về dòng lệnh. GDB thống trị thế giới Linux, WinDbg thống trị những góc sâu nhất của Windows. Bài này không biến bạn thành chuyên gia hai công cụ đó, chỉ đưa đủ để bạn ngồi xuống và làm việc được.

## Vì sao vẫn dùng CLI debugger trong thời đại GUI

Câu hỏi hợp lý. Lý do:

- Trên server Linux hay trong container thường không có màn hình, chỉ có terminal.
- GDB script hoá được: viết một file lệnh, chạy hàng loạt, tự động trích giá trị. GUI không làm gọn chuyện này.
- WinDbg là công cụ gần như duy nhất để debug kernel Windows và dùng Time Travel Debugging, thứ x64dbg không có.

Đừng xem CLI là bước lùi. Nó là công cụ khác cho bài toán khác.

## GDB, bộ xương

GDB (GNU Debugger) trần trụi khó ưa, nhưng nhóm lệnh cốt lõi rất ít. Khởi động:

```
gdb ./chuongtrinh        # nạp chương trình
gdb -p 1234              # attach vào tiến trình đang chạy có PID 1234
```

Việc đầu tiên nên làm, vì GDB mặc định hiện cú pháp AT&T khó đọc:

```
set disassembly-flavor intel
```

Giờ disassembly hiện theo Intel, giống IDA và x64dbg, đỡ nhức đầu.

### Chạy và dừng

| Lệnh | Tác dụng |
|---|---|
| `b main` / `b *0x401136` | Đặt breakpoint tại hàm hoặc địa chỉ (có dấu `*` khi là địa chỉ) |
| `r` | Run, chạy từ đầu |
| `c` | Continue, chạy tiếp sau khi dừng |
| `si` / `ni` | Step into / step over một lệnh (s=instruction) |
| `finish` | Chạy cho tới khi hàm hiện tại return |
| `info breakpoints` | Liệt kê breakpoint |
| `d 1` | Xoá breakpoint số 1 |

Lưu ý `si`/`ni` là bước theo **một lệnh assembly**. Nếu bạn gõ `s`/`n` không có `i`, GDB bước theo **một dòng source** (chỉ có ích khi có debug symbol). Người làm RE thường xài `si`/`ni`.

### Xem dữ liệu

Đây là chỗ GDB mạnh. Lệnh `x` (examine) đọc bộ nhớ theo định dạng bạn muốn:

```
info registers          # xem toàn bộ thanh ghi
p $rax                  # in giá trị rax
p/x $rax                # in dạng hex
x/20i $pc               # xem 20 lệnh (i) bắt đầu từ con trỏ lệnh
x/16xg $rsp             # xem 16 giá trị 8 byte (g=giant) dạng hex tại đỉnh stack
x/s 0x404040            # đọc chuỗi (s) tại địa chỉ
x/4xb $rdi              # xem 4 byte (b) dạng hex tại địa chỉ rdi trỏ tới
```

Cú pháp `x/` đọc là: số lượng, rồi định dạng (x hex, d thập phân, i lệnh, s chuỗi), rồi kích thước (b byte, h 2 byte, w 4 byte, g 8 byte). Nhớ công thức này là đọc được mọi thứ trong bộ nhớ.

### Sửa để đổi luồng

```
set $rax = 1            # gán thanh ghi
set {int}0x404040 = 5   # ghi số 5 (kiểu int) vào địa chỉ
```

Gán thẳng thanh ghi cờ hoặc giá trị trả về là cách nhanh để ép chương trình đi nhánh bạn muốn, ví dụ ép một hàm check trả về 1.

### Chế độ TUI

Gõ `Ctrl+X` rồi `A`, hoặc chạy `gdb -tui`, bạn có giao diện chia khung hiện source hoặc disassembly cùng lúc với dòng lệnh. Dễ nhìn hơn hẳn GDB trần.

## pwndbg và GEF, biến GDB thành công cụ của người

GDB trần không cho bạn thấy ngay stack, heap, thanh ghi khi dừng. Hai bản mở rộng vá lỗ hổng đó: **pwndbg** và **GEF**. Cài một trong hai (đừng cả hai cùng lúc), từ đó mỗi lần dừng GDB tự in ra bối cảnh đầy đủ: thanh ghi, vài lệnh quanh con trỏ, stack, các cờ.

Lệnh thêm hữu ích:

| Lệnh | Tác dụng |
|---|---|
| `vmmap` | Bản đồ bộ nhớ: vùng nào địa chỉ nào, quyền RWX |
| `telescope $rsp` (pwndbg) | Xem stack và tự giải nghĩa con trỏ trỏ đi đâu |
| `context` (pwndbg) | In lại toàn bộ bối cảnh hiện tại |
| `heap` / `bins` | Soi cấu trúc heap (đắc dụng khi làm pwn) |

Với người học RE trên Linux, cài pwndbg gần như là bắt buộc. Nó biến GDB từ khó dùng thành dễ chịu.

## WinDbg, khi cần đi sâu vào Windows

WinDbg (nên dùng bản WinDbg mới, trước gọi là WinDbg Preview) là debugger chính thức của Microsoft. Nó khó hơn x64dbg nhưng làm được những việc x64dbg không làm:

- Debug **kernel-mode**: nhân Windows, driver. x64dbg chỉ chơi được ở user-mode.
- **Time Travel Debugging (TTD)**: ghi lại toàn bộ phiên chạy thành một file trace, rồi bạn tua tới tua lui thoải mái, kể cả chạy ngược thời gian để tìm xem một giá trị bị thay đổi ở đâu. Đây là tính năng đổi đời khi truy một bug khó hoặc lần ngược nguồn một giá trị.

Khái niệm cần nắm: WinDbg phân biệt user-mode (debug một tiến trình) và kernel-mode (debug cả nhân, thường qua hai máy nối với nhau hoặc một máy ảo). Người mới bắt đầu ở user-mode.

Nhóm lệnh cơ bản, phong cách gõ lệnh giống GDB nhưng ký hiệu khác:

| Lệnh | Tác dụng |
|---|---|
| `g` | Go, chạy tiếp (như `c` của GDB) |
| `p` / `t` | Step over / step into (p=step, t=trace) |
| `bp kernel32!CreateFileW` | Breakpoint theo tên module!hàm |
| `u rip` | Unassemble, disassemble tại rip |
| `r` | Xem/sửa thanh ghi (`r rax=1`) |
| `dd` / `dq` / `da` / `du` | Dump dword / qword / chuỗi ASCII / chuỗi Unicode |
| `k` | Call stack (backtrace) |
| `!peb` | In cấu trúc PEB, tiện cho anti-debug |
| `lm` | Liệt kê module đã nạp |

Cú pháp `module!hàm` của WinDbg rất mạnh: đặt breakpoint theo tên hàm API mà không cần biết địa chỉ, WinDbg tự tra qua symbol. Nhớ cấu hình symbol server của Microsoft để có tên hàm đầy đủ.

## CLI và GUI, chọn cái nào

Không có câu trả lời chung, chọn theo việc:

- Học RE cơ bản trên Windows, mổ crackme: cứ **x64dbg**, GUI trực quan, nhanh vào việc.
- Làm trên **Linux**, CTF pwn, binary ELF: **GDB + pwndbg**.
- Debug **kernel Windows, driver**, hoặc cần **tua ngược thời gian**: **WinDbg + TTD**.
- Cần **tự động hoá** phiên debug, trích hàng loạt giá trị: GDB script hoặc WinDbg script.

Người làm lâu dùng cả ba, không trung thành với cái nào. Công cụ chỉ là công cụ.

## Lab tự làm

Mã nguồn và hướng dẫn ở [labs/2.6/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/2.6). Tóm tắt: biên dịch một chương trình C nhỏ có hàm kiểm tra mật khẩu, nạp vào GDB + pwndbg, đặt breakpoint tại hàm so sánh, đọc tham số qua `info registers` và `x`, rồi sửa giá trị thanh ghi để ép chương trình chấp nhận mật khẩu sai. Làm xong bạn sẽ thấy nhịp static rồi dynamic của [Bài 0.4](/posts/tr-0-4-quy-trinh-reverse/) trên chính dòng lệnh. Writeup đầy đủ trong [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/2.6/solution.md), tự làm trước khi mở.

## Checklist ghi nhớ
- GDB: nhớ `set disassembly-flavor intel` ngay đầu cho dễ đọc.
- Nhóm lệnh GDB cốt lõi: `b`, `r`, `c`, `si`/`ni`, `finish`, `info registers`, `x/`, `set`.
- Công thức `x/<số><định dạng><kích thước>`: ví dụ `x/16xg $rsp` là 16 giá trị 8 byte hex tại stack.
- Cài pwndbg (hoặc GEF) để GDB tự hiện bối cảnh, `vmmap` và `telescope` rất đáng dùng.
- WinDbg cho kernel-mode và Time Travel Debugging, hai thứ x64dbg không có.
- Breakpoint WinDbg theo `module!hàm`, nhớ bật symbol server của Microsoft.
- Chọn công cụ theo bài toán: x64dbg cho Windows user-mode, GDB cho Linux, WinDbg cho kernel/TTD.
