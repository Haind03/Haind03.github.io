---
title: "Bài 4.1: C++ dưới mắt reverser, name mangling và this pointer"
date: 2026-10-06 08:31:00 +0700
categories: ["Technique Reverse", "Phần 4 · C++"]
tags: [reverse-engineering, cpp]
render_with_liquid: false
---
Về mặt binary, C++ không phải một ngôn ngữ mới mà là C cộng thêm vài quy ước. Compiler bẻ class, method, template, exception thành đúng những lệnh assembly bạn đã biết. Vấn đề là nó bẻ theo cách khiến tên hàm trông như mèo quào và mỗi lời gọi method lại lén truyền thêm một tham số. Hiểu hai thứ đó, name mangling và this pointer, là qua được 80% nỗi sợ C++.

## Vì sao tên hàm biến thành mèo quào

Trong C, hàm `add` biên dịch ra một symbol tên đúng là `add`. Đơn giản vì C không cho hai hàm trùng tên.

C++ thì cho. Bạn viết được `add(int)` và `add(int, int)` trong cùng một class, đó là overloading. Nhưng linker chỉ làm việc với tên symbol, mà hai hàm cùng tên `add` thì nó biết nối cái nào? Giải pháp của compiler: nhét thông tin class, tên method và kiểu tham số vào tên symbol. Quá trình đó gọi là name mangling (băm tên).

Lấy một class thật:

```cpp
class Counter {
    int value;
public:
    Counter(int start) : value(start) {}
    void add(int n)        { value += n; }
    void add(int n, int m) { value += n + m; }
    int  get() const       { return value; }
};
```

Biên dịch bằng g++ rồi xem symbol (lệnh `nm`), bạn thấy tên thật trong binary:

```
_ZN7Counter3addEi      ->  Counter::add(int)
_ZN7Counter3addEii     ->  Counter::add(int, int)
_ZN7CounterC1Ei        ->  Counter::Counter(int)      (constructor)
_ZNK7Counter3getEv     ->  Counter::get() const
```

Nhìn qua thì rối, nhưng có quy luật: `_ZN` mở đầu, `7Counter` là class dài 7 ký tự, `3add` là method dài 3 ký tự, `E` kết thúc danh sách tên, rồi `i` là int, `ii` là hai int, `v` là void. Chữ `K` trong `_ZNK` nghĩa là method const. Hai hàm `add` giờ có tên khác nhau nhờ phần kiểu tham số, linker phân biệt được.

Đó là kiểu mangling của GCC/Clang (chuẩn Itanium). MSVC dùng kiểu khác, bắt đầu bằng dấu `?`:

```
?add@Counter@@QEAAXH@Z      ->  public: void __cdecl Counter::add(int)
```

Nhìn lạ hơn nữa, nhưng bạn không cần đọc tay. Việc đó để tool làm.

## Demangle: trả tên về cho người đọc

![Name mangling: cùng một method thành tên khác nhau trên GCC và MSVC](/assets/img/technique-reverse/assets/phan-04/name-mangling.svg)

Không ai ngồi giải mangling bằng mắt. Dùng công cụ:

- **c++filt** (đi kèm GCC): `echo _ZN7Counter3addEi | c++filt` ra ngay `Counter::add(int)`. Pipe cả output `nm` qua nó là demangle hàng loạt.
- **undname** (đi kèm MSVC): làm việc tương tự cho tên kiểu `?...`.
- **IDA và Ghidra tự demangle**. IDA hiển thị luôn `Counter::add(int)` trong danh sách hàm, bạn gần như không phải làm gì. Nếu thấy tên vẫn ở dạng mangled, kiểm tra lại cấu hình demangling trong options.

Điểm quan trọng với reverser: **name mangling là món quà, không phải rào cản.** Một binary C++ còn symbol cho bạn biết luôn tên class, tên method, kiểu tham số, nhiều thông tin hơn hẳn C. Chỉ khi binary bị strip symbol thì bạn mới mất phần quà này và phải suy từ cấu trúc.

## this pointer, tham số ẩn của mọi method

