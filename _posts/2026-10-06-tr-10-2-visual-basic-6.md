---
title: "Bài 10.2: Visual Basic 6, hai thế giới trong cùng một file exe"
date: 2026-10-06 09:07:00 +0700
categories: ["Technique Reverse", "Phần 10 · Ngôn ngữ legacy: Delphi, VB6, AutoIt, AHK"]
tags: [reverse-engineering, legacy]
render_with_liquid: false
---
Visual Basic 6 ra đời cuối thập ni 90 nhưng tới giờ vẫn còn vô số phần mềm nội bộ, công cụ nhỏ, và cả malware viết bằng nó. Reverse VB6 có một cái bẫy lớn ngay từ đầu: hai file exe trông giống nhau, cùng là VB6, nhưng cách bạn phân tích chúng khác nhau hoàn toàn. Lý do nằm ở chế độ biên dịch. Hiểu được chỗ này trước là tiết kiệm cả buổi loay hoay.

Trước hết, đừng nhầm VB6 với VB.NET. Cái tên giống nhau nhưng là hai công nghệ khác hẳn. VB.NET biên dịch ra IL và chạy trên CLR, bạn mở nó bằng dnSpy/ILSpy như mọi assembly .NET khác (xem lại Phần 5). VB6 thì không liên quan gì tới .NET, nó biên dịch ra một dạng rất riêng mà bài này nói tới. Nhận ra bạn đang cầm cái nào là việc đầu tiên, và Detect It Easy làm việc đó trong một giây.

## Dấu hiệu nhận ra một file VB6

Mở file trong DIE hoặc nhìn bảng import, dấu hiệu chắc chắn nhất là nó link tới `msvbvm60.dll` (Microsoft Visual Basic Virtual Machine 6.0). Mọi chương trình VB6, dù biên dịch kiểu gì, đều cần runtime này. Thấy `msvbvm60.dll` trong imports là bạn biết ngay đây là VB6, không phải VB.NET, không phải C++.

Một dấu hiệu nữa: entry point của VB6 luôn gọi `ThunRTMain` (hàm khởi động runtime VB). Và trong file có một cấu trúc gọi là VB header (bắt đầu bằng chuỗi "VB5!") mô tả form, object, và project. Cấu trúc này là mỏ vàng, các tool chuyên dụng đọc nó để dựng lại giao diện và danh sách sự kiện.

## P-Code và Native, chỗ quyết định mọi thứ

Khi biên dịch VB6, lập trình viên chọn một trong hai chế độ (trong Project Properties, tab Compile). Đây là cái bẫy chính.

**P-Code (Pseudo-Code).** Chương trình được biên dịch ra một dạng bytecode riêng của VB, và `msvbvm60.dll` đóng vai một máy ảo thông dịch bytecode đó lúc chạy, khá giống cách CPython chạy .pyc hay JVM chạy .class. Khi bạn mở một exe P-Code trong IDA, bạn sẽ thấy rất ít code x86 thật sự, chủ yếu là lời gọi vào runtime, vì logic thật nằm trong bytecode P-Code. IDA không hiểu P-Code, nên nhìn gần như vô dụng. Nhưng tin tốt: P-Code là bytecode cấp cao, giữ khá nhiều thông tin, nên decompiler chuyên dụng khôi phục lại được tương đối sạch, gần với source gốc.

**Native code.** Chương trình được biên dịch thẳng ra x86 như C/C++. Bạn mở IDA ra là thấy assembly thật, đọc được bằng kiến thức Phần 1. Nhưng đừng mừng vội: code native của VB6 vẫn gọi runtime liên tục cho mọi thứ (quản lý chuỗi BSTR, biến Variant, thao tác form), nên nó ngập trong lời gọi `__vba*` tới `msvbvm60.dll`. Đọc được nhưng rườm rà, và nghịch lý là native lại khó khôi phục về source gốc hơn P-Code, vì compiler đã xé logic ra thành assembly và vứt mất cấu trúc cấp cao.

Nghe ngược đời nhưng đúng: với VB6, **P-Code thường dễ khôi phục về gần source hơn native**, vì bytecode giữ nhiều thông tin hơn mã máy đã tối ưu. Đây là điểm khác biệt quan trọng so với trực giác thông thường (ở các ngôn ngữ khác, native luôn là dạng khó nhất).

Phân biệt hai chế độ: nhìn trong DIE hoặc tool chuyên dụng. Nếu phần code chủ yếu là call vào msvbvm60 với rất ít logic x86 thật, đó là P-Code. Nếu có nhiều block assembly thật xen lẫn call runtime, đó là native. VB Decompiler cũng tự báo loại ngay khi mở.

## VB Decompiler, công cụ gần như bắt buộc

Với VB6, công cụ trung tâm là **VB Decompiler** (có bản free giới hạn và bản pro). Nó làm được những việc mà IDA một mình không làm:

- Đọc VB header để **dựng lại danh sách form, control, và event handler** (ví dụ `Command1_Click`, `Form_Load`). Đây là cách nhanh nhất để biết "khi bấm nút OK thì hàm nào chạy".
- Với **P-Code**, nó decompile bytecode về dạng gần giống source VB, đọc được logic trực tiếp.
- Với **native**, nó disassemble và chú thích các lời gọi runtime, dễ theo dõi hơn IDA thô.
- Liệt kê **chuỗi** và tham chiếu, giúp đi từ một thông báo ("Sai mật khẩu") ngược về hàm kiểm tra, đúng kỹ thuật đi-từ-chuỗi quen thuộc.

Quy trình điển hình: mở exe trong VB Decompiler, xem nó báo P-Code hay native, mở cây form, tìm event handler của nút hoặc ô liên quan tới logic bạn quan tâm (ví dụ nút đăng ký), đọc code decompiled ở đó. Nếu là native và cần đi sâu hơn, chuyển sang IDA/x64dbg nhưng mang theo thông tin địa chỉ hàm mà VB Decompiler đã chỉ ra.

## Chuỗi trong VB6: BSTR, không phải chuỗi C

Một chi tiết hay làm người mới bối rối: VB6 dùng BSTR cho chuỗi, là chuỗi Unicode (UTF-16) có một dword length đứng ngay trước con trỏ dữ liệu, và vẫn kết thúc bằng hai byte null. Nên khi soi chuỗi trong hex editor hoặc IDA, bạn thấy chúng ở dạng Unicode (mỗi ký tự ASCII xen một byte 00), không phải chuỗi ASCII đơn giản như C. So sánh chuỗi trong VB6 thường đi qua hàm runtime `__vbaStrCmp` chứ không phải `strcmp`, nên đặt breakpoint vào đó khi debug native là bắt được đúng chỗ so sánh.

## Lab tự làm

Xem [labs/10.2/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/10.2). Nhiệm vụ: nhận diện một exe VB6 qua import `msvbvm60.dll`, xác định nó là P-Code hay native, rồi dùng VB Decompiler mở form và tìm event handler chứa logic kiểm tra.

## Checklist ghi nhớ
- Import `msvbvm60.dll` là dấu hiệu chắc chắn của VB6 (khác hẳn VB.NET chạy trên CLR).
- VB6 có hai chế độ: P-Code (bytecode chạy trên runtime, ít x86 thật) và Native (x86 thật nhưng ngập lời gọi `__vba*`).
- Ngược trực giác: P-Code thường dễ khôi phục về gần source hơn native.
- VB Decompiler là công cụ trung tâm: dựng form, event handler, decompile P-Code, chú thích native.
- Chuỗi VB6 là BSTR (Unicode có length prefix), so sánh qua `__vbaStrCmp`.
