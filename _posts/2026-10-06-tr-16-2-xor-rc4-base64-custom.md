---
title: "Bài 16.2: XOR, RC4 và Base64 custom, ba thứ bạn gặp nhiều nhất"
date: 2026-10-06 09:37:00 +0700
categories: ["Technique Reverse", "Phần 16 · Crypto & thuật toán"]
tags: [reverse-engineering, crypto]
render_with_liquid: false
---
Nếu phải chọn ba kỹ thuật biến đổi dữ liệu mà bạn sẽ đụng nhiều nhất khi mổ crackme và malware, thì đây: XOR, RC4, và Base64 với bảng chữ bị xáo. Chúng chiếm phần lớn các ca "chuỗi trông như rác" mà bạn cần giải. Tin tốt là cả ba đều nhận ra được bằng mắt và giải lại bằng vài dòng Python. Bài này dạy bạn nhìn ra chúng và viết decode.

## XOR, phép toán quốc dân của obfuscation

Lý do XOR ở khắp nơi rất đơn giản: nó đảo ngược chính nó. `A ^ key ^ key == A`. Mã hoá và giải mã dùng chung một hàm, một dòng code, không cần thư viện. Kẻ viết malware lười, và XOR phục vụ sự lười đó hoàn hảo.

Trong assembly, một vòng lặp XOR trông rất đặc trưng:

```asm
loop:
    mov  al, [rsi+rcx]      ; lấy một byte ciphertext
    xor  al, dl             ; XOR với key (ở đây dl giữ 1 byte key)
    mov  [rdi+rcx], al      ; ghi byte đã giải ra
    inc  rcx
    cmp  rcx, rbx           ; đã hết độ dài chưa
    jl   loop
```

Thấy một vòng lặp đi qua một buffer và có `xor` một byte với một hằng số hay một giá trị lấy từ mảng key, gần như chắc đó là routine mã hoá/giải mã chuỗi. Có ba biến thể:

- **Single-byte key**: mọi byte XOR với cùng một giá trị. Dễ nhất, thậm chí brute-force cả 256 khả năng là ra.
- **Multi-byte key (rolling)**: XOR với `key[i % len(key)]`, key lặp vòng. Rất phổ biến.
- **Rolling/running XOR**: byte sau phụ thuộc byte trước (ví dụ XOR với byte vừa giải). Ít gặp hơn.

### Tìm key khi chưa biết: known-plaintext

Mẹo mạnh nhất với XOR là known-plaintext attack. Nếu bạn đoán được một phần plaintext (ví dụ flag luôn bắt đầu bằng `flag{`, hay config JSON luôn mở bằng `{"`), thì XOR phần ciphertext với phần plaintext đã biết sẽ lòi ra key:

```
key[i] = ciphertext[i] ^ plaintext[i]
```

Làm vài byte đầu là lộ key, nếu key ngắn và lặp lại thì bạn thấy ngay chu kỳ. Lab cuối bài làm đúng chuyện này.

## RC4, kẻ không có magic constant

RC4 là stream cipher hay gặp trong malware vì nhỏ gọn và không cần thư viện. Cái khó là nó **không có hằng số đặc trưng** như AES hay SHA, nên findcrypt không bắt được. Bạn phải nhận ra nó qua cấu trúc.

Dấu hiệu nhận diện RC4, không thể nhầm:

1. **Một mảng 256 byte (S-box) được khởi tạo bằng 0, 1, 2, ..., 255.** Thấy một vòng lặp `S[i] = i` chạy 256 lần là chuông báo đầu tiên.
2. **Vòng KSA (Key Scheduling)**: vòng lặp 256 lần hoán vị S dựa trên key: `j = (j + S[i] + key[i % keylen]) & 0xFF; swap(S[i], S[j])`.
3. **Vòng PRGA (sinh keystream)**: `i = (i+1) & 0xFF; j = (j + S[i]) & 0xFF; swap; k = S[(S[i]+S[j]) & 0xFF]` rồi XOR k với dữ liệu.

Thấy mảng 256 khởi tạo tuần tự rồi hoán vị hai lần với phép AND 0xFF (tức mod 256) khắp nơi, đó là RC4. Vì RC4 đối xứng, chỉ cần tìm được key (thường nằm gần đoạn KSA, hoặc là một chuỗi cứng trong binary) là giải xong. Chép thuật toán vào Python, truyền key, chạy.

## Base64 custom, cái bẫy của người vội

Base64 chuẩn dùng bảng 64 ký tự `A-Za-z0-9+/`. Nhiều chương trình đổi thứ tự bảng này để chuỗi mã hoá trông giống Base64 nhưng decode bằng tool chuẩn ra rác. Người mới thấy chuỗi có dạng Base64 (chữ, số, có khi `=` ở cuối) bèn ném vào CyberChef, ra rác, rồi bỏ cuộc.

Chìa khoá: tìm **bảng alphabet 64 ký tự** trong binary. Nó thường nằm trong `.rdata` dưới dạng một chuỗi 64 ký tự liền nhau, ví dụ `ZYXWVUTSRQPO...`. Khi có bảng custom, việc giải chỉ là ánh xạ ngược về bảng chuẩn rồi decode bình thường:

```python
trans = bytes.maketrans(CUSTOM_ALPHABET, STANDARD_ALPHABET)
plaintext = base64.b64decode(ciphertext.translate(trans))
```

Dấu hiệu nhận Base64 custom: chuỗi output chỉ gồm 64 ký tự khác nhau, độ dài bội số 4 (có padding `=`), và khi bạn thử base64 chuẩn thì ra rác nhưng độ dài khớp. Lúc đó đi tìm bảng alphabet.

## Nguyên tắc chung: chép thuật toán, đừng chạy lại binary

Với cả ba thứ trên, cách làm nhanh nhất không phải debug từng byte trong binary mà là **đọc đủ để hiểu thuật toán rồi viết lại bằng Python**. Python có sẵn `base64`, số nguyên to tuỳ ý, và cú pháp bitwise gọn. Một routine mã hoá mất cả buổi để trace trong debugger thường chỉ là mười dòng Python khi bạn đã hiểu nó.

## Lab tự làm

Trong `labs/16.2/` có `src/make_data.py` sinh ba chuỗi bị mã hoá (XOR multi-byte, RC4, Base64 custom) và `src/solve.py` giải cả ba. Nhiệm vụ: nhìn ba ciphertext, nhận ra từng loại, rồi tự viết Python decode trước khi mở lời giải. Tất cả đã chạy thật bằng Python 3.11, kết quả nằm trong [solution](https://github.com/Haind03/Technique-Reverse/blob/main/labs/16.2/solution.md).

## Checklist ghi nhớ
- Vòng lặp XOR một buffer với hằng số hoặc mảng key = routine mã hoá chuỗi. Dùng known-plaintext để lấy key.
- RC4 không có magic constant: nhận qua mảng 256 khởi tạo 0..255 rồi hoán vị hai vòng với mod 256. Tìm key là giải được (đối xứng).
- Base64 custom: tìm bảng alphabet 64 ký tự trong binary, ánh xạ về bảng chuẩn rồi decode.
- Cách nhanh nhất: hiểu thuật toán rồi viết lại bằng Python, đừng trace từng byte.
