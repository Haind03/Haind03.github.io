---
title: "Bài 20.1: Thực chiến trên crackmes.one, từ cấp 1 đến cấp 4"
date: 2026-10-06 09:59:00 +0700
categories: ["Technique Reverse", "Phần 20 · Thực chiến"]
tags: [reverse-engineering, ctf]
render_with_liquid: false
---
Học xong 19 phần, bạn có đủ công cụ và lý thuyết. Giờ là lúc ngồi xuống gỡ binary thật cho tới khi tay quen. Không nơi nào tốt hơn crackmes.one để luyện: hàng nghìn bài do cộng đồng tạo riêng cho mục đích học, phân loại theo độ khó, ngôn ngữ, nền tảng, hoàn toàn hợp pháp để mổ xẻ. Bài này chỉ cho bạn cách khai thác kho đó và đưa ra writeup mẫu cho bốn mức, mỗi mức dùng một crackme tôi tự dựng (có trong `labs/20.1/`) đại diện cho dạng bài bạn sẽ gặp.

## Dùng crackmes.one thế nào

Vào crackmes.one, tạo một tài khoản (cần để tải file, password giải nén các archive luôn là `crackmes.one`). Bộ lọc là bạn thân:

- **Difficulty** từ 1 tới 6. Bắt đầu từ 1, đừng nhảy cóc.
- **Quality** nên chọn cao để tránh bài viết ẩu.
- **Language / Platform**: lọc đúng thứ bạn đang học. Mới thì chọn C/C++ trên Windows hoặc Linux.

Đọc phần mô tả của tác giả trước khi tải, nó thường nói rõ mục tiêu (tìm password, viết keygen, hay unpack). Giải trong VM theo [Bài 0.3](/posts/tr-0-3-dung-lab-an-toan/). Phần lớn crackme vô hại, nhưng tập thói quen cô lập ngay từ đầu là tốt.

Và quan trọng nhất: áp đúng vòng lặp ở [Bài 0.4](/posts/tr-0-4-quy-trinh-reverse/). Triage, static, dynamic, ghi chép. Không có bài nào thắng được bằng cách mở IDA rồi cuộn vô định.

## Cấp 1: đọc static ra ngay, hoặc patch một byte

Dạng điển hình: chương trình đọc input, gọi `strcmp` so với một chuỗi cố định nằm thẳng trong binary. Không mã hoá, không gì cả.

Lấy `labs/20.1/src/level1.c` làm mẫu. Bước đầu luôn là triage. Chạy `strings` trước khi làm gì khác:

```
$ strings -n 6 level1 | grep -i flag
letmein123
Correct! Flag: FLAG{level1_strings_win}
```

Xong. Password `letmein123` lộ ngay trong strings, chẳng cần disassemble. Đây là lý do `strings` luôn là lệnh đầu tiên: rất nhiều crackme cấp 1 chết ở đây.

Nếu muốn tập patch thay vì tìm password, mở decompiler và tìm chỗ so sánh. Trong binary này:

```asm
1270:  call   strcmp
1275:  test   eax, eax
1277:  jne    128a          ; byte: 75 11, nhay toi nhanh "Nope."
1279:  lea    rax, [rip+...] ; nhanh "Correct!"
```

Cặp `test eax,eax` + `jne` chính là câu `if (strcmp(...) == 0)`. `strcmp` trả 0 khi khớp, `test` set ZF, `jne` nhảy sang nhánh "Nope" khi KHÔNG khớp. Muốn chương trình luôn báo đúng, vô hiệu lệnh `jne` bằng cách ghi đè `75 11` thành `90 90` (hai lệnh `nop`) tại file offset `0x1277`. Sau khi patch, nhập password bất kỳ vẫn ra "Correct!". Đây đúng là kỹ thuật ở [Bài 17.1](/posts/tr-17-1-patch-binary-jump-nop-codecave/), và nó đã được kiểm chạy thật trong lab.

