---
title: "Bài 0.1: Reverse engineering là gì, và tại sao nó không đáng sợ như bạn tưởng"
date: 2026-10-06 08:00:00 +0700
categories: ["Technique Reverse", "Phần 0 · Nhập môn"]
tags: [reverse-engineering, nhap-mon]
render_with_liquid: false
---
Lần đầu mở một file `.exe` bằng IDA, màn hình đập vào mặt bạn là một biển assembly xanh lè, hàng nghìn dòng `mov`, `push`, `call` chẳng đầu chẳng cuối. Cảm giác lúc đó là muốn đóng máy đi ngủ. Tôi cũng vậy. Nhưng reverse engineering (RE) không phải là đọc hết đống đó, mà là biết chỗ nào đáng đọc và bỏ qua 95% còn lại.

Nói gọn: **RE là lấy một sản phẩm đã hoàn thiện rồi lần ngược về cách nó hoạt động, khi bạn không có mã nguồn.** Người ta tháo tung động cơ ra để hiểu nó chạy thế nào thì ở đây ta "tháo" một chương trình.

## Người ta reverse để làm gì

Không phải ai học RE cũng để crack phần mềm. Thực tế nghề này nuôi sống rất nhiều mảng:

- **Phân tích malware.** Một mẫu ransomware rơi vào hệ thống công ty, bạn phải biết nó làm gì, lây lan ra sao, liên lạc với server nào. Không ai đưa bạn source code của kẻ tấn công cả.
- **Tìm lỗ hổng (vulnerability research).** Phần mềm đóng, không có source, nhưng bạn vẫn cần biết nó có bug gì để báo cho nhà sản xuất vá, hoặc để bảo vệ hệ thống của mình.
- **Tương thích & khôi phục.** Một định dạng file cũ không còn ai hỗ trợ, một thiết bị phần cứng mất driver, reverse để viết lại cái mới.
- **Kiểm tra bảo mật sản phẩm của chính mình.** Trước khi hacker làm điều đó với bạn.
- **CTF và học thuật.** Đây là sân chơi lành mạnh nhất để luyện tay nghề, và cũng là nơi series này dùng nhiều nhất.

## Hai con đường: static và dynamic

Mọi kỹ thuật RE, dù hoa mỹ đến đâu, đều rơi vào một trong hai nhóm (hoặc kết hợp cả hai):

**Static analysis**, bạn mổ xẻ file mà không chạy nó. Mở bằng disassembler/decompiler, đọc code, xem chuỗi, dò import. An toàn tuyệt đối vì chương trình không bao giờ thực thi. Điểm yếu: code có thể bị mã hoá, đóng gói (packed), và những gì bạn thấy trên đĩa chưa chắc là thứ chạy thật.

**Dynamic analysis**, bạn cho nó chạy trong môi trường kiểm soát rồi quan sát. Dùng debugger đặt breakpoint, xem giá trị biến lúc runtime, theo dõi nó đụng vào file nào, gọi API nào. Thấy được "sự thật" nhưng nguy hiểm hơn (nhất là với malware) và chương trình có thể phát hiện ra bạn đang theo dõi (anti-debug).

Dân RE giỏi không trung thành với phe nào. Dùng static để khoanh vùng "chỗ thú vị ở đâu", rồi dùng dynamic để nhìn tận mắt chỗ đó chạy ra sao.

## Các tầng trừu tượng: chìa khoá của cả nghề

![Các tầng trừu tượng của một chương trình](/assets/img/technique-reverse/assets/common/tang-truu-tuong.svg)

Đây là thứ quan trọng nhất của bài này, nhớ được nó là bạn hiểu được bố cục cả series.

Một chương trình tồn tại ở nhiều tầng, càng xuống dưới càng xa con người:

```
Source code (C, C#, Java, Python...)   <- lập trình viên viết ở đây
        |  compiler / biên dịch
        v
Bytecode / IL  (chỉ với .NET, Java, Python...)
        |  JIT hoặc interpreter
        v
Machine code / Assembly  (native: C, C++, Go, Rust...)
        |  CPU
        v
Điện
```

**Điểm mấu chốt:** reverse khó hay dễ phụ thuộc hoàn toàn vào việc chương trình dừng ở tầng nào.

- Ngôn ngữ **managed** (C#/.NET, Java, Python) biên dịch ra bytecode còn giữ gần như đầy đủ thông tin: tên hàm, tên biến, cấu trúc class. Decompile một file `.NET` bằng dnSpy nhiều khi ra code gần y hệt bản gốc. Vì thế series này bắt đầu "ăn mừng" sớm ở phần .NET và Java.
- Ngôn ngữ **native** (C, C++, Go, Rust) biên dịch thẳng ra machine code. Tên biến bay sạch, cấu trúc bị compiler xé nhỏ và tối ưu. Đây mới là reverse "thứ thiệt", và là lý do ta phải học assembly.

Đó cũng là lý do giáo trình xếp ngôn ngữ **từ dễ phục hồi đến khó phục hồi**, chứ không phải từ phổ biến đến ít phổ biến.

## Bộ đồ nghề tối thiểu

Chưa cần cài gì vội, bài [0.3](/posts/tr-0-3-dung-lab-an-toan/) sẽ dựng lab tử tế. Nhưng để bạn hình dung, bộ "5 món" mà gần như ai làm RE cũng có:

1. Một thứ để **nhận diện file** (Detect It Easy).
2. Một **disassembler/decompiler** (IDA Free hoặc Ghidra).
3. Một **debugger** (x64dbg trên Windows, GDB trên Linux).
4. Một **hex editor** (HxD, ImHex).
5. Công cụ theo ngôn ngữ cụ thể (dnSpy cho .NET, JADX cho Android, pycdc cho Python, cả ba đều đã có sẵn trong repo này).

Danh sách đầy đủ hơn 200 tool nằm ở [kho công cụ](/posts/tr-tai-nguyen-cong-cu/), nhưng đừng cài hết một lúc. Cài khi bài cần.

## Thực tế về đường học

Sẽ có lúc bạn ngồi cả buổi tối chỉ để hiểu một hàm làm gì, và hoá ra nó chỉ kiểm tra độ dài chuỗi. Bình thường. RE là kỹ năng tích luỹ chậm: 80% thời gian ban đầu là làm quen công cụ và tập đọc assembly, phần "aha" đến sau. Ai nói học RE trong hai tuần là giỏi thì hoặc họ nói dối, hoặc họ chỉ bấm nút "decompile" rồi copy ra.

Mục tiêu của series không phải nhồi lý thuyết mà là mỗi bài bạn tự tay làm được một việc cụ thể. Bài tiếp theo nói về ranh giới pháp lý và đạo đức, phần nhàm nhưng bỏ qua là có ngày trả giá.

## Checklist ghi nhớ
- RE = hiểu cách một chương trình hoạt động khi không có source code.
- Hai nhánh: static (không chạy) và dynamic (chạy và quan sát), thường dùng chung.
- Mức độ khó phụ thuộc chương trình dừng ở tầng nào: managed (dễ) vs native (khó).
- Đừng cố đọc hết assembly, học cách tìm chỗ đáng đọc.
