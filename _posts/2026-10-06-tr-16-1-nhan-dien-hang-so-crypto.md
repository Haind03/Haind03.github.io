---
title: "Bài 16.1: Nhận diện thuật toán crypto qua hằng số"
date: 2026-10-06 09:36:00 +0700
categories: ["Technique Reverse", "Phần 16 · Crypto & thuật toán"]
tags: [reverse-engineering, crypto]
render_with_liquid: false
---
Có một tin vui cho người reverse: thuật toán mã hoá rất khó giấu. Không phải vì code của nó dễ đọc, mà vì gần như thuật toán tiêu chuẩn nào cũng mang theo một bộ hằng số cố định (magic constant), và những con số đó không bao giờ đổi. Thấy `0x67452301` nằm đầu một hàm là bạn gần như chắc đang nhìn MD5 hoặc SHA-1. Bài này dạy cách dùng đúng dấu vân tay đó để khoanh vùng crypto trong vài giây thay vì đọc cả nghìn dòng vòng lặp bit.

## Vì sao hằng số là chỉ điểm đáng tin

Một thuật toán như SHA-256 được định nghĩa trong chuẩn với các giá trị khởi tạo và bảng hằng cố định. Bất kỳ ai cài đúng chuẩn, dù bằng C, Rust hay assembly tay, đều phải nhúng đúng những con số đó vào binary. Compiler có thể đổi tên biến, tối ưu vòng lặp, inline hàm, nhưng nó không thể đổi `0x6a09e667` thành số khác mà vẫn ra kết quả đúng.

Nói cách khác: logic có thể bị bóp méo, hằng số thì không. Đó là lý do tìm hằng số là cách nhanh và chắc nhất để nhận ra crypto, chắc hơn nhiều so với cố đọc hiểu vòng lặp xáo bit.

## Bộ dấu vân tay nên thuộc

Không cần nhớ hết, nhưng vài con số sau gặp liên tục nên thuộc lòng thì lợi:

| Thuật toán | Hằng số đặc trưng |
|---|---|
| MD5 | Init: `0x67452301`, `0xEFCDAB89`, `0x98BADCFE`, `0x10325476` |
| SHA-1 | Init giống MD5 bốn số trên, cộng thêm `0xC3D2E1F0` |
| SHA-256 | H init bắt đầu `0x6A09E667`; bảng K bắt đầu `0x428A2F98` |
| TEA / XTEA | Delta `0x9E3779B9` (hằng số vàng, derived từ tỉ lệ vàng) |
| CRC32 | Polynomial phản chiếu `0xEDB88320`, hoặc bảng 256 entry dựng từ nó |
| AES | S-box 256 byte (bắt đầu `63 7C 77 7B F2 6B 6F C5...`) và Rcon `01 02 04 08 10 20 40 80 1B 36` |
| Blowfish | P-array và S-box khởi tạo từ các chữ số của số pi |
| RC4 | Không có hằng số, nhận ra qua pattern KSA (vòng lặp khởi tạo mảng 256 byte rồi hoán vị) |

Để ý hai nhóm. Nhóm có hằng số rõ (MD5, SHA, AES, TEA, CRC) thì findcrypt bắt được ngay. Nhóm không hằng số (RC4, XOR tuỳ biến, Base64 custom) phải nhận bằng pattern, đó là chuyện của bài 16.2.

## Để công cụ làm phần nhàm

Bạn không ngồi dò từng số bằng mắt. Có cả bộ tool quét hằng số tự động:

- **FindCrypt / findcrypt2** (plugin IDA): quét toàn binary, đánh dấu mọi vùng khớp chữ ký thuật toán đã biết, in ra danh sách kèm địa chỉ. Chạy một phát là có bản đồ crypto.
- **FindCrypt-Ghidra**: bản tương đương cho Ghidra.
- **capa** (Mandiant): không chỉ tìm hằng số mà suy ra capability ở mức cao, ví dụ "hash data via MD5", "encrypt data using AES", rất tiện khi triage nhanh.
- **signsrch**: quét chữ ký thuật toán và một số pattern cài đặt phổ biến, chạy độc lập ngoài IDA.
- **yara với rule crypto**: nếu bạn đã có bộ rule, quét hàng loạt mẫu cũng được.

Quy trình thực tế rất gọn: mở binary, chạy findcrypt hoặc capa trước tiên, nó chỉ cho bạn vài địa chỉ "ở đây có AES, ở kia có CRC32". Bạn nhảy thẳng tới đó thay vì bơi trong phần còn lại.

## Xác nhận lại bằng cấu trúc, đừng tin mù

Findcrypt rất tốt nhưng không phải thần thánh. Một bảng hằng số có thể trùng tình cờ, hoặc một thuật toán bị sửa đổi (ví dụ AES với S-box thay thế, hay CRC với polynomial khác) sẽ làm tool báo nhầm hoặc bỏ sót. Sau khi tool khoanh vùng, luôn nhìn qua cấu trúc hàm để xác nhận:

- AES có vòng lặp 10/12/14 round, mỗi round có SubBytes (tra S-box), ShiftRows, MixColumns (nhân trong GF(2^8)), AddRoundKey (xor).
- Hash (MD5/SHA) xử lý theo block 64 byte, có vòng nén với nhiều phép xoay bit (rotate) và cộng.
- CRC32 là vòng lặp qua từng byte, xor rồi tra bảng 256 entry, hoặc dịch bit 8 lần.
- TEA/XTEA có vòng lặp cộng dồn delta `0x9E3779B9` qua 32 round, thao tác trên hai nửa 32-bit.

Khi hằng số khớp và cấu trúc vòng lặp cũng khớp, bạn mới kết luận chắc chắn. Nếu hằng khớp mà cấu trúc lạ, nhiều khả năng đây là biến thể tuỳ biến, và đó mới là chỗ thú vị cần đào sâu.

## Khi hằng số bị che

Malware tinh vi đôi khi không để hằng số trần. Chúng có thể dựng bảng hằng lúc chạy (tính S-box trong runtime thay vì nhúng sẵn), hoặc xor hằng số với một khoá rồi giải lúc dùng. Lúc đó findcrypt tĩnh sẽ trượt. Cách vượt: chạy động, đặt breakpoint sau đoạn khởi tạo rồi dump vùng nhớ chứa bảng ra, chạy findcrypt trên bản dump. Hằng số lúc này đã hiện nguyên hình trong bộ nhớ.

## Checklist ghi nhớ
- Thuật toán crypto tiêu chuẩn mang hằng số cố định, compiler không đổi được chúng.
- Thuộc vài số hay gặp: MD5/SHA `0x67452301`, SHA-256 `0x6A09E667`, TEA delta `0x9E3779B9`, CRC32 `0xEDB88320`.
- Chạy findcrypt/capa/signsrch trước tiên để khoanh vùng crypto, đừng đọc tay.
- Luôn xác nhận lại bằng cấu trúc vòng lặp, tránh tin nhầm chữ ký trùng.
- Hằng số bị dựng/giải lúc chạy thì dump bộ nhớ rồi quét lại.
