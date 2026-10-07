---
title: "Bài 18.7: Reverse giao thức mạng và định dạng file độc quyền"
date: 2026-10-06 09:53:00 +0700
categories: ["Technique Reverse", "Phần 18 · Nâng cao"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
Có một loại bài toán không nằm trong binary mà nằm trong dữ liệu: một file save game không ai mô tả, một giao thức mạng tự chế giữa client và server, một định dạng cấu hình nhị phân. Không có spec, không có tài liệu. Việc của bạn là nhìn vào các mẫu dữ liệu và dựng lại cái spec đó, đủ chính xác để tự đọc và tự tạo ra dữ liệu hợp lệ. Bài này là cách làm.

Có hai nguồn thông tin, và người giỏi dùng cả hai: **bản thân dữ liệu** (so sánh nhiều mẫu), và **code xử lý dữ liệu** (lần theo hàm parse trong binary). Dữ liệu cho bạn giả thuyết nhanh, code xác nhận.

## Nguyên tắc differential: đổi một thứ, xem byte nào nhảy

Đây là kỹ thuật mạnh nhất và dễ nhất. Bạn tạo ra nhiều mẫu chỉ khác nhau một chi tiết, rồi so hex xem byte nào đổi theo. Byte đổi chính là field chứa chi tiết đó.

Lấy ví dụ thật từ lab: một định dạng save game `.sav`. Hai file `save_alice.sav` và `save_rich.sav` chỉ khác nhau ở lượng vàng (1500 so với 999999) và một cờ. So hex:

```
alice: 5341 5645 0200 0100 0700 0000 dc05 0000  SAVE............
rich:  5341 5645 0200 0300 0700 0000 3f42 0f00  SAVE............
                      ^^^^           ^^^^^^^^^
                      offset 6       offset 12
```

Hai chỗ khác: offset 6 (`0100` thành `0300`) và offset 12 (`dc05 0000` thành `3f42 0f00`). Vàng 1500 = `0x05DC`, đọc little-endian là `dc 05`, khớp offset 12. Vàng 999999 = `0x000F423F`, little-endian là `3f 42 0f 00`, cũng khớp. Vậy offset 12 là trường gold kiểu u32 little-endian. Offset 6 là cờ (alice không cheat, rich có). Bạn vừa tìm ra hai field mà không cần đọc một dòng code nào.

Làm tương tự với `save_alice.sav` và `save_bob.sav` (chỉ khác tên): byte đổi bắt đầu từ offset 18, và ngay trước đó có một giá trị cho biết độ dài tên. Đó là cách bạn tìm ra cặp length-prefix + chuỗi.

## Tìm magic và neo cấu trúc

Gần như mọi định dạng mở đầu bằng một magic number cố định để nhận dạng. Nhìn vài byte đầu giống nhau ở mọi mẫu là ra. Trong ví dụ trên, bốn byte `53 41 56 45` là ASCII "SAVE". Magic là mỏ neo: biết nó rồi bạn mới định nghĩa được các offset tiếp theo.

Sau magic thường là version (một số nhỏ, thường tăng dần qua các bản), rồi tới các field. Phân biệt field cố định (giống nhau ở mọi mẫu) với field thay đổi (khác nhau), và trong field thay đổi, phân biệt số (little-endian trên x86, đọc ngược, xem lại [Bài 1.1](/posts/tr-1-1-hex-endian-bitwise/)) với chuỗi (cột ASCII bên phải đọc ra chữ).

## Ba mẫu hay gặp

Khi dò, bạn sẽ gặp đi gặp lại ba khuôn:

- **Fixed field**: luôn cùng kích thước, ví dụ một u32 cho level, một u16 cho flags. Dễ nhất.
- **Length-prefixed**: một giá trị độ dài, theo sau là đúng số byte đó. Chuỗi và mảng hay dùng kiểu này. Trong lab, `name_len` (u16) đứng trước tên, và `n_items` (u16) đứng trước danh sách item. Thấy một số nhỏ rồi đúng chừng ấy byte dữ liệu phía sau là nhận ra ngay.
- **TLV (type-length-value)** hoặc record lặp: một khối lặp nhiều lần, mỗi khối có cấu trúc giống nhau. Danh sách item `(item_id u16, qty u16)` lặp `n_items` lần là một dạng đơn giản của nó.

Và rất hay ở cuối file có một **checksum** (tổng byte, CRC32, hoặc hash) để chương trình phát hiện file bị sửa. Nếu bạn định tạo file hợp lệ của riêng mình, phải tính lại checksum cho đúng, nếu không chương trình từ chối. Đây là lý do một parser tốt luôn kiểm checksum (trong lab, trường cuối là tổng mọi byte phía trước mod 2^32).

## Công cụ mô tả cấu trúc

Khi đã có giả thuyết, viết nó ra dưới dạng template để tool tự parse và highlight:

- **010 Editor Binary Template** và **ImHex pattern** (xem [Bài 2.7](/posts/tr-2-7-hex-editor-template/)): bạn khai báo struct, tool tô màu từng field trên file thật, sai ở đâu thấy ngay.
- **Kaitai Struct**: mô tả định dạng bằng một file YAML, nó sinh ra parser cho nhiều ngôn ngữ (Python, C++, Java...). Hợp khi định dạng phức tạp và bạn muốn parser dùng lại được.

Cuối cùng, viết một parser nhỏ bằng Python với `struct.unpack` là cách xác nhận spec chắc nhất: nếu parser đọc đúng mọi mẫu và checksum khớp, spec của bạn đúng. Lab có sẵn `parse_savefile.py` làm mẫu.

## Xác nhận bằng code: lần theo hàm parse

So sánh dữ liệu cho giả thuyết, nhưng có chỗ mơ hồ chỉ code mới trả lời được: field này là signed hay unsigned, số này là độ dài hay là một ID, checksum tính theo thuật toán nào. Lúc đó mở binary xử lý file trong IDA/Ghidra:

- Đặt breakpoint tại `CreateFile`/`fopen`/`ReadFile`/`fread` (xem [Bài 1.13](/posts/tr-1-13-nhan-dien-windows-api/)) để bắt đúng lúc nó đọc file, rồi lần theo buffer.
- Tìm chỗ so sánh magic (một `cmp` với hằng số trông như "SAVE" đảo byte), đó là đầu hàm parse.
- Đọc tiếp sẽ thấy nó cộng offset, đọc u16/u32, nhân độ dài, lặp qua record. Mỗi phép đọc xác nhận một field trong spec của bạn.
- Hàm tính checksum lộ ra thuật toán thật (tổng đơn giản, hay CRC với bảng 256 entry, nối [Bài 16.1](/posts/tr-16-1-nhan-dien-hang-so-crypto/)).

## Giao thức mạng: cùng tư duy, thêm Wireshark

Giao thức mạng chỉ là định dạng dữ liệu di chuyển theo thời gian. Khác biệt là bạn bắt nó bằng **Wireshark** thay vì mở file:

- Bắt lưu lượng giữa client và server, xem từng gói ở dạng hex.
- Áp đúng ba mẫu trên: mỗi message thường có header (magic/version), một trường length (tổng chiều dài phần còn lại, cực hay gặp để biết đọc tới đâu), rồi payload. Tìm trường length bằng cách so độ dài gói thật với con số trong header.
- Dùng differential: làm cùng một hành động trong app hai lần, so hai gói, phần khác là dữ liệu động (timestamp, session id, nonce), phần giống là khung cố định.
- Nếu payload trông như rác (entropy cao), nó bị mã hoá. Lúc này lần theo code trong binary: đặt breakpoint tại `send`/`WSASend` và `recv`, đi ngược lên sẽ thấy hàm mã hoá chạy ngay trước `send` (và giải mã ngay sau `recv`). Hook đúng chỗ trước khi mã hoá (hoặc sau khi giải mã) bằng Frida ([Bài 17.2](/posts/tr-17-2-frida-toan-tap/)) là bạn thấy payload dạng rõ, không cần bẻ thuật toán.

Kỹ thuật này chính là nền của việc trích config và hiểu giao thức C2 của malware, sẽ dùng lại ở [Bài 19.4](/posts/tr-19-4-trich-config-c2/).

## Lab tự làm

Thư mục [`labs/18.7/`](https://github.com/Haind03/Technique-Reverse/tree/main/labs/18.7). Bạn sẽ chạy `make_savefile.py` tạo ba file `.sav` khác nhau một chi tiết, dùng differential trên hexdump để tự suy ra cấu trúc, viết parser của riêng mình, rồi so với `parse_savefile.py`. Có cả phần dựng pattern cho ImHex.

## Checklist ghi nhớ
- Differential là vũ khí số một: tạo nhiều mẫu khác nhau một chi tiết, byte nào đổi là field đó.
- Mọi định dạng neo vào magic number ở đầu, tìm nó trước tiên.
- Ba khuôn hay gặp: fixed field, length-prefixed (số độ dài rồi dữ liệu), record lặp/TLV.
- Số nhiều byte đọc little-endian (đảo byte), chuỗi đọc thẳng ở cột ASCII.
- Checksum ở cuối: muốn tạo dữ liệu hợp lệ phải tính lại cho đúng.
- Dữ liệu cho giả thuyết, code (hàm parse, hàm send/recv) xác nhận chi tiết mơ hồ.
- Giao thức mạng = định dạng theo thời gian: Wireshark + differential, payload mã hoá thì hook quanh send/recv.
