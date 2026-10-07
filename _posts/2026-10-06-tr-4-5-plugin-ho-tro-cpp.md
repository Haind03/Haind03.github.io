---
title: "Bài 4.5: Plugin dựng lại class C++, để máy làm phần nhàm chán"
date: 2026-10-06 08:35:00 +0700
categories: ["Technique Reverse", "Phần 4 · C++"]
tags: [reverse-engineering, cpp]
render_with_liquid: false
---
Bài 4.2 bạn đã dựng cây class bằng tay: tìm vtable, đọc RTTI, gán kiểu, lần kế thừa. Làm một hai class thì vui, làm một chương trình C++ thật với vài chục class thì đó là cả ngày trời lặp đi lặp lại một việc. Đây đúng là loại việc nên giao cho plugin. Chúng không thay bạn hiểu logic, nhưng dọn sạch phần cơ học để bạn tập trung vào code của tác giả.

Bài này điểm qua các plugin chủ lực cho IDA và Ghidra, và quan trọng hơn là biết khi nào tin chúng, khi nào phải xắn tay làm lại.

## Vì sao tự động hoá được

Nhớ lại bài 4.2: một binary C++ build với RTTI (Run-Time Type Information) bật mang theo sẵn rất nhiều manh mối có cấu trúc. Mỗi class có virtual function sẽ có một `type_info`, một chuỗi tên class đã mangle, và một vtable trỏ tới nó. Những thứ này nằm theo khuôn cố định do ABI quy định (Itanium trên Linux, MSVC ABI trên Windows). Khuôn cố định nghĩa là máy quét được. Plugin chỉ việc đi dọc các cấu trúc RTTI, đọc tên class, nối vtable với class, suy ra cha con từ bảng base class.

Hệ quả thực tế: nếu binary **có RTTI**, plugin làm được 80% việc dựng cây class trong vài giây. Nếu RTTI bị tắt (`/GR-` trên MSVC, `-fno-rtti` trên g++) hoặc bị obfuscate, plugin đuối hẳn và bạn quay về làm tay như bài 4.2.

## Phía IDA

### Class Informer

Class Informer là plugin quét toàn bộ binary tìm cấu trúc RTTI rồi liệt kê mọi class nó thấy, kèm địa chỉ vtable và quan hệ kế thừa. Chạy một lần, bạn có ngay một danh sách class thật với tên thật (`Animal`, `Dog`, `BankAccount`) thay vì `sub_` và `off_`. Nó cũng đánh dấu từng vtable trong IDA để bạn nhảy tới xem các virtual function.

Đây thường là bước đầu tiên khi mở một binary C++ lớn trong IDA: chạy Class Informer để có bản đồ class, rồi mới đi sâu.

### HexRaysPyTools

Nếu Class Informer cho bạn danh sách class, HexRaysPyTools giúp bạn biến danh sách đó thành type dùng được trong decompiler. Vài tính năng hay dùng:

- **Dựng struct từ cách dùng.** Đặt con trỏ vào một biến mà decompiler đang hiển thị là `a1` với một đống `*(a1 + 8)`, `*(a1 + 16)`, plugin gom các offset đó lại và đề xuất một struct. Bạn chấp nhận là Hex-Rays lập tức hiển thị `obj->field_8` thay cho số học con trỏ thô.
- **Nhận diện vtable** và tạo struct vtable, nối method ảo vào đúng chỗ.
- **Scan nhiều hàm** để gộp hiểu biết về cùng một kiểu.

Cặp Class Informer (tìm class) cộng HexRaysPyTools (biến thành type) là combo tiêu chuẩn cho C++ RE trên IDA. Xem thêm ở [kho công cụ](/posts/tr-tai-nguyen-cong-cu/).

### Virtuailor

Một vấn đề riêng: lời gọi virtual trong asm là `call [rax+offset]`, decompiler không biết hàm cụ thể nào được gọi vì nó phụ thuộc runtime. Virtuailor cố giải quyết bằng cách lần theo vtable để gán tên hàm cho các virtual call, giúp bạn thấy `call Dog::speak` thay vì `call qword ptr [rax+0x10]`.

## Phía Ghidra

### RTTIAnalyzer có sẵn

Ghidra không cần cài thêm gì cho bước cơ bản. Trong lúc auto-analysis, nếu bạn bật các analyzer liên quan RTTI (tên kiểu "Windows x86 PE RTTI Analyzer" hoặc phần phân tích C++ class), Ghidra tự tạo các cấu trúc type_info, đặt tên vtable, và dựng một phần hierarchy. Kiểm trong Data Type Manager sau khi phân tích, bạn sẽ thấy các class đã được tạo.

### OOAnalyzer và Kaiju

Với binary không có RTTI (chỗ RTTIAnalyzer bó tay), có các hướng mạnh hơn. OOAnalyzer (thuộc bộ Pharos của CERT) dùng phân tích tĩnh suy ra class, member, method kể cả khi không có RTTI, rồi xuất kết quả nạp vào Ghidra qua plugin. Kaiju (CERT) là bộ tiện ích Ghidra gói nhiều phân tích nhị phân, trong đó có phần hỗ trợ OOAnalyzer. Cài đặt nặng tay hơn plugin thường, nhưng khi gặp binary C++ to mà không có RTTI thì đáng.

Ngoài ra Ghidra scriptable (Java/Python), nên có nhiều script cộng đồng khôi phục class, gán vtable, đặt tên theo RTTI. Khi plugin có sẵn không vừa ý, viết script là lối thoát.

## Khi nào plugin giúp, khi nào phải làm tay

Plugin không phải nút thần kỳ. Nắm ranh giới để khỏi tin nhầm:

| Tình huống | Plugin giúp được? |
|---|---|
| Binary có RTTI, không obfuscate | Rất tốt, dựng cây class gần như tự động |
| RTTI bị tắt (`-fno-rtti`, `/GR-`) | Kém, phải suy class từ vtable và cách dùng, làm tay như bài 4.2 |
| Có packer/obfuscator giấu vtable | Phải unpack trước (Phần 14), plugin vô dụng trên code chưa lộ |
| Chỉ cần hiểu một hàm, không cần cả cây class | Nhiều khi làm tay nhanh hơn, khỏi chạy plugin |
| Class khổng lồ, nhiều kế thừa | Plugin tiết kiệm hàng giờ |

Một cạm bẫy: plugin đặt tên theo RTTI, mà RTTI phản ánh tên class **lúc compile**, không đảm bảo logic. Dựng được cây class đẹp không có nghĩa bạn đã hiểu chương trình làm gì. Tên class chỉ là điểm khởi đầu để đọc, không phải đích đến.

## Lab tự làm

Lab ở [labs/4.5/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/4.5): dùng lại binary C++ có RTTI từ lab 4.2, chạy Class Informer (hoặc Ghidra RTTIAnalyzer) rồi so sánh thời gian và kết quả với lần bạn dựng tay ở 4.2.

## Checklist ghi nhớ
- Plugin dựng class dựa chủ yếu vào RTTI. Có RTTI thì nhanh, không RTTI thì đuối.
- IDA: Class Informer (liệt kê class từ RTTI) + HexRaysPyTools (biến thành type trong decompiler) là combo tiêu chuẩn. Virtuailor cho virtual call.
- Ghidra: RTTIAnalyzer có sẵn cho bước cơ bản, OOAnalyzer/Kaiju cho binary không RTTI.
- Plugin dọn phần cơ học, không thay bạn hiểu logic. Tên class chỉ là điểm khởi đầu.
- Obfuscate hoặc packed thì phải xử lý trước, plugin không chạy trên code chưa lộ.
