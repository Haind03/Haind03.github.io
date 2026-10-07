---
title: "Bài 15.4: Anti-debug nâng cao, self-debug và TLS callback"
date: 2026-10-06 09:29:00 +0700
categories: ["Technique Reverse", "Phần 15 · Anti-Reverse chuyên sâu và cách vượt qua"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
Ba bài trước nói về những check bạn gặp giữa chừng chương trình: hỏi API, đọc PEB, đo thời gian. Bài này khó chịu hơn ở chỗ khác: nó không để bạn kịp attach, hoặc nó chiếm luôn chỗ của debugger để bạn không vào được. Đây là nhóm anti-debug mà người mới hay bị "chương trình thoát ngay khi chạy mà chẳng hiểu vì sao".

## Self-debugging: chiếm chỗ debugger

Windows có một luật đơn giản mà cả mảng kỹ thuật này dựa vào: **một tiến trình tại một thời điểm chỉ có thể bị gắn (attach) bởi đúng một debugger.** Nếu chương trình tự dựng sẵn một debugger cho chính nó, thì cái slot đó đã bị chiếm, và x64dbg của bạn attach vào sẽ thất bại.

Có hai biến thể hay gặp:

- **Tạo tiến trình con rồi để con debug lại cha.** Chương trình `CreateProcess` một bản sao của chính nó với cờ, rồi tiến trình con gọi `DebugActiveProcess` lên cha. Từ đó cha đã có debugger (là con nó), bạn không chen vào được nữa.
- **Tự debug qua một thread riêng.** Ít gặp hơn nhưng ý tưởng tương tự.

Dấu hiệu nhận ra khi đọc tĩnh: thấy `CreateProcess` tạo ra chính đường dẫn của mình, kèm `DebugActiveProcess`, `WaitForDebugEvent`, `ContinueDebugEvent`. Khi thấy cặp cha-con kiểu này, bạn đang nhìn một self-debugger.

Cách xử lý: đừng cố attach vào tiến trình đã bị chiếm. Thay vào đó, chặn ngay bước tạo tiến trình con (đặt breakpoint ở `CreateProcessW`, hoặc patch để nó không tạo con), hoặc phân tích logic trong tiến trình con để hiểu nó làm gì rồi vô hiệu hoá cả cơ chế.

## Parent process check

Một kiểu rẻ tiền nhưng hiệu quả: chương trình tự hỏi "ai đẻ ra tôi?". Khi bạn chạy một file bình thường từ Explorer, parent là `explorer.exe`. Khi bạn chạy nó từ trong x64dbg, parent là `x64dbg.exe`. Khi chạy từ cmd thì là `cmd.exe`.

Chương trình lấy parent PID (qua `NtQueryInformationProcess` với `ProcessBasicInformation`, rồi tra tên tiến trình parent qua `CreateToolhelp32Snapshot`), so với một danh sách tên debugger quen thuộc. Khớp thì nó biết đang bị soi.

Nhận ra: thấy chuỗi tên như "x64dbg", "ollydbg", "ida", "windbg" trong binary, kèm code liệt kê tiến trình. Vượt qua: chạy từ một parent "sạch", hoặc patch đoạn so sánh tên, hoặc dùng plugin ẩn tên tiến trình.

## Debug object

Khi một debugger attach, kernel tạo ra một debug object gắn với tiến trình bị debug. Chương trình có thể hỏi về nó qua `NtQueryInformationProcess` với lớp thông tin `ProcessDebugObjectHandle` (giá trị 0x1E): nếu trả về một handle khác null, nghĩa là có debug object, nghĩa là đang bị debug. Đây là một trong những check khó giả nhất vì nó hỏi thẳng kernel về trạng thái thật.

Cách xử lý thực tế là dùng ScyllaHide/TitanHide (bài 15.9), chúng hook đúng chỗ này để trả lời giả. Làm tay thì đặt breakpoint ở `NtQueryInformationProcess`, khi `ProcessInformationClass == 0x1E` thì sửa giá trị trả về thành 0.

## Thread hiding, nói sâu thêm

Bài 15.1 đã nhắc `NtSetInformationThread(ThreadHideFromDebugger)`. Ý nghĩa của nó đáng nói kỹ: khi một thread được đặt cờ `ThreadHideFromDebugger` (giá trị 0x11), kernel sẽ **không gửi sự kiện debug của thread đó cho debugger nữa**. Hệ quả là breakpoint và exception trong thread đó không còn báo về debugger, chương trình chạy "qua mặt" bạn.

Thường chương trình đặt cờ này cho thread chính rồi mới chạy phần nhạy cảm. Dấu hiệu: lời gọi `NtSetInformationThread` với tham số lớp thông tin là 0x11 và handle thread là `(HANDLE)-2` (pseudo-handle của thread hiện tại). Vượt qua: patch lời gọi đó thành no-op, hoặc ScyllaHide chặn giúp.

## TLS callback: chạy trước cả main

Đây là chỗ bẫy người mới nhiều nhất. Như bài 1.12 đã nói, TLS callback là các hàm được PE loader gọi **trước khi entry point chạy**. Trình tự là: loader map image, gọi các TLS callback, rồi mới nhảy vào entry point.

Kẻ viết anti-debug lợi dụng điều này: đặt check ngay trong TLS callback. Khi bạn mở file trong debugger và nhấn run, debugger thường dừng lần đầu ở entry point (hoặc system breakpoint). Nhưng TLS callback đã chạy xong trước đó rồi. Nghĩa là khi bạn kịp nhìn thấy gì đó, chương trình có khi đã phát hiện debugger và quyết định thoát, hoặc đã âm thầm rẽ sang nhánh khác.

Minh hoạ dòng chảy:

```
PE loader map image vào bộ nhớ
   |
   v
gọi TLS callback 1  <-- anti-debug nằm ở đây, chạy TRƯỚC khi bạn kịp nhìn
   |
   v
gọi TLS callback 2 (nếu có)
   |
   v
nhảy vào entry point  <-- debugger thường mới dừng ở đây, đã muộn
   |
   v
main() của tác giả
```

Cách xử lý:
- Trong x64dbg, vào Options > Preferences > Events, bật tùy chọn dừng ở **TLS Callbacks** (và System Breakpoint, Entry Breakpoint). Khi đó debugger sẽ dừng ngay khi TLS callback đầu tiên sắp chạy, bạn kịp đặt breakpoint và soi.
- Tìm TLS callback tĩnh trước: mở trong PE-bear hoặc CFF Explorer, xem TLS Directory, lấy địa chỉ các callback. Sang IDA/Ghidra đặt breakpoint sẵn ở đó.
- Nếu callback chỉ làm một việc là kiểm tra rồi thoát, patch nó thành return sớm.

Quy tắc bỏ túi: nếu một chương trình "vừa chạy đã chết" trong debugger mà entry point còn chưa tới, nghi ngay TLS callback.

## Nhìn một đoạn TLS callback

Một TLS callback có chữ ký cố định `VOID NTAPI cb(PVOID DllHandle, DWORD Reason, PVOID Reserved)`. Trong binary nó thường trông như một hàm nhỏ, được PE loader gọi với `Reason == DLL_PROCESS_ATTACH` (giá trị 1) lúc khởi động:

```asm
tls_callback:
    cmp  edx, 1            ; Reason == DLL_PROCESS_ATTACH ?
    jne  short done        ; chỉ chạy khi process attach
    ; đọc PEB.BeingDebugged qua gs:[0x60]
    mov  rax, gs:[60h]
    movzx eax, byte ptr [rax+2]
    test eax, eax
    je   short done        ; không bị debug thì về
    ; bị debug: thoát hoặc rẽ nhánh giả
    xor  ecx, ecx
    call ExitProcess
done:
    ret
```

Đọc ra ngay: callback này kiểm `BeingDebugged`, thấy có debugger thì `ExitProcess`. Và vì nó chạy trước main, bạn phải bắt nó từ TLS callback breakpoint chứ không thể đợi tới main.

## Lab tự làm

Xem `labs/15.4/`. Bạn build một chương trình đặt anti-debug trong TLS callback, chạy nó trong x64dbg lần đầu (không bật TLS breakpoint) để thấy nó thoát bí ẩn, rồi bật tùy chọn dừng ở TLS callback và bắt đúng đoạn check, cuối cùng patch để vượt qua.

## Cạm bẫy thường gặp
- Entry point chưa tới mà chương trình đã thoát: gần như chắc là TLS callback, đừng đổ lỗi cho debugger hỏng.
- Attach thất bại không phải lúc nào cũng do lỗi: có thể do self-debugging đã chiếm slot.
- Vô hiệu một check (ví dụ BeingDebugged) mà vẫn chết thì nhớ còn các check khác chạy sớm hơn, nhất là trong TLS.

## Checklist ghi nhớ
- Một tiến trình chỉ có một debugger: self-debugging chiếm slot để bạn không attach được. Chặn ở bước tạo tiến trình con.
- Parent process check so tên parent với danh sách debugger. Patch hoặc chạy từ parent sạch.
- `ProcessDebugObjectHandle` (0x1E) hỏi kernel về debug object, rất khó giả, dùng ScyllaHide.
- `ThreadHideFromDebugger` (0x11) làm kernel ngừng gửi sự kiện debug. Patch no-op hoặc ScyllaHide.
- TLS callback chạy TRƯỚC entry point: bật dừng ở TLS Callbacks trong x64dbg, tìm TLS Directory trong PE-bear. Chương trình chết trước main thì nghi ngay TLS.
