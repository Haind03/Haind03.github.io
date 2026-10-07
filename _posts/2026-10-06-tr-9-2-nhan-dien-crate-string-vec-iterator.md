---
title: "Bài 9.2: Nhận diện String, Vec, iterator và trait object của Rust"
date: 2026-10-06 09:04:00 +0700
categories: ["Technique Reverse", "Phần 9 · Rust"]
tags: [reverse-engineering, rust]
render_with_liquid: false
---
Bài trước bạn đã biết cách nhận ra một binary là Rust và gỡ tên hàm bằng demangle. Giờ tới phần đau đầu hơn: đọc được code bên trong. Rust có một triết lý làm khổ reverser, đó là "zero-cost abstraction". Nghĩa là mọi thứ đẹp đẽ bạn viết ở source, iterator, closure, Option, đều bị compiler nghiền phẳng ra thành vòng lặp và nhánh trần trụi trong binary, không còn dấu vết của hình dạng ban đầu. Đổi lại code chạy nhanh, nhưng người đọc disassembly thì khóc.

Bài này dạy bạn nhận ra vài cấu trúc dữ liệu cốt lõi của Rust, để giữa một biển code inline bạn vẫn biết mình đang nhìn cái gì.

## String và str: con trỏ cộng length, không null-terminated

Đây là thứ đầu tiên làm người quen C vấp. Trong C, chuỗi kết thúc bằng byte `0`, nên bạn cứ đọc tới khi gặp `0` là hết. Rust thì không. Một `String` hay `&str` được biểu diễn bằng một con trỏ tới dữ liệu cộng với một trường length, y hệt Go (xem [Bài 8.3](/posts/tr-8-3-string-slice-interface-goroutine/)).

Hệ quả thực tế khi bạn nhìn vào section dữ liệu:

- Các chuỗi dính liền nhau thành một khối dài không có dấu phân cách. Ví dụ bạn thấy `"errorinvalid inputpassword"` nằm liền một mạch. Đó không phải một chuỗi, mà là ba chuỗi `"error"`, `"invalid input"`, `"password"` ghép lại. Ranh giới nằm ở chỗ khác: trong code, mỗi lần dùng chuỗi, compiler nạp cả con trỏ (trỏ vào giữa khối) lẫn một hằng số length.
- Muốn biết một chuỗi dừng ở đâu, bạn phải tìm cái length đi kèm, thường là một `mov` hằng số ngay cạnh lệnh nạp con trỏ.

Cụ thể, `String` đầy đủ gồm ba trường: con trỏ, length, và capacity (dung lượng đã cấp), tổng 24 byte trên hệ 64-bit. Còn `&str` chỉ là con trỏ cộng length, 16 byte, vì nó chỉ mượn dữ liệu chứ không sở hữu.

```asm
; nạp một &str: lea con trỏ, rồi nạp length là hằng số
lea  rax, [rip+0x...]   ; con trỏ tới "password" trong khối chuỗi
mov  esi, 8             ; length = 8, đây mới là thứ cho biết chuỗi dài bao nhiêu
```

Mẹo: thấy một cặp "nạp con trỏ vào khối chuỗi, rồi nạp ngay một hằng số nhỏ", gần như chắc đó là một `&str` với hằng số là length của nó.

## Vec: giống String nhưng chứa phần tử bất kỳ

`Vec<T>` cũng là ba trường con trỏ, length, capacity, đúng như phần dữ liệu của `String` (thật ra `String` bên trong là một `Vec<u8>`). Khác biệt duy nhất là phần tử không nhất thiết là byte. Truy cập `v[i]` thành `[con_tro + i * sizeof(T)]`, đúng công thức mảng bạn đã quen ở [Bài 3.2](/posts/tr-3-2-bien-con-tro-mang-chuoi/).

Khi thấy một struct ba trường mà trường thứ hai và thứ ba trông như length và capacity (hai số nguyên, số sau lớn hơn hoặc bằng số trước), bạn đang nhìn một `Vec` hoặc `String`.

## Iterator: nơi mọi vẻ đẹp biến mất

Đây là chỗ Rust khác hẳn mọi ngôn ngữ trên. Bạn viết source rất thanh lịch:

```rust
let sum: u32 = data.iter().map(|x| x * 2).filter(|x| x > &10).sum();
```

Bạn mong trong binary có ba hàm riêng cho `map`, `filter`, `sum`. Không có đâu. Compiler Rust inline toàn bộ chuỗi iterator đó thành **một vòng lặp phẳng duy nhất**, trong đó mỗi phần tử được nhân đôi, so sánh với 10, rồi cộng dồn, tất cả trong cùng một thân vòng lặp. Cấu trúc `map`/`filter`/`sum` bốc hơi hoàn toàn.

Hệ quả cho người đọc:

