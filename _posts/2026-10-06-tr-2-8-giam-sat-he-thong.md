---
title: "Bài 2.8: Giám sát hệ thống, nhìn hành vi mà không cần mở debugger"
date: 2026-10-06 08:24:00 +0700
categories: ["Technique Reverse", "Phần 2 · Làm quen bộ công cụ"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
Có một sự thật dễ chịu cho người mới: rất nhiều khi bạn không cần đọc một dòng assembly nào cũng biết chương trình đang làm gì. Chỉ cần quan sát nó đụng vào đâu trên hệ thống. Nó tạo file ở đâu, ghi khóa registry nào, gọi về server nào, đẻ ra tiến trình con gì. Đây gọi là behavioral analysis, và nó thường là bước dynamic đầu tiên trước khi bạn quyết định có cần ngồi debug chi tiết hay không.

Bài này là bộ công cụ quan sát. Không cái nào khó dùng, cái khó là biết đọc đống sự kiện chúng phun ra.

## Procmon, cuốn nhật ký mọi thứ

Process Monitor (Procmon, của Sysinternals) ghi lại gần như mọi tương tác giữa tiến trình và hệ điều hành theo thời gian thực: thao tác file, registry, tạo/thoát tiến trình, hoạt động mạng cơ bản, và thread. Chạy nó lên vài giây là có hàng chục nghìn dòng, nên kỹ năng thật sự nằm ở bộ lọc (filter).

Thói quen chuẩn:

- Mở Procmon, bật capture, chạy chương trình mục tiêu, rồi tắt capture ngay để khỏi ngập.
- Lọc trước tiên theo tiến trình: `Process Name is <ten>.exe then Include`. Cả biển sự kiện co lại còn đúng thứ bạn cần.
- Lọc tiếp theo loại thao tác qua mấy nút trên thanh công cụ: file system, registry, network, process/thread. Muốn xem nó ghi file gì thì chỉ bật file system.
- Những cột đáng nhìn: Operation (vd `CreateFile`, `RegSetValue`, `WriteFile`), Path (file hay khóa nào), Result (`SUCCESS` hay `NAME NOT FOUND`), và Detail.

Vài pattern đọc được ngay mà không cần disassemble:
- Một loạt `RegSetValue` vào `...\CurrentVersion\Run` nghĩa là chương trình đang cài persistence, tức tự chạy lại sau khi khởi động máy.
- `CreateFile` rồi `WriteFile` vào `%TEMP%` rồi `Process Create` chính file vừa ghi: dấu hiệu kinh điển của dropper, thả payload ra rồi chạy.
- `RegQueryValue` vào các khóa như `...\VMware` hay `...\VirtualBox` là nó đang dò xem có đang chạy trong máy ảo không (anti-VM, nói ở Phần 15).

Procmon không cho bạn biết tại sao, nhưng cho biết cái gì và theo thứ tự nào. Đó đã là nửa câu chuyện.

## Process Hacker / System Informer, kính hiển vi tiến trình

Process Hacker (bản kế nhiệm tên System Informer) là Task Manager phiên bản dành cho người làm RE. Nó cho bạn nhìn vào ruột một tiến trình đang chạy:

- Cây tiến trình: ai đẻ ra ai, màu sắc phân loại (dịch vụ, tiến trình .NET, bị pack...).
- Tab Memory: xem bản đồ bộ nhớ, và quan trọng là nút để quét chuỗi (strings) ngay trong bộ nhớ sống. Nhiều chương trình giấu chuỗi trên đĩa nhưng lúc chạy phải giải mã ra trong RAM, và đây là chỗ bạn tóm được chúng.
- Tab Handles: file, registry key, mutex, event mà tiến trình đang mở. Mutex đặc biệt hữu ích, nhiều malware tạo một mutex tên cố định để tránh chạy trùng, và tên đó trở thành một IOC để nhận diện.
- Tab Threads: xem call stack từng thread, tìm điểm bắt đầu.
- Chuột phải vào vùng nhớ hoặc module là có thể dump ra đĩa để phân tích tĩnh, rất tiện khi code đã được giải nén trong bộ nhớ.

Khi bạn nghi một chương trình tự giải mã chuỗi lúc chạy, mở Process Hacker quét strings bộ nhớ nhanh hơn nhiều so với ngồi dò routine giải mã trong disassembler.

## Process Explorer, phiên bản gọn hơn

Process Explorer cũng của Sysinternals, nhẹ hơn Process Hacker, mạnh ở cây tiến trình, xem DLL mà một tiến trình nạp, và tra nhanh một handle đang bị giữ bởi ai. Nếu chỉ cần nhìn tổng quan và quan hệ cha con thì nó đủ. Process Hacker hợp hơn khi cần đào sâu bộ nhớ và handle.

## API Monitor, nghe lén lời gọi API

Procmon chỉ thấy tương tác ở mức hệ điều hành. API Monitor đi gần code hơn: nó hook và ghi lại các lời gọi Win32 API kèm tham số thật và giá trị trả về. Bạn chọn nhóm API muốn theo dõi (file, registry, memory, crypto, network...), chạy chương trình, rồi đọc được những thứ như:

- `CreateFileW(L"C:\\Users\\...\\secret.dat", GENERIC_READ, ...)`, thấy luôn tên file đầy đủ.
- `CryptEncrypt(...)` hay `VirtualAlloc(..., PAGE_EXECUTE_READWRITE)`, cấp vùng nhớ vừa ghi vừa chạy, một cờ đỏ hay gặp khi code chuẩn bị chạy payload.

Điểm mạnh là thấy tham số ở dạng người đọc được. Điểm yếu là nhiều malware né hook của nó, hoặc gọi thẳng Native API/syscall để đi vòng (nhắc ở bài 1.12). Khi API Monitor im lặng một cách đáng ngờ, bản thân sự im lặng đó cũng là manh mối.

## Autoruns, soi persistence

Autoruns liệt kê gần như mọi điểm mà thứ gì đó có thể tự khởi động trên Windows: khóa Run, scheduled task, service, driver, trình cắm Explorer, và hàng chục chỗ khác bạn không ngờ tới. Sau khi chạy một mẫu, so sánh Autoruns trước và sau là thấy ngay nó đã cắm cái gì để tồn tại qua lần khởi động sau. Có tùy chọn ẩn các mục đã ký bởi Microsoft để lọc bớt nhiễu.

## Wireshark, nhìn lưu lượng mạng

Khi chương trình nói chuyện với bên ngoài, Wireshark bắt từng gói. Bạn thấy nó resolve domain nào (DNS), kết nối IP và cổng nào, và nếu không mã hóa thì cả nội dung. Với malware, đây là cách tìm server điều khiển (C2) và hiểu giao thức liên lạc. Nhớ cấu hình mạng lab cho đúng: thường bạn chạy trong môi trường mạng giả lập (INetSim/FakeNet) để mẫu tưởng mình ra được internet mà gói không đi đâu, xem bài 0.3.

## Trên Linux: strace và ltrace

Thế giới Linux gọn hơn, hai lệnh là đủ cho phần lớn việc:

- `strace ./chuongtrinh` ghi lại mọi system call: `open`, `read`, `write`, `connect`, `execve`. Tương đương Procmon ở mức syscall.
- `ltrace ./chuongtrinh` ghi lại lời gọi tới hàm thư viện (libc...), gần với API Monitor. Thấy luôn `strcmp`, `malloc`, `fopen` kèm tham số.

Ví dụ `strace` một chương trình kiểm tra license đôi khi phô ra thẳng nó `open` file `/etc/mylicense` hay `connect` tới một IP, và bạn hiểu cơ chế mà chưa cần mở disassembler.

## Ghép lại thành bức tranh

Không công cụ nào cho bạn câu trả lời đầy đủ, nhưng cộng lại thì có:

- Procmon trả lời nó đụng vào file và registry nào.
- Process Hacker trả lời trong bộ nhớ nó đang giấu gì, giữ mutex và handle nào.
- API Monitor trả lời nó gọi API gì với tham số ra sao.
- Autoruns trả lời nó cắm vào đâu để sống dai.
- Wireshark trả lời nó nói chuyện với ai.

Chạy mẫu một lần với cả bộ này bật sẵn, bạn có một hồ sơ hành vi trước khi động tới một dòng assembly. Từ hồ sơ đó mới quyết định chỗ nào đáng ngồi debug sâu. Đó đúng là tinh thần triage, static, dynamic ở bài 0.4, chỉ khác là dynamic ở đây làm bằng quan sát chứ chưa phải bằng debugger.

Và nhắc lại cho chắc: mọi thứ trong bài này, khi mục tiêu là malware thật, phải chạy trong VM cô lập theo [Bài 0.3](/posts/tr-0-3-dung-lab-an-toan/). Bật Procmon lên không làm bạn an toàn hơn, chương trình vẫn chạy thật.

## Checklist ghi nhớ
- Behavioral analysis cho bạn biết chương trình làm gì mà nhiều khi không cần đọc assembly.
- Procmon: lọc theo tên tiến trình trước, rồi theo loại thao tác (file/registry/network).
- Process Hacker: quét strings trong bộ nhớ sống, xem handle và mutex, dump vùng đã giải nén.
- API Monitor: thấy lời gọi API kèm tham số dạng người đọc được; im lặng bất thường cũng là manh mối.
- Autoruns để soi persistence, Wireshark để soi mạng.
- Linux: strace cho syscall, ltrace cho hàm thư viện.
- Malware thật: luôn trong VM cô lập.
