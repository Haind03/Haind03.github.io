---
title: "Bài 1.1: Đọc hexdump như đọc chữ"
date: 2026-10-06 08:04:00 +0700
categories: ["Technique Reverse", "Phần 1 · Nền tảng máy tính cho RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Trước khi chạm vào assembly, bạn phải quen với cách máy tính biểu diễn số. Nghe chán, nhưng mỗi lần bạn nhìn vào một hex editor mà thấy `48 65 6C 6C 6F` rồi tự dịch ra "Hello" trong đầu, đó là lúc hệ số đã thành bản năng. Bài này đưa bạn tới đó.

## Vì sao là hệ 16 (hex)

Máy tính nghĩ bằng bit, từng con 0 và 1. Con người đọc nhị phân thì loạn mắt ngay: một byte là 8 bit, `01001000`, nhìn mãi không ra. Hệ 16 là cách viết gọn: mỗi 4 bit gộp thành một chữ số hex, nên một byte luôn vừa khít **2 chữ số hex**. Gọn, thẳng hàng, dễ đọc.

Bảng quy đổi 4 bit, thuộc được càng tốt:

```
0000=0  0001=1  0010=2  0011=3
0100=4  0101=5  0110=6  0111=7
1000=8  1001=9  1010=A  1011=B
1100=C  1101=D  1110=E  1111=F
```

Vậy `0100 1000` = `48` hex = 72 thập phân. Ký hiệu hex thường viết `0x48` hoặc `48h`.

Những mốc nên nhớ nằm lòng:
- 1 byte = 8 bit = 2 chữ số hex, giá trị `0x00` tới `0xFF` (0 tới 255).
- `0xFF` = 255, `0xFFFF` = 65535, `0xFFFFFFFF` = hơn 4 tỉ (giới hạn 32-bit).
- `0x10` = 16, `0x100` = 256, `0x1000` = 4096. Thấy số tròn trong hex là thường có ý nghĩa (kích thước, căn lề).

## Byte, word, và mấy cái tên gây lú

Trong thế giới x86, kích thước có tên riêng mà bạn sẽ gặp suốt trong IDA:

| Tên | Số bit | Số byte | Hậu tố assembly |
|---|---|---|---|
| byte | 8 | 1 | `db` |
| word | 16 | 2 | `dw` |
| dword (double word) | 32 | 4 | `dd` |
| qword (quad word) | 64 | 8 | `dq` |

Chữ "word" ở đây cố định 16 bit vì lý do lịch sử, đừng nhầm với kích thước thanh ghi. Trong IDA bạn thấy `dword_401000` nghĩa là "một biến 4 byte ở địa chỉ 0x401000".

## ASCII: khi byte là chữ

Mỗi byte có thể là một ký tự theo bảng ASCII. Không cần thuộc cả bảng, chỉ cần vài mốc:
- `0x41` = 'A', nên 'B' = 0x42, cứ thế tới 'Z' = 0x5A.
- `0x61` = 'a', 'z' = 0x7A. Để ý chữ thường hơn chữ hoa đúng 0x20.
- `0x30` = '0', tới '9' = 0x39.
- `0x20` = dấu cách.
- `0x00` = NUL, dùng để kết thúc chuỗi trong C (null-terminated string).

Mẹo: hiệu 0x20 giữa chữ hoa và thường chính là lý do nhiều thuật toán đổi hoa/thường chỉ cần `xor 0x20` hoặc `or 0x20`. Thấy pattern đó trong code là đoán được ngay.

## Đọc một hexdump thật

Đây là dạng bạn gặp trong HxD, ImHex, hay lệnh `xxd`:

```
Offset    Hex bytes                                         ASCII
00000000  48 65 6C 6C 6F 2C 20 52 45 21 00 00 00 00 00 00   Hello, RE!......
```

Ba cột: offset (vị trí tính từ đầu file), các byte ở dạng hex, và cùng những byte đó dịch sang ASCII (byte không in được hiện thành dấu chấm). Nhìn cột ASCII bên phải là cách nhanh nhất để soi chuỗi trong file. `48 65 6C 6C 6F` chính là "Hello", và `00` phía sau là ký tự kết thúc chuỗi.

## Endianness, cái bẫy kinh điển của người mới

![Little-endian: giá trị 0x12345678 lưu trong bộ nhớ thành 78 56 34 12](/assets/img/technique-reverse/assets/phan-01/little-endian.svg)

Đây là chỗ hầu hết người mới vấp. Câu hỏi: số 32-bit `0x12345678` được lưu trong bộ nhớ theo thứ tự byte nào?

Có hai cách:
- **Big-endian**: byte quan trọng nhất trước, `12 34 56 78`. Giống cách ta viết số thường.
- **Little-endian**: byte quan trọng nhất **sau cùng**, `78 56 34 12`. Ngược đời, nhưng đây lại là cách x86, x64 và ARM (thường) dùng.

Nghĩa là khi bạn nhìn trong hex editor thấy bốn byte `78 56 34 12`, giá trị thật của nó là `0x12345678`. Phải đọc ngược lại.

Ví dụ cụ thể hay làm người mới toát mồ hôi: tìm một địa chỉ `0x00401000` trong file. Bạn grep `00 40 10 00` thì không ra gì, vì trên đĩa nó nằm là `00 10 40 00`. Lộn byte là quên mất little-endian.

Quy tắc sống còn: **trên x86/x64, số nhiều byte luôn đọc ngược thứ tự byte.** Chuỗi ký tự thì không, vì chuỗi là dãy byte riêng lẻ chứ không phải một con số. Phân biệt được hai thứ này là qua được cái bẫy.

## Bitwise, ngôn ngữ của xáo trộn dữ liệu

Reverse crypto và obfuscation là gặp phép toán bit liên tục. Bốn phép cốt lõi:

- **AND (`&`)**: cả hai bit là 1 thì ra 1. Dùng để "che" lấy một số bit (masking). `x & 0xFF` lấy byte thấp nhất.
- **OR (`|`)**: một trong hai là 1 thì ra 1. Dùng để bật bit.
- **XOR (`^`)**: hai bit khác nhau thì ra 1. Đây là ngôi sao của reverse: XOR một giá trị hai lần với cùng khoá thì về như cũ, nên nó là cách mã hoá đơn giản nhất và phổ biến nhất trong malware và crackme. `A ^ key ^ key == A`.
- **NOT (`~`)**: lật mọi bit.

Và dịch bit:
- **Shift trái (`<<`)** mỗi bước nhân đôi, **shift phải (`>>`)** mỗi bước chia đôi. Compiler hay thay phép nhân/chia cho lũy thừa 2 bằng shift vì nó nhanh hơn. Thấy `shl eax, 3` là biết đang nhân 8.

Vì XOR xuất hiện khắp nơi, ghi nhớ một điều: thấy một vòng lặp đi qua dữ liệu và `xor` từng byte với một hằng số hay một khoá, 90% đó là routine mã hoá/giải mã chuỗi. Bài [16.2](https://github.com/Haind03/Technique-Reverse/tree/main/phan-16-crypto-thuat-toan) sẽ đào sâu.

## Tự luyện

Không cần tool, làm nhẩm rồi kiểm bằng máy tính lập trình (hoặc Python):
1. `0x4D5A` là hai ký tự ASCII gì? (Gợi ý: đây là magic number mở đầu mọi file PE Windows, "MZ".)
2. Trong hex editor bạn thấy `90 1F 00 00`. Đây là số 32-bit little-endian, giá trị thập phân là bao nhiêu?
3. `'a' ^ 0x20` ra ký tự gì? Còn `'A' ^ 0x20`?
4. Muốn lấy 4 bit thấp của một byte thì AND với giá trị hex nào?

Đáp án: 1) "MZ". 2) 0x00001F90 = 8080. 3) 'a'^0x20='A', 'A'^0x20='a' (XOR 0x20 đổi hoa thường). 4) `& 0x0F`.

## Checklist ghi nhớ
- 1 byte = 2 chữ số hex, `0x00` tới `0xFF`.
- byte/word/dword/qword = 1/2/4/8 byte.
- x86/x64 là little-endian: số nhiều byte lưu ngược thứ tự byte, phải đọc ngược.
- Chuỗi ký tự không bị đảo, chỉ số nhiều byte mới đảo.
- XOR là phép toán bạn sẽ gặp nhiều nhất trong crypto và obfuscation.
