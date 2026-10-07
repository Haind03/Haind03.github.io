---
title: "Bài 1.3: Assembly x86/x64 (1), thanh ghi và những lệnh bạn gặp hàng ngày"
date: 2026-10-06 08:06:00 +0700
categories: ["Technique Reverse", "Phần 1 · Nền tảng máy tính cho RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Nhiều người sợ assembly vì tưởng phải thuộc hàng trăm lệnh. Sự thật dễ chịu hơn nhiều: trong 95% thời gian reverse, bạn chỉ gặp đi gặp lại chừng hai mươi lệnh. Học chắc nhóm đó là đọc được phần lớn code. Bài này là nhóm đó.

## Thanh ghi, chỗ CPU để đồ

CPU không tính toán trực tiếp trên RAM. Nó chép dữ liệu vào các ô nhớ siêu nhanh bên trong gọi là thanh ghi (register), xử lý ở đó, rồi ghi ngược ra. Hiểu thanh ghi là hiểu nửa assembly.

Trên x64 có 16 thanh ghi đa dụng (general purpose), mỗi cái 64 bit:

```
rax rbx rcx rdx rsi rdi rbp rsp
r8  r9  r10 r11 r12 r13 r14 r15
```

Điều hay gây rối cho người mới: **cùng một thanh ghi có nhiều tên theo kích thước bạn muốn dùng.** Lấy rax làm ví dụ:

```
rax  = 64 bit (toàn bộ)
eax  = 32 bit thấp của rax
ax   = 16 bit thấp
al   = 8 bit thấp nhất
```

Nên khi thấy `eax` và `rax` trong cùng một hàm, chúng là một thanh ghi, chỉ khác bạn đang nhìn bao nhiêu bit. Tương tự `rbx/ebx/bx/bl`, `rcx/ecx/cx/cl`, v.v. Với r8 tới r15 thì là `r8/r8d/r8w/r8b`.

Vài thanh ghi có vai trò quy ước mà bạn phải nhớ vì nó giúp đọc code rất nhanh:

| Thanh ghi | Vai trò hay thấy |
|---|---|
| `rax` | Giá trị **trả về** của hàm nằm ở đây. Sau một `call`, nhìn rax là biết hàm trả gì |
| `rsp` | Con trỏ **đỉnh stack** (stack pointer). Đừng tự ý ghi đè |
| `rbp` | Con trỏ **base** của stack frame, dùng để tham chiếu biến cục bộ |
| `rip` | Con trỏ lệnh, trỏ tới lệnh sắp chạy. Không gán trực tiếp được |
| `rcx rdx r8 r9` | 4 tham số đầu của hàm trên **Windows x64** |
| `rdi rsi rdx rcx r8 r9` | 6 tham số đầu trên **Linux/macOS x64** |

Chi tiết chuyện truyền tham số để bài [1.4](/posts/tr-1-4-assembly-2-stack-calling-convention/) lo. Ở đây chỉ cần biết: trả về xem rax, tham số xem mấy thanh ghi trên.

Ngoài ra có **thanh ghi cờ** (RFLAGS). Bạn không đọc nó trực tiếp mà qua các lệnh nhảy. Vài cờ quan trọng: ZF (zero flag, bật khi kết quả bằng 0), SF (sign flag, dấu âm), CF (carry), OF (overflow).

## Cú pháp: Intel vs AT&T

Có hai cách viết assembly, đọc là biết ngay:

- **Intel** (IDA, x64dbg, Windows): `mov eax, 5` nghĩa là eax = 5. Đích đứng **trước**.
- **AT&T** (GDB mặc định, Linux): `mov $5, %eax`, có `%` trước thanh ghi, `$` trước số, đích đứng **sau**.

Series này dùng Intel vì nó gần với công cụ Windows ta xài nhiều. Trong GDB bạn gõ `set disassembly-flavor intel` để đổi sang Intel cho đỡ nhức đầu.

## Nhóm lệnh phải thuộc

### mov, lea: chuyển dữ liệu

```asm
mov eax, 5          ; eax = 5
mov eax, ebx        ; eax = ebx
mov eax, [rbx]      ; eax = giá trị tại địa chỉ rbx (ngoặc vuông = truy cập bộ nhớ)
mov [rbx], eax      ; ghi eax vào địa chỉ rbx
```

Ngoặc vuông `[...]` là chìa khoá: có ngoặc là **truy cập bộ nhớ tại địa chỉ đó**, không ngoặc là làm việc với chính giá trị. Nhầm hai cái này là hiểu sai cả hàm.

`lea` (load effective address) hay làm người mới bối rối:

```asm
lea rax, [rbx+rcx*4+8]   ; rax = rbx + rcx*4 + 8, KHÔNG truy cập bộ nhớ
```

`lea` tính ra địa chỉ rồi bỏ vào thanh ghi, nhưng không đọc bộ nhớ tại đó. Compiler còn lạm dụng `lea` để làm toán (nhân, cộng) vì nó gọn. Thấy `lea` đừng vội nghĩ "địa chỉ", nhiều khi chỉ là phép tính.

### add, sub, inc, dec: số học

```asm
add eax, 10     ; eax += 10
sub eax, ebx    ; eax -= ebx
inc eax         ; eax++
dec eax         ; eax--
imul eax, 3     ; eax *= 3 (có dấu)
```

### xor, and, or, shl, shr: bit

```asm
xor eax, eax    ; eax = 0  (mẹo kinh điển: xor chính nó = 0, gọn hơn mov eax,0)
and eax, 0xFF   ; giữ lại byte thấp nhất
or  eax, 1      ; bật bit 0
shl eax, 2      ; dịch trái 2 = nhân 4
shr eax, 1      ; dịch phải 1 = chia 2
```

Nhớ mẹo `xor eax, eax` nghĩa là "gán 0", gặp liên tục ở đầu hàm. Không nhận ra nó là tưởng đang mã hoá gì đó.

### cmp, test, và lệnh nhảy: đây là if/else

Đây là nhóm quan trọng nhất để đọc logic. CPU không có lệnh "if". Nó làm hai bước:

1. **So sánh**, đặt cờ:
   - `cmp a, b` thử tính a trừ b, chỉ để đặt cờ (không lưu kết quả). Nếu a == b thì ZF bật.
   - `test a, b` thử AND a với b, đặt cờ. `test eax, eax` là cách kiểm tra "eax có bằng 0 không".
2. **Nhảy có điều kiện** dựa trên cờ:

```asm
cmp eax, 10
je  somewhere      ; nhảy nếu eax == 10 (jump if equal)
jne somewhere      ; nhảy nếu eax != 10
jg  somewhere      ; nhảy nếu eax > 10 (có dấu)
jl  somewhere      ; nhảy nếu eax < 10 (có dấu)
ja  / jb           ; trên / dưới (không dấu)
```

Công thức đọc code nằm lòng: **cặp `cmp`/`test` + `j*` ngay sau nó chính là một câu `if` trong source.** Tìm được cặp này ở đâu là bạn tìm được chỗ rẽ nhánh logic ở đó. Trong một crackme, chỗ `cmp` trước khi in "Sai mật khẩu" thường là chính nơi nó so sánh serial.

`jmp` (không điều kiện) thì luôn nhảy, giống `goto`.

### call, ret: gọi hàm

```asm
call 0x401500   ; gọi hàm tại 0x401500
ret             ; trả về nơi gọi
```

`call` đẩy địa chỉ trở về lên stack rồi nhảy tới hàm. `ret` lấy địa chỉ đó ra và quay lại. Sau `call`, giá trị trả về nằm ở rax.

### nop: không làm gì, nhưng rất hữu ích

`nop` (no operation) chẳng làm gì cả. Nghe vô dụng nhưng đây là công cụ patch số một: muốn "xoá" một lệnh kiểm tra phiền phức mà không làm lệch các địa chỉ khác, bạn ghi đè nó bằng `nop`. Bài [17.1](https://github.com/Haind03/Technique-Reverse/tree/main/phan-17-patch-hook-frida) dùng nhiều.

## Đọc thử một đoạn thật

Đây là một hàm kiểm tra đơn giản, kiểu bạn gặp trong crackme:

```asm
check_password:
    push rbp
    mov  rbp, rsp
    mov  eax, [rbp-4]      ; nạp một biến cục bộ (độ dài chuỗi nhập vào) vào eax
    cmp  eax, 8            ; so sánh với 8
    jne  fail             ; nếu khác 8 thì nhảy tới fail
    mov  eax, 1            ; eax = 1 (đúng)
    jmp  done
fail:
    xor  eax, eax         ; eax = 0 (sai)
done:
    pop  rbp
    ret
```

Dịch ngược ra C trong đầu:

```c
int check_password() {
    int len = ...;       // biến cục bộ tại [rbp-4]
    if (len != 8)        // cmp + jne
        return 0;        // nhánh fail
    return 1;
}
```

Hàm này chỉ kiểm tra chuỗi nhập có đúng 8 ký tự hay không. Bạn vừa đọc assembly và dịch ra logic, đó chính là reverse. Không có phép màu nào cả, chỉ là quen cặp `cmp`/`jne` và biết rax là giá trị trả về.

## Checklist ghi nhớ
- Một thanh ghi nhiều tên theo kích thước: `rax`(64)/`eax`(32)/`ax`(16)/`al`(8), chúng là một.
- rax = giá trị trả về. rsp = đỉnh stack. Tham số đầu: Windows `rcx rdx r8 r9`, Linux `rdi rsi rdx rcx r8 r9`.
- `[...]` = truy cập bộ nhớ, không ngoặc = chính giá trị. Đừng nhầm.
- `lea` tính địa chỉ/toán, không đọc bộ nhớ.
- `xor eax, eax` nghĩa là gán 0.
- Cặp `cmp`/`test` + `j*` = một câu `if`. Đây là chìa khoá đọc logic.
