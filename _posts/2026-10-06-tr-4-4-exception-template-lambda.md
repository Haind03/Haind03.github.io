---
title: "Bài 4.4: Exception, template và lambda, ba thứ C++ hiện đại làm binary rối"
date: 2026-10-06 08:34:00 +0700
categories: ["Technique Reverse", "Phần 4 · C++"]
tags: [reverse-engineering, cpp]
render_with_liquid: false
---
Tới đây bạn đã đọc được class, vtable, này nọ. Nhưng code C++ thật ngoài đời còn ba thứ làm người mới hoảng khi mở decompiler: khối try/catch biến thành một mớ bảng khó hiểu, một hàm nhỏ bỗng xuất hiện năm sáu bản gần giống nhau, và một lambda trông đơn giản lại hoá thành cả một class ẩn. Hiểu cơ chế của ba thứ này thì chúng hết đáng sợ, chỉ còn là tiếng ồn bạn biết cách bỏ qua.

## Template: một hàm nguồn, nhiều hàm binary

Đây là thứ dễ hiểu nhất nên nói trước. Khi bạn viết một template:

```cpp
template <typename T>
T add_one(T x) { return x + (T)1; }
```

thì trong source chỉ có một hàm. Nhưng compiler không sinh ra "một hàm chung" cho mọi kiểu. Mỗi lần bạn gọi với một kiểu mới, nó sinh hẳn một hàm riêng biệt, gọi là một instantiation. Gọi `add_one<int>` và `add_one<double>` cho ra hai hàm máy khác nhau hoàn toàn.

Nhìn danh sách symbol của chương trình lab là thấy ngay:

```
int    add_one<int>(int)       -> _Z7add_oneIiET_S0_
double add_one<double>(double) -> _Z7add_oneIdET_S0_
```

Và đoạn asm của bản int (gcc -O0, đã demangle tên):

```asm
_Z7add_oneIiET_S0_:        ; add_one<int>
    mov   [rbp-0x4], edi    ; x (tham số, int)
    mov   eax, [rbp-0x4]
    add   eax, 0x1          ; return x + 1
    ret
```

Bản double sẽ dùng thanh ghi SSE (xmm) và lệnh `addsd` thay vì `add`, vì nó làm số thực. Cùng một logic nguồn, hai thân hàm khác nhau.

Hệ quả khi reverse:
- **Binary phình to.** Một template dùng với mười kiểu là mười hàm. Thư viện nặng template (STL, Boost) đẩy số hàm lên hàng nghìn.
- **Bạn sẽ thấy nhiều hàm gần như giống hệt**, chỉ khác kích thước dữ liệu hoặc kiểu lệnh. Đừng tưởng tác giả copy-paste, đó là template instantiation.
- **Mẹo tiết kiệm công:** hiểu một bản là hiểu cả họ. Đọc `add_one<int>`, rồi các bản khác chỉ liếc qua xác nhận cùng logic. Đặt tên nhất quán kiểu `add_one_int`, `add_one_double` để khỏi lẫn.

## Lambda: một class ẩn đội lốt hàm

Lambda nhìn như một hàm vô danh nhỏ xíu, nhưng compiler biến nó thành một object. Cụ thể, lambda này:

```cpp
int base = n * 10;
auto make = [base](int k) { return base + k; };
make(7);
```

được compiler dịch thành đại khái:

```cpp
struct __lambda {
    int base;                 // capture by value -> field
    int operator()(int k) const { return base + k; }
};
__lambda make{ n * 10 };
make(7);                      // thực chất gọi make.operator()(7)
```

Nghĩa là: **mỗi biến capture trở thành một field** của một struct ẩn, và **thân lambda trở thành method `operator()`** của struct đó. Gọi lambda chính là gọi method, nên nó có `this` pointer y như bài [4.1](/posts/tr-4-1-name-mangling-this-method-call/) đã nói.

Đây là asm thật của `operator()` của lambda trên (gcc -O0), nhìn là ra ngay:

```asm
main::{lambda(int)#1}::operator()(int) const:
    mov   [rbp-0x8], rdi     ; rdi = this (object lambda chứa capture)
    mov   [rbp-0xc], esi     ; esi = k (tham số thật)
    mov   rax, [rbp-0x8]     ; rax = this
    mov   edx, [rax]         ; edx = this->base  (capture nằm ở offset 0)
    mov   eax, [rbp-0xc]     ; eax = k
    add   eax, edx           ; return base + k
    ret
```

