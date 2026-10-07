---
title: "Bài 1.13: Nhận diện Windows API khi reverse, đọc tham số như đọc câu lệnh"
date: 2026-10-06 08:16:00 +0700
categories: ["Technique Reverse", "Phần 1 · Nền tảng máy tính cho RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Ở bài [1.10](/posts/tr-1-10-windows-internals-1-win32-api-dll/) bạn đã thấy danh sách API là tấm bản đồ ý đồ của chương trình. Ở bài [1.4](/posts/tr-1-4-assembly-2-stack-calling-convention/) bạn đã biết tham số được truyền qua đâu. Bài này ghép hai thứ đó lại thành một kỹ năng dùng hàng ngày: nhìn một lời gọi API bất kỳ trong disassembly hay debugger, và đọc ra nó đang mở file nào, ghi khoá registry nào, kết nối tới đâu.

Đây không phải lý thuyết nữa. Đây là thao tác bạn làm vài trăm lần mỗi buổi reverse.

## Bước một: biết prototype của hàm

Muốn đọc tham số thì phải biết hàm nhận bao nhiêu tham số và mỗi cái là gì. Nguồn chuẩn là MSDN (Microsoft Learn). Gõ tên hàm vào, bạn có ngay prototype.

Lấy `CreateFileW` làm ví dụ, prototype của nó:

```c
HANDLE CreateFileW(
  LPCWSTR               lpFileName,            // tham số 1: tên file (chuỗi Unicode)
  DWORD                 dwDesiredAccess,       // tham số 2: quyền truy cập
  DWORD                 dwShareMode,           // tham số 3: chế độ chia sẻ
  LPSECURITY_ATTRIBUTES lpSecurityAttributes,  // tham số 4
  DWORD                 dwCreationDisposition,  // tham số 5
  DWORD                 dwFlagsAndAttributes,   // tham số 6
  HANDLE                hTemplateFile           // tham số 7
);
```

Bảy tham số, trả về một HANDLE. Nhớ cái suffix `W` nghĩa là bản Unicode (còn `A` là ANSI), đã nói ở bài 1.10. Tham số đầu là tên file ta quan tâm nhất.

## Bước hai: tham số nằm ở đâu

Trên Windows x64 (calling convention Win64, xem lại bài 1.4), thứ tự là cố định:

- Tham số 1 tới 4: `rcx`, `rdx`, `r8`, `r9`.
- Tham số 5 trở đi: nằm trên stack, tại `[rsp+0x20]`, `[rsp+0x28]`, v.v. (0x20 byte đầu là shadow space, bỏ qua).
- Giá trị trả về: `rax`.

Ghép vào `CreateFileW`:

| Tham số | Vị trí | Ý nghĩa |
|---|---|---|
| 1 lpFileName | `rcx` | con trỏ tới tên file |
| 2 dwDesiredAccess | `rdx` | quyền (đọc/ghi) |
| 3 dwShareMode | `r8` | chế độ chia sẻ |
| 4 lpSecurityAttributes | `r9` | thường 0 |
| 5 dwCreationDisposition | `[rsp+0x20]` | tạo mới hay mở sẵn |
| 6 dwFlagsAndAttributes | `[rsp+0x28]` | thuộc tính |
| 7 hTemplateFile | `[rsp+0x30]` | thường 0 |

Giờ nhìn đoạn asm thật ngay trước lời gọi:

```asm
lea     r9, [rsp+0x40]        ; param 4 = lpSecurityAttributes (ở đây là con trỏ, hiếm)
mov     dword ptr [rsp+0x28], 0x80   ; param 6 = FILE_ATTRIBUTE_NORMAL
mov     dword ptr [rsp+0x20], 3      ; param 5 = OPEN_EXISTING (3)
xor     r9d, r9d              ; param 4 = 0 (ghi đè, lpSecurityAttributes = NULL)
mov     r8d, 1               ; param 3 = FILE_SHARE_READ
mov     edx, 0x80000000      ; param 2 = GENERIC_READ
lea     rcx, aConfigIni      ; param 1 = con trỏ tới chuỗi "config.ini"
call    CreateFileW
mov     [rbp+hFile], rax     ; lưu HANDLE trả về
```

Đọc ngược từ lời gọi lên: `rcx` trỏ tới chuỗi `aConfigIni`, nên chương trình đang mở file `config.ini`. `edx` = 0x80000000 là `GENERIC_READ`, tức mở để đọc. `[rsp+0x20]` = 3 là `OPEN_EXISTING`, mở file có sẵn chứ không tạo mới. `rax` sau đó được cất đi, đó là handle của file.

Chỉ bằng đọc tham số, bạn đã biết: "chương trình mở file config.ini để đọc". Không cần chạy, không cần đoán. Đây là toàn bộ trò chơi.

Một quy ước nhỏ nhưng tiết kiệm thời gian: những giá trị như `0x80000000`, `3`, `0x80` là các hằng số định nghĩa sẵn trong Windows SDK (GENERIC_READ, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL). Tra chúng trên MSDN hoặc để IDA/Ghidra tự dịch (xem bước tiếp).

## Bước ba: để công cụ làm hộ phần nhàm

May mắn là bạn không phải tra tay mỗi lần. Khi IDA hoặc Ghidra nhận ra một lời gọi là API đã biết, chúng tự chú thích luôn.

- Trong **IDA**, bật type library phù hợp và nó sẽ hiện tên tham số ngay cạnh lệnh chuẩn bị, kiểu `; lpFileName`. Decompiler (F5) còn gộp cả lời gọi thành một dòng C đọc liền: `CreateFileW(L"config.ini", 0x80000000, 1, 0, 3, 0x80, 0)`.
- Trong **Ghidra**, decompiler tự áp prototype từ dữ liệu của nó, và bạn có thể phải "apply" đúng signature nếu nó chưa nhận ra. Khi áp đúng, pseudocode hiện tên tham số rõ ràng.
- Cả hai đều dịch được hằng số sang tên hằng (enum) nếu bạn gán đúng kiểu cho tham số đó. Thấy `3` biến thành `OPEN_EXISTING` là lúc đọc nhanh hơn hẳn.

Nói vậy không có nghĩa bỏ qua bước đọc tay. Khi gặp API ít gặp hoặc công cụ không nhận ra, bạn vẫn phải tự tra MSDN và đếm thanh ghi. Kỹ năng tay là cái cứu bạn lúc công cụ im lặng.

## Bắt API lúc chạy, khi static chưa đủ

Đôi khi tham số chỉ có giá trị thật lúc chạy (tên file ghép từ nhiều chuỗi, khoá registry giải mã động). Lúc đó chuyển sang dynamic.

Trong x64dbg, đặt breakpoint ngay tại hàm API bằng tên:

```
bp CreateFileW
```

Khi chương trình gọi tới, debugger dừng ngay ở đầu hàm, trước khi nó chạy. Lúc này các tham số đang nằm nguyên trong `rcx`, `rdx`, `r8`, `r9` và trên stack. Nhìn cửa sổ register, right-click `rcx` chọn "Follow in Dump" là thấy ngay chuỗi tên file. Đây là cách nhanh nhất để biết "lúc này nó đang mở cái gì".

Công cụ chuyên dụng hơn là **API Monitor**: nó bắt mọi lời gọi API kèm tham số đã được giải nghĩa sẵn, bày ra thành bảng, bạn không phải đọc thanh ghi thủ công. Rất tiện khi muốn xem bức tranh tổng thể một chương trình đụng vào những gì. Đổi lại nó ồn ào, phải biết lọc.

## Khi API bị giấu

Người viết phần mềm (nhất là malware) không phải lúc nào cũng gọi API lộ liễu qua IAT. Hai chiêu hay gặp:

- **Gọi gián tiếp qua GetProcAddress.** Thay vì import `CreateFileW` thẳng, chương trình gọi `LoadLibrary("kernel32.dll")` rồi `GetProcAddress(h, "CreateFileW")` để lấy địa chỉ hàm lúc chạy, sau đó `call` qua con trỏ. Trong IAT tĩnh bạn không thấy `CreateFileW` đâu cả. Dấu hiệu: thấy `GetProcAddress` được gọi nhiều lần, hoặc một con trỏ hàm được gọi `call rax` mà không rõ tên. Cách xử lý là đặt breakpoint tại `GetProcAddress` xem nó đang xin hàm nào, hoặc chạy tới lời gọi gián tiếp rồi xem `rax` trỏ vào đâu.
- **Hashed API / API hashing.** Tinh vi hơn: chương trình không chứa cả chuỗi tên API, mà chỉ chứa một giá trị hash của tên, rồi tự duyệt bảng export của DLL, băm từng tên và so khớp. Mục đích là giấu hẳn tên API khỏi strings và IAT. Khi thấy một vòng lặp duyệt danh sách module trong PEB (xem bài [1.11](/posts/tr-1-11-windows-internals-2-peb-teb-handle-token/)) rồi tính hash, bạn đang gặp chiêu này. Công cụ như **Apiscout** hoặc các script resolve hash (so hash với bảng tên API dựng sẵn) giúp khôi phục tên thật. Chủ đề này quay lại kỹ ở phần malware.

Không cần thành thạo mấy chiêu giấu API ngay bây giờ. Chỉ cần nhận ra "ủa sao chương trình này đụng file mà IAT chẳng có hàm file nào", đó là tín hiệu nó đang giấu, và bạn biết phải chuyển sang dynamic.

## Lab tự làm

Bài tập ở [labs/1.13/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/1.13): tự build một chương trình C nhỏ gọi `CreateFileW` và `RegOpenKeyExW`, rồi dùng x64dbg đặt breakpoint tại hai API đó và đọc đủ tham số theo đúng thứ tự thanh ghi, so với output của API Monitor. Lời giải trong `solution.md`, nhưng tự đọc tham số trước đã.

## Checklist ghi nhớ
- Luôn tra prototype trên MSDN trước, để biết số và kiểu tham số.
- Win64: tham số 1 tới 4 ở `rcx rdx r8 r9`, tham số 5 trở đi ở `[rsp+0x20]` tăng dần, trả về ở `rax`.
- Đọc ngược từ lệnh `call` lên để gom các tham số được chuẩn bị.
- Hằng số (0x80000000, 3...) là macro Windows, tra MSDN hoặc để IDA/Ghidra dịch sang tên hằng.
- Tham số chỉ biết lúc chạy: `bp CreateFileW` trong x64dbg rồi đọc thanh ghi, hoặc dùng API Monitor.
- IAT không có API mong đợi: nghi gọi gián tiếp qua GetProcAddress hoặc API hashing, chuyển sang dynamic.