Hai con đường, chọn cái nào cũng được: tìm password là hiểu bài, patch là qua bài. Người ra đề cấp 1 thường chấp nhận cả hai.

## Cấp 2: serial có biến đổi, phải đảo ngược

Lên một bậc, tác giả không để password trần nữa. Họ biến đổi từng ký tự rồi so với một mảng hằng số nhúng trong binary. `strings` vô dụng vì password không tồn tại dưới dạng chuỗi.

`labs/20.1/src/level2.c` làm thế này: `enc[i] = (pw[i] ^ 0x2A) + 3`, rồi so `enc` với mảng `TARGET`. Khi đọc decompiler bạn sẽ thấy một vòng lặp qua input, một phép `xor 0x2A`, một phép `+3`, và so sánh với mảng byte. Mảng đó đọc được ngay trong `.rodata`:

```
TARGET = 5C 1C 4C 5B 1C 61 21 1B
```

Có phép biến đổi và có kết quả, việc còn lại là đảo ngược. Phép thuận là `xor` rồi `+3`, nên phép nghịch là trừ 3 rồi `xor` lại (xor là phép tự nghịch đảo, xem [Bài 1.1](/posts/tr-1-1-hex-endian-bitwise/)):

```python
TARGET = [0x5C,0x1C,0x4C,0x5B,0x1C,0x61,0x21,0x1B]
pw = ''.join(chr(((b - 3) & 0xFF) ^ 0x2A) for b in TARGET)
print(pw)   # s3cr3t42
```

Chạy ra `s3cr3t42`, nhập vào crackme là "Correct!". Mấu chốt của cấp 2 là nhận ra chuỗi phép toán rồi đảo lại. Phần lớn chỉ là xor, add, sub, rotate, đúng những gì ở [Bài 16.2](/posts/tr-16-2-xor-rc4-base64-custom/).

## Cấp 3: viết keygen

Cấp 3 là ranh giới giữa người bắt chước và người hiểu. Serial không còn cố định mà phụ thuộc username theo một thuật toán. Patch thì được, nhưng đề yêu cầu keygen: sinh serial hợp lệ cho username bất kỳ, nghĩa là bạn phải hiểu và tái tạo đúng thuật toán.

`labs/20.1/src/level3.c` tính serial từ username bằng một hash tuyến tính rồi in hex:

```c
acc = 0x1337;
for each ch in name:  acc = acc*33 + ch;
acc ^= 0xC0FFEE;
serial = "%08X" % (acc & 0xFFFFFFFF);
```

Khi reverse, bạn nhận ra hằng số khởi tạo `0x1337`, phép nhân với 33 (hay thấy ở hash kiểu djb2), và `xor 0xC0FFEE` cuối cùng. Chép nguyên logic sang Python là có keygen, không cần đảo ngược gì vì hash một chiều nhưng ta chỉ cần tính xuôi để sinh serial đúng cho username ta chọn:

```python
def gen(name):
    acc = 0x1337
    for ch in name.encode():
        acc = (acc*33 + ch) & 0xFFFFFFFF
    return "%08X" % (acc ^ 0xC0FFEE)
```

Kiểm thật: `gen("reverser")` ra `F10E026B`, nhập cặp `reverser` / `F10E026B` vào crackme thì "Correct!". Đổi username khác, keygen vẫn ra serial hợp lệ. Đây chính là tư duy ở [Bài 3.6](/posts/tr-3-6-lab-viet-keygen/).

Khi thuật toán kiểm tra rối tới mức đảo ngược bằng tay quá mệt (nhiều ràng buộc chéo giữa các ký tự), đừng cố giải tay: ném cho **Z3** như [Bài 16.4](/posts/tr-16-4-viet-lai-python-z3/), hoặc **angr** như [Bài 18.3](/posts/tr-18-3-symbolic-execution-angr-triton/). Solver tìm input thoả điều kiện giúp bạn.

