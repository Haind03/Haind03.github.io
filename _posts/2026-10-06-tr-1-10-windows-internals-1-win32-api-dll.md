---
title: "Bài 1.10: Windows internals (1), Win32 API và DLL, đọc ý đồ qua danh sách hàm"
date: 2026-10-06 08:13:00 +0700
categories: ["Technique Reverse", "Phần 1 · Nền tảng máy tính cho RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Một chương trình Windows gần như không tự làm được gì một mình. Muốn mở file, nó phải hỏi Windows. Muốn cấp bộ nhớ, tạo thread, ghi registry, gửi gói mạng, tất cả đều phải nhờ hệ điều hành. Nó nhờ bằng cách gọi API. Và đây là tin vui lớn nhất cho người làm RE: **danh sách API mà một chương trình gọi kể gần hết câu chuyện nó định làm gì, trước cả khi bạn đọc một dòng assembly.**

Bài này dạy bạn đọc câu chuyện đó.

## Win32 API là gì, và nó nằm ở đâu

Win32 API là bộ hàm Windows công khai cho lập trình viên. Chúng không nằm trong exe của bạn mà sống trong các thư viện liên kết động, file `.dll` (Dynamic Link Library). Khi chạy, exe được nạp kèm các DLL nó cần, rồi gọi hàm trong đó.

Vài DLL cốt lõi phải thuộc tên, vì nhìn tên là đoán được nhóm chức năng:

| DLL | Chứa gì |
|---|---|
| `kernel32.dll` | Lõi: file, process, thread, memory, module (CreateFile, VirtualAlloc, CreateThread, LoadLibrary) |
| `ntdll.dll` | Tầng thấp nhất ở user-mode, cổng xuống kernel (các hàm Nt*/Zw*) |
| `user32.dll` | Giao diện: cửa sổ, message, input (MessageBox, GetWindowText, SetWindowsHookEx) |
| `advapi32.dll` | Registry, service, token, crypto cũ (RegSetValueEx, OpenSCManager, CryptEncrypt) |
| `gdi32.dll` | Vẽ đồ hoạ 2D |
| `ws2_32.dll` / `wininet.dll` / `winhttp.dll` | Mạng: socket và HTTP |

## Chuỗi gọi xuống kernel

Điều nhiều người mới không biết: phần lớn hàm trong `kernel32.dll` không tự làm việc thật. Chúng chỉ là lớp bọc gọi tiếp xuống `ntdll.dll`, và `ntdll` mới là nơi thực hiện cú nhảy vào kernel (qua lệnh `syscall`). Ví dụ:

```
Chương trình -> CreateFileW (kernel32) -> NtCreateFile (ntdll) -> syscall -> kernel
```

Vì sao điều này quan trọng với RE: malware tinh vi hay bỏ qua `kernel32` và gọi thẳng hàm `Nt*` trong `ntdll`, hoặc thậm chí tự gọi `syscall` để né các hook mà công cụ bảo mật đặt ở tầng kernel32. Thấy một chương trình bình thường mà gọi trực tiếp `NtCreateFile`, `NtAllocateVirtualMemory` là một dấu hiệu đáng để ý. Chuyện Native API và syscall để bài [1.12](/posts/tr-1-12-windows-internals-3-seh-tls-syscall/) đào sâu.

## A và W, hai phiên bản của gần như mọi hàm

Bạn sẽ thấy `CreateFileA` và `CreateFileW`, `MessageBoxA` và `MessageBoxW`. Hậu tố cho biết kiểu chuỗi:

- `A` = ANSI, chuỗi 1 byte mỗi ký tự (kiểu cũ).
- `W` = Wide, chuỗi Unicode UTF-16, 2 byte mỗi ký tự (kiểu hiện đại của Windows).

Khi đọc trong IDA, biết hậu tố giúp bạn biết đang tìm chuỗi dạng nào trong bộ nhớ. Một chuỗi W nhìn trong hex editor sẽ có byte `00` xen kẽ (`H.e.l.l.o.`), còn A thì liền mạch. Nhầm chỗ này là tìm chuỗi mãi không ra.

## Hai cách một chương trình gọi API

Đây là phần cốt lõi, vì nó quyết định bạn thấy API ở đâu.

### Import tĩnh, qua IAT

Cách thông thường: lúc biên dịch, trình liên kết ghi sẵn vào file PE một danh sách "tôi cần hàm X của DLL Y". Danh sách này nằm trong Import Directory, và khi nạp, Windows điền địa chỉ thật của từng hàm vào một bảng gọi là IAT (Import Address Table). Mọi lời gọi API trong code đi qua bảng này.

Với bạn, điều tuyệt vời là: danh sách import nằm ngay trong file, đọc được mà không cần chạy. Mở DIE hay PE-bear là thấy toàn bộ hàm chương trình định dùng. Đây là thứ bạn xem đầu tiên sau khi triage.

### Dynamic, qua LoadLibrary và GetProcAddress

Cách giấu mình: chương trình không khai báo import trước, mà lúc chạy mới gọi:

```c
HMODULE h = LoadLibrary("wininet.dll");      // nạp DLL
void* f = GetProcAddress(h, "InternetOpenA"); // lấy địa chỉ hàm theo tên
f(...);                                        // gọi
```

Cặp `LoadLibrary` + `GetProcAddress` là chữ ký kinh điển của việc gọi API động. Malware chuộng cách này vì danh sách import tĩnh trông sạch sẽ vô hại, hàm thật chỉ lộ ra lúc chạy. Có khi tên hàm còn bị mã hoá chuỗi để qua mặt cả người đọc static. Thấy `GetProcAddress` gọi nhiều lần trong một vòng lặp là biết nó đang tự dựng bảng API riêng, một cờ đỏ.

Kết luận thực tế: import tĩnh cho bạn bức tranh trên đĩa, nhưng đừng tin nó là đầy đủ. Luôn để mắt tới `LoadLibrary`/`GetProcAddress`.

## Đọc ý đồ qua nhóm API

Đây là kỹ năng kiếm cơm. Nhóm hàm theo mục đích, và sự có mặt của một nhóm là manh mối:

| Nhóm | Hàm tiêu biểu | Gợi ý chương trình làm gì |
|---|---|---|
| File | CreateFile, ReadFile, WriteFile, DeleteFile, FindFirstFile | Đọc/ghi/quét file. Ransomware duyệt file sẽ đầy nhóm này |
| Registry | RegOpenKeyEx, RegSetValueEx, RegQueryValueEx | Đọc/ghi registry, thường để cấu hình hoặc cài persistence |
| Process/Thread | CreateProcess, OpenProcess, CreateRemoteThread, CreateThread | Tạo/can thiệp tiến trình. OpenProcess + CreateRemoteThread là bộ đôi injection |
| Memory | VirtualAlloc, VirtualProtect, WriteProcessMemory | Cấp/đổi quyền bộ nhớ. VirtualAlloc quyền RWX + ghi code là dấu hiệu unpack/shellcode |
| Network | socket, connect, send, InternetOpen, HttpSendRequest, WinHttpConnect | Liên lạc mạng, có thể là tải payload hoặc gọi C2 |
| Crypto | CryptEncrypt, CryptDecrypt, BCryptEncrypt, CryptAcquireContext | Mã hoá/giải mã, thường gặp trong ransomware hoặc giấu cấu hình |
| Service | OpenSCManager, CreateService, StartService | Cài service, một kiểu persistence quyền cao |

Một ví dụ ghép lại: thấy đồng thời `CreateFile` + `CryptEncrypt` + `FindFirstFile` + `RegSetValueEx`, bạn chưa đọc dòng code nào đã có thể nghi: chương trình quét file, mã hoá chúng, ghi gì đó vào registry. Đó là profile của ransomware. Static analysis sau đó chỉ việc xác nhận.

## Xem import trong thực tế

Hai cách nhanh:
- **DIE**: tab Import liệt kê DLL và hàm. Tiện khi triage.
- **PE-bear / CFF Explorer**: xem Import Directory chi tiết, cả IAT.
- Trong **IDA**, cửa sổ Imports (Shift+F3 hoặc View > Open subviews > Imports) cho danh sách, double-click một hàm rồi nhấn `X` để xem nó được gọi ở đâu trong code. Đây là cách bạn đi từ "chương trình có gọi VirtualAlloc" tới "nó gọi ở hàm nào, với tham số gì".

## Lab tự làm

Bài tập ở [labs/1.10/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/1.10): mở import của vài exe khác nhau rồi tập đoán chức năng chỉ từ danh sách API, và ghép từng hàm vào đúng nhóm mục đích. Writeup mẫu trong `solution.md`.

## Checklist ghi nhớ
- Win32 API sống trong DLL (kernel32, user32, advapi32, ntdll...), exe gọi vào đó để nhờ Windows làm việc.
- kernel32 thường gọi tiếp xuống ntdll rồi syscall vào kernel. Gọi thẳng Nt*/syscall là đáng ngờ.
- Hậu tố A = ANSI, W = Unicode UTF-16 (có byte 00 xen kẽ trong bộ nhớ).
- Import tĩnh hiện trong IAT, đọc được từ file (DIE/PE-bear). Nhưng LoadLibrary + GetProcAddress mới là cách giấu API, luôn để mắt.
- Nhóm API theo mục đích (file, registry, process, memory, network, crypto) để đoán ý đồ trước khi đọc code.
