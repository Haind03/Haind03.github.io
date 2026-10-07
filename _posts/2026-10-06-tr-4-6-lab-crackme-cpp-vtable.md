---
title: "Bài 4.6: Lab crackme C++ có vtable, đi qua vtable để tìm hàm check"
date: 2026-10-06 08:36:00 +0700
categories: ["Technique Reverse", "Phần 4 · C++"]
tags: [reverse-engineering, cpp]
render_with_liquid: false
---
Đây là bài gom lại cả Phần 4. Bạn sẽ giải một crackme C++ mà điểm mấu chốt là nó không gọi hàm kiểm tra một cách thẳng thắn như crackme C ở Bài 3.5. Thay vào đó nó gọi qua virtual function, nghĩa là lời gọi đi gián tiếp qua vtable. Nếu bạn quen nếp "tìm chỗ `call check`" của C thì ở đây sẽ hụt, vì trong asm chỉ thấy một `call rcx` trống trơn. Học cách lần qua vtable là mục tiêu của bài.

Crackme nằm ở `labs/4.6/`. Hãy tự giải trước, phần dưới là lời dẫn.

## Bước 1: triage, xác nhận đây là C++

Mở binary bằng Detect It Easy, thường thấy compiler là GCC hoặc MSVC. Nhưng dấu hiệu chắc chắn nhất đây là C++ nằm ở chỗ khác: chạy `nm -C` (Linux) hoặc để IDA/Ghidra demangle, bạn thấy những cái tên như:

```
SerialValidator::check(char const*) const
Validator::Validator()
SerialValidator::~SerialValidator()
```

Tên có `::`, có tham số trong ngoặc, có `const` đuôi. Đó là tên C++ đã demangle. Trong file thô chúng nằm ở dạng mangled kiểu `_ZNK15SerialValidator5checkEPKc`. Thấy mangling là biết ngay không còn ở thế giới C phẳng nữa, có class và method ở đây (xem lại Bài 4.1).

Ngoài ra RTTI để lại chuỗi tên class ngay trong binary. Tìm trong Strings bạn sẽ thấy `SerialValidator`, `Validator`. Đây là quà miễn phí: tên class lộ ra giúp bạn định hướng.

## Bước 2: object có vtable pointer ở đầu

`main` tạo object bằng `new SerialValidator()` rồi gán vào con trỏ kiểu `Validator*`. Vì `check` là virtual, trình biên dịch không biết lúc dịch sẽ gọi hàm nào, nên nó phải tra bảng lúc chạy. Bảng đó là vtable, và mỗi object có virtual function đều mang một con trỏ tới vtable của class mình ngay tại offset 0 (8 byte đầu object trên x64).

Nhớ hình dung này: `object -> [vtable_ptr][field1][field2]...`, và `vtable -> [&check][&name][&destructor]...`. Gọi virtual là hai lần dereference: lấy vtable_ptr từ object, rồi lấy địa chỉ hàm từ vtable.

## Bước 3: đọc lời gọi virtual trong asm

Đây là đoạn thật từ `main` (g++ -O0, cắt gọn), chính là chỗ gọi `v->check(argv[1])`:

```asm
mov  rax, QWORD PTR [rbp-0x18]   ; rax = con trỏ object (this)
mov  rax, QWORD PTR [rax]        ; rax = vtable_ptr (8 byte đầu object)
mov  rcx, QWORD PTR [rax]        ; rcx = vtable[0] = địa chỉ hàm check
mov  rax, QWORD PTR [rbp-0x30]
add  rax, 0x8
mov  rdx, QWORD PTR [rax]        ; rdx = argv[1] (chuỗi nhập)
mov  rax, QWORD PTR [rbp-0x18]
mov  rsi, rdx                    ; rsi = tham số: input
mov  rdi, rax                    ; rdi = this (tham số ẩn đầu tiên)
call rcx                         ; gọi gián tiếp qua vtable
```

Để ý ba điều:

