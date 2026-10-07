---
title: "Bài 6.8: Obfuscation và packer trên Android"
date: 2026-10-06 08:51:00 +0700
categories: ["Technique Reverse", "Phần 6 · Java / Kotlin / Android (JADX)"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
Tới đây bạn mở APK nào cũng thấy code Java sạch sẽ trong JADX. Thực tế sẽ phũ phàng hơn: app thương mại gần như luôn được làm rối. Mở ra toàn `a.a.a`, chuỗi biến thành đống ký tự vô nghĩa, có khi JADX còn chẳng thấy code đâu. Bài này giúp bạn nhận ra mình đang gặp loại bảo vệ nào, và quan trọng hơn, biết đường gỡ.

Có hai nhóm khác hẳn nhau mà người mới hay gộp làm một: obfuscation (làm code khó đọc nhưng vẫn nằm đó) và packing (giấu luôn code, chỉ bung ra lúc chạy). Cách xử lý mỗi nhóm một khác.

## R8 và ProGuard: rename là chính

Mọi app Android build ở chế độ release gần như đều đi qua R8 (trước kia là ProGuard, giờ R8 là mặc định của Android Gradle). Việc chính của nó không phải chống reverse mà là thu gọn (minify) và tối ưu: xoá code chết, gộp hàm, và đổi tên class/method/field thành những tên ngắn nhất có thể để giảm kích thước.

Hệ quả cho người reverse: bạn mở JADX ra và thấy la liệt `a`, `b`, `c`, `a.a.b.c`. Logic vẫn còn nguyên và đọc được, chỉ là mất hết tên có nghĩa. Đây là mức nhẹ nhất, hoàn toàn đọc được, chỉ tốn công đặt lại tên khi bạn hiểu từng phần.

Một chi tiết quan trọng: khi build, R8 sinh ra một `mapping.txt` ánh xạ tên gốc sang tên bị rút gọn. File này dùng để giải mã lại crash report. Bạn gần như không bao giờ có nó khi reverse app của người khác, nhưng nhớ sự tồn tại của nó: nếu đang phân tích chính app của mình, giữ lại `mapping.txt` là đọc được tên gốc ngay.

Dấu hiệu nhận ra R8/ProGuard:
- Tên class/method một hai ký tự, package lồng kiểu `a.a.a`.
- Vẫn còn tên của thư viện bên thứ ba và các entry point mà framework bắt buộc giữ (Activity trong manifest, method `onCreate`...), vì những cái đó không rename được.
- Code logic vẫn liền mạch, đọc hiểu được.

## DexGuard và các obfuscator thương mại: nặng hơn nhiều

DexGuard (bản thương mại cùng nhà với ProGuard) và vài tool tương tự thêm những lớp mà R8 không làm:

- **String encryption**: chuỗi literal bị mã hoá, lúc chạy mới giải qua một hàm giải mã. Trong JADX bạn thấy `decrypt("...")` hoặc một mảng byte khó hiểu thay vì chuỗi gốc.
- **Control flow obfuscation**: chèn nhánh rác, biến vòng lặp và if thành dạng rối để decompiler dựng lại sai hoặc xấu.
- **Class/API encryption, reflection**: lời gọi method thật bị giấu sau reflection, nên xref tĩnh đứt.
- **Anti-tamper, anti-debug, anti-Frida**: kiểm tra chữ ký app, phát hiện debugger và Frida.

Với lớp này, đọc tĩnh thuần tuý thường không đủ. Cách thực tế là phân tích động: để app tự giải mã chuỗi rồi đọc kết quả ở runtime, hoặc hook hàm giải mã bằng Frida (xem [Bài 6.6](/posts/tr-6-6-frida-android-hook/)) để in ra chuỗi đã giải.

## Packer: khi code không nằm trong DEX

Đây là nhóm làm người mới hoang mang nhất. Packer (hay "app shielding", "DEX protection") không chỉ làm rối mà **giấu hẳn** code thật: `classes.dex` bạn thấy chỉ là một cái vỏ (loader stub). Code thật bị nén hoặc mã hoá, cất trong assets hoặc một section riêng, và chỉ được giải ra rồi nạp vào bộ nhớ lúc chạy.

Các packer hay gặp (phần lớn từ Trung Quốc vì thị trường app ở đó): Bangcle (SecShell), Qihoo Jiagu, Tencent Legu, Ali (Alibaba) protection, Baidu. Nhiều cái miễn phí nên malware cũng dùng.

Dấu hiệu một app bị pack:
- Mở JADX ra gần như trống: chỉ có một Application class lạ và vài class loader, không thấy logic nghiệp vụ đâu.
- Trong `AndroidManifest.xml`, thẻ `application` trỏ tới một class `android:name` lạ của packer (ví dụ `com.secshell.shellwrapper...`, `com.stub.StubApp`, `com.qihoo...`). Đây là loader chạy đầu tiên.
- Có file `.so` tên lạ trong `lib/`, và file lớn khó hiểu trong `assets/` (chính là DEX đã mã hoá).
- `classes.dex` nhỏ bất thường so với độ phức tạp của app.
- Entropy của file trong assets rất cao (dấu hiệu đã nén/mã hoá, giống packer PE ở [Bài 14.1](https://github.com/Haind03/Technique-Reverse/tree/main/phan-14-packer-obfuscation)).

## Chiến lược gỡ packer: dump DEX lúc chạy

Chìa khoá: dù giấu kỹ đến đâu, trước khi chạy code thật thì packer **phải** giải mã DEX và nạp nó vào bộ nhớ cho Android runtime (ART) thực thi. Nghĩa là tại một thời điểm, DEX đã giải mã nằm sờ sờ trong bộ nhớ tiến trình. Việc của bạn là chộp nó ở đó.

Công cụ phổ biến nhất là **frida-dexdump**: nó quét vùng nhớ của tiến trình tìm các magic DEX (`dex\n035` và các biến thể), rồi dump từng DEX ra file. Quy trình gọn:

```
# cài frida-server trên thiết bị/emulator đã root, frida-dexdump trên host
frida-dexdump -U -f com.example.packed.app     # spawn app và dump
# hoặc attach vào app đang chạy:
frida-dexdump -U -n ten_app
```

Kết quả là một hoặc nhiều file `.dex`. Kéo chúng vào JADX là thấy code thật. Với packer ngoan cố giải mã theo từng phần (lazy), bạn có thể phải dùng app một lúc cho các phần nạp hết rồi mới dump, hoặc dùng các tool chuyên hơn (FRIDA-DEXDump bản nâng, hoặc unpacker riêng cho từng họ packer).

Cách tiếp cận này là một ví dụ của nguyên tắc chung trong unpacking: đừng cố giải mã thủ công, hãy để chính chương trình tự giải rồi lấy kết quả. Bạn sẽ gặp lại đúng tư duy này với packer PE ở [Bài 14.2](https://github.com/Haind03/Technique-Reverse/tree/main/phan-14-packer-obfuscation).

## Khi gặp app lạ, hỏi theo thứ tự

1. Mở JADX. Thấy logic nghiệp vụ không? Nếu có mà chỉ xấu/đổi tên, đó là obfuscation, cứ đọc và rename dần, hook Frida khi gặp chuỗi mã hoá.
2. Nếu JADX trống trơn, xem `android:name` của `application` trong manifest và các file trong `assets/lib`. Nhận ra loader của packer là biết mình phải unpack.
3. Dump DEX runtime bằng frida-dexdump, rồi quay lại bước 1 với DEX đã bung.

## Lab tự làm

Xem [labs/6.8/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/6.8): nhận diện một APK có bị obfuscate hay pack không chỉ qua dấu hiệu, và nếu có packer thì dump DEX ra bằng frida-dexdump rồi mở lại trong JADX. File [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/6.8/solution.md) có writeup.

## Checklist ghi nhớ
- Phân biệt obfuscation (code vẫn nằm đó, chỉ khó đọc) với packing (code bị giấu, chỉ bung lúc chạy). Xử lý khác nhau.
- R8/ProGuard: rename là chính, logic vẫn đọc được, mapping.txt là của người build.
- DexGuard và obfuscator thương mại: thêm string encryption, control flow, anti-debug. Dùng phân tích động để giải chuỗi.
- Dấu hiệu packer: JADX trống, application class lạ trong manifest, file lớn entropy cao trong assets, classes.dex nhỏ bất thường.
- Gỡ packer bằng cách để app tự giải mã rồi dump DEX từ bộ nhớ (frida-dexdump), sau đó mở JADX như thường.
