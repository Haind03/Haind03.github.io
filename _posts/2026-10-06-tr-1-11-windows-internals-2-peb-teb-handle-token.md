---
title: "Bài 1.11: Windows internals (2), PEB, TEB, handle và token"
date: 2026-10-06 08:14:00 +0700
categories: ["Technique Reverse", "Phần 1 · Nền tảng máy tính cho RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Có một cấu trúc dữ liệu mà bạn sẽ gặp đi gặp lại trong code Windows, nhất là malware: PEB. Nó nằm ngay trong không gian địa chỉ của tiến trình, không cần gọi API nào để chạm tới, và chính vì thế nó là mỏ vàng cho cả anti-debug lẫn các trò liệt kê module lén lút. Hiểu PEB và vài người anh em của nó (TEB, handle, token) là hiểu được một mảng lớn code mà nếu không biết thì nhìn như ma trận.

## TEB và PEB, hai cuốn sổ tay của tiến trình

Mỗi thread có một cuốn sổ riêng tên TEB (Thread Environment Block), và mỗi process có một cuốn chung tên PEB (Process Environment Block). Hệ điều hành dựng sẵn hai cấu trúc này trong bộ nhớ tiến trình để lưu đủ thứ thông tin về bản thân nó: đang chạy ở đâu, đã nạp những DLL nào, có đang bị debug không, biến môi trường là gì.

Điểm mấu chốt làm reverser phải để ý: **lấy được chúng mà không cần gọi API.** CPU luôn giữ con trỏ tới TEB trong một thanh ghi segment đặc biệt:

```asm
; x64: lấy con trỏ TEB rồi tới PEB
mov rax, gs:[0x30]      ; rax = địa chỉ TEB
mov rax, gs:[0x60]      ; rax = địa chỉ PEB (lối tắt phổ biến)

; x86: dùng fs thay cho gs
mov eax, fs:[0x18]      ; eax = địa chỉ TEB
mov eax, fs:[0x30]      ; eax = địa chỉ PEB
```

Thấy `gs:[0x60]` hay `fs:[0x30]` trong disassembly là bật đèn ngay: code đang với tay vào PEB. Nó không gọi `GetModuleHandle` hay `IsDebuggerPresent`, nó đọc thẳng. Đây là lý do số một khiến người mới bối rối, vì không có tên API nào để tra.

## Những trường trong PEB mà bạn sẽ gặp

PEB có nhiều trường, nhưng ba cái dưới đây chiếm phần lớn các lần bạn đụng tới nó.

### BeingDebugged (offset +0x2)

Một byte, bằng 1 khi tiến trình đang bị debugger gắn vào. Hàm `IsDebuggerPresent` của Windows bên trong chỉ đọc đúng byte này, không hơn. Nên malware thường bỏ qua API luôn mà đọc trực tiếp:

```asm
mov rax, gs:[0x60]        ; PEB
movzx eax, byte ptr [rax+2]  ; đọc BeingDebugged
test eax, eax
jne  found_debugger       ; khác 0: đang bị debug
```

Đọc được đoạn này là bạn nhận ra một chiêu anti-debug kinh điển, chi tiết ở [Bài 15.2](https://github.com/Haind03/Technique-Reverse/tree/main/phan-15-anti-reverse). Cách vượt qua đơn giản nhất lúc debug: sửa byte đó về 0.

### Ldr, danh sách module đã nạp

Trường `Ldr` (offset +0x18 trên x64) trỏ tới một cấu trúc chứa ba danh sách liên kết (linked list) liệt kê mọi module (DLL) đã nạp vào tiến trình, kèm base address và tên. Vì sao quan trọng:

- Malware duyệt danh sách này để **tự tìm địa chỉ của kernel32.dll** rồi lần ra `GetProcAddress`, `LoadLibrary`, mà không cần import chúng. Nhờ vậy bảng import của nó sạch bong, nhìn qua tưởng vô hại. Đây là nền tảng của shellcode và nhiều loader.
- Khi bạn thấy code duyệt một linked list bắt đầu từ PEB rồi so sánh tên chuỗi (thường bằng hash chứ không phải tên thật để giấu), gần như chắc nó đang resolve API bằng tay.

### NtGlobalFlag và heap flags

Khi một tiến trình chạy dưới debugger, Windows đặt vài cờ khác đi: `NtGlobalFlag` trong PEB mang các bit như `FLG_HEAP_ENABLE_TAIL_CHECK`, và heap có cờ debug. Malware so các cờ này với giá trị "bình thường" để đoán có debugger. Cũng là anti-debug, cũng đọc thẳng từ PEB.

## Handle, cách tiến trình nắm giữ tài nguyên

Khi code mở một file, tạo một thread, hay một mutex, Windows trả về một HANDLE: một con số nguyên nhỏ đóng vai "vé" tham chiếu tới đối tượng (object) thật nằm trong kernel. Bạn không chạm trực tiếp vào object, bạn đưa cái vé đó cho các API.

Điều hữu ích cho RE:

- Mỗi tiến trình có một **bảng handle** riêng. Dùng Process Hacker hoặc System Informer mở một tiến trình rồi xem tab Handles là thấy nó đang giữ file nào, khóa registry nào, mutex nào, kết nối gì. Với malware đây là cách nhanh để biết nó động vào đâu mà chưa cần đọc code.
- Các loại object hay gặp: process, thread, file, event, mutex (mutant), section (shared memory), registry key.

## Mutex, dấu vết nhận diện malware

Mutex (mutual exclusion) vốn để đồng bộ hóa giữa các thread, nhưng malware lạm dụng nó theo cách rất có ích cho người phân tích: nó tạo một mutex tên cố định ngay khi chạy, và nếu mutex đó đã tồn tại thì tự thoát. Mục đích là tránh lây nhiễm trùng trên cùng một máy.

Hệ quả: cái tên mutex đó trở thành một IOC (indicator of compromise) tuyệt vời. Thấy `CreateMutexW` với một chuỗi tên lạ, ghi ngay chuỗi đó lại, nó nhận diện được cả họ malware. Có khi chỉ cần tạo sẵn mutex đó trên máy là malware tưởng đã chạy rồi và không chạy nữa, một cách "vaccine" đơn giản.

## Access token, ai được làm gì

Mỗi tiến trình mang một access token mô tả danh tính và quyền: chạy dưới user nào, thuộc nhóm nào, có các privilege gì (ví dụ `SeDebugPrivilege` cho phép mở tiến trình khác để đọc/ghi bộ nhớ, nền tảng của injection). Khi reverse một mẫu cố leo thang đặc quyền, bạn sẽ thấy nó gọi `OpenProcessToken`, `AdjustTokenPrivileges` để bật `SeDebugPrivilege`. Nhận ra cụm này là biết nó đang chuẩn bị đụng vào tiến trình khác.

## Lab tự làm

Chi tiết trong [labs/1.11/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/1.11). Tóm tắt:

1. Mở một tiến trình bất kỳ trong x64dbg, dùng lệnh để nhảy tới PEB, tìm byte `BeingDebugged` và xác nhận nó bằng 1 (vì đang bị debug).
2. Mở Process Hacker hoặc System Informer, xem tab Handles của một tiến trình, tìm các mutex và file nó đang giữ.
3. Đối chiếu offset bạn thấy với bảng offset trong [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/1.11/solution.md).

## Checklist ghi nhớ
- TEB (mỗi thread) và PEB (mỗi process) nằm ngay trong bộ nhớ tiến trình, lấy qua `gs:[0x60]` (x64) hoặc `fs:[0x30]` (x86), không cần API.
- `gs:[0x60]`/`fs:[0x30]` trong code là dấu hiệu đang chạm vào PEB, thường cho anti-debug hoặc resolve API lén.
- BeingDebugged (+2) là ruột của `IsDebuggerPresent`. Ldr chứa danh sách module đã nạp.
- Handle là "vé" tham chiếu object trong kernel. Xem bảng handle bằng Process Hacker để biết tiến trình động vào đâu.
- Tên mutex cố định là IOC tốt để nhận diện malware.
- `SeDebugPrivilege` qua `AdjustTokenPrivileges` là dấu hiệu chuẩn bị injection.
