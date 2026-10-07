---
title: "Bài 1.6: Từ source đến binary, và vì sao cùng một đoạn code lại ra hai kiểu khác nhau"
date: 2026-10-06 08:09:00 +0700
categories: ["Technique Reverse", "Phần 1 · Nền tảng máy tính cho RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Có một câu hỏi người mới hay thắc mắc: tôi viết một hàm C rõ ràng mạch lạc, sao khi mở trong IDA nó biến thành một mớ assembly chẳng còn hình dạng gì của bản gốc? Câu trả lời nằm ở chặng đường từ source tới binary, và nhất là ở một anh chàng tên là optimizer. Hiểu chặng đường này, bạn sẽ bớt bực khi decompiler cho ra code kỳ cục, và quan trọng hơn, biết trước mình đang đối mặt với loại binary nào.

## Dây chuyền biên dịch

Khi bạn gõ `gcc hello.c -o hello`, trông như một bước, nhưng thật ra có bốn công đoạn nối tiếp. Compiler chỉ là tên gọi chung.

```
hello.c
   |  1. Preprocessor (tiền xử lý)
   v
hello.i   (C đã khai triển macro, #include)
   |  2. Compiler (trình biên dịch thật sự)
   v
hello.s   (assembly)
   |  3. Assembler (trình hợp dịch)
   v
hello.o   (object file, machine code nhưng chưa hoàn chỉnh)
   |  4. Linker (trình liên kết)
   v
hello     (file thực thi)
```

Điểm qua từng khâu, vì mỗi khâu để lại dấu vết bạn gặp khi reverse:

1. **Preprocessor** xử lý mọi dòng bắt đầu bằng `#`: dán nội dung `#include` vào, thay macro `#define`, bỏ comment. Sau bước này, mọi macro đã biến mất. Đó là lý do một hằng số `#define MAX 100` trong code gốc chỉ còn là số `100` trần trụi trong binary, không còn cái tên MAX nào cả.

2. **Compiler** dịch C đã khai triển thành assembly. Đây là khâu thông minh nhất, và là nơi tối ưu hóa xảy ra. Code của bạn bị biến đổi nhiều nhất ở đây.

3. **Assembler** dịch assembly (văn bản) thành machine code (nhị phân) trong một object file. Dịch gần như một đổi một, không sáng tạo gì.

4. **Linker** ráp các object file lại, nối lời gọi hàm giữa các file, và gắn code thư viện. Khâu này quyết định chuyện static hay dynamic linking ngay dưới đây.

## Static vs dynamic linking, thứ bạn thấy ngay khi mở file

Chương trình của bạn gọi `printf`. Nhưng `printf` không do bạn viết, nó nằm trong thư viện C. Có hai cách gắn nó vào:

- **Dynamic linking** (mặc định phổ biến): file thực thi chỉ chứa một lời "nhắc nợ" rằng nó cần `printf` từ thư viện ngoài (libc.so trên Linux, các DLL trên Windows). Lúc chạy, loader mới tìm và nạp thư viện đó. File nhỏ, và quan trọng với bạn: nhìn vào bảng import là thấy ngay nó dùng những hàm nào. `CreateFileW`, `socket`, `RegOpenKey` lộ hết. Đây là nguồn manh mối số một khi triage.

- **Static linking**: toàn bộ code thư viện được nhét thẳng vào file thực thi lúc link. File phình to, và `printf` giờ nằm lẫn trong code của bạn, không còn import nào để nhìn. Reverse khó hơn vì bạn phải tự phân biệt đâu là code mình cần đọc, đâu là hàng nghìn hàm thư viện. Đây là lúc FLIRT signature (Bài 3.4) cứu bạn, nó nhận diện và dán nhãn các hàm thư viện đã biết để bạn bỏ qua.

Go và Rust mặc định thiên về static linking, nên binary của chúng to và đầy code runtime, một phần lý do chúng mang tiếng khó reverse.

## Loader, khâu cuối cùng lúc chạy

Khi bạn chạy file, hệ điều hành gọi loader: nó đọc header (PE hoặc ELF, Bài 1.7 và 1.8), ánh xạ các section vào bộ nhớ đúng quyền (code thì R-X, data thì RW-), nạp các thư viện dynamic cần thiết, điền bảng địa chỉ import (IAT), xử lý relocation nếu ASLR đổi base, rồi mới nhảy vào entry point. Toàn bộ quy trình này là lý do "thứ trên đĩa" và "thứ trong bộ nhớ lúc chạy" không hoàn toàn giống nhau, một điểm ta đã chạm ở Bài 1.2.

## Optimizer, thủ phạm chính làm code khó đọc

Giờ tới phần quan trọng nhất của bài. Cùng một source C, build với mức tối ưu khác nhau cho ra assembly khác nhau một trời một vực.

Mức tối ưu đặt bằng cờ `-O`:
- `-O0`: không tối ưu. Compiler dịch gần như từng dòng C một cách thật thà. Code dài dòng, nhiều lệnh thừa, nhưng bám sát source. **Đây là món quà của reverser.**
- `-O1`, `-O2`: tối ưu vừa và mạnh. `-O2` là mặc định của hầu hết phần mềm release.
- `-O3`: tối ưu tích cực, đôi khi đổi cả cấu trúc vòng lặp.
- `-Os`: tối ưu theo kích thước.

Những gì optimizer làm, và vì sao chúng làm bạn đau đầu:

- **Inlining**: một hàm nhỏ bị nhét thẳng vào nơi gọi nó, thay vì `call`. Lợi cho tốc độ, hại cho bạn: hàm `is_valid()` gọn gàng trong source biến mất, logic của nó rải vào giữa hàm cha. Bạn tìm mãi không thấy `call is_valid` đâu vì nó không còn tồn tại như một hàm riêng.

- **Loop unrolling**: một vòng lặp chạy 4 lần bị trải phẳng thành 4 khối lệnh nối nhau, bỏ luôn biến đếm. Nhìn vào không còn thấy "vòng lặp" nữa.

- **Strength reduction**: thay phép đắt bằng phép rẻ. `x * 8` thành `shl x, 3`. `x / 2` thành shift. Phép chia cho hằng số còn bị biến thành một màn nhân với số nghịch đảo kỳ dị kèm shift, nhìn hoàn toàn không ra là phép chia. Gặp một đoạn `imul` với hằng số to lạ rồi `shr`, nhiều khả năng đó chỉ là một phép chia vô hại.

- **Mất biến trung gian**: biến tạm trong source bị giữ hẳn trong thanh ghi, không bao giờ chạm bộ nhớ, nên decompiler không có gì để đặt tên và bịa ra `v1`, `v2`, `v3`.

- **Sắp xếp lại lệnh, gộp nhánh, loại code chết**: thứ tự lệnh có thể khác source, các nhánh if bị trộn, code không bao giờ chạy bị xóa thẳng.

Thông điệp rút ra: khi decompiler cho ra code trông kỳ quặc với đống `v1 = v2 >> 3`, đừng vội nghĩ tác giả viết thế. Rất có thể source gốc sạch sẽ, chỉ là `-O2` đã nhào nặn nó. Ngược lại, nếu bạn tự tạo binary để học (như trong lab), hãy build với `-O0` cho dễ thở, rồi mới thử `-O2` để thấy sự khác biệt.

## Symbol, stripped, và debug info

Trong object file và file thực thi có thể có **symbol**: tên hàm, tên biến toàn cục, gắn với địa chỉ. Khi symbol còn đó, mở trong IDA bạn thấy luôn `check_password` thay vì `sub_401500`, sướng vô cùng.

- File **không stripped** còn giữ bảng symbol. Nhiều phần mềm build debug, và khá nhiều binary Linux, rơi vào loại này.
- File **stripped** đã bị gỡ bảng symbol (bằng lệnh `strip`), chỉ còn những symbol tối thiểu cần cho dynamic linking. Mọi tên hàm nội bộ biến thành `sub_xxx`. Phần mềm release thường stripped.
- **Debug info** (DWARF trên Linux/ELF, PDB trên Windows) là tầng thông tin dày hơn cả symbol: kiểu dữ liệu, số dòng source, tên biến cục bộ. Thường tách riêng (file `.pdb`, `.dSYM`). Vớ được file PDB đi kèm là coi như trúng số, decompile ra gần như có cả tên biến.

Khi triage, biết file stripped hay không cho bạn kỳ vọng đúng về độ khó. Detect It Easy và các công cụ ở Bài 2.1 nói ngay điều này.

## Lab tự làm

Lab ở [labs/1.6/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/1.6). Bạn sẽ build cùng một file C bốn kiểu (-O0 và -O2, có strip và không), rồi mở trong Ghidra để tự mắt thấy inlining, strength reduction, và sự khác biệt giữa stripped với không stripped. Lời giải kèm đối chiếu ở [labs/1.6/solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/1.6/solution.md), nhưng thử trước khi mở.

## Checklist ghi nhớ
- Biên dịch có bốn khâu: preprocessor, compiler, assembler, linker. Macro biến mất ngay ở khâu một.
- Dynamic linking để lộ import (manh mối vàng khi triage), static linking nhét code thư viện vào trong, khó hơn.
- Loader lúc chạy ánh xạ section, nạp DLL, điền IAT, xử lý relocation. "Trên đĩa" khác "trong bộ nhớ".
- Optimizer là thủ phạm chính làm code khó đọc: inlining, loop unrolling, strength reduction, mất biến trung gian.
- Code decompile kỳ cục thường do `-O2`, không phải do tác giả. Tự build để học thì dùng `-O0`.
- Stripped là mất hết tên hàm nội bộ. Có PDB/DWARF đi kèm là như trúng số.
