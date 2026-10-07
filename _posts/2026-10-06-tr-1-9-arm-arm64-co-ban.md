---
title: "Bài 1.9: ARM/ARM64 cơ bản cho người đã biết x86"
date: 2026-10-06 08:12:00 +0700
categories: ["Technique Reverse", "Phần 1 · Nền tảng máy tính cho RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Nếu bạn định reverse app Android, app iOS, hay firmware của router và camera, sớm muộn gì cũng đụng ARM. Tin tốt: khi đã quen x86, học ARM64 không phải bắt đầu lại từ đầu. Khái niệm (thanh ghi, stack, call/ret, tham số, giá trị trả về) y hệt, chỉ khác cú pháp và vài thói quen. Bài này chỉ tập trung vào chỗ khác, để bạn không phí thời gian học lại cái đã biết.

## RISC vs CISC, vì sao code ARM dài hơn

x86 là CISC (Complex Instruction Set): một lệnh làm được nhiều việc, ví dụ `add eax, [rbx+rcx*4]` vừa tính địa chỉ, vừa đọc bộ nhớ, vừa cộng, tất cả trong một lệnh.

ARM là RISC (Reduced Instruction Set): mỗi lệnh làm một việc đơn giản, lệnh dài cố định (4 byte với ARM64), và quan trọng nhất là **lệnh tính toán chỉ làm việc trên thanh ghi, không đụng thẳng vào bộ nhớ.** Muốn cộng một giá trị trong bộ nhớ, bạn phải: nạp (load) nó vào thanh ghi, cộng, rồi ghi (store) ngược ra. Ba lệnh thay vì một.

Hệ quả thực tế khi đọc: code ARM64 thường dài hơn x86 về số lệnh, nhưng từng lệnh lại dễ hiểu hơn vì đơn giản. Bạn sẽ thấy rất nhiều cặp `ldr`/`str` bao quanh phần tính toán.

## Thanh ghi ARM64

ARM64 (còn gọi là AArch64) có 31 thanh ghi đa dụng, thoải mái hơn x86 nhiều:

```
x0  x1  x2  ... x30     (64 bit)
w0  w1  w2  ... w30     (32 bit thấp của x tương ứng)
```

Giống hệt chuyện `rax`/`eax` bên x86: `x0` là 64 bit, `w0` là 32 bit thấp của chính nó. Thấy `w0` và `x0` trong cùng hàm là cùng một thanh ghi, chỉ khác độ rộng.

Vài thanh ghi có vai trò quy ước phải nhớ, vì chúng giúp đọc nhanh:

| Thanh ghi | Vai trò |
|---|---|
| `x0` tới `x7` | 8 tham số đầu của hàm. Nhiều hơn hẳn x86 (x86-64 chỉ 4 hoặc 6) |
| `x0` | Cũng là nơi chứa **giá trị trả về**, y như rax |
| `x29` (fp) | Frame pointer, con trỏ base của stack frame, vai trò như rbp |
| `x30` (lr) | Link register, chỗ này mới lạ, xem bên dưới |
| `sp` | Stack pointer, như rsp |
| `pc` | Program counter, như rip |

Điểm người quen x86 hay vấp số một: tham số nằm ở `x0..x7`, không phải `rcx rdx` gì cả. Giá trị trả về ở `x0` chứ không phải rax. Đọc một lời gọi hàm ARM64 là nhìn `x0, x1, x2...` để biết tham số.

## lr, chỗ khác biệt lớn nhất

Bên x86, lệnh `call` đẩy địa chỉ trở về lên stack, rồi `ret` lấy từ stack ra. ARM làm khác: lệnh gọi hàm `bl` (branch with link) lưu địa chỉ trở về vào **thanh ghi lr (x30)**, không đụng stack.

Nghĩa là với hàm lá (leaf function, hàm không gọi hàm khác), địa chỉ trở về nằm gọn trong lr, chẳng cần stack. `ret` đơn giản là nhảy về địa chỉ trong lr.

Nhưng nếu hàm A gọi hàm B, thì lr đang giữ địa chỉ trở về của A sẽ bị `bl` ghi đè khi gọi B. Nên hàm không phải leaf buộc phải **cất lr lên stack ở đầu hàm** (prologue) và **khôi phục trước khi ret** (epilogue). Bạn sẽ thấy pattern này liên tục:

```asm
stp  x29, x30, [sp, #-16]!   ; cất fp(x29) và lr(x30) lên stack, đồng thời trừ sp 16
mov  x29, sp                 ; dựng frame pointer
... thân hàm, có thể bl gọi hàm khác ...
ldp  x29, x30, [sp], #16     ; khôi phục fp và lr, cộng sp lại 16
ret                          ; nhảy về lr
```

`stp`/`ldp` là "store pair"/"load pair", cất/nạp hai thanh ghi cùng lúc, ARM rất hay dùng để tiết kiệm lệnh. Dấu `!` nghĩa là cập nhật luôn sp (pre-index). Thấy `stp x29, x30` ở đầu một hàm là bạn biết ngay: đây là prologue, hàm này có gọi hàm khác.

## Nhóm lệnh hay gặp

Đối chiếu trực tiếp với x86 cho dễ nhớ:

```asm
mov  x0, #5          ; x0 = 5           (số tức thời có dấu #)
mov  x1, x2          ; x1 = x2
add  x0, x1, x2      ; x0 = x1 + x2     (ba toán hạng: đích, nguồn1, nguồn2)
sub  x0, x1, #8      ; x0 = x1 - 8
cmp  x0, #10         ; so sánh, đặt cờ  (giống x86)
```

Để ý: ARM dùng ba toán hạng, `add x0, x1, x2` là `x0 = x1 + x2`, đích tách riêng khỏi nguồn. Khác x86 nơi `add eax, ebx` là `eax += ebx` (đích cũng là một nguồn).

Truy cập bộ nhớ tách bạch bằng `ldr`/`str`:

```asm
ldr  x0, [x1]        ; x0 = *(x1)        nạp từ địa chỉ trong x1
ldr  x0, [x1, #8]    ; x0 = *(x1 + 8)    thường là đọc field của struct
str  x0, [x1]        ; *(x1) = x0        ghi ra bộ nhớ
```

Đây chính là cặp load/store thay cho `mov eax, [rbx]` bên x86. Mọi truy cập bộ nhớ đều qua `ldr`/`str`, nhớ vậy là đọc được.

Rẽ nhánh và gọi hàm:

```asm
b    label           ; nhảy vô điều kiện    (như jmp)
b.eq label           ; nhảy nếu bằng        (như je, sau cmp)
b.ne label           ; nhảy nếu khác        (như jne)
b.gt / b.lt / ...    ; lớn hơn / nhỏ hơn
cbz  x0, label       ; nhảy nếu x0 == 0     (compare and branch if zero, gộp cmp+je)
cbnz x0, label       ; nhảy nếu x0 != 0
bl   func            ; gọi hàm, lưu địa chỉ trở về vào lr  (như call)
blr  x8              ; gọi hàm tại địa chỉ trong x8 (gọi gián tiếp)
ret                  ; trả về (nhảy tới lr)
```

`cbz`/`cbnz` là tiện lợi riêng của ARM: gộp so sánh với 0 và nhảy vào một lệnh. Thấy `cbz x0, somewhere` thì dịch là "nếu x0 bằng 0 thì nhảy", khỏi cần tìm lệnh cmp trước đó.

## Đọc thử một đoạn thật

Cùng kiểu hàm kiểm tra độ dài như bài 1.3, nhưng bằng ARM64:

```asm
check_password:
    ldr  w0, [sp, #12]      ; nạp biến cục bộ (độ dài chuỗi) vào w0
    cmp  w0, #8             ; so sánh với 8
    b.ne fail              ; nếu khác 8 thì nhảy tới fail
    mov  w0, #1            ; w0 = 1 (đúng)
    ret
fail:
    mov  w0, #0            ; w0 = 0 (sai)
    ret
```

Dịch ra C:

```c
int check_password() {
    int len = ...;        // biến cục bộ tại [sp+12]
    if (len != 8)         // cmp + b.ne
        return 0;
    return 1;
}
```

Giống hệt bản x86 về mặt logic. Chỉ khác: `w0` thay cho `eax` làm giá trị trả về, `ldr` thay cho `mov` khi đọc bộ nhớ, `b.ne` thay cho `jne`. Quen rồi là đọc trôi chảy.

## ARM 32-bit và chế độ Thumb, nhắc ngắn

Trên thiết bị cũ và nhiều firmware, bạn gặp ARM 32-bit (AArch32), thanh ghi là `r0..r15` (r13=sp, r14=lr, r15=pc). Nó còn có hai chế độ mã hoá lệnh: **ARM** (lệnh 4 byte) và **Thumb** (lệnh 2 hoặc 4 byte, gọn hơn, hay dùng để tiết kiệm bộ nhớ). Một binary có thể trộn cả hai, và chuyển chế độ qua bit thấp nhất của địa chỉ hàm (lẻ = Thumb). Điểm này hay làm disassembler nhận nhầm, nếu thấy code ARM32 giải mã ra rác thì thử ép sang Thumb hoặc ngược lại. Chi tiết để dành cho các bài firmware ở Phần 18.

## Lab tự làm

Xem [labs/1.9/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/1.9). Bạn sẽ cross-compile một file C nhỏ sang ARM64 rồi tự đối chiếu assembly với source, hoặc nếu không cài được toolchain thì đọc đoạn ARM64 cho sẵn và dịch ngược ra C. Lời giải ở `labs/1.9/solution.md`, tự làm trước khi mở.

## Checklist ghi nhớ
- ARM là RISC: lệnh đơn giản, dài cố định, tính toán chỉ trên thanh ghi, truy cập bộ nhớ phải qua `ldr`/`str`.
- Thanh ghi: `x0..x30` (64 bit), `w0..w30` (32 bit thấp). Tham số ở `x0..x7`, trả về ở `x0`.
- `bl` lưu địa chỉ trở về vào `lr` (x30), không đẩy stack như `call`. Hàm không phải leaf phải cất lr lên stack ở prologue (`stp x29, x30, [sp,...]`).
- Đối chiếu nhanh: `mov`/`ldr`/`str` cho dữ liệu, `add`/`sub`/`cmp` cho tính toán, `b`/`b.eq`/`cbz`/`bl`/`ret` cho rẽ nhánh và gọi hàm.
- ARM32 có chế độ ARM và Thumb trộn lẫn, coi chừng disassembler nhận nhầm chế độ.
