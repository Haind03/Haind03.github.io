---
title: "Bài 15.1: Anti-debug qua Windows API, nhóm dễ gặp nhất"
date: 2026-10-06 09:26:00 +0700
categories: ["Technique Reverse", "Phần 15 · Anti-Reverse chuyên sâu và cách vượt qua"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
Khi một chương trình không muốn bạn gắn debugger vào nó, thứ đầu tiên nó thử thường là hỏi thẳng hệ điều hành: "này, tiến trình của tôi có đang bị debug không?". Windows có sẵn vài API trả lời đúng câu hỏi đó, và đó cũng là nhóm anti-debug đầu tiên bạn gặp. May là nhóm này cũng dễ vượt nhất, vì chỗ nào hỏi thì chỗ đó có một giá trị trả về để bạn sửa.

Bài này nhìn anti-debug từ góc người phân tích: hiểu cơ chế để nhận ra nó trong code và đi qua, chứ không phải để viết phần mềm chống phân tích. Hiểu cách phá một lớp bảo vệ cũng chính là hiểu cách nó bảo vệ.

## Nguyên tắc chung: chỗ nào hỏi, chỗ đó sửa được

Mọi check trong bài này đều theo cùng một khuôn: gọi một API, lấy kết quả, so sánh, rồi rẽ nhánh (thoát, chạy sai, hoặc giả vờ bình thường). Khi bạn đã khoanh được lời gọi API đó, có ba cách vượt luôn dùng được:

1. Đặt breakpoint ngay sau khi API trả về, sửa giá trị trong rax (hoặc biến lưu kết quả) thành giá trị "không bị debug".
2. Patch nhánh rẽ: đổi `jne` thành `jmp` hoặc nop nó đi.
3. Dùng plugin như ScyllaHide hoặc TitanHide để tự động trả lời dối mọi API này, khỏi làm tay từng cái.

Giữ nguyên tắc này trong đầu, phần còn lại chỉ là nhận mặt từng API.

## IsDebuggerPresent

Đơn giản nhất. API này đọc một cờ trong PEB (Process Environment Block, xem [Bài 1.11](/posts/tr-1-11-windows-internals-2-peb-teb-handle-token/)) tên BeingDebugged và trả về 1 nếu đang bị debug.

Trong code bạn sẽ thấy đại loại:

```asm
call    IsDebuggerPresent
test    eax, eax
jnz     debugger_found        ; eax != 0 nghĩa là bị debug
```

Vượt: đặt breakpoint tại `IsDebuggerPresent`, chạy tới khi nó return, đặt `eax = 0`. Hoặc nhanh hơn, patch `jnz` thành nop. Vì nó chỉ đọc một byte trong PEB, bạn còn có thể sửa thẳng BeingDebugged trong bộ nhớ về 0 là xong vĩnh viễn cho cả tiến trình.

## CheckRemoteDebuggerPresent

Họ hàng của cái trên nhưng hỏi về một tiến trình (kể cả chính mình) qua handle. Nó ghi kết quả vào một biến con trỏ truyền vào chứ không trả qua rax:

```c
BOOL present = FALSE;
CheckRemoteDebuggerPresent(GetCurrentProcess(), &present);
if (present) exit(1);
```

Vượt: breakpoint sau lời gọi, sửa giá trị tại địa chỉ `present` (tham số thứ hai, trên Win64 là rdx trỏ tới) về 0.

## NtQueryInformationProcess

Đây là con ngựa thồ của anti-debug API. Hàm native trong ntdll này nhận một mã thông tin và trả về đủ thứ về tiến trình. Ba mã hay bị lạm dụng:

- **ProcessDebugPort (0x07)**: nếu đang bị debug, trả về một giá trị khác 0 (cổng debug). Chương trình kiểm tra khác 0 là biết.
- **ProcessDebugFlags (0x1F)**: trả về 0 khi đang bị debug (ngược đời, vì flag "no debug inherit" bị tắt).
- **ProcessDebugObjectHandle (0x1E)**: trả về một handle khác 0 nếu có debug object gắn vào.

Nhận ra trong code: tìm lời gọi `NtQueryInformationProcess` và để ý tham số thứ hai (hằng số 7, 0x1E hay 0x1F) là biết nó đang dò cái gì. IsDebuggerPresent chỉ đọc PEB nên dễ qua mặt, còn NtQueryInformationProcess hỏi thẳng kernel nên "thật" hơn, patch byte PEB không ăn thua với nó.

Vượt: breakpoint sau lời gọi, sửa buffer kết quả (ProcessDebugPort về 0, ProcessDebugObjectHandle về 0, ProcessDebugFlags về 1). Hoặc để ScyllaHide hook sẵn.

## NtSetInformationThread (ThreadHideFromDebugger)

Cái này khác tính chất: không phải để phát hiện mà để trốn. Gọi `NtSetInformationThread` với mã ThreadHideFromDebugger (0x11) khiến thread không gửi sự kiện debug tới debugger nữa, nên debugger "mù" với thread đó, đặt breakpoint có khi không dừng.

Nhận ra: lời gọi `NtSetInformationThread` với tham số 0x11. Vượt: nop lời gọi đó đi, hoặc ScyllaHide chặn.

## OutputDebugString

Mẹo cũ: gọi `OutputDebugString` rồi xem hành vi. Trên Windows đời cũ, khi không có debugger, hàm này set lỗi (GetLastError khác 0); khi có debugger bắt chuỗi thì không. Cách dùng đã lỗi thời nhưng vẫn gặp trong mẫu cũ. Nhận ra qua cặp OutputDebugString + GetLastError liền nhau.

## CloseHandle với handle rác

Khi tiến trình đang bị debug, gọi `CloseHandle` (hoặc NtClose) với một handle không hợp lệ sẽ ném exception EXCEPTION_INVALID_HANDLE; khi không bị debug thì chỉ trả lỗi lặng lẽ. Chương trình bọc lời gọi trong try/except, nếu bắt được exception thì biết có debugger.

Nhận ra: `CloseHandle` với một giá trị handle lạ (như 0x1234) nằm trong khối SEH. Vượt: nuốt exception, hoặc patch nhánh xử lý.

## Lab

Thư mục `labs/15.1/` có `antidebug.c` gom vài check trên vào một chương trình in ra "clean" hay "debugger detected". Nhiệm vụ:

1. Build và chạy bình thường, thấy báo clean.
2. Chạy dưới x64dbg, thấy nó báo detected ở check nào.
3. Vượt từng check bằng cách sửa giá trị trả về, rồi thử lại với ScyllaHide cho nhanh.

Hướng dẫn và lời giải trong `labs/15.1/README.md` và `solution.md`.

## Checklist ghi nhớ
- Mọi anti-debug API theo cùng khuôn: gọi API, so kết quả, rẽ nhánh. Khoanh được API là vượt được.
- IsDebuggerPresent và CheckRemoteDebuggerPresent chỉ đọc PEB, dễ qua (sửa eax hoặc byte BeingDebugged).
- NtQueryInformationProcess hỏi thẳng kernel (ProcessDebugPort 0x07, DebugFlags 0x1F, DebugObjectHandle 0x1E), mạnh hơn, phải sửa buffer kết quả.
- NtSetInformationThread + 0x11 là để trốn debugger, không phải phát hiện.
- Cách lười mà hiệu quả: ScyllaHide trả lời dối hết nhóm API này cho bạn.

## Cạm bẫy thường gặp
- Patch byte BeingDebugged trong PEB không qua được NtQueryInformationProcess, vì nó hỏi kernel chứ không đọc PEB.
- Một chương trình thường gọi nhiều check rải rác, vượt một cái chưa chắc xong. Dùng ScyllaHide để quét sạch rồi mới soi phần còn lại.
