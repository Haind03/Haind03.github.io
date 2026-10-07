---
title: "Bài 5.2: ILSpy và dnSpy, khi decompile trả lại gần như source gốc"
date: 2026-10-06 08:38:00 +0700
categories: ["Technique Reverse", "Phần 5 · C# / .NET (dnSpy, ILSpy)"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
Sau khi khổ sở với assembly native suốt hai phần, mở một file .NET bằng dnSpy là một cú sốc dễ chịu. Bạn bấm vào một method, và thay vì biển `mov`/`call`, cửa sổ hiện ra C# gần y như bản tác giả viết: tên class, tên method, tên biến cục bộ, cả vòng lặp `foreach` còn nguyên. Lý do nằm ở bài [5.1](/posts/tr-5-1-net-ben-trong-clr-il-metadata/): .NET biên dịch ra IL kèm metadata đầy đủ, nên decompiler dựng lại được rất nhiều. Bài này là cách dùng hai công cụ chủ lực để khai thác điều đó.

Cả hai đều có sẵn trong repo: `dnSpy-net-win64/dnSpy.exe` và `ILSpy_binaries_9.0.0.7660-preview2-x64/ILSpy.exe`.

## ILSpy hay dnSpy, chọn cái nào

Ngắn gọn: dùng cả hai, mỗi cái một việc.

- **ILSpy** chuyên để *đọc*. Nhẹ, nhanh, mở đa nền (có bản Avalonia chạy Linux/macOS), và có bản dòng lệnh `ilspycmd` để xuất cả project C# ra đĩa rồi grep thoải mái. Khi chỉ cần hiểu code, ILSpy là đủ.
- **dnSpy** (bản còn được bảo trì là **dnSpyEx**) làm được nhiều hơn: ngoài đọc, nó *debug* được assembly không có source, và *sửa* rồi lưu lại. Bài [5.3](https://github.com/Haind03/Technique-Reverse/blob/main/phan-05-csharp-dotnet/5.3-debug-net-dnspy.md) và [5.4](https://github.com/Haind03/Technique-Reverse/blob/main/phan-05-csharp-dotnet/5.4-sua-il-csharp-patch.md) sẽ khai thác hai khả năng đó. Ở bài này ta dùng dnSpy chủ yếu để đọc và điều tra.

Giao diện hai công cụ gần giống nhau nên học một cái là dùng được cái kia.

## Mở một assembly và nhìn quanh

Kéo thả một file `.exe` hoặc `.dll` .NET vào cửa sổ, hoặc File > Open. Bên trái hiện cây (tree) phân cấp:

```
MyApp.exe
  references        (các assembly phụ thuộc)
  MyApp             (namespace gốc)
    Program         (class)
      Main(string[]) : void       (method)
      CheckLicense(string) : bool
    Resources
```

Cây đi theo đúng cấu trúc .NET: assembly chứa namespace, namespace chứa type (class/struct/enum/interface), type chứa method và field. Bấm vào một method là decompiler dịch nó ra C# ngay ở panel bên phải.

Điểm cần biết: file `.exe` apphost của .NET Core (ví dụ `dnSpy.exe`) nhiều khi chỉ là vỏ launcher, còn code thật nằm trong file `.dll` cùng tên. Nếu mở `.exe` mà thấy rỗng, hãy mở file `.dll` tương ứng. Đây là điều DIE cũng chỉ ra ở bài [2.1](/posts/tr-2-1-triage-die-strings-pebear/).

## Xem C#, rồi lật sang IL

Mặc định decompiler hiện C#. Nhưng đôi khi decompiler dịch sai hoặc giấu chi tiết (nhất là với code bị obfuscate), lúc đó bạn cần nhìn IL thô, thứ không nói dối.

- Trong **ILSpy**: hộp chọn ngôn ngữ trên thanh công cụ, đổi từ `C#` sang `IL`. Có thể chọn `IL with C#` để xem song song.
- Trong **dnSpy**: menu ngữ cảnh hoặc nút chọn ngôn ngữ, chuyển giữa `C#` và `IL`.

IL dễ đọc hơn assembly native nhiều: nó là stack machine với opcode có tên rõ (`ldarg`, `call`, `brtrue`, `ldstr`). Khi C# decompile trông kỳ quặc, lật sang IL thường sáng ra ngay.

## Search: nhảy thẳng tới chỗ cần

Thay vì lần mò cây, dùng search (ILSpy: ô Search hoặc `Ctrl+Shift+K` trong dnSpy). Tìm được theo tên type, method, và quan trọng nhất là theo **chuỗi (string)**. Giống kỹ thuật đi-từ-chuỗi ở bài [0.4](/posts/tr-0-4-quy-trinh-reverse/): thấy thông báo "License invalid" trong chương trình thì search chuỗi đó, nó dẫn thẳng tới method kiểm tra license.

## Analyze: vũ khí mạnh nhất, dùng xref cho .NET

Đây là tính năng làm .NET RE nhanh hơn hẳn native. Chuột phải vào một method, field, hay type rồi chọn **Analyze** (trong dnSpy) hoặc mở panel Analyze (ILSpy). Nó cho bạn:

- **Used By**: những method nào gọi method này. Đây chính là cross-reference ngược, tương đương phím `X` trong IDA.
- **Uses**: method này gọi những gì.
- **Instantiated By**: nơi nào tạo object của class này.
- **Assigned By / Read By** cho field.

Quy trình điển hình: bạn nghi một method `CheckLicense` là trung tâm. Analyze nó, xem Used By để biết nó được gọi từ đâu (thường là từ `Main` hoặc một nút bấm), rồi lần ngược lên để hiểu luồng. Hoặc ngược lại, từ chuỗi thông báo lỗi, Analyze field chứa chuỗi để tìm nơi dùng. Lần theo đồ thị Used By/Uses là cách bạn dựng lại logic chương trình mà không cần đọc hết.

## Xuất cả project để grep

Khi assembly lớn, mở GUI từng method thì chậm. ILSpy cho xuất nguyên project:

- GUI: chuột phải assembly > Save Code, nó ghi ra một thư mục `.csproj` với đầy đủ file `.cs`.
- CLI: `ilspycmd MyApp.dll -p -o outdir` (ilspycmd là dotnet tool cài riêng qua `dotnet tool install -g ilspycmd`).

Có source trên đĩa rồi thì bạn dùng grep, ripgrep, hay mở trong editor yêu thích để tìm kiếm toàn văn, nhanh hơn nhiều so với click trong GUI.

## Lab tự làm

Trong [labs/5.2/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/5.2) có hướng dẫn mở chính các DLL .NET có sẵn trong repo (ví dụ `ICSharpCode.Decompiler.dll` của ILSpy) bằng cả ILSpy và dnSpy, decompile, dùng Search và Analyze để lần theo một method, và thử xuất project ra C# bằng ilspycmd. Lời giải ở `solution.md`.

## Cạm bẫy thường gặp
- Mở nhầm file apphost `.exe` rỗng thay vì `.dll` chứa code. Mở file `.dll` cùng tên.
- Tin tuyệt đối vào C# decompile. Khi thấy lạ, lật sang IL để kiểm.
- Bỏ qua Analyze mà cố đọc tuần tự. Used By/Uses tiết kiệm rất nhiều thời gian.
- Code bị obfuscate (tên kiểu `a.b.c`, chuỗi mã hoá) thì decompile vẫn ra nhưng khó đọc. Đó là chuyện của bài [5.5](https://github.com/Haind03/Technique-Reverse/blob/main/phan-05-csharp-dotnet/5.5-obfuscator-de4dot.md).

## Checklist ghi nhớ
- ILSpy để đọc (nhẹ, đa nền, có ilspycmd xuất project), dnSpy để đọc + debug + sửa.
- Cây: assembly > namespace > type > method. Bấm method là ra C#.
- Lật C# sang IL khi decompile trông đáng ngờ.
- Search theo chuỗi để nhảy thẳng tới logic.
- Analyze (Used By / Uses) là cross-reference của .NET, dùng nó để dựng lại luồng.
