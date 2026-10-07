---
title: "Bài 5.6: .NET hiện đại, khi món quà decompile bị lấy lại"
date: 2026-10-06 08:42:00 +0700
categories: ["Technique Reverse", "Phần 5 · C# / .NET (dnSpy, ILSpy)"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
Mấy bài trước của Phần 5 cho bạn một cảm giác dễ chịu: mở dnSpy, bấm nút, ra gần như source gốc. Đó là thế giới .NET Framework cũ. Nhưng .NET Core và các bản .NET 5, 6, 7, 8 trở đi thêm vào nhiều kiểu publish, và có một kiểu trong số đó lấy lại toàn bộ món quà ấy, biến bài toán thành reverse native như C++. Bài này giúp bạn nhận ra mình đang cầm kiểu nào, để không phí cả buổi tìm IL trong một file chẳng còn IL.

Ba kiểu đáng quan tâm: single-file, ReadyToRun, và NativeAOT. Mức độ khó tăng dần, và NativeAOT là bước ngoặt.

## Trước tiên: .NET Core khác .NET Framework ở đâu

.NET Framework cũ chạy trên CLR cài sẵn trong Windows, một file `.exe` nhỏ gọi vào runtime hệ thống. .NET Core (và .NET 5+) thì tự mang runtime theo, nên cách đóng gói linh hoạt hơn nhiều. Một app .NET hiện đại có thể publish thành:

- **framework-dependent**: cần runtime cài sẵn trên máy, file nhỏ, vẫn là IL thuần. Dễ như .NET Framework.
- **self-contained**: kèm cả runtime, nặng hơn nhưng vẫn là IL.
- **single-file**: gộp mọi thứ vào một exe duy nhất.
- **ReadyToRun (R2R)**: chèn sẵn native code cạnh IL.
- **NativeAOT**: biên dịch thẳng ra native, vứt bỏ IL.

Ba cái sau là chỗ cần hiểu kỹ.

## Single-file: gộp tất cả vào một exe

![So sánh single-file, ReadyToRun, NativeAOT về khả năng decompile](/assets/img/technique-reverse/assets/phan-05/dotnet-packaging.svg)

Khi publish với `PublishSingleFile=true`, toolchain nhét toàn bộ DLL phụ thuộc (và có khi cả runtime) vào trong một file `.exe` duy nhất cho gọn. Nghe như bị giấu, nhưng thực chất đây chỉ là một cái bundle: các DLL `.NET` vẫn nằm nguyên bên trong, chỉ bị đóng gói lại.

Cách xử lý:
- dnSpy và ILSpy bản mới nhiều khi mở thẳng được single-file và tự liệt kê các assembly bên trong.
- Nếu không, dùng tool trích bundle như **ExtractAllTheThings** hoặc các script `dotnet-bundle extract`, chúng tách file ra lại thành từng DLL. Sau đó mở từng DLL như bình thường.
- Dấu hiệu: file `.exe` khá to (vài chục MB nếu self-contained), và DIE hoặc một lần xem hex thấy dấu vết của nhiều assembly `.NET` ghép lại.

Nói cách khác, single-file chỉ là lớp đóng gói. Món quà decompile vẫn còn nguyên, chỉ cần mở đúng cách.

## ReadyToRun (R2R): native có sẵn, nhưng IL vẫn ở đó

R2R biên dịch trước (ahead-of-time) một phần IL thành native code để app khởi động nhanh hơn, không phải JIT lại từ đầu. Điểm mấu chốt cho người reverse: **R2R giữ cả hai**, có native code đã biên dịch sẵn, nhưng IL và metadata vẫn nằm trong file.

Nghĩa là bạn vẫn decompile ra C# được. dnSpy/ILSpy đọc phần IL như thường. Phần native chỉ là bản sao đã biên dịch của chính IL đó, không chứa thông tin gì mới. Trừ khi bạn nghi ngờ runtime chạy native khác với IL (hiếm), cứ đọc IL là đủ.

Tóm lại R2R trông đáng sợ hơn thực tế. Vẫn là managed, vẫn decompile tốt.

## NativeAOT: đây mới là bước ngoặt

NativeAOT (Native Ahead-Of-Time) biên dịch toàn bộ chương trình thẳng ra machine code native, giống như C++. Không còn CLR nạp IL lúc chạy, không còn JIT, và quan trọng nhất: **không còn IL, không còn metadata dạng managed để decompile.**

Hệ quả rất thật:
- Mở một binary NativeAOT bằng dnSpy hay ILSpy sẽ thất bại, hoặc chỉ thấy một PE native trống rỗng phần managed. Đừng phí thời gian.
- Bạn phải reverse nó **như một binary C++**: IDA, Ghidra, x64dbg, đọc assembly, khôi phục logic bằng tay. Mọi thứ đã học ở Phần 1 tới Phần 4 quay lại dùng ở đây.
- Có chút an ủi: runtime .NET để lại vài dấu vết. Có thể còn một ít metadata cho reflection, tên type trong các bảng runtime, hoặc chuỗi đặc trưng của CoreCLR/NativeAOT runtime. Vài script cộng đồng cố khôi phục tên method từ các bảng này, nhưng đừng kỳ vọng ra C# đẹp đẽ như trước.

NativeAOT còn mới và chưa phổ biến bằng kiểu IL truyền thống, nhưng nó đang được dùng nhiều dần cho CLI tool và app cần khởi động nhanh. Gặp một "app .NET" mà dnSpy chịu thua, NativeAOT là nghi phạm số một.

## Nhận diện nhanh bằng Detect It Easy

Bước triage (nhớ lại [Bài 2.1](/posts/tr-2-1-triage-die-strings-pebear/)) quyết định bạn đi hướng nào:

- DIE báo **".NET"** kèm thông tin assembly, mở dnSpy thấy cây namespace: đây là IL thuần (framework-dependent, self-contained, hoặc R2R). Decompile thoải mái.
- File rất to, DIE vẫn nhận ra dấu .NET nhưng mở hơi lạ: khả năng single-file bundle. Trích ra rồi mở.
- DIE báo một **PE native bình thường** (ví dụ "C++" hoặc chỉ "PE") nhưng bạn biết chắc nguồn gốc là app .NET, hoặc thấy chuỗi liên quan tới CoreCLR/NativeAOT runtime, mutex, type name của .NET nằm trong một file không có managed header: rất có thể NativeAOT. Chuyển sang IDA/Ghidra.

Mẹo kiểm tra thủ công: một PE có managed code sẽ có một CLI header (Data Directory COM Descriptor khác 0). Native thuần thì mục này rỗng. PE-bear hoặc DIE cho bạn thấy điều này.

## Checklist ghi nhớ
- .NET hiện đại có nhiều kiểu publish, khó dần: framework-dependent, self-contained, single-file, R2R, NativeAOT.
- Single-file chỉ là bundle: trích ra (dnSpy, ExtractAllTheThings) rồi mở từng DLL. Vẫn là IL.
- R2R giữ cả native lẫn IL: cứ đọc IL, decompile bình thường.
- NativeAOT vứt bỏ IL/metadata managed: phải reverse như C++ bằng IDA/Ghidra. Đây là bước ngoặt.
- Luôn triage bằng DIE trước: có CLI header (managed) hay không quyết định toàn bộ cách tiếp cận.