Để ý hai điều khẳng định đúng mô hình trên: tham số đầu `rdi` là `this` (SysV, trên Windows sẽ là `rcx`), và `[rax]` đọc field `base` ngay đầu object. Capture đã thành dữ liệu trong object, không còn là biến cục bộ.

Khi reverse, nhận ra lambda qua: một struct nhỏ được dựng ngay tại chỗ (các `mov` ghi capture vào object trên stack), rồi một lời gọi method với object đó làm `this`. Tên mangled của nó chứa chuỗi kiểu `ZZ...EUl...` (U cho unnamed lambda). IDA/Ghidra thường hiển thị tên dài loằng ngoằng, cứ rename thành `lambda_xxx` cho dễ.

## Exception: cái giá của try/catch

Đây là phần làm rối nhất. Trong source, try/catch gọn gàng. Trong binary, nó tách thành hai phần: đường chạy bình thường (happy path) và bộ máy xử lý khi có exception, nằm tách biệt, nối với nhau qua các bảng dữ liệu.

Hai ABI chính, khác nhau khá nhiều:

**Linux / Itanium C++ ABI.** Khi `throw`, runtime gọi `__cxa_throw`, rồi nó lần ngược stack (stack unwinding) để tìm handler. Thông tin "frame này có handler nào, cần dọn gì" không nằm trong code mà trong các section riêng: `.eh_frame`, `.gcc_except_table`. Chỗ code bắt exception gọi là landing pad. Trong decompiler bạn thấy hàm có vẻ "kết thúc" ở `ret` nhưng vẫn còn những khối code lẻ phía sau không ai gọi tới trực tiếp, đó là landing pad, runtime nhảy vào khi unwind.

**Windows / MSVC.** Dùng cơ chế khác, với các funclet (hàm con cho catch block) và dữ liệu unwind trong `.pdata`/`.xdata`. Bạn sẽ thấy các con trỏ tới bảng `FuncInfo`, `__CxxFrameHandler`. Các hàm liên quan: `_CxxThrowException`.

Điểm chung thực tế cho người reverse:
- **Code try/catch bị cắt rời.** Thân try chạy thẳng, phần catch nằm ở khối tách biệt mà luồng chính không nhảy tới bằng `jmp` thường. Đừng hoảng khi thấy code "mồ côi" sau hàm, đó thường là handler.
- **Đừng sa đà vào bảng unwind** trừ khi bạn thực sự cần. Trong 90% trường hợp reverse một crackme hay tìm logic chính, bạn chỉ cần biết "chỗ này có thể ném exception, chỗ kia bắt" rồi đi tiếp. Bản thân bảng EH hiếm khi là nơi giấu bí mật.
- Thấy lời gọi `__cxa_throw` / `_CxxThrowException` là biết có một đường thoát bằng exception từ đây. Thấy `__cxa_begin_catch` / `__CxxFrameHandler` là đang ở vùng xử lý.

## Gộp lại: đừng để tiếng ồn che mất tín hiệu

Cả ba thứ này đều là compiler sinh thêm code quanh logic thật của tác giả. Chiến lược chung giống nhau: nhận ra chúng, dán nhãn, rồi tập trung vào phần logic. Template là nhiều bản của một hàm (hiểu một, suy ra cả họ). Lambda là class ẩn (tìm `operator()` và field capture). Exception là code bị cắt rời (happy path là chính, handler để sau). Biết ba khuôn này, bạn đọc code C++ hiện đại mà không bị số lượng hàm và các khối lạ làm nản.

## Lab tự làm

Thư mục [labs/4.4/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/4.4). Build `src/modern.cpp`, rồi:
- Tìm trong symbol hai instantiation `add_one<int>` và `add_one<double>`, so asm của chúng.
- Tìm `operator()` của lambda, xác định đâu là `this`, đâu là field capture.
- Khoanh vùng khối try/catch: tìm lời gọi throw và chỗ handler nằm tách ra.

Chi tiết và lời giải trong [README](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/4.4/README.md) và [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/4.4/solution.md).

## Checklist ghi nhớ
- Template: mỗi kiểu là một hàm riêng trong binary. Nhiều hàm gần giống nhau thường là instantiation, không phải copy-paste.
- Lambda: trở thành struct ẩn, capture thành field, thân thành `operator()` có `this` pointer.
- Exception: try/catch bị tách thành happy path và handler rời, nối qua bảng unwind (.eh_frame/.gcc_except_table trên Linux, .pdata/.xdata trên Windows).
- Dấu hiệu throw: `__cxa_throw` (Linux), `_CxxThrowException` (MSVC).
- Đừng sa đà vào bảng EH, phần lớn thời gian chỉ cần biết "có thể ném ở đây, bắt ở kia".
