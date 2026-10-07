---
title: "Bài 10.1: Reverse chương trình Delphi và C++Builder"
date: 2026-10-06 09:06:00 +0700
categories: ["Technique Reverse", "Phần 10 · Ngôn ngữ legacy: Delphi, VB6, AutoIt, AHK"]
tags: [reverse-engineering, legacy]
render_with_liquid: false
---
Có một ngày bạn mở một file exe cũ trong IDA, decompiler nhả ra pseudocode nhưng mọi hàm đều là `sub_xxx`, không một cái tên quen thuộc, các chuỗi thì dính length phía trước, và cả nghìn hàm của một framework nào đó ngập màn hình. Khả năng cao bạn vừa gặp một binary Delphi. Đây là loại chương trình legacy vẫn còn sống khỏe trong phần mềm doanh nghiệp, POS, phần mềm kế toán Việt Nam, và kha khá malware. Nó không khó hơn C, chỉ là khác, và cần đúng công cụ.

## Delphi là cái gì, và vì sao nó khác

Delphi (cùng người anh em C++Builder) dùng compiler của Borland, nay là Embarcadero. Code viết bằng Object Pascal, biên dịch thẳng ra native x86/x64, nên về bản chất bạn vẫn đang đọc assembly thường. Nhưng Delphi để lại vài dấu vân tay rất riêng khiến việc reverse lệch khỏi thói quen C:

- **Framework VCL** (Visual Component Library). Gần như mọi app Delphi kéo theo cả rừng hàm VCL (quản lý form, button, string, stream). Giống libc tĩnh trong C, phần lớn code bạn thấy không phải của tác giả mà là framework. Lọc được nó ra là thắng một nửa.
- **Chuỗi kiểu Pascal**. Khác C dùng null-terminated, chuỗi Delphi (AnsiString, UnicodeString) có **length prefix**: độ dài và refcount nằm ngay trước con trỏ dữ liệu. Trong IDA bạn thấy chuỗi không kết thúc bằng `00` mà có mấy byte độ dài phía trước. Biết điều này mới đọc đúng.
- **Form nhúng trong resource**. Giao diện được lưu dưới dạng DFM (Delphi Form Module) ngay trong resource section của exe. DFM mô tả từng component và quan trọng là tên các **event handler** (ví dụ `Button1Click`). Đây là mỏ vàng để lần ra logic.
- **Calling convention register**. Delphi mặc định dùng `register` (fastcall riêng của Borland): ba tham số đầu qua EAX, EDX, ECX, khác cdecl/stdcall quen thuộc. Đọc nhầm convention là hiểu sai tham số.

## Nhận ra Delphi trong một phút

Kéo file vào **Detect It Easy (DIE)**. Nó thường chỉ thẳng ra compiler là Borland Delphi hoặc Embarcadero, kèm cả phiên bản. Vài dấu hiệu khác cũng tố cáo Delphi:

- Chuỗi `Borland` / `Embarcadero` / tên unit như `System`, `SysUtils`, `Classes`, `Vcl.Forms` trong strings.
- Entry point gọi vào một hàm khởi tạo runtime rất đặc trưng (thiết lập VCL, gọi `InitExe`).
- Resource section có các blob DFM (bạn sẽ thấy tên component, `TForm`, `TButton`).

Xác nhận được là Delphi thì đừng vội cắm đầu đọc assembly trong IDA. Lấy đúng đồ nghề đã.

## IDR: trợ thủ không thể thiếu

Vấn đề của IDA thuần với Delphi là nó không biết hàng nghìn hàm kia là VCL, nên để nguyên `sub_xxx` và bạn chết chìm. **IDR (Interactive Delphi Reconstructor)** sinh ra để giải đúng chuyện này. IDR làm ba việc quan trọng:

1. **Khôi phục tên hàm VCL/RTL** đã biết, đặt lại tên như `TStringList.Add`, `ShowMessage`, để bạn bỏ qua chúng và tập trung vào code tác giả.
2. **Dựng lại form và event handler** từ DFM. Bạn thấy được `Button1Click` nằm ở địa chỉ nào, tức là biết ngay chỗ xử lý khi người dùng bấm nút.
3. **Xuất ra map/idc** để import ngược vào IDA, biến đống `sub_xxx` thành tên có nghĩa.

Quy trình thực tế: chạy IDR trên exe Delphi, để nó phân tích, xuất file hỗ trợ (ví dụ .idc hoặc .map), rồi nạp vào IDA. Sau bước này IDA của bạn đột nhiên đọc được. **DeDe** là công cụ cũ hơn cùng ý tưởng, chỉ hợp với Delphi rất xưa, giờ gần như luôn chọn IDR.

Với C++Builder thì phức tạp hơn một chút vì trộn C++ (có name mangling, class, vtable như Phần 4) với runtime Borland, nhưng cách tiếp cận tương tự: nhận diện bằng DIE, dùng IDR cho phần VCL, rồi áp kiến thức C++ cho phần còn lại.

## Đi từ event handler, không đi từ main

Đây là mẹo quan trọng nhất của bài. Với app C bạn tìm `main`. Với app Delphi có giao diện, `main` chỉ là vòng lặp message của VCL, không có gì thú vị. Logic thật nằm trong các **event handler**: người dùng nhập serial rồi bấm nút OK, thì hàm `btnOKClick` (hay tên tương tự) mới là nơi kiểm tra.

Nhờ IDR dựng lại form, bạn biết tên và địa chỉ các handler. Nhảy thẳng tới handler của nút liên quan là tới đúng chỗ, bỏ qua toàn bộ code khởi tạo UI. Nếu không có tên, hãy tìm theo chuỗi thông báo ("Sai mật khẩu", "Đăng ký thành công") rồi xref ngược, đúng như thói quen đã học ở các phần trước, chỉ nhớ chuỗi Delphi có length prefix nên khi tìm hãy tìm phần text chứ đừng kèm byte độ dài.

## Checklist ghi nhớ
- Delphi/C++Builder là native x86/x64, nhưng kéo theo rừng hàm VCL và có dấu vân tay riêng.
- Chuỗi Delphi có length prefix, không null-terminated. Đọc và tìm kiếm phải nhớ điều này.
- Mặc định dùng calling convention register (EAX, EDX, ECX cho 3 tham số đầu).
- Nhận diện bằng DIE, rồi dùng IDR để khôi phục tên VCL và dựng lại form/event handler.
- Đi từ event handler (ví dụ Button1Click) chứ đừng đi từ main, vì main chỉ là message loop.

## Lab tự làm
Xem [labs/10.1/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/10.1): nhận diện một exe Delphi bằng DIE, dùng IDR dựng lại form và event handler, rồi lần tới hàm xử lý nút OK.
