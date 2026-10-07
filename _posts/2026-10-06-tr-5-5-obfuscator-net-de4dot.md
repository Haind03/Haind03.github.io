---
title: "Bài 5.5: Obfuscator .NET và cách gỡ"
date: 2026-10-06 08:41:00 +0700
categories: ["Technique Reverse", "Phần 5 · C# / .NET (dnSpy, ILSpy)"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
Bốn bài trước bạn thấy .NET dễ reverse tới mức gần như gian lận: decompile ra C# đọc như bản gốc. Chính vì thế người viết phần mềm .NET mới dựng cả một ngành công nghiệp obfuscator để làm khó bạn. Tin tốt là phần lớn obfuscator phổ biến đã có tool gỡ gần như tự động. Tin không vui là vẫn còn những lớp phải tự tay bóc. Bài này cho bạn bản đồ: nhận ra đang gặp cái gì, thử tool nào trước, và khi tool bó tay thì làm sao.

Trước khi đi tiếp, nhắc lại ranh giới ở [Bài 0.2](/posts/tr-0-2-phap-ly-dao-duc/): những kỹ thuật dưới đây chỉ dùng cho assembly của chính bạn, mẫu học, crackme, hoặc phân tích malware phòng thủ. Gỡ bảo vệ phần mềm thương mại để dùng chùa là chuyện khác hẳn.

## Obfuscator thực ra làm những gì

Obfuscation không mã hoá chương trình, nó vẫn phải chạy được trên CLR. Nó chỉ làm cho code sau khi decompile trở nên khó đọc. Có vài nhóm kỹ thuật, bạn sẽ gặp lẫn lộn:

- **Renaming.** Đổi tên class, method, field, biến từ `CheckLicense` thành `a`, `b`, hoặc tệ hơn là các ký tự Unicode vô hình, chữ Trung, hay chuỗi lộn xộn. Đây là lớp phổ biến nhất và cũng khó chịu nhất vì nó xoá hết manh mối ngữ nghĩa.
- **String encryption.** Mọi chuỗi (thông báo, tên hàm gọi động, URL) bị mã hoá, thay bằng lời gọi kiểu `Decrypt(0x1234)`. Bạn không còn grep được chuỗi "Invalid license" nữa.
- **Control flow obfuscation.** Nhét thêm nhánh giả, biến luồng thẳng thành một cái máy trạng thái (switch lồng vòng while) để decompiler dựng lại thành mớ bòng bong `goto`.
- **Proxy / indirect call.** Thay lời gọi method trực tiếp bằng lời gọi gián tiếp qua một lớp trung gian, để Analyze không lần ra ai gọi ai.
- **Anti-tamper.** Assembly tự kiểm tra toàn vẹn của chính nó lúc chạy, sửa một byte là nó hỏng hoặc thoát.
- **Anti-debug.** Phát hiện dnSpy đang attach rồi thoát hoặc rẽ nhánh khác (xem thêm Phần 15).

## Các protector hay gặp

Biết tên để biết đường tra:

- **ConfuserEx.** Mã nguồn mở, miễn phí, cực phổ biến trong crackme và malware .NET. Có nhiều fork (ConfuserEx2, các bản custom). Vì phổ biến nên có nhiều tool unpack riêng.
- **.NET Reactor.** Thương mại, mạnh, có native stub bọc ngoài, anti-tamper và control flow khó.
- **Eazfuscator.NET.** Thương mại, string encryption và virtualization tốt.
- **Dotfuscator.** Đi kèm Visual Studio bản community, nhẹ.
- **SmartAssembly** (Red Gate). Hay thấy trong phần mềm thương mại.
- **Agile.NET, Babel, .NET Guard...** các tên ít gặp hơn.

## Bước đầu luôn là nhận diện

Đừng đoán. Mở file bằng **Detect It Easy** hoặc chỉ cần mở trong **dnSpy**, nhìn vài dấu hiệu:

- DIE thường ghi thẳng tên protector (ConfuserEx, .NET Reactor...).
- Trong dnSpy, nếu tên type/method toàn ký tự lạ, có module `<Module>` chứa nhiều method khả nghi, hoặc thấy attribute kiểu `ConfusedByAttribute`, là biết ngay.
- Entropy cao bất thường và một đống chuỗi byte array to là dấu hiệu string/resource encryption.

Nhận ra protector rồi mới chọn tool đúng, chứ quăng đại de4dot vào một mẫu .NET Reactor thì phí công.

## de4dot: con dao đa năng

**de4dot** là tool gỡ obfuscation .NET kinh điển, nhận ra và tự xử lý nhiều protector (gồm ConfuserEx cũ, Dotfuscator, Babel, Eazfuscator ở mức nào đó). Nó làm được mấy việc chính: giải mã chuỗi, bỏ proxy call, khôi phục control flow phần nào, và đổi lại tên cho dễ đọc hơn (tuy không trả lại tên gốc, chỉ là tên sạch kiểu `Class0`, `method_3`).

Dùng rất gọn từ dòng lệnh:

```
de4dot.exe target.exe
```

Nó tạo `target-cleaned.exe`. Mở bản cleaned trong dnSpy, bạn sẽ thấy decompile ra C# đọc được hơn hẳn: chuỗi đã hiện, luồng đã thẳng lại.

Với ConfuserEx hiện đại, de4dot gốc nhiều khi bó tay. Khi đó dùng bản fork **de4dot-cex** (de4dot chuyên cho ConfuserEx) hoặc các unpacker chuyên dụng theo từng phiên bản ConfuserEx. Riêng **.NET Reactor** có tool riêng tên **.NET Reactor Slayer** xử lý tốt hơn de4dot.

## Khi tool không gỡ hết: trace string decryption bằng dnSpy

Thường gặp nhất là tool gỡ được renaming và control flow nhưng chuỗi vẫn còn mã hoá, hoặc tool mới không hỗ trợ protector phiên bản mới. Lúc này con bài mạnh nhất là **để chính chương trình tự giải mã cho bạn** bằng dnSpy debugger (nhắc lại [Bài 5.3](/posts/tr-5-3-debug-net-khong-source-dnspy/)):

1. Tìm hàm giải mã chuỗi. Nó thường là một method static nhận một `int` (hoặc token) và trả về `string`, bị gọi khắp nơi.
2. Đặt breakpoint ngay sau lời gọi `Decrypt(...)`, hoặc đặt trong chính hàm Decrypt tại chỗ `return`.
3. Chạy chương trình (F5). Mỗi lần dừng, nhìn giá trị trả về trong Locals, đó là chuỗi thật.
4. Ghi lại các chuỗi ứng với từng tham số. Giờ bạn có bản đồ `0x1234 -> "Invalid license"`.

Cách này ăn được vì dù obfuscate thế nào, tới lúc dùng chuỗi thì nó phải tồn tại ở dạng rõ trong bộ nhớ. Nguyên tắc này đúng với mọi lớp bảo vệ: thứ gì chương trình cần dùng, nó phải giải ra, và chỗ giải ra là chỗ bạn rình.

Với anti-debug chặn dnSpy, bạn patch hoặc bỏ qua check đó trước (kỹ thuật ở Phần 15), hoặc dùng bản dnSpy có sẵn chống anti-debug, rồi mới trace.

## Nhịp làm việc gợi ý

```
1. Nhận diện protector   (DIE / dnSpy)
2. Thử tool tự động       (de4dot / de4dot-cex / Reactor Slayer)
3. Mở bản cleaned         (dnSpy / ILSpy)
4. Còn chuỗi mã hoá?      -> trace runtime bằng dnSpy debugger
5. Còn control flow rối?  -> đọc từng khối, hoặc để debugger chạy qua
```

Đừng kỳ vọng ra lại source đẹp như chưa obfuscate. Mục tiêu là đủ đọc được để hiểu logic, không phải khôi phục hoàn hảo.

## Lab tự làm

Thực hành ở [labs/5.5/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/5.5): tự obfuscate một assembly nhỏ bằng ConfuserEx rồi dùng de4dot gỡ và so sánh, hoặc nếu không cài được thì làm theo quy trình trace string decryption trong dnSpy trên một mẫu obfuscated.

## Checklist ghi nhớ
- Obfuscation không mã hoá chương trình, chỉ làm code sau decompile khó đọc. Nó vẫn phải chạy được.
- Bốn lớp hay gặp: renaming, string encryption, control flow, anti-tamper/anti-debug.
- Luôn nhận diện protector trước (DIE/dnSpy) rồi mới chọn tool.
- de4dot là lựa chọn đầu tiên, de4dot-cex cho ConfuserEx, Reactor Slayer cho .NET Reactor.
- Tool không gỡ hết thì để chương trình tự giải mã: đặt breakpoint sau hàm Decrypt và đọc chuỗi thật trong dnSpy.
- Mục tiêu là đọc hiểu được logic, không phải khôi phục source hoàn hảo.
