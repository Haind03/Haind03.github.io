---
title: "Bài 1.4: Assembly x86/x64 (2), stack frame và calling convention"
date: 2026-10-06 08:07:00 +0700
categories: ["Technique Reverse", "Phần 1 · Nền tảng máy tính cho RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Bài trước bạn đọc được một hàm đơn giản. Nhưng hàm thật nhận tham số, có biến cục bộ, gọi hàm khác. Tất cả những thứ đó diễn ra trên stack theo một bộ luật gọi là calling convention (quy ước gọi hàm). Nắm được bộ luật này, bạn nhìn vào một `call` là biết tham số nào đang được truyền, hàm trả về cái gì, và biến cục bộ nằm ở đâu. Không nắm, bạn sẽ đoán mò cả buổi.

![Stack frame của một lời gọi hàm: tham số, địa chỉ trở về, rbp cũ, biến cục bộ, shadow space](/assets/img/technique-reverse/assets/phan-01/stack-frame.svg)

## Call và ret thật sự làm gì

Hai lệnh này nghe tầm thường nhưng là xương sống của mọi lời gọi hàm, nên phải hiểu từng bước.

Khi CPU chạy `call 0x401500`:
1. Nó đẩy (push) địa chỉ của lệnh **ngay sau** `call` lên stack. Đây là địa chỉ trở về (return address), để lát nữa biết đường quay lại.
2. Nó nhảy tới `0x401500`.

Khi hàm chạy xong và gặp `ret`:
1. Nó lấy (pop) địa chỉ trở về khỏi stack.
2. Nó nhảy về đó.

Vậy stack giữ địa chỉ trở về, và đây chính là lý do stack dính chặt với lời gọi hàm. Nhớ từ bài 1.2: stack mọc xuống, nên `push` làm rsp giảm, `pop` làm rsp tăng.

## Prologue và epilogue, hai đoạn mở đầu kết thúc quen mặt

Gần như mọi hàm (khi biên dịch không tối ưu, `-O0`) đều mở đầu bằng vài lệnh giống hệt nhau. Đây gọi là prologue (đoạn dựng khung) và epilogue (đoạn dọn khung):

```asm
my_function:
    push rbp            ; prologue: lưu base pointer cũ
    mov  rbp, rsp       ; đặt base pointer mới = đỉnh stack hiện tại
    sub  rsp, 0x20      ; chừa chỗ cho biến cục bộ (0x20 byte)
    ...                 ; thân hàm
    leave              ; epilogue: tương đương mov rsp,rbp; pop rbp
    ret
```

Thấy cặp `push rbp` / `mov rbp, rsp` ở đầu là biết chắc đây là bắt đầu một hàm. Sau đó `sub rsp, N` là hàm đang chừa N byte trên stack để chứa biến cục bộ. Cuối hàm `leave` dọn sạch khung đó rồi `ret` quay về. Nhận ra bộ khung này giúp bạn khoanh vùng một hàm ngay cả khi IDA chưa nhận diện đúng.

Khối stack mà một hàm dùng (gồm biến cục bộ, base pointer đã lưu, địa chỉ trở về) gọi là stack frame (khung stack). Mỗi hàm đang chạy có một frame của riêng nó, xếp chồng lên frame của hàm đã gọi nó.

## Calling convention, bộ luật truyền tham số

Đây là phần cốt lõi. Calling convention trả lời ba câu hỏi:
1. Tham số truyền qua đâu? (thanh ghi hay stack)
2. Giá trị trả về nằm ở đâu?
3. Ai chịu trách nhiệm dọn tham số khỏi stack sau khi gọi xong? (bên gọi hay bên bị gọi)

Luật khác nhau theo kiến trúc (32 hay 64 bit) và theo hệ điều hành. Bạn không cần thuộc hết, chỉ cần nắm chắc hai cái dùng nhiều nhất hôm nay là Win64 và System V, rồi biết sơ mấy cái 32-bit cũ để không ngơ ngác khi gặp code cũ.

### Thế giới 64-bit (cái bạn gặp nhiều nhất)

Ở 64-bit, tham số được ưu tiên truyền qua thanh ghi cho nhanh, chỉ khi hết thanh ghi mới tràn ra stack. Hai bộ luật:

**Microsoft x64 (Win64), dùng trên Windows:**
- 4 tham số nguyên/con trỏ đầu tiên: `rcx`, `rdx`, `r8`, `r9` (đúng thứ tự này).
- Tham số thứ 5 trở đi: đẩy lên stack.
- Trả về: `rax`.
- Có một đặc sản gọi là **shadow space** (vùng bóng): bên gọi phải chừa sẵn 32 byte (0x20) trên stack ngay trên địa chỉ trở về, kể cả khi hàm có ít hơn 4 tham số. Vùng này để hàm được gọi có chỗ lưu tạm 4 thanh ghi tham số nếu cần. Thấy `sub rsp, 0x28` hoặc các con số kiểu 0x20 cộng thêm trước một loạt `call` là dấu hiệu của shadow space. Lúc đầu nó làm người mới bối rối vì "sao chừa chỗ mà không dùng", biết tên nó rồi là hết thắc mắc.

**System V AMD64, dùng trên Linux và macOS:**
- 6 tham số nguyên/con trỏ đầu: `rdi`, `rsi`, `rdx`, `rcx`, `r8`, `r9`.
- Tham số thứ 7 trở đi: stack.
- Trả về: `rax`.
- Không có shadow space, nhưng có "red zone" 128 byte ngay dưới rsp mà hàm lá được dùng thoải mái.

Nhìn hai danh sách là thấy ngay chúng khác nhau. Cùng một hàm `f(a, b, c)`, trên Windows `a` nằm ở rcx, trên Linux `a` nằm ở rdi. Đọc nhầm hệ điều hành là đọc nhầm hết tham số. Khi mở một binary, nhớ hỏi: đây là file Windows hay Linux?

Một đoạn gọi hàm thật trên Win64:

```asm
; gọi add3(10, 20, 30) trên Windows x64
mov  r8d, 30        ; tham số 3 -> r8
mov  edx, 20        ; tham số 2 -> rdx
mov  ecx, 10        ; tham số 1 -> rcx
call add3
; kết quả giờ nằm trong eax
```

Cùng hàm đó trên Linux:

```asm
mov  edx, 30        ; tham số 3 -> rdx
mov  esi, 20        ; tham số 2 -> rsi
mov  edi, 10        ; tham số 1 -> rdi
call add3
```

### Thế giới 32-bit (code cũ, vẫn gặp)

Ở 32-bit không có nhiều thanh ghi để xài nên tham số chủ yếu đẩy lên stack, thứ tự từ phải sang trái. Ba convention hay nghe tên:

- **cdecl**: tham số đẩy lên stack phải-sang-trái, **bên gọi** dọn stack sau khi gọi (bạn sẽ thấy `add esp, N` ngay sau `call`). Mặc định của C trên 32-bit.
- **stdcall**: cũng đẩy stack phải-sang-trái, nhưng **bên bị gọi** tự dọn (kết thúc bằng `ret N` thay vì `ret`). Đây là convention của hầu hết Win32 API. Thấy `ret 0xC` là biết hàm dọn 12 byte tham số, tức khoảng 3 tham số.
- **fastcall**: 2 tham số đầu vào `ecx`, `edx`, còn lại lên stack. Nhanh hơn chút.

Mẹo phân biệt nhanh khi đọc 32-bit: nhìn sau `call`. Có `add esp, N` là cdecl (caller dọn). Hàm kết thúc `ret N` là stdcall (callee dọn). Đây là cách bạn suy ra số tham số mà không cần đọc thân hàm.

## Đọc stack frame trong IDA

IDA làm giúp bạn phần nặng nhất: nó phân tích frame rồi đặt tên tử tế cho các ô. Bạn sẽ thấy hai loại tên:

- `var_4`, `var_8`, `var_C`...: đây là **biến cục bộ** (local variable), nằm ở các địa chỉ âm so với rbp (`[rbp-4]`, `[rbp-8]`). Số sau `var_` chính là độ lệch, ví dụ `var_4` là `[rbp-4]`.
- `arg_0`, `arg_4`, `arg_8`...: đây là **tham số** được truyền qua stack (phần tràn, hoặc ở 32-bit), nằm ở địa chỉ dương so với rbp.

Khi bạn double-click vào `var_8` trong IDA và đổi tên nó thành `password_len`, mọi chỗ dùng ô đó đổi theo. Đây là cách bạn biến một hàm đầy `var_x` khó hiểu thành code đọc được như tiếng người. Cứ thấy một biến hiểu ra nó là gì thì đặt tên ngay, đừng để dành.

Một điểm hay nhầm: với hàm 64-bit, tham số đến qua thanh ghi (rcx, rdx...) chứ không qua stack, nên ở đầu hàm compiler thường copy chúng vào biến stack để tiện dùng. Bạn sẽ thấy kiểu `mov [rbp-18h], rcx` ngay sau prologue, nghĩa là "cất tham số 1 vào một ô cục bộ". Nhận ra pattern này giúp bạn lần ra tham số gốc nằm ở thanh ghi nào.

## Đọc thử một hàm có tham số

```asm
; Win64, -O0
sum3:
    push rbp
    mov  rbp, rsp
    mov  [rbp-18h], ecx    ; cất tham số 1 (a) vào biến cục bộ
    mov  [rbp-14h], edx    ; tham số 2 (b)
    mov  [rbp-10h], r8d    ; tham số 3 (c)
    mov  eax, [rbp-18h]    ; eax = a
    add  eax, [rbp-14h]    ; eax += b
    add  eax, [rbp-10h]    ; eax += c
    pop  rbp
    ret                    ; trả về eax = a+b+c
```

Dịch ngược:

```c
int sum3(int a, int b, int c) {   // a=rcx, b=rdx, c=r8 (Win64)
    return a + b + c;
}
```

Bạn vừa làm hai việc: nhận ra ba tham số từ rcx/rdx/r8 (nên biết đây là Win64), và theo dõi chúng được cộng dồn vào eax để trả về. Đó là toàn bộ nghề đọc hàm.

## Lab tự làm

Thư mục [labs/1.4/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/1.4) có một file C với vài hàm số tham số khác nhau. Nhiệm vụ: build với `-O0` trên cả Windows (hoặc hình dung Win64) và Linux, rồi mở bằng IDA/Ghidra/objdump và tự xác nhận tham số nằm ở thanh ghi nào trên mỗi hệ, đâu là shadow space, đâu là biến cục bộ. Lời giải ở `solution.md`, nhưng tự so trước đã.

## Checklist ghi nhớ
- `call` đẩy địa chỉ trở về lên stack rồi nhảy, `ret` lấy ra và quay về.
- Prologue `push rbp; mov rbp, rsp` đánh dấu đầu hàm, `leave; ret` đánh dấu cuối.
- Win64: tham số 1-4 ở `rcx, rdx, r8, r9`, có shadow space 32 byte. Trả về `rax`.
- System V (Linux/macOS): tham số 1-6 ở `rdi, rsi, rdx, rcx, r8, r9`. Trả về `rax`.
- 32-bit: tham số lên stack. `add esp, N` sau call = cdecl (caller dọn), `ret N` = stdcall (callee dọn).
- Trong IDA: `var_x` là biến cục bộ (`[rbp-x]`), `arg_x` là tham số qua stack. Đổi tên ngay khi hiểu.