1. Cặp `mov rax,[rax]` rồi `mov rcx,[rax]` là chữ ký kinh điển của một lời gọi virtual: dereference object ra vtable, dereference vtable ra con trỏ hàm.
2. Lệnh cuối là `call rcx`, không phải `call <tên hàm>`. Trong graph của IDA/Ghidra, chỗ này không có mũi tên chỉ tới hàm đích, nên bạn không thể chỉ nhấn đúp để nhảy vào. Đây là chỗ người mới kẹt.
3. `rdi` nhận `this`, `rsi` nhận input. Đây là System V (Linux). Trên Windows x64 sẽ là `rcx` cho `this`, `rdx` cho input (xem lại Bài 4.1 về this pointer).

Vậy làm sao biết `call rcx` thực ra gọi `SerialValidator::check`? Hai cách:

- **Tĩnh:** `vtable[0]` được nạp từ con trỏ vtable, mà vtable của `SerialValidator` do constructor gán vào. Lần theo constructor (hoặc để IDA/Ghidra phân tích RTTI tự gắn) sẽ ra vtable, trong đó slot đầu trỏ tới `check`. Khi đã có RTTI, IDA thường tự đặt tên vtable là `SerialValidator::vftable` và bạn chỉ việc mở ra đọc.
- **Động:** đặt breakpoint tại `call rcx`, nhìn giá trị `rcx` lúc chạy, nó chính là địa chỉ `check`. Nhấn step-into là vào thẳng hàm. Đây là lối tắt khi phân tích tĩnh vtable rối.

## Bước 4: đọc logic trong check

Vào được `SerialValidator::check` rồi thì phần còn lại giống crackme C. Logic nó làm:

```c
if (strlen(input) != 12) return false;
for (int i = 0; i < 12; i++) {
    uint8_t t = (input[i] ^ 0x5A) + i;
    if (t != expected[i]) return false;
}
return true;
```

Mảng `expected` 12 byte nằm trong object (là field của `SerialValidator`, được constructor điền vào). Thuật toán biến đổi từng ký tự rồi so với hằng số, hệt dạng ở Bài 3.5, chỉ khác giờ bạn phải chui qua vtable mới tới được nó.

## Bước 5: đảo ngược để tìm password

Phép biến đổi `t = (c ^ 0x5A) + i` đảo được: `c = (expected[i] - i) ^ 0x5A`. Viết vài dòng Python là ra password. Chi tiết số và lời giải đầy đủ nằm trong `labs/4.6/solution.md`, password đã được kiểm bằng cách build và chạy thật.

## Vì sao bài này quan trọng

Crackme C bạn tìm `call check` là xong. Crackme C++ với virtual function không cho bạn cái đó. Rất nhiều phần mềm thật, nhất là game engine và ứng dụng lớn, dùng đầy virtual call, interface, plugin. Quen lần qua vtable (nhận ra pattern hai lần dereference, dùng RTTI, hoặc đặt breakpoint đọc con trỏ hàm lúc chạy) là kỹ năng bạn sẽ xài suốt đời khi reverse C++.

## Checklist ghi nhớ
- Tên có `::` và tham số sau demangle, cùng chuỗi tên class từ RTTI, là dấu hiệu chắc chắn của C++.
- Object có virtual function mang vtable pointer tại offset 0.
- Lời gọi virtual trong asm: `mov reg,[obj]` rồi `mov reg2,[reg]` rồi `call reg2`. Không có tên hàm đích.
- `this` là tham số ẩn đầu tiên: rdi (Linux) hoặc rcx (Windows).
- Khi kẹt với vtable tĩnh, đặt breakpoint tại `call reg` và đọc giá trị thanh ghi để biết hàm đích.

## Lab tự làm
Thư mục `labs/4.6/`:
- `src/crackme.cpp`: mã nguồn và lệnh build (g++ / MSVC / MinGW).
- `README.md`: nhiệm vụ.
- `solution.md`: writeup đầy đủ kèm password đã kiểm.
