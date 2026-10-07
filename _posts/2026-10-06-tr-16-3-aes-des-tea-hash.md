---
title: "Bài 16.3: Nhận diện AES, DES, TEA, ChaCha và hàm hash qua cấu trúc"
date: 2026-10-06 09:38:00 +0700
categories: ["Technique Reverse", "Phần 16 · Crypto & thuật toán"]
tags: [reverse-engineering, crypto]
render_with_liquid: false
---
Bài trước bạn học tìm hằng số crypto bằng findcrypt. Nhưng công cụ không phải lúc nào cũng chạy, và nhiều khi bạn chỉ có một đoạn pseudocode trước mặt phải tự đoán. Tin tốt: mỗi thuật toán crypto phổ biến có một "dáng đi" riêng, quen vài dáng là nhìn một cái biết ngay đang gặp thằng nào. Mà biết tên rồi thì bạn không cần tự cài lại, cứ gọi thư viện chuẩn mà giải.

Bài này đi qua những thuật toán hay gặp nhất, với dấu hiệu nhận ra nhanh nhất của từng cái.

## TEA và XTEA: dễ nhận nhất nhờ một con số

Bắt đầu bằng thằng dễ nhất. TEA (Tiny Encryption Algorithm) và biến thể XTEA nhỏ gọn, hay bị nhét vào malware và crackme vì code ngắn, không cần bảng tra. Dấu hiệu nhận ra gần như tức thì: hằng số **delta 0x9E3779B9**.

Con số này là phần phân số của tỉ lệ vàng nhân 2^32, và nó xuất hiện trong mọi vòng của TEA. Thấy `0x9E3779B9` trong code là 90% đang gặp TEA/XTEA. Vòng lặp thường chạy 32 lần, mỗi vòng cộng dồn delta vào một biến sum rồi trộn hai nửa khối bằng shift trái 4, shift phải 5, cộng và XOR.

Trong assembly, một vòng TEA nhìn như thế này:

```asm
; v0, v1 là hai nửa 32-bit của khối; sum trong một thanh ghi
add  esi, 0x9E3779B9      ; sum += delta   <- CHỈ ĐIỂM
mov  eax, edx             ; eax = v1
shl  eax, 4               ; v1 << 4
add  eax, [key+0]         ; + key[0]
mov  ecx, edx
add  ecx, esi             ; v1 + sum
xor  eax, ecx             ; ^ ...
mov  ecx, edx
shr  ecx, 5               ; v1 >> 5
add  ecx, [key+4]         ; + key[1]
xor  eax, ecx
add  ebx, eax             ; v0 += ...
```

Cái pattern "shl 4, shr 5, cộng key, XOR, cộng vào nửa kia" lặp đối xứng cho v0 và v1, kèm delta, là chữ ký không lẫn vào đâu được. Giải TEA rất dễ vì nó đối xứng: chạy ngược 32 vòng, trừ delta thay vì cộng.

## AES: nhìn S-box

AES (Rijndael) là thuật toán mã hoá đối xứng phổ biến nhất thế giới, nên gặp hoài. Dấu hiệu:

- **S-box 256 byte** bắt đầu bằng `63 7C 77 7B F2 6B 6F C5 30 01 67 2B...`. Đây là bảng thay thế byte, thấy đúng dãy này là chắc chắn AES.
- **Rcon** (round constant) cho key schedule: `01 02 04 08 10 20 40 80 1B 36...`.
- Số vòng 10, 12 hoặc 14 tương ứng key 128, 192, 256 bit.
- MixColumns dùng nhân trong trường Galois, hay thấy phép nhân với 2 và 3 kèm điều kiện XOR `0x1B`.

Nhiều cài đặt tối ưu gộp SubBytes, ShiftRows, MixColumns thành các **T-table** (4 bảng 1KB), khi đó bạn thấy bốn bảng lớn và nhiều phép tra bảng cộng XOR. Dù là S-box thuần hay T-table, findcrypt đều bắt được, nhưng nhớ dãy `63 7C 77 7B` mở đầu S-box là đủ nhận bằng mắt.

## DES: nhiều hoán vị và 8 S-box

DES cũ nhưng vẫn gặp trong hệ thống legacy. Dấu hiệu: hàng loạt **bảng hoán vị** (initial permutation, final permutation, expansion, P-box) và **8 S-box** riêng biệt mỗi cái biến 6 bit thành 4 bit. Code DES ngập phép dịch bit và tra bảng nhỏ. 16 vòng Feistel. Thấy nhiều bảng hoán vị cố định kèm 8 bảng S nhỏ là nghĩ tới DES/3DES.

