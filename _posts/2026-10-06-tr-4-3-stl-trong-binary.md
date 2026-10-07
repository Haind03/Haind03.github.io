---
title: "Bài 4.3: STL trong binary, đọc std::string và std::vector như người bản xứ"
date: 2026-10-06 08:33:00 +0700
categories: ["Technique Reverse", "Phần 4 · C++"]
tags: [reverse-engineering, cpp]
render_with_liquid: false
---
Code C++ thật gần như không bao giờ chỉ dùng mảng C trần. Nó đầy `std::string`, `std::vector`, `std::map`. Tin tốt: mỗi container này có một layout cố định, lặp đi lặp lại. Một khi bạn nhận ra khuôn của chúng, một đống `[rax]`, `[rax+8]`, `[rax+10h]` trong pseudocode đột nhiên có nghĩa, và bạn đọc được "à đây là một string, kia là một vector" mà không cần decompiler nói hộ.

Bài này tập trung vào hai container bạn gặp nhiều nhất (`string` và `vector`), rồi điểm nhanh phần còn lại. Mọi con số layout dưới đây là từ libstdc++ trên x64 (toolchain g++), đã kiểm bằng chương trình lab. MSVC khác đôi chút, có ghi chú ở cuối.

## std::string, và cú lừa mang tên SSO

Người mới hay tưởng `std::string` chỉ là một con trỏ tới chuỗi. Sai, và chính chỗ sai đó làm họ đọc nhầm binary.

Trên libstdc++, `std::string` là một object **32 byte** gồm:

```
offset 0  : char*   con trỏ tới dữ liệu (_M_p)
offset 8  : size_t  độ dài chuỗi (_M_string_length)
offset 16 : union 16 byte {
              char   buffer nội bộ [16]   // dùng khi chuỗi ngắn
              size_t capacity             // dùng khi chuỗi dài
            }
```

Điểm mấu chốt là **Small String Optimization (SSO)**: nếu chuỗi đủ ngắn (tối đa 15 ký tự trên libstdc++), nó không cấp phát heap mà nhét luôn ký tự vào 16 byte buffer ngay bên trong object. Con trỏ ở offset 0 khi đó trỏ vào **chính object** (địa chỉ object + 16).

Lab in ra đúng điều này:

```
--- std::string ngan (SSO) ---
addr object  = 0x7ffec62d5060
data()       = 0x7ffec62d5070   (= object + 16, tro VAO chinh no)
size         = 2
capacity     = 15

--- std::string dai (heap) ---
addr object  = 0x7ffec62d5080
data()       = 0x6306a1464eb0   (tro ra heap, xa object)
size         = 39
capacity     = 39
```

Cách nhận ra `std::string` trong lúc debug: tìm một object mà offset 0 là con trỏ, offset 8 là một số nhỏ hợp lý (độ dài), và nếu con trỏ đó trỏ ngược vào chính object thì bạn đang nhìn một chuỗi ngắn SSO. Thấy capacity là 15 cũng là dấu hiệu rất đặc trưng của string rỗng hoặc ngắn trên libstdc++.

Trong asm, một thao tác lấy độ dài chuỗi thường là:

```asm
mov  rax, [rbx+8]      ; rax = độ dài chuỗi (field _M_string_length)
```

và lấy con trỏ dữ liệu để đọc ký tự:

```asm
mov  rax, [rbx]       ; rax = con trỏ data
movzx eax, byte [rax] ; đọc ký tự đầu
```

Thấy cặp "đọc [obj] làm con trỏ, đọc [obj+8] làm độ dài" là gần như chắc chắn một `std::string`.

## std::vector, ba con trỏ nói lên tất cả

![Layout std::string với SSO và std::vector ba con trỏ](/assets/img/technique-reverse/assets/phan-04/stl-layout.svg)

`std::vector` còn dễ nhận hơn. Trên libstdc++ nó chỉ là **ba con trỏ, 24 byte**:

```
offset 0  : T* _M_start            con trỏ tới phần tử đầu
offset 8  : T* _M_finish           con trỏ tới sau phần tử cuối
offset 16 : T* _M_end_of_storage   con trỏ tới hết vùng đã cấp
```

Từ ba con trỏ này suy ra mọi thứ:

```
size()     = (_M_finish - _M_start) / sizeof(T)
capacity() = (_M_end_of_storage - _M_start) / sizeof(T)
```

