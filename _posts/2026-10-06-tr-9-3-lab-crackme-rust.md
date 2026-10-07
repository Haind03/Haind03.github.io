---
title: "Bài 9.3: Lab crackme Rust, gỡ một binary ít thân thiện"
date: 2026-10-06 09:05:00 +0700
categories: ["Technique Reverse", "Phần 9 · Rust"]
tags: [reverse-engineering, rust]
render_with_liquid: false
---
Rust không khó vì bí hiểm, mà khó vì compiler nhiệt tình quá mức: nó inline cả đống, gộp iterator chain thành vòng lặp phẳng, và rải panic machinery khắp nơi. Nhưng chính đống panic đó lại là bạn của người reverse. Bài này gom 9.1 và 9.2 thành một ca thực tế: lấy password từ một crackme Rust.

File lab nằm ở [labs/9.3/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/9.3). Cứ tự làm trước, dưới đây là đường đi.

## Bước 0: xác nhận nó là Rust

Trước khi mở disassembler, chạy triage cho nhanh. `strings crackme | grep -iE "rustc|\.rs|panicked"` gần như luôn trả về thứ gì đó: chuỗi phiên bản `rustc`, đường dẫn file `.rs` nhúng trong thông điệp panic, và symbol mangled kiểu `_ZN` hoặc `_R`. Thấy mấy dấu này là biết ngay đang cầm Rust chứ không phải C.

Detect It Easy cũng nhận ra, nhưng thói quen `strings` vẫn đáng giữ vì nó cho bạn luôn các chuỗi mốc để lát nữa xref.

## Bước 1: dùng panic string và chuỗi làm mốc

Đây là khác biệt lớn nhất khi reverse Rust so với C. Trong C bạn đi từ `main`. Trong Rust, `main` thật bị bọc trong `lang_start` và một lớp closure, nên đi thẳng vào hơi mệt. Thay vào đó, đi ngược từ chuỗi.

Crackme này in `Nope.` khi sai và `Correct!` khi đúng. Mở Strings window, tìm `Nope.`, nhấn xref. Nó đưa thẳng tới nhánh thất bại của hàm kiểm tra, và ngay phía trên là vòng lặp so sánh. Bạn vừa bỏ qua toàn bộ phần runtime Rust mà không phải đọc một dòng nào của nó.

Nếu binary chưa stripped, bạn còn sướng hơn: symbol demangle (bằng rustfilt hoặc để IDA/Ghidra tự làm) cho thấy tên hàm `check` rõ ràng.

## Bước 2: tìm mảng hằng

Trong hàm `check`, decompiler cho thấy đầu vào được so với một khối byte cố định nằm trong `.rodata`:

```
6e 4a 49 4b 5f 0a 45 5a 72 42 44 10
```

Mười hai byte. Và ngay đầu hàm có một phép kiểm tra độ dài: nếu độ dài chuỗi nhập khác 12 thì trả về false luôn. Vậy password dài đúng 12 ký tự. Biết độ dài trước là đã đi được nửa đường.

Nhớ từ [bài 9.2](/posts/tr-9-2-nhan-dien-crate-string-vec-iterator/): Rust `String`/`str` là con trỏ cộng length, không null-terminated. Mảng hằng cũng chỉ là một khối byte liền nhau. Đừng trông chờ dấu `00` ngăn cách như chuỗi C.

## Bước 3: đọc phép biến đổi

Phần iterator trong source gốc có thể là một chain `.enumerate().map(...)`, nhưng sau khi compiler inline, bạn chỉ thấy một vòng lặp phẳng. Đừng cố dựng lại cú pháp iterator, chỉ cần hiểu nó làm gì cho mỗi ký tự ở vị trí `i`:

```
enc = (input[i] + i) & 0xFF      ; cộng chỉ số
enc = enc ^ 0x3C                 ; XOR hằng số
if enc != EXPECTED[i] -> Nope
```

Hai phép đơn giản: cộng index rồi XOR. Cái hay là cả hai đều khả nghịch.

## Bước 4: keygen thay vì đoán

Vì phép kiểm tra đảo ngược được, đừng brute force, hãy tính thẳng. Đảo lại: `input[i] = (EXPECTED[i] ^ 0x3C) - i`.

```python
EXPECTED = [0x6e,0x4a,0x49,0x4b,0x5f,0x0a,0x45,0x5a,0x72,0x42,0x44,0x10]
pw = "".join(chr(((b ^ 0x3C) - i) & 0xFF) for i, b in enumerate(EXPECTED))
print(pw)   # Rust_1s_Fun!
```

Chạy lại crackme với password đó:

```
./crackme 'Rust_1s_Fun!'
Correct! Flag: RE{Rust_1s_Fun!}
```

Xong. Lưu ý: binary trong lab này tôi chưa build chạy tại chỗ vì môi trường không có `rustc`, nhưng thuật toán đã kiểm bằng Python (mã hoá xuôi ra đúng mảng hằng, đảo ngược ra đúng password). Trên máy có Rust nó chạy đúng như mô tả. Chi tiết ở [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/9.3/solution.md).

## Vì sao Rust bõ công luyện

Phần lớn người mới né Rust vì decompiler ra một mớ inline rối mắt. Nhưng mẹo thật ra ít: bám panic string và chuỗi để định vị, nhìn độ dài khối hằng để biết độ dài input, và ưu tiên đảo ngược phép kiểm tra thay vì đọc từng dòng assembly đã bị tối ưu. Ba thói quen đó giải được đa số crackme Rust mức nhập môn tới trung bình.

## Checklist ghi nhớ
- Xác nhận Rust bằng `strings`: phiên bản rustc, đường dẫn `.rs`, mangling `_ZN`/`_R`.
- Đi từ chuỗi (`Nope.`, `Correct!`) và panic string ngược vào hàm check, đừng vật lộn với `main` bị bọc.
- Độ dài khối hằng trong `.rodata` thường chính là độ dài password.
- Iterator chain bị inline thành vòng lặp phẳng, đọc tác dụng chứ đừng dựng lại cú pháp.
- Phép kiểm tra khả nghịch thì keygen, đừng brute force.
