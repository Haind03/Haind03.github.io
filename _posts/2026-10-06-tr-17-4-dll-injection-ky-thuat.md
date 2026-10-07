---
title: "Bài 17.4: Nhận diện các kỹ thuật DLL injection"
date: 2026-10-06 09:43:00 +0700
categories: ["Technique Reverse", "Phần 17 · Patch, Hook, Injection & Instrumentation"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
DLL injection là chuyện một tiến trình ép một tiến trình khác nạp và chạy code của mình. Phần mềm tử tế thỉnh thoảng cũng dùng (overlay game, công cụ accessibility, EDR), nhưng malware dùng nó liên tục: để chạy ẩn trong một tiến trình hợp pháp như `explorer.exe`, né allowlist, và khó bị tắt.

Bài này không dạy bạn viết injector. Mục tiêu ngược lại: khi mổ một mẫu hoặc nhìn một tiến trình nghi vấn, bạn nhận ra ngay "à, đây là CreateRemoteThread injection" hay "đây là manual mapping", biết đặt breakpoint ở đâu, và biết công cụ nào soi ra nó. Đây là kiến thức analyst chuẩn, nhìn từ phía người phòng thủ.

## Khung chung để đọc mọi kỹ thuật injection

Dù biến thể nào, một lần inject gần như luôn gồm ba việc:

1. **Mở tiến trình đích** để lấy quyền thao tác (thường qua `OpenProcess` với quyền `PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_CREATE_THREAD`).
2. **Đặt code hoặc đường dẫn DLL vào bộ nhớ đích** (cấp vùng nhớ rồi ghi vào).
3. **Buộc đích thực thi code đó** (tạo thread mới, hoặc cướp một thread sẵn có, hoặc dùng một cơ chế callback của Windows).

Bắt được chuỗi ba bước này là bắt được injection. Khác biệt giữa các kỹ thuật chủ yếu nằm ở bước 2 và 3.

## 1. LoadLibrary + CreateRemoteThread

Đây là kỹ thuật kinh điển, đơn giản nhất, và vẫn gặp nhiều nhất.

**Cơ chế (khái niệm):** injector ghi *chuỗi đường dẫn tới file DLL* vào bộ nhớ đích, rồi tạo một remote thread chạy thẳng vào hàm `LoadLibraryW` của `kernel32` với tham số là chuỗi đó. Vì `LoadLibraryW` có chữ ký giống một thread start routine (nhận một con trỏ, trả một giá trị), Windows vui vẻ chạy nó, và DLL được nạp đúng theo loader chuẩn.

**Chuỗi API đặc trưng** (đặt breakpoint tại đây khi debug):
```
OpenProcess
VirtualAllocEx        ; cấp vùng nhớ trong tiến trình đích
WriteProcessMemory    ; ghi đường dẫn DLL vào vùng đó
GetProcAddress        ; lấy địa chỉ LoadLibraryW
CreateRemoteThread    ; chạy LoadLibraryW(duong_dan_dll)
```

**Dấu hiệu nhận diện:**
- DLL lạ xuất hiện trong danh sách module của một tiến trình không có lý do nạp nó (một file DLL nằm ở thư mục temp, tên ngẫu nhiên).
- Một thread có start address trỏ thẳng vào `LoadLibraryW`.
- Trên đĩa có file DLL thật, vì kỹ thuật này cần DLL là file (các kỹ thuật sau thì không).

**Phát hiện:** Process Hacker hoặc System Informer, mở tiến trình, xem tab Modules tìm DLL lạ, xem tab Threads tìm thread có start address ở `kernel32!LoadLibraryW`. Procmon bắt được thao tác `Load Image` của DLL lạ.

## 2. SetWindowsHookEx

**Cơ chế:** Windows cho phép đăng ký một hook vào chuỗi message của các cửa sổ (ví dụ `WH_KEYBOARD`, `WH_GETMESSAGE`). Khi hook nằm trong một DLL, Windows **tự nạp DLL đó vào mọi tiến trình có cửa sổ** nhận message tương ứng. Vậy chỉ cần đăng ký hook trỏ tới một hàm trong DLL của mình là DLL được rải khắp nơi, không cần `CreateRemoteThread`.

**Dấu hiệu:** lời gọi `SetWindowsHookEx` với `hMod` trỏ tới một DLL lạ, DLL xuất hiện trong nhiều tiến trình GUI cùng lúc. Keylogger cũ rất chuộng cách này.

**Phát hiện:** cùng một DLL khả nghi có mặt trong nhiều tiến trình; GMER và một số tool anti-rootkit liệt kê hook.

## 3. AppInit_DLLs (và các registry autoload)

**Cơ chế:** khoá registry `HKLM\Software\Microsoft\Windows NT\CurrentVersion\Windows\AppInit_DLLs` liệt kê các DLL mà `user32.dll` tự nạp vào mọi tiến trình có dùng `user32`. Đặt tên DLL vào đó là có persistence kiêm injection toàn hệ thống, không cần đụng tới tiến trình đích.

**Dấu hiệu:** giá trị `AppInit_DLLs` khác rỗng, `LoadAppInit_DLLs` bằng 1. Các biến thể khác cùng ý tưởng: IFEO (Image File Execution Options) với `Debugger`, `Netsh Helper DLL`, `COM hijacking`.

**Phát hiện:** Autoruns (Sysinternals) có hẳn tab AppInit và quét gần như mọi điểm autoload. Đây là nơi đầu tiên blue-team nhìn khi nghi persistence.

## 4. Manual mapping

Đây là bước nâng cấp để **né loader chuẩn**. Thay vì nhờ `LoadLibrary`, injector tự làm công việc của Windows loader bằng tay.

**Cơ chế (khái niệm):** injector tự parse PE của DLL, cấp vùng nhớ trong đích, copy từng section vào đúng vị trí, tự áp relocation, tự resolve import (IAT), rồi gọi tới entry point (DllMain). Vì không qua `LoadLibrary`, DLL **không xuất hiện trong danh sách module** của tiến trình (Windows không biết nó tồn tại theo nghĩa chính thức).

**Dấu hiệu:** đây là lý do manual mapping được chuộng để lẩn trốn, nên dấu hiệu tinh vi hơn:
- Một vùng nhớ `PRIVATE` có quyền thực thi (RX hoặc RWX) nhưng **không thuộc module nào** (unbacked executable memory). Đây là cờ đỏ kinh điển.
- Có đủ bố cục giống một PE (dấu `MZ`/`PE`, section header) trong một vùng private, dù danh sách module không khai báo.

**Phát hiện:** **PE-sieve** và **HollowsHunter** sinh ra chính là để bắt loại này. Chúng quét từng vùng nhớ, so với file trên đĩa, và báo các vùng code không khớp module hoặc không có module hậu thuẫn. Process Hacker cũng hiện được vùng memory có quyền execute lạ.

## 5. Reflective DLL loading

Cùng tinh thần manual mapping nhưng đẩy xa hơn: **chính DLL tự nạp mình**. DLL chứa một hàm bootstrap đặc biệt (reflective loader) có khả năng tự map bản thân vào bộ nhớ từ một buffer, không cần file trên đĩa và không cần `LoadLibrary`.

**Cơ chế:** code shellcode trong buffer tìm lại địa chỉ các API cần thiết (parse PEB để tìm `kernel32`, duyệt export table lấy `LoadLibraryA`/`GetProcAddress`), rồi tự làm việc của loader. Vì DLL chưa bao giờ nằm trên đĩa, phân tích tĩnh file gần như không có gì để bám.

**Dấu hiệu:** giống manual mapping (vùng RX/RWX unbacked, PE trong private memory), cộng thêm việc code tự parse PEB để resolve API (một pattern bạn đã gặp ở các bài anti-analysis). Metasploit và Cobalt Strike dùng rộng rãi, nên dấu vết của chúng được tài liệu hoá kỹ trong tài liệu threat intel.

**Phát hiện:** PE-sieve vẫn là bạn tốt nhất; ngoài ra giám sát hành vi (một tiến trình bỗng cấp vùng RWX rồi chạy code trong đó) là chỉ dấu mạnh cho EDR.

## Quy trình phân tích khi nghi có injection

1. **Triage tiến trình sống:** Process Hacker, xem Modules (DLL lạ) và Memory (vùng RX/RWX private, unbacked).
2. **Chạy PE-sieve/HollowsHunter** trên tiến trình nghi vấn, nó dump ra các module bị implant để bạn mở trong IDA/Ghidra.
3. **Giám sát động:** Procmon lọc theo tiến trình, chú ý `Load Image` của path lạ và các thao tác registry (AppInit, IFEO).
4. **Nếu có mẫu injector:** đặt breakpoint tại chuỗi API ở từng mục trên, đọc tham số (nối lại [Bài 1.13](/posts/tr-1-13-nhan-dien-windows-api/)) để biết nó inject vào đâu, bằng cách nào.
5. **Dump payload** đã bị inject rồi phân tích như một module độc lập.

Shellcode injection, APC injection, thread hijacking và process hollowing (các biến thể của bước 3) được tách riêng sang [Bài 17.5](https://github.com/Haind03/Technique-Reverse/blob/main/phan-17-patch-hook-frida/17.5-shellcode-apc-hollowing.md).

## Checklist ghi nhớ
- Mọi injection gần như luôn gồm: mở tiến trình, đặt code/path vào bộ nhớ đích, buộc nó chạy.
- LoadLibrary + CreateRemoteThread: cần DLL trên đĩa, thread start = LoadLibraryW, dễ thấy nhất.
- SetWindowsHookEx và AppInit_DLLs: để Windows tự rải DLL, soi bằng Autoruns.
- Manual mapping và reflective loading: né loader, DLL không có trong danh sách module. Dấu hiệu là vùng execute private không hậu thuẫn module.
- PE-sieve/HollowsHunter là công cụ phát hiện chủ lực; Process Hacker và Procmon bổ trợ.