Nên trong pseudocode, khi thấy compiler tính `(v[8] - v[0]) >> 2` thì đó chính là `size()` của một `vector<int>` (chia 4 vì int 4 byte, `>>2` là chia 4). Nhận ra pattern "hiệu hai con trỏ rồi chia cho kích thước phần tử" là nhận ra vector.

Lab xác nhận:

```
sizeof(std::vector<int>) = 24    (đúng 3 con trỏ)
begin (data) = 0x...ee0          (trỏ ra heap)
size = 4, capacity = 4
```

Vòng lặp duyệt vector trong asm thường có dạng: nạp `_M_start` vào một thanh ghi, nạp `_M_finish` vào thanh ghi khác, lặp tăng con trỏ tới khi bằng nhau. Thấy khuôn "chạy con trỏ từ [obj] tới [obj+8]" là vòng `for (auto& x : v)`.

## Các container còn lại, điểm nhanh

Bạn sẽ gặp ít hơn, nhưng nên biết mặt:

- **std::map / std::set**: cài bằng cây đỏ đen (red-black tree). Mỗi node có con trỏ parent, left, right, một bit màu, rồi tới key/value. Trong binary bạn thấy rất nhiều thao tác con trỏ xoay cây và so sánh. `sizeof` của bản thân map nhỏ (48 byte ở lab, chủ yếu là header node và bộ đếm). Nhận ra map qua việc nó gọi các hàm thư viện rất dài tên liên quan `_Rb_tree`.
- **std::unique_ptr**: thường chỉ là một con trỏ trần (8 byte), gần như biến mất sau tối ưu. Nó chỉ khác con trỏ thường ở chỗ destructor tự gọi `delete`.
- **std::shared_ptr**: hai con trỏ (16 byte), một trỏ object, một trỏ control block chứa reference count. Thấy thao tác tăng giảm một số nguyên qua lock (atomic) cạnh một con trỏ là dấu hiệu shared_ptr.

## MSVC khác gì

Nếu binary build bằng MSVC (hay gặp trên Windows), con số đổi nhưng ý tưởng giữ nguyên:

- `std::string` MSVC cũng có SSO nhưng buffer 16 byte và ngưỡng 15 ký tự, layout field khác thứ tự, `sizeof` thường là 32 (x64) nhưng bố trí union ở đầu.
- `std::vector` MSVC vẫn là ba con trỏ (first, last, end), giống về bản chất.
- Tên hàm thư viện khác (mangling kiểu MSVC `?...@@`), nhưng IDA/Ghidra demangle ra là nhận ra ngay.

Quy tắc thực dụng: đừng học thuộc offset của mọi toolchain. Học **khuôn tư duy**: string = con trỏ + size + (buffer hoặc capacity), vector = ba con trỏ. Gặp binary lạ thì build một chương trình nhỏ bằng đúng compiler đó, in offset ra, rồi áp vào. Đó chính là nội dung lab.

## Mẹo khi dùng decompiler

Cả IDA và Ghidra đều cho bạn khai báo kiểu `std::string` / `std::vector` rồi gán cho biến, sau đó pseudocode tự hiển thị `.size()`, `.data()` thay vì offset trần. Với IDA Pro, plugin như HexRaysPyTools (xem [Bài 4.5](/posts/tr-4-5-plugin-ho-tro-cpp/)) còn tự nhận diện nhiều container. Nhưng ngay cả khi không có plugin, nhận ra khuôn bằng mắt vẫn là kỹ năng nền tảng, vì không phải lúc nào decompiler cũng đoán đúng.

## Lab tự làm

Thư mục [labs/4.3/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/4.3). Bạn sẽ build `containers.cpp`, chạy để thấy số liệu layout thật trên máy mình, rồi mở trong debugger quan sát SSO và ba con trỏ của vector tận mắt. Chi tiết trong README của lab, lời giải ở `solution.md`.

## Checklist ghi nhớ
- `std::string` (libstdc++, 32 byte): [0]=con trỏ data, [8]=size, [16]=union buffer/capacity.
- SSO: chuỗi tối đa 15 ký tự nằm ngay trong object, con trỏ data trỏ vào chính object (object+16).
- `std::vector` = ba con trỏ (24 byte): start, finish, end_of_storage. size = (finish-start)/sizeof(T).
- Thấy "hiệu hai con trỏ rồi chia kích thước phần tử" là đang tính size của vector.
- map/set là cây đỏ đen (_Rb_tree), shared_ptr có control block với refcount atomic.
- MSVC khác số nhưng cùng ý tưởng. Build thử bằng đúng compiler để lấy offset chuẩn.