Đây là khác biệt lớn thứ hai. Khi bạn viết `c.add(5)`, có vẻ chỉ một tham số. Nhưng method cần biết nó đang làm việc trên object nào (`c` nào), nên compiler lén truyền thêm địa chỉ của object làm tham số đầu tiên. Đó là this pointer.

Quy tắc nằm lòng:

- Trên **Linux/SysV**, this nằm ở **rdi** (tham số đầu), tham số thật dồn xuống rsi, rdx...
- Trên **Windows x64**, this nằm ở **rcx** (tham số đầu), tham số thật dồn xuống rdx, r8...

Nhìn asm thật của `c.add(5)` trên Linux (g++, -O0), với object `c` là biến cục bộ tại `[rbp-0xc]`:

```asm
lea    rax, [rbp-0xc]      ; rax = địa chỉ của object c
mov    esi, 0x5            ; tham số thật n = 5 vào rsi (tham số thứ hai)
mov    rdi, rax            ; this = &c vào rdi (tham số đầu, ẩn)
call   _ZN7Counter3addEi   ; gọi Counter::add(int)
```

Dịch ngược ra C++ thì chỉ là `c.add(5)`, nhưng ở mức binary nó là một hàm hai tham số: `add(&c, 5)`. Thấy một lời gọi mà tham số đầu (rdi/rcx) là một con trỏ trỏ tới vùng nhớ chứa dữ liệu object, bạn đang nhìn một method call, không phải hàm thường.

Mẹo thực chiến: trong pseudocode của IDA/Ghidra, nếu một hàm dùng tham số đầu kiểu `a1->field` liên tục, gần như chắc `a1` chính là this, và bạn nên đổi tên nó thành `this` rồi gán kiểu class. Pseudocode sẽ gọn hẳn.

## Phân biệt method call với hàm thường

Gộp hai thứ trên lại, đây là cách nhận ra bạn đang xem C++ chứ không phải C:

1. **Tên hàm mangled** (`_ZN...` hoặc `?...@@`) trong danh sách hàm. Dấu hiệu rõ ràng nhất.
2. **Lời gọi luôn nạp một con trỏ object vào rdi/rcx trước call**, và con trỏ đó được tái sử dụng để truy cập field theo offset (`[this+0]`, `[this+4]`).
3. **Constructor** chạy ngay sau khi cấp vùng nhớ cho object (trên stack hoặc sau `new`), thường là hàm đầu tiên đụng tới vùng nhớ đó.

Khi gặp cả ba, bỏ tư duy "hàm C độc lập" đi và bắt đầu nghĩ theo object: cái gì là this, class có những field gì, method nào đọc/ghi field nào. Bài [4.2](https://github.com/Haind03/Technique-Reverse/blob/main/phan-04-cpp/4.2-class-vtable-ke-thua.md) đi tiếp vào vtable và kế thừa, nơi C++ thật sự khác C.

## Lab tự làm

Thư mục [labs/4.1/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/4.1). Bạn sẽ build một class nhỏ, xem tên mangled trong binary, demangle, và chỉ ra this pointer ở rdi/rcx trong một lời gọi method. Làm xong đối chiếu [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/4.1/solution.md).

## Checklist ghi nhớ
- C++ ở mức binary là C cộng vài quy ước, không phải thế giới mới.
- Name mangling nhét class + method + kiểu tham số vào tên symbol để hỗ trợ overloading. GCC/Clang dùng `_ZN...`, MSVC dùng `?...@@`.
- Đừng giải mangling bằng tay: c++filt, undname, hoặc để IDA/Ghidra tự demangle.
- Symbol C++ là quà: cho biết tên class/method/tham số, nhiều hơn C.
- Mọi method có tham số ẩn this: rdi trên Linux, rcx trên Windows x64.
- Lời gọi nạp con trỏ object vào rdi/rcx rồi truy cập field theo offset chính là method call.

---
Phần trước: Phần 3 C · [Về mục lục](/technique-reverse/) · Bài tiếp: 4.2 Class, vtable, kế thừa, RTTI