## ChaCha và Salsa20: nhìn chuỗi hằng

Stream cipher hiện đại, ngày càng phổ biến (TLS, WireGuard, nhiều malware mới). Dấu hiệu đẹp nhất là một chuỗi ASCII nằm thẳng trong binary:

- **"expand 32-byte k"** (ChaCha20/Salsa20 với key 256-bit) hoặc "expand 16-byte k".

Thấy chuỗi này trong strings là gần như chắc ChaCha/Salsa. Cấu trúc bên trong là quarter-round: bốn phép cộng, XOR, và xoay bit (rotate) với các hằng xoay đặc trưng (ChaCha dùng 16, 12, 8, 7). Không có S-box, chỉ toàn add-rotate-XOR (gọi là ARX).

## Hàm hash: MD5, SHA, CRC

Hash không mã hoá mà băm, nhưng nhận diện tương tự qua hằng số:

- **MD5**: bốn init value `0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476` và bảng K 64 phần tử (sin table). 64 vòng.
- **SHA-1**: init `0x67452301...0xC3D2E1F0`, bốn hằng vòng `0x5A827999, 0x6ED9EBA1, 0x8F1BBCDC, 0xCA62C1D6`.
- **SHA-256**: bảng K 64 hằng số bắt đầu `0x428A2F98, 0x71374491...`, init tám giá trị từ căn bậc hai số nguyên tố.
- **CRC32**: một **bảng 256 entry** sinh từ polynomial `0xEDB88320` (dạng reversed), vòng lặp XOR và shift phải 8. CRC hay bị nhầm là crypto nhưng nó chỉ là checksum, không bảo mật.

Điểm chung: hash có padding (thêm bit 1 rồi các bit 0 rồi độ dài ở cuối) và một vòng nén xử lý từng block 64 byte.

## Bảng tra nhanh bằng mắt

| Thấy cái này | Nghĩ tới |
|---|---|
| `0x9E3779B9` | TEA / XTEA |
| S-box mở đầu `63 7C 77 7B` | AES |
| Chuỗi "expand 32-byte k" | ChaCha / Salsa20 |
| 8 S-box nhỏ + nhiều hoán vị | DES / 3DES |
| Init `67452301 EFCDAB89` + 64 vòng | MD5 |
| Bảng K 64 phần tử `428A2F98...` | SHA-256 |
| Bảng 256 entry, poly `0xEDB88320` | CRC32 (checksum, không phải crypto) |

## Biết tên rồi thì đừng tự cài lại

Sai lầm của người mới: nhận ra AES xong ngồi dịch tay từng vòng ra Python. Không cần. Một khi đã biết thuật toán, khoá, và mode (ECB/CBC/CTR), bạn gọi thư viện chuẩn là xong trong vài dòng:

```python
from Crypto.Cipher import AES
cipher = AES.new(key, AES.MODE_CBC, iv)
plaintext = cipher.decrypt(ciphertext)
```

Việc của bạn chỉ là reverse để lấy đúng ba thứ: thuật toán nào, khoá ở đâu, mode gì (và IV nếu có). Phần tính toán để thư viện lo. Với TEA thì vì nó quá nhỏ và không có trong thư viện chuẩn, viết lại tay cũng chỉ chục dòng (xem lab).

## Lab tự làm

Thư mục [labs/16.3/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/16.3): một chương trình mã hoá flag bằng TEA. Nhiệm vụ của bạn là nhận ra TEA qua delta trong disassembly, lấy khoá, rồi viết Python giải ngược. Lời giải và script kiểm chứng trong `solution.md`.

## Checklist ghi nhớ
- TEA/XTEA: nhận qua delta `0x9E3779B9`, 32 vòng, shl 4 / shr 5. Dễ giải vì đối xứng.
- AES: S-box mở đầu `63 7C 77 7B`, hoặc 4 T-table; số vòng 10/12/14.
- ChaCha/Salsa: chuỗi "expand 32-byte k", toàn add-rotate-XOR.
- DES: 8 S-box nhỏ + nhiều bảng hoán vị, 16 vòng Feistel.
- Hash nhận qua init value và bảng K; CRC32 là checksum với poly `0xEDB88320`.
- Nhận ra thuật toán rồi thì dùng thư viện chuẩn để giải, chỉ cần tìm đúng thuật toán, khoá, mode.