## Cấp 4: có anti-reverse, phải dùng dynamic

Lên cấp 4, bài bắt đầu chống lại bạn: một lớp anti-debug nhẹ, chuỗi bị mã hoá giải lúc chạy, đôi khi packed bằng UPX. Đọc tĩnh không còn ra ngay vì thứ bạn cần chỉ xuất hiện trong bộ nhớ lúc chạy.

Không có một file mẫu cố định cho mức này vì nó là sự kết hợp, nhưng quy trình thì cố định:

1. **Triage kỹ hơn.** DIE báo packed thì unpack trước ([Bài 14.2](/posts/tr-14-2-unpack-upx-oep/)). Entropy cao, import nghèo là dấu hiệu.
2. **Chuẩn bị debugger chịu được anti-debug.** Bật ScyllaHide trong x64dbg ([Bài 15.9](/posts/tr-15-9-bypass-scyllahide-titanhide/)) để qua `IsDebuggerPresent`, PEB check, timing. Nếu có TLS callback anti-debug thì bật dừng ở TLS callback ([Bài 15.4](/posts/tr-15-4-anti-debug-selfdebug-tls/)).
3. **Để chương trình tự giải mã rồi bắt tại chỗ.** Chuỗi mã hoá thì đặt breakpoint sau hàm giải mã, đọc kết quả trong bộ nhớ thay vì giải tay.
4. **Khi anti-debug quá dày, bỏ debugger đi.** Emulate đoạn giải mã bằng Unicorn ([Bài 18.2](/posts/tr-18-2-emulation-unicorn-qiling/)): không có debugger thật thì cả loạt anti-debug thành vô dụng.

Chiến lược tổng cho nhiều lớp anti nằm ở [Bài 15.10](/posts/tr-15-10-chien-luoc-nhieu-lop-anti/). Điểm cốt lõi: bóc từng lớp từ ngoài vào, và chuyển sang dynamic ngay khi static bị chặn.

## Lời khuyên để tiến bộ nhanh

- **Làm theo thứ tự độ khó.** Nhảy vào cấp 4 khi chưa chắc cấp 2 chỉ tổ nản.
- **Viết writeup cho mỗi bài giải được.** Viết lại buộc bạn hiểu thật, và sau này tra lại rất nhanh. Đăng lên crackmes.one còn giúp người khác.
- **Đặt giới hạn thời gian.** Kẹt một bài quá hai buổi tối thì đọc writeup của người khác, học cách họ nghĩ, rồi quay lại bài tương tự.
- **Mỗi phần ngôn ngữ học xong, tìm một crackme đúng ngôn ngữ đó mà làm.** Lý thuyết chỉ dính lại khi bạn tự tay gỡ.

## Lab tự làm

Trong `labs/20.1/`:

- `src/level1.c`, `level2.c`, `level3.c`: ba crackme đại diện cấp 1 tới 3, build bằng gcc. Đáp án và cách giải trong `solution.md`, nhưng tự làm trước đã.
- `src/keygen_level3.py`: keygen tham khảo cho level3.
- Nhiệm vụ chính: tạo tài khoản crackmes.one, giải lần lượt từ difficulty 1, và viết writeup cho mỗi bài.

Chi tiết trong [labs/20.1/README.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/20.1/README.md).

## Checklist ghi nhớ

- `strings` là lệnh đầu tiên, cấp 1 hay chết ở đó.
- Cặp `test`/`cmp` + `j*` là chỗ rẽ nhánh, patch nó để qua check nhanh.
- Serial có biến đổi thì nhận ra chuỗi phép toán rồi đảo ngược (xor tự nghịch).
- Keygen là hiểu và tái tạo thuật toán, khi rối thì dùng Z3/angr.
- Gặp anti-reverse thì unpack trước, bật ScyllaHide, chuyển sang dynamic hoặc emulation.
- Giải theo thứ tự độ khó, viết writeup, đặt giới hạn thời gian.