- Đừng đi tìm hàm `map` hay `filter`. Chúng không tồn tại như hàm riêng.
- Thay vào đó, hãy đọc thân vòng lặp và tự nhận ra các bước: "à, mỗi vòng nó nhân đôi (phép `map`), rồi có một nhánh bỏ qua nếu nhỏ hơn 10 (phép `filter`), rồi cộng vào một biến tích luỹ (phép `sum`)".
- Decompiler (Ghidra, Hex-Rays) thường cho ra một vòng `for` lớn với nhiều `if` lồng. Việc của bạn là dịch ngược cái vòng đó về ý đồ iterator gốc.

Nói cách khác, với Rust bạn reverse ở mức "vòng lặp làm gì", không phải "gọi hàm nào", vì gần như không còn lời gọi hàm để bám.

## Option và Result: hai nhánh quen mặt

Rust không có `null`, thay bằng `Option<T>` (có `Some` hoặc `None`) và `Result<T, E>` (có `Ok` hoặc `Err`). Trong binary, chúng thường thành một tag nhỏ (một số nguyên cho biết là biến thể nào) cộng với dữ liệu. Với kiểu tối ưu được (như `Option<&T>`), compiler dùng chính giá trị `0`/null làm `None`, nên nhiều khi một `Option` chỉ là một phép kiểm tra "con trỏ có bằng 0 không". Thấy `panic` được gọi sau một nhánh kiểm tra, thường đó là chỗ `unwrap()` một `None` hoặc `Err`.

## Trait object: vtable kiểu fat pointer

Nếu bạn đã đọc [Bài 4.2](/posts/tr-4-2-class-vtable-ke-thua-rtti/) về vtable của C++, trait object của Rust gần giống nhưng có một khác biệt quan trọng. C++ giấu con trỏ vtable ở đầu object. Rust thì tách ra: một trait object (`&dyn Trait`, `Box<dyn Trait>`) là một **fat pointer**, tức hai con trỏ đi cạnh nhau: một trỏ tới dữ liệu, một trỏ tới vtable.

Nên lời gọi method qua trait trông như:

```asm
; rax = data pointer, rdx = vtable pointer (đi thành cặp)
mov  rcx, rax            ; truyền data làm self
call [rdx+0x18]          ; gọi method tại slot trong vtable
```

Thấy hai con trỏ luôn đi cùng nhau, một trong hai được dùng để `call [reg+offset]`, đó là trait object đang dispatch động.

## Nhận diện crate qua chuỗi và symbol

Dù bị inline nặng, binary Rust vẫn rò rỉ nhiều manh mối về thư viện (crate) nó dùng:

- Chuỗi path trong thông báo panic thường lộ tên crate và cả đường dẫn file source, ví dụ `src/main.rs` hay `.cargo/registry/.../serde-1.0.x/src/...`. Đây là mỏ vàng để biết code dùng crate gì.
- Symbol (nếu chưa strip) chứa tên crate trong phần mangle, ví dụ `_ZN4core`, `_ZN5alloc`, `_ZN5serde`.
- Các crate phổ biến để ý: `std`/`core`/`alloc` (luôn có), `serde` (serialize), `tokio` (async), `reqwest`/`hyper` (HTTP), `clap` (parse argument).

Biết crate nào đang dùng giúp bạn đoán được chương trình làm gì trước cả khi đọc code chi tiết.

## Khi decompiler ra một mớ, làm gì

Thực tế reverse Rust, đây là nhịp làm việc đỡ nản nhất:

1. Demangle và khôi phục symbol trước (Bài 9.1), để có tên hàm bám vào.
2. Đọc chuỗi panic để biết crate và đường dẫn source, suy ra cấu trúc dự án.
3. Với mỗi hàm, đừng cố map từng dòng về source. Hiểu "hàm này nhận gì, trả gì, biến đổi ra sao" ở mức vòng lặp.
4. Chấp nhận rằng iterator chain đã phẳng, đọc vòng lặp theo hành vi chứ không theo hình dạng gốc.
5. Nếu cần giá trị cụ thể lúc chạy (ví dụ chuỗi đã giải mã), chuyển sang dynamic như mọi khi.

## Lab tự làm

Xem [labs/9.2/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/9.2). Bạn build một chương trình Rust nhỏ dùng `String`, `Vec` và một iterator chain, rồi quan sát trong Ghidra để thấy tận mắt chuỗi dính liền, cấu trúc ba trường của `Vec`, và iterator bị inline thành một vòng lặp phẳng.

## Checklist ghi nhớ
- String/str và Vec đều là con trỏ cộng length (Vec/String thêm capacity), không null-terminated. Chuỗi dính liền nhau, ranh giới nằm ở hằng số length trong code.
- Iterator chain (map/filter/sum) bị inline thành một vòng lặp phẳng, không còn hàm riêng. Đọc theo hành vi, không tìm tên hàm.
- Option/Result thành tag cộng dữ liệu, nhiều khi `None` chính là null; `panic` sau một nhánh thường là `unwrap`.
- Trait object là fat pointer: cặp con trỏ data và vtable, dispatch qua `call [vtable+offset]`.
- Chuỗi panic lộ tên crate và đường dẫn source, dùng để đoán chương trình làm gì.
