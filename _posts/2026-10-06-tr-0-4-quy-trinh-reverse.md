---
title: "Bài 0.4: Quy trình reverse, hay làm sao để không lạc trong biển assembly"
date: 2026-10-06 08:03:00 +0700
categories: ["Technique Reverse", "Phần 0 · Nhập môn"]
tags: [reverse-engineering, nhap-mon]
render_with_liquid: false
---
Người mới mở file lên là lao thẳng vào đọc code từ đầu tới cuối. Hai tiếng sau họ vẫn ở hàm khởi tạo của thư viện C runtime, chưa chạm tới dòng nào do tác giả viết, và bỏ cuộc. Người có kinh nghiệm làm ngược lại: họ dành mười phút đầu để **không đọc code**, mà để trả lời câu hỏi "thứ này là cái gì, và chỗ đáng xem nằm ở đâu".

Bài này là bộ khung bạn áp vào mọi mục tiêu, từ crackme bé tí tới malware phức tạp. Bốn bước: **Triage, Static, Dynamic, Ghi chép.** Không phải đường thẳng, bạn sẽ nhảy qua lại liên tục, nhưng luôn bắt đầu từ triage.

## Bước 1: Triage, nhìn từ xa trước khi lại gần

Triage là khám sơ bộ. Chưa mở disassembler, chỉ cần biết mình đang cầm cái gì. Vài phút ở đây tiết kiệm hàng giờ về sau.

Những câu hỏi cần trả lời:

- **Đây là loại file gì?** PE (Windows), ELF (Linux), Mach-O (macOS), APK, `.pyc`, `.NET`, hay cái gì khác? Kéo vào **Detect It Easy (DIE)** là xong phần lớn.
- **Viết bằng ngôn ngữ nào?** DIE thường chỉ ra compiler. Đây là lúc bạn quyết định đi hướng nào: thấy ".NET" là mở dnSpy ăn mừng, thấy "Go" là chuẩn bị tinh thần dài hơi.
- **Nó có bị đóng gói (packed) không?** Xem entropy trong DIE. Entropy cao gần 8.0 và bảng import nghèo nàn là dấu hiệu packer. Nếu có, việc đầu tiên là unpack, chứ đọc code packed vô nghĩa.
- **32-bit hay 64-bit?** Chọn đúng x32dbg hay x64dbg, đúng chế độ trong IDA.
- **Có gì lộ ra trong strings không?** Chạy `strings` hoặc FLOSS. URL, đường dẫn file, thông báo lỗi, tên hàm, khoá registry. Nhiều khi câu trả lời nằm ngay ở đây mà chẳng cần disassemble.

Kết thúc triage bạn phải có một câu tóm tắt kiểu: "File PE 64-bit, viết bằng C++ MSVC, không packed, có chuỗi nhắc tới việc kiểm tra serial". Giờ mới biết đường đi tiếp.

## Bước 2: Static analysis, đọc mà không chạy

Mở disassembler/decompiler (Ghidra, IDA) và bắt đầu đọc, nhưng có chiến lược chứ không đọc tuần tự.

Cách khoanh vùng:

