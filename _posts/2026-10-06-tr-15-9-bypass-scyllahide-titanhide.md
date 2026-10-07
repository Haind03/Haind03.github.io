---
title: "Bài 15.9: Vượt anti-debug, từ một cú tick chuột tới driver kernel"
date: 2026-10-06 09:34:00 +0700
categories: ["Technique Reverse", "Phần 15 · Anti-Reverse chuyên sâu và cách vượt qua"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
Bốn bài trước (15.1 tới 15.4) cho bạn thấy đủ kiểu anti-debug: hỏi API, đọc PEB, đo thời gian, giăng bẫy trap, nấp trong TLS callback. Nếu phải vá tay từng cái một thì một mẫu malware có hai chục check sẽ ngốn của bạn cả buổi. Bài này là tin vui: phần lớn công việc đó đã có người đóng gói sẵn thành plugin, bạn chỉ bật lên. Và khi plugin chưa đủ, có một nhúm kỹ thuật thủ công gọn gàng để bù vào.

Nguyên tắc chung trước đã: gần như mọi anti-debug đều quy về một câu hỏi "tôi có đang bị theo dõi không", trả lời bằng cách đọc một cờ, một giá trị, hay một hành vi hệ thống. Vượt nó không phải là xoá câu hỏi, mà là trả lời dối: làm cho mọi nguồn thông tin đều nói "không có debugger nào cả". Các tool dưới đây làm đúng việc nói dối đó, khác nhau ở chỗ chúng nói dối ở tầng nào.

## ScyllaHide: tuyến phòng thủ đầu tiên, ở user-mode

ScyllaHide là plugin cho x64dbg (và cả IDA, OllyDbg). Nó hook các hàm trong ntdll ngay trong tiến trình bạn đang debug, rồi chỉnh giá trị trả về và các cờ sao cho mọi check user-mode đều trượt. Một lần bật, nó lo cùng lúc cả loạt thứ bạn đã học:

- `IsDebuggerPresent` và `PEB.BeingDebugged`: ép về 0.
- `PEB.NtGlobalFlag` và heap flags: xoá các cờ lộ debugger (bài 15.2).
- `NtQueryInformationProcess` với ProcessDebugPort/DebugFlags/DebugObjectHandle: trả về giá trị của tiến trình sạch (bài 15.1).
- `NtSetInformationThread` với ThreadHideFromDebugger: nuốt lời gọi để thread của bạn không tự ẩn (bài 15.4).
- `NtQueryObject`, `NtClose` (CloseHandle trap), `OutputDebugString`, timing qua `NtQuerySystemTime`/`GetTickCount`.

Cách dùng trong x64dbg: cài plugin vào thư mục `plugins`, mở menu ScyllaHide, chọn một profile (thường bắt đầu với profile "x64dbg" mặc định đã bật hầu hết tùy chọn), apply, rồi chạy lại. Phần lớn crackme và malware hạng phổ thông sẽ ngừng kêu "debugger detected" ngay tại đây.

Mẹo thực tế: đừng bật mù quáng mọi option. Một vài option hiếm khi gây lệch hành vi chương trình. Nếu bật hết mà app crash, tắt bớt nhóm bạn không chắc, bật lại từng nhóm cho tới khi vừa qua check vừa chạy ổn.

## TitanHide: khi check nhìn xuống kernel

ScyllaHide sống trong user-mode, nên nó chỉ sửa được những gì đi qua ntdll của tiến trình đó. Có những check nhìn sâu hơn, ví dụ gọi thẳng xuống kernel hoặc kiểm tra trạng thái debug ở mức object của hệ điều hành, mà hook user-mode không chạm tới. Lúc đó cần TitanHide.

TitanHide là một driver kernel-mode. Nó chặn các system service (như NtQueryInformationProcess) ở ngay trong kernel, trước khi kết quả kịp quay lên user-mode, nên nó qua được cả những check mà ScyllaHide bó tay. Vì là driver, nó cần quyền admin và cần tắt hoặc xử lý Driver Signature Enforcement (thường chạy trong VM test đã bật test-signing). Thực tế hai tool này bổ trợ nhau: nhiều người bật ScyllaHide trước, gặp check cứng đầu mới lôi TitanHide ra.

## HyperHide: tầng sâu nhất

Khi cả driver cũng bị phát hiện (một số protector kiểm tra sự hiện diện của TitanHide), HyperHide đẩy việc nói dối xuống mức hypervisor, dùng ảo hoá phần cứng để can thiệp mà trong tiến trình và trong kernel đều không thấy dấu vết hook thông thường. Đây là mức bạn hiếm khi cần, chỉ gặp khi đụng protector thương mại cứng. Biết nó tồn tại để lôi ra khi ScyllaHide và TitanHide đều thua.

Ngoài ra còn SharpOD, một plugin anti-anti-debug khác từng rất phổ biến cho OllyDbg và x64dbg, nguyên lý tương tự ScyllaHide. Có nó trong hộp đồ nghề như một phương án hai.

## Bốn tầng, chọn đúng mức

Đừng nhảy ngay xuống hypervisor cho một crackme. Thang leo hợp lý:

| Mức | Công cụ | Dùng khi |
|---|---|---|
| User-mode | ScyllaHide, SharpOD | Mặc định, thử trước tiên, qua được đa số |
| Kernel-mode | TitanHide | Check gọi thẳng kernel hoặc ScyllaHide không qua |
| Hypervisor | HyperHide | Protector phát hiện cả driver |
| Thủ công | x64dbg script, hardware BP | Check lạ không tool nào cover, hoặc muốn hiểu rõ |

## Kỹ thuật thủ công, khi plugin chưa đủ

Plugin cover các check phổ biến. Với một check tự chế lạ đời, bạn tự xử, và ba mẹo này đủ cho hầu hết tình huống.

**Conditional breakpoint tự sửa giá trị.** Thay vì dừng rồi sửa tay mỗi lần, đặt breakpoint có điều kiện kèm lệnh trong x64dbg. Ví dụ muốn `IsDebuggerPresent` luôn trả 0, đặt breakpoint ngay sau lời gọi và cho nó tự gán `rax = 0` rồi chạy tiếp, không cần dừng. Trong ô Command hoặc tab Breakpoints, x64dbg cho phép gắn một biểu thức chạy mỗi lần trúng, kiểu:

```
bp IsDebuggerPresent
SetBreakpointCommand IsDebuggerPresent, "ret; mov rax,0"
```

(cú pháp cụ thể tuỳ bản, ý tưởng là: trúng thì tự sửa giá trị trả về và continue). Cách này biến một check phiền phức thành vô hình mà không phải patch file.

**Hardware breakpoint thay cho software breakpoint.** Software breakpoint của debugger hoạt động bằng cách ghi đè byte đầu lệnh thành `0xCC` (INT 3). Code anti-debug có thể quét code section tìm byte `0xCC` lạ để phát hiện bạn đã đặt breakpoint (bài 15.3). Hardware breakpoint thì khác: nó dùng thanh ghi debug DR0 tới DR3 của CPU, không sửa một byte code nào, nên cách quét `0xCC` không thấy gì. Nhược điểm: chỉ có 4 slot, và có check riêng đọc DR qua GetThreadContext (ScyllaHide giả luôn được phần này). Khi nghi binary quét `0xCC`, chuyển sang hardware breakpoint.

**Patch có mục tiêu.** Khi đã định vị đúng chỗ rẽ nhánh của check (cặp `cmp`/`je` dẫn tới nhánh "detected"), đôi khi gọn nhất là NOP cái nhảy hoặc đảo điều kiện ngay tại đó, như bài 17.1 sẽ nói kỹ. Dùng khi bạn muốn một bản vá cố định thay vì phải bật plugin mỗi lần.

Quy tắc ngón tay cái: bật ScyllaHide trước cho sạch 90%, phần còn lại soi xem check nào vẫn kêu, rồi xử từng cái bằng conditional breakpoint hoặc patch. Hiếm khi phải leo tới kernel cho mục đích học.

## Checklist ghi nhớ
- Vượt anti-debug = làm mọi nguồn thông tin trả lời "không có debugger", không phải xoá check.
- ScyllaHide (user-mode) là tuyến đầu, bật profile mặc định là qua đa số check của bài 15.1 tới 15.4.
- TitanHide (kernel driver) cho check nhìn xuống kernel; HyperHide (hypervisor) cho protector phát hiện cả driver.
- Hardware breakpoint (DR0-DR3) không ghi `0xCC` vào code nên né được check quét breakpoint.
- Conditional breakpoint tự sửa giá trị trả về giúp vô hiệu một check lạ mà không cần patch file.
- Leo tầng từ thấp lên: user-mode trước, kernel sau, hypervisor cuối. Đừng dùng dao mổ trâu giết gà.
