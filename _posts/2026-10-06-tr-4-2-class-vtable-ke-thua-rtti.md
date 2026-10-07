---
title: "Bài 4.2: Class, vtable, kế thừa và RTTI, dựng lại cây class"
date: 2026-10-06 08:32:00 +0700
categories: ["Technique Reverse", "Phần 4 · C++"]
tags: [reverse-engineering, cpp]
render_with_liquid: false
---
Nếu bài trước nói về `this` pointer và name mangling, thì bài này là trái tim của C++ reverse. Lý do dân mới ghét C++ không phải vì cú pháp, mà vì một lời gọi hàm tưởng đơn giản lại biến thành `call rdx` không rõ gọi đi đâu. Đó là virtual call, và đằng sau nó là vtable. Hiểu vtable là bạn đọc được C++, không hiểu thì mãi mắc kẹt ở đống `call [reg]` bí ẩn.

## Vì sao có vtable

Trong C++, khi một class có virtual function, compiler phải giải quyết một bài toán: lúc biên dịch nó chưa biết `s->area()` sẽ gọi `Circle::area` hay `Rectangle::area`, vì `s` chỉ là con trỏ `Shape*`, kiểu thật chỉ biết lúc chạy. Giải pháp là bảng hàm ảo (virtual function table, gọi tắt vtable).

Cơ chế gồm hai phần:

- Mỗi class có virtual function sẽ có **một vtable riêng**, là một mảng con trỏ hàm nằm trong vùng chỉ đọc (.rdata trên Windows, .rodata trên Linux). Mỗi virtual function chiếm một ô.
- Mỗi object của class đó, ở **offset 0** (ngay đầu object), chứa một con trỏ trỏ tới vtable của class mình. Con trỏ này gọi là vptr.

Khi gọi `s->area()`, code không nhảy thẳng tới một địa chỉ cố định. Nó làm ba bước: lấy vptr từ đầu object, vào vtable lấy đúng ô của `area`, rồi gọi con trỏ hàm trong ô đó. Vì Circle và Rectangle có vptr trỏ tới hai vtable khác nhau, cùng một dòng code gọi ra hai hàm khác nhau. Đó là polymorphism nhìn từ dưới lên.

## Layout của một object

Lấy ví dụ lab trong bài này:

```cpp
class Shape {
    int id;
    virtual double area() = 0;
    virtual const char* name();
    virtual ~Shape();
};
class Circle : public Shape {
    double radius;
};
```

Trên x86-64, object `Circle` nằm trong bộ nhớ như sau (số liệu lấy từ biên dịch thật bằng g++):

```
offset 0  : vptr        (8 byte, con trỏ tới vtable của Circle)
offset 8  : id          (4 byte, kế thừa từ Shape)
offset 12 : padding     (4 byte, để radius thẳng hàng 8)
offset 16 : radius      (8 byte, field riêng của Circle)
tổng sizeof(Circle) = 24
```

Hai điều cần khắc cốt:

1. **vptr luôn ở offset 0.** Thấy một hàm nạp `[object]` rồi lại nạp `[kết quả đó]` để gọi, đó là đang đi qua vptr vào vtable. Đây là dấu vân tay của C++.
2. **Field của class cha nằm trước field của class con.** Circle gồm toàn bộ phần Shape (vptr + id) rồi mới tới radius. Kế thừa đơn chính là xếp chồng layout: một `Circle*` ép sang `Shape*` không đổi địa chỉ, vì phần Shape nằm ngay đầu.

## Nhận ra virtual call trong assembly

![Object, vtable và lời gọi virtual qua call reg+offset](/assets/img/technique-reverse/assets/phan-04/vtable.svg)

Đây là đoạn asm thật của hàm `report(Shape* s)` gọi `s->name()` và `s->area()`, biên dịch bằng `g++ -O0`:

```asm
mov  QWORD PTR [rbp-0x18], rdi   ; lưu tham số s (con trỏ object)
mov  rax, QWORD PTR [rbp-0x18]   ; rax = s
mov  rax, QWORD PTR [rax]        ; rax = *s = vptr  (đọc vtable tại offset 0)
mov  rdx, QWORD PTR [rax]        ; rdx = vtable[0]  (ô đầu tiên của vtable)
mov  rdi, QWORD PTR [rbp-0x18]   ; rdi = s          (this pointer, tham số ẩn đầu tiên)
call rdx                         ; gọi virtual function qua con trỏ
...
mov  rax, QWORD PTR [rax]        ; rax = vptr lần nữa
add  rax, 0x8                    ; rax = vtable + 8
mov  rdx, QWORD PTR [rax]        ; rdx = vtable[1]  (ô thứ hai)
call rdx                         ; gọi virtual function thứ hai
...
mov  eax, DWORD PTR [rax+0x8]    ; đọc s->id  (field thường tại offset 8)
```