- **Đi từ strings ngược lại.** Thấy chuỗi "Sai mật khẩu" thú vị? Nhấn vào nó, xem cross-reference (xref) tới nơi nào dùng chuỗi đó. Nơi đó gần như chắc chắn là hàm kiểm tra mật khẩu. Đây là kỹ thuật số một của người mới, cực kỳ hiệu quả.
- **Đi từ import.** Thấy `CreateFileW`, `RegSetValueEx`, `InternetOpen`? Mỗi API kể một phần câu chuyện: file, registry, mạng. Đặt xref lên các API đáng ngờ.
- **Tìm `main` thật.** Điểm vào (entry point) của binary native không phải `main` của tác giả mà là code khởi tạo của runtime. Bài [3.1](https://github.com/Haind03/Technique-Reverse/tree/main/phan-03-c) dạy cách nhận ra `main` thật giữa đống đó.
- **Đọc decompiler trước, assembly sau.** Với người mới, pseudocode C của Hex-Rays hay Ghidra dễ nuốt hơn nhiều. Chỉ tụt xuống assembly khi decompiler dịch sai hoặc bạn cần độ chính xác từng lệnh.
- **Đổi tên và ghi chú ngay khi hiểu.** Thấy hàm `sub_401000` hoá ra băm chuỗi? Đổi tên thành `hash_string` liền. Mỗi cái tên bạn đặt làm hàm kế tiếp dễ đọc hơn. Đây là khác biệt lớn giữa người làm chậm mà chắc và người ngập trong `sub_xxx`.

Static cho bạn bản đồ. Nhưng bản đồ có chỗ mờ: code mã hoá, giá trị chỉ biết lúc chạy, vòng lặp khó lần bằng mắt. Đó là lúc chuyển sang dynamic.

## Bước 3: Dynamic analysis, cho nó chạy và nhìn tận mắt

Mở debugger (x64dbg, GDB), đặt breakpoint ở chỗ static đã khoanh vùng, rồi chạy tới đó và soi.

Dùng dynamic khi:

- Bạn muốn **thấy giá trị thật**: tham số truyền vào hàm check, chuỗi sau khi giải mã, kết quả so sánh.
- Code **tự giải mã / unpack** lúc chạy, nên trên đĩa nhìn không ra.
- Bạn cần **đi theo một nhánh cụ thể**, ví dụ nhập serial sai để xem nó rẽ đi đâu.
- Logic rối tới mức đọc tĩnh tốn hơn là chạy thử.

Mẹo nền tảng:
- Đặt breakpoint tại API quan trọng (ví dụ `strcmp`, `GetWindowTextW`) để bắt đúng thời điểm.
- Khi tới chỗ so sánh serial, nhìn cả hai toán hạng: một bên là cái bạn nhập, bên kia nhiều khi chính là serial đúng, lộ ra trần trụi trên thanh ghi.
- Với malware, nhớ bạn đang chạy thật: làm trong VM cô lập theo [Bài 0.3](/posts/tr-0-3-dung-lab-an-toan/).

Static và dynamic bổ trợ nhau liên tục. Đọc tĩnh thấy chỗ nghi ngờ, chạy động xác nhận, rồi quay lại đọc tĩnh với hiểu biết mới. Vòng lặp này là nhịp làm việc thật sự của RE.

## Bước 4: Ghi chép, bước ai cũng lười và ai cũng hối hận

Reverse một chương trình cỡ vừa có thể kéo dài nhiều ngày. Hôm nay bạn hiểu rõ một hàm, ba hôm sau quay lại đã quên sạch. Không ghi chép là tự bắt mình làm lại từ đầu.

Ghi tối thiểu những thứ này:

- **Bên trong công cụ:** đổi tên hàm/biến, thêm comment ngay trong IDA/Ghidra. Đây là dạng ghi chép có giá trị nhất vì nó ở ngay cạnh code.
- **Ngoài công cụ, một file riêng:** câu hỏi đang theo đuổi, giả thuyết, địa chỉ quan trọng, cái gì đã thử và thất bại. Markdown là đủ.
- **Với malware:** IOC (hash, IP, domain, mutex, khoá registry), hành vi, và cuối cùng là một rule YARA hoặc capa nếu cần nhận diện lại.

Một mẹo nhỏ mà hiệu quả: viết câu hỏi trước, trả lời sau. "Hàm tại 0x401500 làm gì?" rồi khi hiểu thì ghi đáp án ngay dưới. Nó giữ bạn tập trung thay vì trôi dạt.

## Ráp lại thành một vòng

![Quy trình reverse là một vòng lặp Triage, Static, Dynamic, Ghi chép](/assets/img/technique-reverse/assets/common/quy-trinh-reverse.svg)

```
   TRIAGE  (DIE, strings, file type)
      |  biết mình cầm cái gì
      v
   STATIC  <--------------------+
      |  đọc, khoanh vùng       |
      v                         |  hiểu mới -> đọc lại
   DYNAMIC -----------------------+
      |  xác nhận bằng mắt
      v
   GHI CHÉP  (rename, comment, note, IOC)
      |
      v
   lặp lại tới khi trả lời xong câu hỏi ban đầu
```

Điều quan trọng nhất không phải thuộc lòng sơ đồ mà là **luôn bắt đầu bằng câu hỏi**. "Tôi đang muốn biết điều gì?" Serial đúng là gì? Malware này liên lạc với đâu? Hàm này mã hoá bằng thuật toán nào? Có câu hỏi rõ ràng thì bạn biết khi nào dừng. Không có nó, bạn sẽ đọc assembly tới sáng mà chẳng để làm gì.

## Checklist ghi nhớ
- Luôn triage trước: loại file, ngôn ngữ, packed hay không, bit, strings.
- Static để vẽ bản đồ, đi từ strings và import ngược lại, đổi tên ngay khi hiểu.
- Dynamic để thấy sự thật lúc chạy, bổ trợ chứ không thay thế static.
- Ghi chép ngay trong tool và trong file riêng, nếu không bạn sẽ làm lại từ đầu.
- Bắt đầu mỗi phiên bằng một câu hỏi cụ thể, để biết lúc nào xong.
