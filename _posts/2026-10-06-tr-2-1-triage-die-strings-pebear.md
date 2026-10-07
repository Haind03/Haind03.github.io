---
title: "Bài 2.1: Triage trong năm phút với DIE, strings và PE-bear"
date: 2026-10-06 08:17:00 +0700
categories: ["Technique Reverse", "Phần 2 · Làm quen bộ công cụ"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
Trước khi mở IDA hay Ghidra, có một việc người làm lâu năm luôn làm còn người mới hay bỏ qua: khám sơ bộ. Năm phút ngồi hỏi "mình đang cầm cái gì" tiết kiệm cho bạn hàng giờ đi lạc về sau. Mở disassembler một file đã bị packed là nhìn vào rác, mở sai chế độ 32/64-bit là lệch hết địa chỉ, không đọc strings trước là bỏ lỡ câu trả lời nằm ngay trên bề mặt.

Bài này là quy trình triage thực tế với bốn công cụ, trong đó Detect It Easy đã nằm sẵn trong repo (thư mục `die_win64_portable_3.08_x64`), khỏi cài gì.

## Detect It Easy, con dao mở đầu

DIE trả lời ba câu hỏi quan trọng nhất của triage: file này là gì, viết bằng gì, và có bị đóng gói không.

### Dùng GUI

Chạy `die.exe`, kéo thả file vào. Những chỗ cần nhìn:

- **Dòng kết quả chính** cho biết loại file (PE32, PE32+, ELF, ...) và thứ DIE đoán ra: compiler (MSVC, GCC, MinGW), linker, hoặc protector/packer (UPX, VMProtect, Themida, .NET). Chữ "PE32+" nghĩa là 64-bit, "PE32" là 32-bit.
- **Nút Entropy.** Đây là thứ hay bị ngó lơ nhưng cực giá trị. Entropy đo độ "ngẫu nhiên" của dữ liệu, thang 0 tới 8. Code bình thường tầm 6, dữ liệu đã nén hoặc mã hoá vọt lên gần 8. Một section `.text` có entropy 7.9 gần như chắc chắn là đã packed hoặc mã hoá. DIE vẽ biểu đồ entropy theo từng section, nhìn phát biết chỗ nào bất thường.
- **Nút Import / PE.** Xem nhanh file nhập những DLL và hàm nào. Bảng import nghèo nàn đến mức chỉ còn `LoadLibrary` và `GetProcAddress` là một dấu hiệu kinh điển của packer: nó giấu các API thật, chỉ nạp chúng lúc chạy.

### Dùng dòng lệnh (diec)

`diec.exe` là phiên bản console, tiện khi làm hàng loạt hoặc viết script:

```
diec.exe duong_dan_file.exe
```

Nó in ra loại file và thứ phát hiện được. Thêm tùy chọn để lấy entropy:

```
diec.exe -e duong_dan_file.exe
```

Khi phải triage cả thư mục mẫu, một vòng lặp gọi `diec` là xong, không cần mở GUI từng cái.

## Lệnh file, câu trả lời nhanh trên Linux

Trên Linux (hoặc WSL), `file` nhận diện loại theo magic number trong vài phần nghìn giây:

```
$ file mau.bin
mau.bin: ELF 64-bit LSB pie executable, x86-64, dynamically linked, not stripped
```

Một dòng này đã nói: ELF 64-bit, chạy được, liên kết động, và quan trọng là "not stripped" nghĩa là còn giữ symbol, sẽ dễ đọc hơn nhiều. Nếu thấy "stripped" thì chuẩn bị tinh thần không có tên hàm.

## Strings, nơi câu trả lời hay nằm lộ thiên

Rất nhiều lần, thứ bạn cần tìm nằm ngay trong chuỗi của file: URL, đường dẫn, thông báo lỗi, tên khoá registry, thậm chí cả mật khẩu hoặc flag trong crackme dễ. Trước khi disassemble, cứ liếc strings đã.

```
$ strings -n 6 mau.exe
```

`-n 6` chỉ lấy chuỗi dài từ 6 ký tự, lọc bớt rác. Trên Windows có thể dùng `strings.exe` của Sysinternals, hoặc để DIE/PE-bear liệt kê.

Vấn đề của `strings` cổ điển: nó chỉ thấy chuỗi để trần. Malware và cả phần mềm có bảo vệ thường mã hoá chuỗi, hoặc dựng chuỗi ngay trên stack từng ký tự một (stack string), nên `strings` không ra gì. Đây là lúc dùng **FLOSS** (của Mandiant). FLOSS vừa làm việc của `strings`, vừa cố giải các chuỗi bị mã hoá đơn giản và dựng lại stack string:

```
floss mau.exe
```

Thấy strings trống trơn trong khi file rõ ràng làm nhiều việc là một manh mối: hoặc nó packed, hoặc nó giấu chuỗi. Cả hai đều đáng ghi chú.

## PE-bear, nhìn sâu vào cấu trúc PE

Khi cần xem kỹ hơn bên trong một file PE, PE-bear hiển thị toàn bộ cấu trúc một cách trực quan và cho sửa tại chỗ. Những tab hay dùng khi triage:

- **Sections.** Danh sách section kèm kích thước thô (raw) và kích thước ảo (virtual), entropy từng section, quyền. Một section có virtual size lớn hơn hẳn raw size (ví dụ raw gần 0 mà virtual lớn) là chỗ packer sẽ giải nén code vào lúc chạy, dấu hiệu packed rất rõ.
- **Imports.** Xem đầy đủ DLL và hàm nhập. Đối chiếu với những gì file tự xưng là làm.
- **Resources.** Đôi khi payload thật nằm trong resource dưới dạng dữ liệu entropy cao.

PE-bear còn cho sửa byte và lưu lại, nhưng ở bước triage ta chỉ đọc.

## Ráp lại thành quy trình

Đặt cạnh nhau, năm phút đầu của bạn nên là:

1. Kéo file vào DIE: loại gì, compiler/packer gì, 32 hay 64-bit.
2. Xem entropy trong DIE: có section nào gần 8 không. Có thì nhiều khả năng packed, việc tiếp theo là unpack chứ chưa phải đọc code.
3. Liếc import (DIE hoặc PE-bear): bảng import nghèo nàn là thêm một phiếu cho "packed".
4. Chạy strings hoặc FLOSS: nhặt manh mối lộ thiên, URL, path, thông báo.
5. Ghi một câu tóm tắt: "PE 64-bit, MSVC, không packed, có chuỗi nhắc tới kiểm tra license". Giờ mới mở disassembler.

Cái đích của triage không phải hiểu chương trình, mà là biết nên đi đường nào tiếp theo. Nhận ra sớm một file đã packed giúp bạn không phí một tiếng đọc đống byte vô nghĩa.

## Lab tự làm

Thực hành ngay trên các công cụ có sẵn trong repo. Chi tiết và lời giải ở [labs/2.1/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/2.1):

- Chạy `diec` trên vài file exe có sẵn (`die.exe`, `dnSpy.exe`, `ILSpy.exe`, `jadx-gui-1.5.1.exe`) rồi so sánh compiler/loại file mỗi cái báo ra.
- Đọc entropy của chúng, tìm xem có cái nào bất thường.
- Chạy strings trên một file và nhặt ra ba manh mối thú vị.

## Checklist ghi nhớ
- Luôn triage trước khi mở disassembler. Năm phút đổi lấy hàng giờ.
- DIE trả lời: loại file, compiler/packer, 32/64-bit. "PE32+" là 64-bit.
- Entropy gần 8 ở một section = nhiều khả năng packed hoặc mã hoá. Việc tiếp theo là unpack.
- Bảng import nghèo nàn (chỉ còn LoadLibrary/GetProcAddress) là dấu hiệu packer giấu API.
- strings trước khi disassemble. Trống trơn thì dùng FLOSS để giải chuỗi mã hoá và stack string.
- PE-bear: section có virtual size lớn hơn hẳn raw size là nơi code sẽ được giải nén lúc chạy.
