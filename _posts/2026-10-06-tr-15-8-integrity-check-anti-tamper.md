---
title: "Bài 15.8: Integrity check và anti-tamper, khi patch xong thì chương trình tự biết"
date: 2026-10-06 09:33:00 +0700
categories: ["Technique Reverse", "Phần 15 · Anti-Reverse chuyên sâu và cách vượt qua"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
Bạn tìm ra chỗ kiểm license, NOP một cái `jz`, lưu file, chạy lại. Thay vì "Correct!", chương trình lặng lẽ thoát, hoặc tệ hơn, chạy sai một cách khó hiểu ba hàm sau đó. Bạn không làm gì sai trong bước patch cả. Vấn đề là chương trình vừa tự sờ vào code của chính nó, thấy có người động vào, và giận dỗi.

Đó là integrity check (kiểm tra toàn vẹn), còn gọi là self-check hay anti-tamper. Bài này nói nó hoạt động ra sao và vì sao cách đối phó đúng không phải là patch cẩn thận hơn, mà là đừng để nó kiểm tra nữa.

## Ý tưởng cốt lõi

Chương trình tự đọc các byte code của chính nó, tính một checksum (CRC32, hoặc một hash), rồi so với một giá trị đã nhúng sẵn lúc build. Nếu khớp, code còn nguyên vẹn. Nếu lệch, ai đó đã sửa, và nó phản ứng.

```c
uint32_t got = crc32(dia_chi_ham_can_bao_ve, kich_thuoc);
if (got != EXPECTED_CHECKSUM) {
    // code da bi sua
    exit(3);
}
```

`EXPECTED_CHECKSUM` được tính một lần lúc phát hành rồi ghi cứng vào binary. Khi bạn patch dù chỉ một byte trong vùng được kiểm, checksum đổi, và `got != EXPECTED` thành đúng.

Điểm quan trọng: vùng bị kiểm là **code đã biên dịch** (các byte lệnh), không phải logic C. Đổi một bit trong một lệnh là đủ làm hỏng checksum. Trong lab kèm bài, chỉ cần lật một bit trong hàm được bảo vệ:

```
Bản sạch:   checksum = 0xEE604937  -> "Correct!"
Lật 1 bit:  checksum = 0x245EBAA4  -> "Integrity check FAILED. Code da bi sua." (thoát, exit 3)
```

Cùng một input đúng, nhưng vì code bị động vào, chương trình từ chối chạy.

## Vì sao patch trực tiếp luôn thua

Phản xạ của người mới là patch cho khéo hơn: NOP ít byte hơn, sửa đúng một lệnh. Vô ích. Checksum không quan tâm bạn sửa bao nhiêu hay sửa khéo cỡ nào, chỉ cần một byte trong vùng kiểm khác đi là lộ. Bạn không thắng được một hàm băm bằng cách patch tinh tế.

Tệ hơn, protector nghiêm túc rải nhiều lớp check chéo nhau: hàm A checksum vùng chứa hàm B, hàm B lại checksum vùng chứa hàm A và cả hàm kiểm license. Vô hiệu hoá một chỗ thì chỗ khác bắt được. Có loại không thoát ngay mà làm hỏng dữ liệu từ từ để bạn tưởng mình patch sai.

## Hướng đi đúng: tấn công người gác, không sửa cái cửa

Nguyên tắc: thay vì sửa code bị canh, hãy vô hiệu hoá chính cái canh. Ba cách, từ sạch tới bẩn.

**1. Tắt hàm integrity check.** Hàm `verify_integrity` thường không tự kiểm chính nó (ai canh người canh?). Nên bạn ghi đè đầu nó bằng `mov eax, 1; ret` (byte `B8 01 00 00 00 C3`), nó luôn báo "còn nguyên vẹn", rồi patch logic license thoải mái. Trong lab, sau khi lật bit hàm license (checksum đã hỏng), chỉ cần làm thêm bước này:

```
Lật bit license + tắt verify_integrity  ->  "Correct!" (exit 0)
```

Hàm check nằm ngoài vùng tự kiểm nên sửa nó không làm hỏng checksum của chính nó. Người gác ngủ, cái cửa mở toang.

**2. Patch nhánh so sánh checksum.** Nếu không muốn đụng cả hàm, tìm đúng chỗ `cmp got, EXPECTED` rồi `jne fail` và đảo/NOP nhánh đó. Cùng tư tưởng: làm kết quả so sánh luôn "khớp".

**3. Patch trong bộ nhớ sau khi check đã chạy.** Để chương trình tự kiểm lúc khởi động (code trên đĩa còn nguyên nên qua), rồi dùng debugger sửa code trong RAM sau thời điểm đó. Checksum đã chạy xong, không ai kiểm lại nữa. Đây là lý do runtime patch nhiều khi dễ hơn patch trên đĩa, nối lại [Bài 17.1](https://github.com/Haind03/Technique-Reverse/tree/main/phan-17-patch-hook-frida).

Có một cách thứ tư ít dùng: tính lại `EXPECTED` cho đúng với code đã patch rồi ghi đè giá trị nhúng. Chỉ khả thi khi bạn hiểu rõ thuật toán checksum và tìm được chỗ lưu giá trị, mà nhiều lớp chéo nhau làm nó mệt.

## Tìm hàm integrity check ở đâu

Dấu hiệu nhận ra trong lúc static:
- Một hàm **đọc chính code section của mình**: con trỏ trỏ vào vùng `.text` (địa chỉ của một hàm khác, hoặc base của image) rồi lặp qua từng byte.
- Một **vòng lặp CRC**: `xor`, `shr`, và một hằng số đặc trưng. CRC32 hay lộ polynomial `0xEDB88320`, nối lại cách nhận hằng số ở [Bài 16.1](https://github.com/Haind03/Technique-Reverse/tree/main/phan-16-crypto-thuat-toan).
- So sánh kết quả với một **hằng số 32-bit cứng** rồi rẽ nhánh thoát.
- Hàm được gọi **rất sớm** (trong khởi tạo, hoặc TLS callback, xem [Bài 15.4](/posts/tr-15-4-anti-debug-selfdebug-tls/)) hoặc gọi lặp lại nhiều lần.

Mẹo động: đặt breakpoint khi có đoạn code đọc bộ nhớ trong vùng `.text` của chính mình (memory breakpoint read trên code section). Hàm nào chạm vào code mà không phải để thực thi thì rất đáng ngờ.

## Checklist ghi nhớ
- Integrity check = chương trình tự checksum code của mình rồi so với giá trị nhúng, phát hiện patch.
- Patch một byte trong vùng kiểm là đủ làm lộ. Patch khéo hơn không cứu được bạn.
- Đừng sửa code bị canh, hãy vô hiệu hoá hàm check (mov eax,1; ret), hoặc patch nhánh so sánh, hoặc patch trong RAM sau khi check đã chạy.
- Hàm check hiếm khi tự kiểm chính nó, đó là điểm yếu để khai thác.
- Nhận ra qua: đọc chính .text, vòng lặp CRC (hằng số 0xEDB88320), so với hằng số cứng rồi thoát.
- Protector mạnh rải nhiều lớp chéo nhau: tìm cho hết trước khi mừng.
