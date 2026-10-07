---
title: "Bài 9.1: Đặc trưng binary Rust, nhận mặt trước khi đọc"
date: 2026-10-06 09:03:00 +0700
categories: ["Technique Reverse", "Phần 9 · Rust"]
tags: [reverse-engineering, rust]
render_with_liquid: false
---
Rust đang lan nhanh, từ công cụ dòng lệnh tới malware, nên sớm muộn bạn cũng vấp một binary Rust. Tin xấu: Rust là một trong những thứ khó đọc nhất ở tầng native, khó hơn C++ và hơn hẳn Go. Tin tốt: nó để lại vài dấu vết rất đặc trưng, và có một món quà tên là panic string giúp bạn định vị code nhanh. Bài này dạy cách nhận mặt một binary Rust và biết trước mình đang đương đầu với cái gì.

## Vì sao Rust khó đọc

Ba lý do, hiểu được là bớt sốc khi mở decompiler:

1. **Monomorphization.** Generic trong Rust không dùng chung một bản như template bị chia sẻ. Mỗi kiểu cụ thể sinh ra một bản copy riêng của hàm. Một `Vec<T>` dùng với năm kiểu là năm bản hàm gần giống nhau, binary phình và đầy hàm trùng lặp.
2. **Inline hung hãn.** Trình tối ưu của Rust (qua LLVM) inline rất mạnh. Một iterator chain đẹp đẽ kiểu `.iter().map().filter().collect()` biến thành một vòng lặp phẳng, không còn ranh giới hàm nào để bám.
3. **Static link mặc định.** Giống Go, binary Rust thường gói cả standard library vào, nên file to và lẫn rất nhiều code thư viện với code của tác giả.

Khác Go một điểm quan trọng: Rust **không có runtime GC**, không có scheduler goroutine. Về cấu trúc, nó gần C++ hơn, nên kinh nghiệm đọc C++ ở Phần 4 (nhất là vtable, struct, STL) áp dụng được nhiều.

## Nhận ra một binary Rust

![Binary Rust: panic string, mangling v0, iterator inline](/assets/img/technique-reverse/assets/phan-09/rust-binary.svg)

Vài dấu hiệu, dùng DIE hoặc `strings`:

- **Chuỗi đường dẫn source** kiểu `src/main.rs`, `library/std/src/...`, `/rustc/<hash>/...`. Rust nhúng đường dẫn file vào thông tin panic, lộ ra ngay.
- **Chuỗi phiên bản** `rustc 1.xx.x`.
- **Tên crate** trong symbol: `core::`, `alloc::`, `std::`, và tên crate bên thứ ba.
- **Symbol bị mangle** bắt đầu bằng `_ZN` (legacy) hoặc `_R` (v0), xem phần dưới.
- **Chuỗi panic** kiểu `called \`Option::unwrap()\` on a \`None\` value`, `index out of bounds`, `attempt to add with overflow`.

## Name mangling: hai kiểu

Rust có hai kiểu mangling, bạn sẽ gặp cả hai tuỳ phiên bản và cờ build:

- **Legacy** (mặc định cũ): trông như C++ Itanium, bắt đầu `_ZN`, ví dụ `_ZN4core3fmt9Formatter3pad17h...E`. Có một hash ở cuối (`17h...`) để phân biệt các bản monomorphized.
- **v0** (mới, bật bằng `-C symbol-mangling-version=v0`): bắt đầu `_R`, mã hoá được cả generic, ví dụ `_RNvNtCs...`. Đọc thô thì rối hơn nhưng chứa nhiều thông tin hơn.

Để đọc lại tên, demangle:
- **rustfilt**: `cat symbols.txt | rustfilt`, hoặc `nm binary | rustfilt`.
- **IDA/Ghidra** đời mới tự demangle được cả hai kiểu, bật trong cấu hình demangler.
- `c++filt` xử lý được phần legacy `_ZN` ở mức cơ bản vì nó giống Itanium.

Cái hash `h...` ở cuối tên legacy là thứ hay làm người mới bối rối. Nó chỉ là định danh để tránh trùng tên giữa các bản monomorphized, bỏ qua được khi đọc.

## Panic string: người bạn tốt nhất của bạn

Đây là mẹo giá trị nhất của cả bài. Khi code Rust có thể panic (unwrap một None, truy cập mảng ngoài biên, chia cho 0, tràn số trong debug build), compiler chèn một lời gọi tới machinery panic kèm theo **một chuỗi chứa tên file và số dòng source gốc**.

Nghĩa là trong binary Rust, bạn thường thấy những chuỗi như:

```
src/validator.rs
called `Result::unwrap()` on an `Err` value
```

Đi ngược từ chuỗi đó (xref, giống kỹ thuật ở [Bài 0.4](/posts/tr-0-4-quy-trinh-reverse/)) là bạn nhảy thẳng tới đúng hàm trong code của tác giả, bỏ qua biển code thư viện. Với binary Rust bị tối ưu nặng, panic string nhiều khi là mỏ neo duy nhất đáng tin để định hướng.

## Option, Result, enum biểu diễn thế nào

Rust dùng `Option<T>` và `Result<T, E>` khắp nơi, nên nhận ra chúng giúp đọc logic:

- `Option<T>` và `Result<T, E>` là enum có tag (discriminant) cho biết đang là biến thể nào (Some/None, Ok/Err), kèm payload. Trong assembly, bạn thấy code đọc một tag rồi rẽ nhánh, giống union có nhãn.
- **Niche optimization**: với một số kiểu, Rust không cần tag riêng. Ví dụ `Option<&T>` dùng chính giá trị 0 (null) để biểu diễn `None`, nên nó gọn như một con trỏ. Thấy một con trỏ được kiểm `== 0` rồi rẽ nhánh, nhiều khi đó là `Option` đang được match.
- `match` trên enum biến thành so sánh tag rồi jump table hoặc chuỗi `cmp`/`je`, giống switch-case ở [Bài 1.5](/posts/tr-1-5-assembly-3-cau-truc-dieu-khien/).

## Chiến lược tiếp cận

Gộp lại thành một nhịp làm việc:

1. Triage bằng DIE, xác nhận là Rust, ghi lại phiên bản rustc nếu thấy.
2. Bật demangler trong IDA/Ghidra, hoặc chạy rustfilt lên bảng symbol.
3. Dùng panic string đi ngược về hàm của tác giả, bỏ qua `core`/`alloc`/`std`.
4. Chấp nhận iterator chain đã phẳng, đọc theo logic chứ đừng cố tìm lại ranh giới hàm gốc.
5. Dùng kinh nghiệm C++ (Phần 4) cho struct và cách truyền tham số.

## Lab tự làm

Xem [labs/9.1/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/9.1). Nếu máy bạn có `rustc`, build một chương trình nhỏ ở cả hai chế độ debug và release, quan sát mangling và panic string, rồi demangle bằng rustfilt.

## Checklist ghi nhớ
- Rust khó đọc vì monomorphization, inline mạnh, static link. Về cấu trúc gần C++ hơn Go (không có GC runtime).
- Nhận ra Rust qua đường dẫn `src/*.rs`, chuỗi `rustc`, symbol `core::`/`alloc::`/`std::`, panic string.
- Mangling hai kiểu: legacy `_ZN...` (có hash `h...`) và v0 `_R...`. Demangle bằng rustfilt hoặc IDA/Ghidra.
- Panic string chứa tên file và dòng source, dùng nó đi ngược về code của tác giả. Đây là mỏ neo quý nhất.
- Option/Result là enum có tag, để ý niche optimization (None thành null).
