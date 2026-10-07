---
title: "Bài 1.12: Windows internals cho RE (3), SEH, TLS callback và tầng syscall"
date: 2026-10-06 08:15:00 +0700
categories: ["Technique Reverse", "Phần 1 · Nền tảng máy tính cho RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Ba thứ trong bài này có một điểm chung khó chịu: chúng cho code chạy ở những chỗ bạn không ngờ tới. Ngoại lệ (exception) nhảy luồng sang một handler bạn chưa đọc. TLS callback chạy trước cả `main`. Và syscall thì tụt thẳng xuống kernel, bỏ qua mọi hàm Win32 bạn đang theo dõi. Malware yêu ba thứ này vì đúng lý do đó. Hiểu chúng là bịt được ba lỗ hổng lớn trong tầm quan sát của bạn.

## SEH, khi lỗi không làm chương trình chết

Structured Exception Handling (SEH) là cơ chế của Windows để xử lý ngoại lệ: chia cho 0, truy cập bộ nhớ sai, hay một lỗi do code tự ném ra. Thay vì sập ngay, Windows đi tìm một handler đã đăng ký và chuyển quyền điều khiển cho nó.

Trên x86, chuỗi handler SEH là một danh sách liên kết nằm trên stack, mà con trỏ đầu danh sách lại nằm ở `fs:[0]` (chính là trường đầu tiên của TEB, xem [Bài 1.11](/posts/tr-1-11-windows-internals-2-peb-teb-handle-token/)). Mỗi record có hai trường: con trỏ tới record kế tiếp, và con trỏ tới hàm handler.

```asm
; x86: đăng ký một SEH handler thủ công, pattern kinh điển
push offset my_handler   ; địa chỉ handler
push fs:[0]              ; link tới handler cũ
mov  fs:[0], esp         ; đặt record mới làm đầu chuỗi
```

Trên x64 thì khác hẳn: SEH không còn nằm trên stack mà dựa vào bảng tĩnh trong PE (section `.pdata`, cấu trúc exception directory). An toàn hơn trước kiểu tấn công ghi đè handler, nhưng với bạn nghĩa là phải tra bảng chứ không đọc được chuỗi trên stack.

Còn VEH (Vectored Exception Handling) là bản bổ sung: handler đăng ký qua `AddVectoredExceptionHandler`, chạy **trước** cả SEH, và không gắn với khung hàm nào. Malware thích VEH vì nó bao trùm toàn tiến trình.

### Vì sao reverser phải quan tâm

Malware lạm dụng SEH/VEH làm công cụ che luồng và chống phân tích theo vài kiểu:

- **Điều hướng luồng bằng lỗi cố ý.** Code cố tình gây ra một exception (ví dụ ghi vào địa chỉ null, hoặc chạy `int 3`), rồi logic thật nằm trong handler. Người đọc tĩnh bám theo luồng thẳng sẽ bỏ sót handler, vì nhìn bề ngoài nó chỉ là code chết.
- **Phát hiện debugger.** Khi có debugger, một số exception (như breakpoint `int 3`) bị debugger nuốt mất, không tới được handler. Chương trình đăng ký handler, tự ném exception, rồi kiểm tra xem handler có chạy không. Không chạy nghĩa là có debugger đang xía vào. Chi tiết chiêu này ở [Bài 15.3](https://github.com/Haind03/Technique-Reverse/tree/main/phan-15-anti-reverse).

Mẹo khi phân tích: thấy một `AddVectoredExceptionHandler` hoặc một pattern đăng ký SEH thủ công, hãy đặt breakpoint ngay tại hàm handler đó, vì rất có thể logic bạn tìm nằm trong đó chứ không phải ở luồng chính. Trong x64dbg, bật tùy chọn để debugger chuyển exception cho chương trình xử lý (pass exception to application) thay vì tự nuốt, nếu không bạn sẽ không bao giờ thấy handler chạy.

## TLS callback, code chạy trước main

Thread Local Storage (TLS) sinh ra để mỗi thread có bản sao riêng của một biến. Nhưng kèm theo nó là một tính năng bị lợi dụng nhiều hơn cả mục đích gốc: **TLS callback**, các hàm được gọi tự động mỗi khi tiến trình hoặc thread khởi tạo và kết thúc.

Điểm mấu chốt: TLS callback chạy **trước** entry point của chương trình (`AddressOfEntryPoint`). Nghĩa là trước cả dòng code đầu tiên mà bạn tưởng là nơi bắt đầu, đã có code khác chạy rồi.

Với anti-debug, đây là món quà. Chương trình nhét một đoạn kiểm tra debugger vào TLS callback. Người mới đặt breakpoint ở entry point rồi mới chạy, thì lúc breakpoint đó dính, TLS callback đã chạy xong và đã phát hiện ra bạn từ đời nào. Bạn tới bữa tiệc muộn.

TLS callback nằm trong PE ở TLS Directory, trỏ tới một mảng con trỏ hàm kết thúc bằng null:

```
TLS Directory -> AddressOfCallBacks -> [callback1, callback2, ..., NULL]
```

Cách xử lý:
- Trong PE-bear hoặc CFF Explorer, mở TLS Directory để xem có callback nào không và nó trỏ tới đâu.
- Trong x64dbg, vào Options và bật dừng ở "TLS Callbacks" (và bật luôn "System Breakpoint", "Entry Breakpoint"). Khi đó debugger dừng ngay ở callback đầu tiên, trước entry point, cho bạn đọc nó trước khi nó kịp dò bạn.

Không phải TLS callback nào cũng độc. Nhiều runtime và thư viện dùng nó hợp lệ. Nhưng thấy TLS callback trong một file đáng ngờ thì luôn đọc nó đầu tiên.

## Native API và tầng syscall

Đây là phần làm sáng tỏ cả chuỗi đường đi của một lời gọi hệ thống, và lý giải vì sao đôi khi theo dõi API Win32 vẫn hụt.

Nhớ lại từ [Bài 1.10](/posts/tr-1-10-windows-internals-1-win32-api-dll/): kernel32 không tự làm việc nặng, nó gọi xuống ntdll. Các hàm trong ntdll có tiền tố `Nt` hoặc `Zw` (ví dụ `NtCreateFile`, `NtAllocateVirtualMemory`), và đây mới là tầng Native API sát kernel nhất ở user-mode. Chuỗi đầy đủ:

```
Chương trình
   -> CreateFileW        (kernel32.dll, tầng Win32)
      -> NtCreateFile    (ntdll.dll, Native API)
         -> syscall      (chuyển xuống kernel-mode)
            -> nửa kernel của NtCreateFile
```

Lệnh `syscall` (x64) hoạt động như sau: đặt một con số định danh (system service number) vào thanh ghi `eax`, rồi thực thi `syscall`, CPU chuyển sang kernel-mode và kernel tra số đó trong bảng dịch vụ (SSDT) để biết gọi hàm nào.

Một đoạn stub ntdll điển hình nhìn như thế này:

```asm
NtCreateFile:
    mov  r10, rcx          ; quy ước gọi syscall
    mov  eax, 0x55         ; số syscall (ví dụ, thay đổi theo bản Windows)
    syscall
    ret
```

Hai điều quan trọng cho reverser:

**Số syscall không cố định.** Con số `0x55` ở trên chỉ đúng cho một bản Windows cụ thể. Microsoft đổi các số này giữa các phiên bản, thậm chí giữa các bản cập nhật. Nên đừng học thuộc số, hãy tra theo bản Windows bạn đang phân tích (có các bảng tra công khai theo build).

**Direct syscall, cách malware né hook.** Nhiều EDR và tool giám sát cài hook ở đầu các hàm `Nt*` trong ntdll (inline hook, [Bài 17.3](https://github.com/Haind03/Technique-Reverse/tree/main/phan-17-patch-hook-frida)) để bắt mọi lời gọi. Malware đối phó bằng cách tự nhét lệnh `mov eax, <số>; syscall` thẳng vào code của mình, không gọi qua ntdll nữa, nên cái hook ở ntdll chẳng bao giờ dính. Đây gọi là direct syscall, và các biến thể như "indirect syscall" nhảy tới lệnh `syscall` nằm sẵn trong ntdll để trông tự nhiên hơn.

Nói rõ: ở đây ta học cơ chế để **phát hiện và phân tích** nó, không phải để viết. Khi reverse, dấu hiệu nhận ra là: thấy lệnh `syscall` xuất hiện trong code của chính module đang phân tích (chứ không phải trong ntdll), hoặc thấy một đoạn nạp số vào `eax` rồi `syscall` mà không đi qua import. Lúc đó bạn biết chương trình đang cố tránh tầng theo dõi thông thường, và phải chuyển sang quan sát ở mức thấp hơn (kernel callback, ETW, hoặc hardware breakpoint tại chính lệnh syscall).

Hệ quả thực hành: nếu bạn chỉ hook hoặc đặt breakpoint ở tầng kernel32, một chương trình gọi thẳng ntdll sẽ lọt lưới. Muốn chắc ăn, đặt breakpoint ở tầng `Nt*` trong ntdll. Và nếu ngay cả thế vẫn hụt, khả năng cao nó dùng direct syscall.

## Checklist ghi nhớ
- SEH/VEH cho code nhảy sang handler mà luồng thẳng không thấy. Malware ném exception cố ý để giấu logic hoặc dò debugger. Đặt breakpoint tại handler, và cho debugger pass exception cho chương trình.
- x86 giữ chuỗi SEH trên stack tại `fs:[0]`, x64 dùng bảng tĩnh trong `.pdata`.
- TLS callback chạy TRƯỚC entry point. Luôn kiểm tra TLS Directory và bật dừng ở TLS callback trong x64dbg trước khi chạy.
- Chuỗi gọi: Win32 (kernel32) -> Native API (ntdll, `Nt`/`Zw`) -> `syscall` -> kernel.
- Số syscall thay đổi theo bản Windows, tra chứ đừng thuộc.
- Direct syscall là cách né hook ở ntdll. Dấu hiệu: lệnh `syscall` nằm trong code module, không qua import. Gặp nó thì hạ tầng quan sát xuống thấp hơn.
