---
title: "Bài 18.2: Emulation, chạy một mẩu code mà không cần cả chương trình"
date: 2026-10-06 09:48:00 +0700
categories: ["Technique Reverse", "Phần 18 · Nâng cao"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
Có những lúc bạn chỉ cần biết một hàm trả ra cái gì, nhưng để chạy được nó thì phải vượt qua cả một rừng anti-debug, hoặc hàm đó nằm sâu trong một binary không chạy nổi trên máy bạn (sai kiến trúc, thiếu thư viện, cần phần cứng đặc biệt). Debug thì vướng, đọc tĩnh thì tốn cả buổi. Emulation là lối thứ ba: dựng một CPU ảo, nạp đúng mẩu byte code đó vào, set thanh ghi và bộ nhớ như lúc nó được gọi, bấm chạy, rồi đọc kết quả. Không có debugger thật nào ở đây, nên hầu hết anti-debug trở thành vô nghĩa.

## Unicorn: một CPU trong 20 dòng Python

Unicorn Engine là bộ máy emulate CPU tách khỏi QEMU, hỗ trợ x86, ARM, ARM64, MIPS và nhiều kiến trúc khác. Nó không biết gì về hệ điều hành, file, hay syscall. Nó chỉ làm đúng một việc: cho một dãy byte là lệnh máy, nó thực thi từng lệnh và cập nhật thanh ghi, bộ nhớ. Đúng việc đó là đủ để chạy một hàm thuần tính toán như routine giải mã chuỗi.

Mô hình dùng Unicorn luôn gồm bốn bước:

1. Tạo máy ảo với kiến trúc và chế độ (`Uc(UC_ARCH_X86, UC_MODE_64)`).
2. Cấp phát bộ nhớ (`mem_map`) rồi ghi code và dữ liệu vào (`mem_write`).
3. Set thanh ghi đầu vào (`reg_write`): tham số, con trỏ stack, con trỏ buffer.
4. Chạy (`emu_start`) rồi đọc kết quả ra (`reg_read`, `mem_read`).

Đây là đoạn giải mã XOR, chạy được thật (xem lab 18.2):

```python
from unicorn import *
from unicorn.x86_const import *

# xor byte [rdi],0x5A ; inc rdi ; dec rsi ; jnz loop ; ret
CODE = bytes.fromhex("80375A48ffc748ffce75f5c3")
BASE, DATA, STACK = 0x1000000, 0x2000000, 0x3000000

enc = bytes(c ^ 0x5A for c in b"emulation_wins!")

mu = Uc(UC_ARCH_X86, UC_MODE_64)
for addr in (BASE, DATA, STACK):
    mu.mem_map(addr, 0x1000)
mu.mem_write(BASE, CODE)
mu.mem_write(DATA, enc)
mu.reg_write(UC_X86_REG_RDI, DATA)         # con tro buffer
mu.reg_write(UC_X86_REG_RSI, len(enc))     # do dai
mu.reg_write(UC_X86_REG_RSP, STACK + 0x800)

mu.emu_start(BASE, BASE + len(CODE))
print(bytes(mu.mem_read(DATA, len(enc))).decode())  # -> emulation_wins!
```

Cái hay là bạn không cần hiểu từng chi tiết của hàm. Bạn chỉ cần biết nó nhận con trỏ ở `rdi` và độ dài ở `rsi`, copy đúng byte code của vòng lặp ra khỏi IDA, rồi để Unicorn làm nốt. Đây là cách giải nhanh những hàm deobfuscate chuỗi mà malware hay dùng: thay vì ngồi tính XOR bằng tay, bạn để CPU ảo chạy chính đoạn code của malware.

## Ba cái bẫy khi dùng Unicorn

- **Lệnh `ret` cần địa chỉ trở về hợp lệ trên stack**, nếu không máy ảo sẽ nhảy vào vùng chưa map và văng lỗi. Mẹo: ghi sẵn một địa chỉ đã biết lên đỉnh stack rồi dừng `emu_start` tại đúng địa chỉ đó.
- **Lời gọi ra ngoài (call tới API, syscall) sẽ vỡ** vì Unicorn không có hệ điều hành. Phải hoặc tránh đoạn có call, hoặc đặt hook để giả lập lời gọi đó.
- **Map đủ bộ nhớ**: code, dữ liệu, stack, và vùng hàm đụng tới. Quên map một vùng là lỗi `UC_ERR_READ_UNMAPPED` ngay.

## Qiling: Unicorn cộng thêm cả hệ điều hành

Khi hàm bạn cần chạy có gọi API Windows hoặc syscall Linux, Unicorn trần không đủ. Qiling là framework dựng trên Unicorn, bổ sung lớp giả lập OS: nó load được cả một file PE hoặc ELF hoàn chỉnh, giả lập loader, syscall, và một phần Win32 API, cho phép bạn hook bất kỳ API nào. Nghĩa là bạn chạy được cả một binary malware trong một hộp cát Python, chặn và sửa mọi lời gọi của nó, mà không cần Windows thật.

Qiling hợp khi bạn muốn: chạy một binary sai kiến trúc với máy của mình, bắt các API mà malware gọi, hoặc tự động hoá việc trích config bằng cách chạy tới một điểm rồi đọc bộ nhớ.

## Speakeasy: chuyên trị shellcode và malware Windows

Speakeasy của Mandiant là emulator hướng thẳng vào phân tích malware Windows và shellcode. Nó giả lập sẵn rất nhiều Win32 API và kernel, log lại mọi lời gọi, nên bạn ném một mẩu shellcode vào là nó kể cho bạn shellcode đó làm gì (gọi API nào, kết nối đâu) mà không cần chạy thật trên máy. Rất hợp cho khâu triage nhanh.

## Khi nào emulation thắng debug và static

Chọn emulation khi:

- Hàm mục tiêu **thuần tính toán** (giải mã, băm, biến đổi) và bạn chỉ cần input ra output. Đây là điểm ngọt nhất.
- Binary **đầy anti-debug**: không có debugger thật thì các check IsDebuggerPresent, timing, trap đều vô dụng (nối lại Phần 15).
- Binary **sai kiến trúc** với máy bạn (một hàm ARM64 chạy ngon trên Unicorn dù bạn ngồi máy x86).
- Bạn muốn **tự động hoá**: chạy cùng một hàm với hàng nghìn input để tìm quy luật.

Emulation không hợp khi code dính chặt vào OS/API/phần cứng tới mức giả lập còn tốn công hơn chạy thật, hoặc khi nó bị virtualize (lúc đó bytecode VM mới là thứ cần hiểu, xem bài 14.5). Và nhớ: emulate đúng một mẩu thì dễ, emulate trọn một chương trình lớn thì công sức tăng nhanh. Hãy cắt nhỏ mục tiêu.

## Lab tự làm

Xem [labs/18.2/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/18.2): chạy `emu_xor.py` để tự tay dùng Unicorn giải mã một chuỗi mà không viết lại thuật toán, rồi thử sửa key và độ dài. Bài giải và cách mở rộng sang hàm có nhiều tham số nằm ở `solution.md`.

## Checklist ghi nhớ
- Emulation = dựng CPU ảo, nạp byte code, set thanh ghi/bộ nhớ, chạy, đọc kết quả.
- Unicorn: emulate CPU thuần, không có OS. Hợp với hàm tính toán tách rời.
- Mô hình bốn bước: tạo máy, map và ghi bộ nhớ, set thanh ghi, chạy rồi đọc.
- Bẫy: `ret` cần địa chỉ trở về, call ra ngoài sẽ vỡ, phải map đủ bộ nhớ.
- Qiling thêm lớp OS/syscall để chạy cả binary; Speakeasy chuyên shellcode/malware Windows.
- Không có debugger thật nên emulation vượt qua phần lớn anti-debug.
