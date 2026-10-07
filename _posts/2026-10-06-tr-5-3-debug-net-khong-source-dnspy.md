---
title: "Bài 5.3: Debug .NET không cần source với dnSpy"
date: 2026-10-06 08:39:00 +0700
categories: ["Technique Reverse", "Phần 5 · C# / .NET (dnSpy, ILSpy)"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
Ở native, muốn debug bạn phải vật lộn với địa chỉ, thanh ghi, stack frame. Ở .NET thì khác hẳn, và đây là lúc bạn thấy vì sao dân RE thích đụng phải một chương trình .NET: dnSpy cho bạn đặt breakpoint ngay trên dòng C# mà nó vừa decompile ra từ một file không hề có source, rồi chạy, dừng, xem biến, sửa biến, y như đang debug chính project của mình trong Visual Studio. Nghe hơi phi lý, nhưng đó là sự thật, và bài này chỉ bạn cách tận dụng.

## Vì sao debug managed lại dễ đến vậy

Nhớ lại [Bài 5.1](/posts/tr-5-1-net-ben-trong-clr-il-metadata/): assembly .NET mang theo đầy đủ metadata và IL. dnSpy decompile IL ra C#, nhưng quan trọng hơn, nó biết **từng dòng C# đó ứng với lệnh IL nào**. Khi bạn đặt breakpoint trên một dòng, dnSpy đặt breakpoint thật ở đúng offset IL tương ứng. CLR dừng tại đó, và vì metadata còn nguyên tên biến cục bộ, tham số, field, dnSpy hiển thị lại mọi thứ có tên tử tế.

So với native: ở x64dbg bạn nhìn `[rbp-4]` và phải tự đoán đó là biến gì. Ở dnSpy bạn thấy thẳng `int attempts = 3`. Khoảng cách đúng bằng khoảng cách giữa đọc hex và đọc chữ.

dnSpy đã có sẵn trong repo này tại thư mục cha `dnSpy-net-win64` (chạy `dnSpy.exe`), không cần cài gì thêm.

## Hai cách bắt đầu: Start và Attach

Có hai tình huống:

- **Start**: dnSpy tự khởi chạy chương trình dưới quyền debugger. Mở assembly trong dnSpy, bấm Start (F5), chọn đúng file thực thi. Dùng khi bạn muốn debug từ đầu, bắt được cả code chạy sớm.
- **Attach**: chương trình đã chạy sẵn, bạn gắn debugger vào. Debug menu, Attach to Process, chọn tiến trình .NET. Dùng khi muốn bắt nó ở trạng thái đang chạy, hoặc chương trình được khởi động bởi thứ khác.

Với một crackme đơn giản, cứ Start cho gọn.

## Đặt breakpoint ở đâu

Quy trình giống hệt native nhưng dễ hơn: dùng static trước để khoanh vùng, rồi đặt breakpoint tại đó.

1. Mở assembly, dùng search (Ctrl+Shift+K) hoặc duyệt cây để tìm chuỗi thông báo kiểu "Wrong" hoặc "Correct".
2. Nhấn vào chuỗi, dùng Analyze để xem method nào dùng nó. Đó là hàm kiểm tra.
3. Trong code C# đã decompile của hàm đó, click vào lề trái dòng cần dừng (hoặc đặt con trỏ rồi F9) để toggle breakpoint. Một chấm đỏ hiện ra.
4. Chỗ đáng đặt nhất là ngay dòng so sánh: `if (input == password)` hoặc `if (CheckSerial(...))`.

## Dừng rồi thì xem gì

Khi breakpoint trúng, chương trình đóng băng và dnSpy highlight dòng sắp chạy. Giờ bạn có mấy cửa sổ:

- **Locals**: mọi biến cục bộ và tham số với giá trị hiện tại. Đây là nơi câu trả lời hay nằm. Nếu hàm so sánh `input` với một biến `expected`, nhìn Locals là thấy luôn `expected` chứa serial đúng.
- **Watch**: tự thêm biểu thức muốn theo dõi, ví dụ gõ `input.Length`.
- **Call Stack**: chuỗi hàm đã gọi tới đây, để biết mình đang ở đâu trong luồng.
- **Immediate**: chạy biểu thức C# ngay lúc dừng.

Các phím điều khiển quen thuộc: F10 step over (bước qua, không vào trong hàm con), F11 step into (vào trong), Shift+F11 step out (chạy hết hàm hiện tại rồi dừng), F5 continue.

## Chiêu mạnh nhất: sửa biến lúc chạy

Đây là thứ làm debug .NET thành vũ khí. Khi dừng tại `if (input == password)`, bạn không cần biết password là gì để qua check. Trong cửa sổ Locals, double-click vào giá trị của biến điều kiện và sửa nó.

Ví dụ hàm trả về `bool isValid`. Bạn để nó chạy tới dòng `return isValid`, đặt breakpoint, khi dừng thì sửa `isValid` từ `false` thành `true` ngay trong Locals, rồi F5. Chương trình tưởng bạn nhập đúng. Đây là cách qua một check mà không cần hiểu thuật toán, hữu ích để xác nhận "đúng là chỗ này quyết định" trước khi ngồi đọc kỹ.

Cũng sửa được cả biến chuỗi: nếu thấy `expected = "S3cr3t"` trong Locals, bạn đã có đáp án, khỏi sửa gì.

## Conditional breakpoint, khi vòng lặp chạy nhiều lần

Nếu hàm kiểm tra nằm trong vòng lặp chạy hàng trăm lần, dừng mỗi vòng thì mệt. Right-click breakpoint, chọn Edit Breakpoint (hoặc Settings), đặt điều kiện kiểu `i == 10` hoặc `c == 'X'`. dnSpy chỉ dừng khi điều kiện đúng. Giống conditional breakpoint của x64dbg nhưng viết bằng cú pháp C#, dễ chịu hơn nhiều.

## Nhịp làm việc gọn

Ráp lại thành một quy trình bạn sẽ lặp đi lặp lại:

1. Static trong dnSpy/ILSpy: tìm hàm kiểm tra qua chuỗi và Analyze.
2. Đặt breakpoint tại dòng so sánh.
3. Start, nhập thử một giá trị sai.
4. Khi dừng, đọc Locals để lấy giá trị đúng, hoặc sửa biến điều kiện để qua.
5. Nếu cần, dùng conditional breakpoint để bắt đúng lần lặp.

Phần lớn crackme .NET cấp nhập môn gục trước đúng năm bước này. Với mẫu đã bị obfuscate thì khó hơn, để [Bài 5.5](/posts/tr-5-5-obfuscator-net-de4dot/) lo.

## Lab tự làm

Bài tập trong `labs/5.3/`: debug một crackme .NET nhỏ bằng dnSpy, đặt breakpoint tại chỗ so sánh, đọc biến để lấy đáp án, rồi thử cách sửa biến điều kiện để qua check mà không cần biết password. Có hướng dẫn build (cần dotnet SDK) và writeup từng bước trong `solution.md`.

## Checklist ghi nhớ
- dnSpy map dòng C# decompile về đúng IL, nên đặt breakpoint thẳng trên code không có source được.
- Start để chạy từ đầu, Attach để gắn vào tiến trình đang chạy.
- Locals là nơi giá trị đúng hay lộ ra, nhìn trước khi ngồi đọc thuật toán.
- Sửa biến điều kiện lúc chạy (ví dụ `isValid = true`) để qua check mà không cần hiểu logic.
- Conditional breakpoint viết bằng cú pháp C#, tiện cho vòng lặp.
