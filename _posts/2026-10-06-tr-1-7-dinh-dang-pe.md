---
title: "Bài 1.7: Định dạng PE, giải phẫu một file .exe Windows"
date: 2026-10-06 08:10:00 +0700
categories: ["Technique Reverse", "Phần 1 · Nền tảng máy tính cho RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Mỗi file `.exe`, `.dll`, `.sys` trên Windows đều theo cùng một khuôn gọi là PE (Portable Executable). Hiểu khuôn này giải thích rất nhiều thứ: vì sao DIE biết file viết bằng gì, vì sao packer giấu được code, entry point nằm ở đâu để đặt breakpoint đầu tiên, và vì sao một hàm từ `kernel32.dll` lại gọi được từ chương trình của bạn. Bài này mổ PE từ đầu file xuống, vừa đủ để bạn tự tay dò trong PE-bear.

## Nhìn tổng thể trước

![Cấu trúc file PE: DOS header, PE signature, File header, Optional header, section table và các section](/assets/img/technique-reverse/assets/phan-01/pe-structure.svg)

Một file PE xếp tuần tự thế này, từ offset 0 đi xuống:

```
+-----------------------------+  offset 0
|  DOS header  (bắt đầu "MZ")  |
|  DOS stub                    |
+-----------------------------+
|  PE signature  ("PE\0\0")    |
|  File header                 |   <- NT headers
|  Optional header             |
+-----------------------------+
|  Section table               |  mô tả từng section
+-----------------------------+
|  .text   (code)              |
|  .rdata  (hằng số, chuỗi,IAT)|
|  .data   (biến toàn cục)     |
|  .rsrc   (tài nguyên)        |
|  ...                         |
+-----------------------------+
```

Hai phần đầu (header) là "giấy khai sinh" mô tả file. Phần sau là nội dung thật. Loader của Windows đọc header để biết nạp cái gì vào đâu.

## DOS header và cái "MZ" huyền thoại

Mở bất kỳ exe nào bằng hex editor, hai byte đầu luôn là `4D 5A`, tức ký tự ASCII "MZ". Đây là magic number nhận diện file PE. "MZ" là tên viết tắt của Mark Zbikowski, kỹ sư Microsoft thời DOS. Thấy `4D 5A` ở offset 0 là biết ngay đang cầm một file thực thi Windows.

DOS header chỉ có một trường thực sự quan trọng với ta: `e_lfanew` ở offset `0x3C`. Nó là một con số chỉ tới chỗ bắt đầu của NT headers. Nói cách khác: đọc 4 byte tại offset `0x3C`, nhảy tới đó, bạn tới phần PE thật.

Ngay sau DOS header là DOS stub, một đoạn chương trình DOS tí hon in ra dòng quen thuộc "This program cannot be run in DOS mode." nếu ai đó lỡ chạy file trên DOS. Với RE thì đoạn này vô hại, bỏ qua.

## NT headers, nơi khai báo thật

Tại vị trí mà `e_lfanew` trỏ tới, bạn gặp:

**PE signature**: 4 byte `50 45 00 00`, tức "PE\0\0". Đây là dấu xác nhận "phần PE bắt đầu từ đây".

**File header** (còn gọi COFF header), vài trường đáng chú ý:
- `Machine`: kiến trúc. `0x14C` là x86 (32-bit), `0x8664` là x64. Đây là cách phân biệt chọn x32dbg hay x64dbg.
- `NumberOfSections`: file có bao nhiêu section.
- `Characteristics`: cờ mô tả, ví dụ đây là EXE hay DLL.

**Optional header** (tên "optional" gây hiểu lầm, nó bắt buộc với file thực thi). Đây mới là phần giàu thông tin:
- `Magic`: `0x10B` cho PE32 (32-bit), `0x20B` cho PE32+ (64-bit).
- `AddressOfEntryPoint`: điểm vào, nơi code bắt đầu chạy. Đây là một RVA (giải thích ngay bên dưới). Breakpoint đầu tiên của bạn khi debug thường đặt ở đây.
- `ImageBase`: địa chỉ ảo mà file muốn được nạp vào. Cổ điển là `0x400000` cho exe 32-bit. Với ASLR bật thì thực tế loader đặt chỗ khác, nhưng ImageBase là mốc để tính toán.
- `SectionAlignment` và `FileAlignment`: căn lề của section trong bộ nhớ và trên đĩa. Hai con số này là lý do RVA và file offset lệch nhau.
- `DataDirectory`: một mảng con trỏ tới các bảng quan trọng (Import, Export, Relocation, TLS, Resource...). Bạn sẽ quay lại đây suốt.

## RVA và file offset, cái bẫy khi tự tay tính

Đây là khái niệm làm người mới lú nhiều nhất, nên đọc chậm.

- **File offset** (còn gọi raw offset): vị trí tính bằng byte kể từ đầu file, khi file nằm trên đĩa. Hex editor dùng cái này.
- **RVA** (Relative Virtual Address): vị trí tính từ ImageBase, khi file đã được nạp vào bộ nhớ. IDA, debugger, và các trường trong PE header dùng cái này.

Hai con số này khác nhau vì căn lề trên đĩa (`FileAlignment`, thường 0x200) khác căn lề trong bộ nhớ (`SectionAlignment`, thường 0x1000). Cùng một byte code có file offset này nhưng RVA khác.

Công thức quy đổi, làm theo từng bước:
1. Tìm section chứa RVA đó: RVA nằm trong khoảng `[VirtualAddress, VirtualAddress + VirtualSize)` của section nào.
2. Tính độ lệch trong section: `delta = RVA - VirtualAddress` (của section đó).
3. File offset = `PointerToRawData` (của section đó) `+ delta`.

Nói gọn: `file_offset = RVA - section.VirtualAddress + section.PointerToRawData`.

Để tính địa chỉ ảo thật (VA): `VA = ImageBase + RVA`. Khi IDA cho bạn một VA như `0x401500` mà bạn muốn tìm byte đó trên đĩa, bạn lần ngược: VA trừ ImageBase ra RVA, rồi áp công thức trên ra file offset.

May mắn là PE-bear và CFF Explorer làm hết phép tính này cho bạn, có nút chuyển RVA sang offset. Nhưng hiểu công thức để không hoảng khi hai con số không khớp.

## Section table

Ngay sau NT headers là một mảng, mỗi phần tử mô tả một section. Mỗi entry cho biết: tên (`.text`, `.data`...), `VirtualAddress` (RVA khi nạp), `VirtualSize` (kích thước trong bộ nhớ), `PointerToRawData` (file offset trên đĩa), `SizeOfRawData` (kích thước trên đĩa), và `Characteristics` (quyền R/W/X).

Các section quen mặt:
- `.text`: code. Cờ thường là readable + executable.
- `.rdata`: dữ liệu chỉ đọc, chứa hằng số, chuỗi, và quan trọng là IAT.
- `.data`: biến toàn cục ghi được.
- `.rsrc`: tài nguyên (icon, dialog, version info, đôi khi payload giấu trong đây).
- `.reloc`: thông tin relocation.

Mẹo triage: nếu bạn thấy một section lạ tên kiểu `.UPX0`, `.vmp0`, hoặc `.text` có `VirtualSize` khổng lồ nhưng `SizeOfRawData` gần như bằng 0, đó là dấu hiệu file bị packed. Code thật sẽ được giải nén vào vùng ảo lúc chạy.

## Import Directory và IAT, cách gọi hàm người khác

Chương trình của bạn gọi `MessageBoxW`, nhưng code của `MessageBoxW` nằm trong `user32.dll`, không nằm trong file bạn. Làm sao nối lại?

PE giải quyết bằng Import Directory. Nó liệt kê: với mỗi DLL cần dùng (`kernel32.dll`, `user32.dll`...), những hàm nào được import từ DLL đó. Khi loader nạp chương trình, nó cũng nạp các DLL này, tìm địa chỉ thật của từng hàm (qua Export Directory của DLL đó, xem dưới), rồi ghi các địa chỉ đó vào một bảng gọi là **IAT** (Import Address Table).

Trong assembly, lời gọi hàm import nhìn như `call [IAT_entry]`, tức gọi gián tiếp qua một ô trong IAT. Khi đọc code, thấy một `call` tới một địa chỉ trong `.rdata` thì gần như chắc đó là gọi API, và PE-bear/IDA sẽ dịch cho bạn tên hàm.

Vì sao IAT quan trọng với RE: bảng import là một bản tóm tắt chức năng miễn phí. Thấy import `CreateFileW`, `WriteFile` là chương trình đụng tới file. Thấy `socket`, `send`, `WSAStartup` là có mạng. Thấy `VirtualAllocEx`, `WriteProcessMemory`, `CreateRemoteThread` là nghi ngờ injection ngay. Và khi unpack một file, dựng lại IAT là bước cuối cùng (Scylla làm việc này, xem Bài 14.3), vì file dump từ bộ nhớ thường mất IAT đúng.

## Export Directory

Ngược với import. Một DLL "xuất" các hàm cho người khác dùng, và Export Directory liệt kê chúng kèm RVA tới code của từng hàm. Hàm có thể xuất theo tên hoặc chỉ theo ordinal (số thứ tự). Khi reverse một DLL, Export Directory cho bạn danh sách điểm vào công khai, là chỗ tốt để bắt đầu đọc.

## Relocation

ImageBase chỉ là mong muốn. Khi địa chỉ đó đã bị chiếm (hoặc ASLR dời đi), loader phải nạp file ở base khác, và mọi địa chỉ tuyệt đối hard-code trong code phải được sửa lại. Bảng `.reloc` liệt kê những chỗ cần sửa. Bạn hiếm khi đọc tay bảng này, nhưng biết nó tồn tại để hiểu vì sao cùng một file chạy ở địa chỉ khác nhau mỗi lần.

## TLS directory và TLS callback, bẫy anti-debug

TLS (Thread Local Storage) là cơ chế cấp cho mỗi thread một bản dữ liệu riêng. Điều đáng nói với RE nằm ở **TLS callback**: đây là các hàm được đăng ký trong TLS directory, và loader gọi chúng **trước cả khi tới entry point** (trước `main`).

Đây là chỗ malware và protector rất thích lợi dụng: đặt code kiểm tra debugger trong TLS callback, nó chạy trước khi bạn kịp đặt breakpoint ở entry point, và phát hiện bạn trước khi bạn kịp quan sát. Nếu bạn đặt breakpoint ở entry point mà chương trình đã "biết" có debugger và thoát, hãy kiểm tra TLS directory. x64dbg có tùy chọn dừng ở TLS callback, bật nó lên. Chi tiết ở Bài 15.4.

## Tất cả hiện ra trong PE-bear

Lý thuyết tới đây đủ rồi. Mở PE-bear (hoặc CFF Explorer), kéo một file exe vào, bạn sẽ thấy từng phần vừa nói hiện thành cây: DOS header, NT headers với Optional header đầy đủ trường, section table với quyền của từng section, Import table với danh sách DLL và hàm. DIE thì không chi tiết bằng nhưng cho bạn bức tranh nhanh: compiler, entropy, có packed hay không. Quy trình quen tay: DIE để triage nhanh, PE-bear để soi kỹ.

## Lab tự làm

Xem [labs/1.7/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/1.7). Nhiệm vụ gồm tự tay tìm entry point, liệt kê section, đọc IAT của một exe trên máy bạn, và một bài tập quy đổi RVA sang file offset bằng công thức ở trên. Lời giải mẫu trong `solution.md`, nhưng làm trước khi mở.

## Checklist ghi nhớ
- File PE bắt đầu bằng "MZ" (`4D 5A`); `e_lfanew` tại offset 0x3C trỏ tới NT headers, mở đầu bằng "PE\0\0".
- Machine phân biệt x86 (0x14C) với x64 (0x8664); AddressOfEntryPoint là nơi code bắt đầu; ImageBase là base mong muốn.
- RVA tính từ ImageBase (dùng trong bộ nhớ/IDA), file offset tính từ đầu file (trên đĩa). Quy đổi: `offset = RVA - VirtualAddress + PointerToRawData` của section chứa nó.
- IAT là bảng địa chỉ các hàm import, và cũng là bản tóm tắt chức năng của chương trình.
- Section lạ hoặc VirtualSize lớn mà SizeOfRawData nhỏ là dấu hiệu packed.
- TLS callback chạy trước entry point, là chỗ hay giấu anti-debug.