Đọc ra ngay ba đặc trưng:

- **Hai lần dereference trước khi call:** `mov rax,[s]` rồi `mov rax,[rax]`. Lần một lấy vptr (vì vptr ở offset 0 nên `[s]` chính là vptr), lần hai lấy con trỏ hàm từ vtable. Đây là mẫu không lẫn đi đâu được.
- **`call rdx` thay vì `call địa_chỉ`:** gọi gián tiếp qua thanh ghi, vì địa chỉ hàm chỉ biết lúc chạy.
- **`vtable[0]`, `vtable+8`, `vtable+16`...:** mỗi offset là một virtual function theo thứ tự khai báo. Biết thứ tự này là biết đang gọi hàm nào.

So với một lời gọi thường (`call sub_401500`, địa chỉ cố định), virtual call luôn có dạng `call [reg]` hoặc `call [reg+offset]`. Thấy nó là biết mình đang ở trong code C++ hướng đối tượng.

## Dùng vtable để dựng lại cây class

Vtable không chỉ gây khó, nó còn là món quà: nó cho bạn danh sách mọi virtual function của một class, gom lại một chỗ.

Quy trình dựng lại hierarchy:

1. **Tìm các vtable.** Chúng là những mảng con trỏ hàm trong .rdata/.rodata. IDA và Ghidra thường tự nhận ra và đặt tên kiểu `Circle::vftable` hoặc `vtable for Circle`.
2. **Đọc các ô trong một vtable** để biết class đó có những virtual function nào. Mỗi ô trỏ tới một hàm, đọc hàm đó là hiểu class làm gì.
3. **Tìm constructor để biết class nào dùng vtable nào.** Constructor là nơi vptr được ghi vào offset 0 của object (`mov [object], offset vtable`). Thấy một hàm ghi một địa chỉ vtable vào `[rcx]` hoặc `[rdi]` ở đầu, đó gần như chắc là constructor, và nó buộc object với class tương ứng.
4. **So các vtable để suy kế thừa.** Nếu vtable của Circle và Rectangle chia sẻ vài ô đầu (cùng con trỏ, hoặc cùng chữ ký) rồi khác ở các ô sau, chúng nhiều khả năng có chung class cha.

## RTTI, con đường tắt khi có

RTTI (Run-Time Type Information) là dữ liệu C++ sinh ra để hỗ trợ `dynamic_cast` và `typeid`. Khi binary được biên dịch có RTTI (mặc định với g++ và MSVC, trừ khi tắt bằng `-fno-rtti` hoặc `/GR-`), mỗi class polymorphic có một cấu trúc `type_info` chứa **tên class ở dạng chuỗi**.

Đây là vàng cho reverser:

- Trong binary có RTTI, bạn sẽ thấy chuỗi kiểu `.?AVCircle@@` (MSVC) hoặc `6Circle` (Itanium ABI của g++) trong strings. Tên class lộ ra trần trụi.
- IDA (với plugin như Class Informer) và Ghidra tự đọc RTTI để đặt tên vtable và class theo đúng tên gốc. Tự nhiên `sub_xxx::vftable` thành `Circle::vftable`.
- RTTI còn mô tả quan hệ kế thừa (base class array), nên nhiều khi dựng lại được cả cây mà không cần đoán.

Ngược lại, binary biên dịch `-fno-rtti` sẽ không có các chuỗi này, vtable vẫn còn nhưng bạn phải tự đặt tên class. Vì vậy một trong những việc đầu tiên khi gặp C++ là kiểm tra có RTTI hay không: có thì nhẹ nhõm, không thì xắn tay dựng tay.

## Checklist ghi nhớ
- Virtual function dẫn tới vtable: mỗi class một vtable (mảng con trỏ hàm trong .rdata/.rodata), mỗi object có vptr ở offset 0 trỏ tới vtable của mình.
- Virtual call trong asm: hai lần dereference rồi `call [reg]` hoặc `call [reg+offset]`. Offset chọn hàm theo thứ tự khai báo.
- Kế thừa đơn = xếp chồng layout: phần class cha nằm trước, nên `Derived*` ép sang `Base*` không đổi địa chỉ.
- Constructor ghi vptr vào offset 0 của object, dùng nó để biết object thuộc class nào.
- RTTI (nếu có) lộ tên class dưới dạng chuỗi, IDA/Ghidra tự đặt tên theo đó. Kiểm tra RTTI là việc đầu tiên khi gặp C++.
