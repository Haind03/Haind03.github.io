---
title: "Bài 1.8: ELF và Mach-O, hai định dạng ngoài Windows"
date: 2026-10-06 08:11:00 +0700
categories: ["Technique Reverse", "Phần 1 · Nền tảng máy tính cho RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Bài trước mổ xẻ PE của Windows. Nhưng reverse không chỉ sống trên Windows: server chạy Linux, điện thoại Android cũng là Linux ở lõi, máy Mac và iPhone dùng định dạng riêng. Nếu PE là "hộ chiếu" của file Windows thì ELF là của Linux, Mach-O là của Apple. Hiểu ba cái này là bạn đọc được header của gần như mọi binary gặp trong đời.

Tin vui: cả ba giải quyết cùng một bài toán (đóng gói code, dữ liệu, thông tin nạp vào bộ nhớ thế nào), nên học một cái là hiểu nhanh hai cái kia. Bài này tập trung ELF vì bạn sẽ gặp nó nhiều nhất, rồi lướt qua Mach-O và so sánh.

## ELF: xương sống của Linux

ELF (Executable and Linkable Format) dùng cho mọi thứ chạy được trên Linux: chương trình thực thi, thư viện `.so`, file object `.o`, thậm chí core dump. Nhận ra nó dễ: 4 byte đầu luôn là `7F 45 4C 46`, tức `0x7F` rồi ba ký tự ASCII "ELF". Mở bất cứ file nào trong `/bin` bằng hex editor là thấy ngay.

### Header, tấm bản đồ đầu file

ELF header nằm ở đầu file, cho biết những thứ cốt lõi:

- **Magic** (`7F 45 4C 46`): xác nhận đây là ELF.
- **Class**: 32-bit (ELFCLASS32) hay 64-bit (ELFCLASS64).
- **Endianness**: little hay big endian.
- **Type**: `ET_EXEC` (thực thi địa chỉ cố định), `ET_DYN` (shared object hoặc PIE, chạy được ở địa chỉ bất kỳ), `ET_REL` (file object).
- **Machine**: kiến trúc CPU, x86-64, ARM, MIPS, RISC-V...
- **Entry point** (`e_entry`): địa chỉ ảo nơi code bắt đầu chạy. Giống `AddressOfEntryPoint` của PE.
- Vị trí của **program header table** và **section header table**.

Lệnh đọc nhanh:

```
readelf -h ./a.out      # đọc ELF header
file ./a.out            # tóm tắt một dòng: loại, bit, động/tĩnh, stripped hay chưa
```

### Hai bảng header, điểm hay gây lẫn

Đây là chỗ ELF khác PE và làm nhiều người bối rối: ELF có **hai** bảng mô tả, phục vụ hai mục đích khác nhau.

- **Program header table** nói cho *loader* (hệ điều hành) biết cách nạp file vào bộ nhớ lúc chạy. Đơn vị của nó là **segment**. Mỗi segment là một khối sẽ được map vào bộ nhớ kèm quyền (R/W/X).
- **Section header table** nói cho *linker* và công cụ phân tích biết file chia thành những **section** nào (.text, .data...). Khi chạy thì loader không cần bảng này.

Nói gọn: **segment để chạy, section để phân tích.** Một segment thường gom nhiều section lại. Ví dụ segment code chứa cả `.text` lẫn `.rodata`. Khi file bị strip, section header có thể bị cắt bớt nhưng program header thì không thể thiếu, vì không có nó file không chạy được.

```
readelf -l ./a.out      # program headers (segment) + section nào thuộc segment nào
readelf -S ./a.out      # section headers
```

### Các section quen mặt

Nhiều cái giống PE, gọi tên hơi khác:

- **.text**: code, quyền R-X.
- **.data**: biến toàn cục đã khởi tạo, RW.
- **.bss**: biến toàn cục bằng 0, không tốn chỗ trên đĩa.
- **.rodata**: dữ liệu chỉ đọc, hằng số và chuỗi. Chuỗi "Access denied" của bạn nằm đây.
- **.plt** và **.got**: trái tim của dynamic linking, nói ở phần dưới.
- **.symtab** và **.strtab**: bảng symbol và tên. Đây là thứ bị cắt khi strip.
- **.dynsym** và **.dynstr**: symbol cho dynamic linking, cái này không bị strip vì cần lúc chạy.

### PLT và GOT, cách Linux gọi hàm thư viện

Khi chương trình gọi `printf` từ libc, lúc biên dịch nó chưa biết `printf` nằm ở địa chỉ nào (libc được ASLR đặt ngẫu nhiên mỗi lần chạy). Linux giải quyết bằng cặp PLT/GOT, và bạn sẽ gặp hai cái tên này suốt đời reverse Linux nên hiểu luôn cho chắc.

- **GOT** (Global Offset Table) là một bảng con trỏ. Mỗi ô sẽ chứa địa chỉ thật của một hàm ngoài, điền vào lúc chạy.
- **PLT** (Procedure Linkage Table) là các đoạn code nhỏ đứng trung gian. Code của bạn không gọi thẳng `printf` mà gọi `printf@plt`.

Cơ chế **lazy binding**, giải quyết địa chỉ chỉ khi hàm được gọi lần đầu, diễn ra thế này: lần đầu gọi `printf@plt`, nó nhảy qua GOT tới bộ giải (resolver) của dynamic linker, tìm ra địa chỉ thật của `printf`, ghi vào ô GOT, rồi mới gọi. Từ lần sau, `printf@plt` nhảy thẳng qua GOT tới địa chỉ đã lưu, không phải giải lại.

Với người reverse, điều cần nhớ: thấy `call printf@plt` nghĩa là đang gọi một hàm ngoài, và muốn biết địa chỉ thật của nó lúc chạy thì nhìn vào ô GOT tương ứng trong debugger. GOT cũng là mục tiêu kinh điển của tấn công (GOT overwrite), nhưng đó là chuyện của mảng exploit.

### Stripped hay không

Giống PE, binary ELF có thể giữ hoặc bỏ thông tin symbol:

- **Không stripped**: còn `.symtab`, tên hàm và biến hiện ra đẹp đẽ trong Ghidra/IDA. Dễ thở.
- **Stripped**: `.symtab` bị cắt, chỉ còn `.dynsym` (các hàm thư viện import vẫn thấy tên, nhưng hàm nội bộ của tác giả thành `sub_xxxx`). Phần lớn phần mềm thật và malware đều stripped.

```
nm ./a.out              # liệt kê symbol (báo "no symbols" nếu đã strip)
strip ./a.out           # tự tay strip để xem khác biệt
```

## Mach-O: định dạng của Apple

macOS và iOS dùng Mach-O. Cấu trúc tư duy giống ELF nhưng tên gọi và vài chỗ khác.

- **Magic**: `0xFEEDFACE` (32-bit) hoặc `0xFEEDFACF` (64-bit). Vui là người Apple cố tình ghép thành chữ "feed face".
- **Fat binary (universal binary)**: một file Mach-O có thể gói nhiều kiến trúc cùng lúc, ví dụ x86-64 và ARM64 cho máy Intel lẫn Apple Silicon. Magic của file fat là `0xCAFEBABE`. Khi reverse, bạn thường phải tách lấy đúng kiến trúc mình cần bằng `lipo`.
- **Load commands**: thay cho program header của ELF. Đây là danh sách chỉ thị cho loader: segment nào map vào đâu, cần thư viện nào, entry point ở đâu, chữ ký code ra sao.
- **Segment và section**: Mach-O cũng chia segment, tên viết hoa với hai gạch dưới: `__TEXT` (code, chỉ đọc), `__DATA` (dữ liệu ghi được). Trong mỗi segment lại có section như `__text`, `__cstring`.

Công cụ trên Mac:

```
otool -hv binary        # header và load commands
otool -l binary         # liệt kê load commands đầy đủ
lipo -info binary       # xem file chứa những kiến trúc nào
lipo binary -thin arm64 -output binary_arm64   # tách lấy một kiến trúc
nm binary               # symbol
```

Objective-C và Swift còn có những section metadata riêng cho runtime, nhưng đó để Phần 12 lo. Ở đây chỉ cần quen bộ xương Mach-O.

## So sánh ba định dạng cho dễ nhớ

| Khái niệm | PE (Windows) | ELF (Linux) | Mach-O (Apple) |
|---|---|---|---|
| Magic | `MZ` rồi `PE\0\0` | `7F 45 4C 46` | `FEEDFACE/FACF`, fat `CAFEBABE` |
| Mô tả nạp bộ nhớ | Section table | Program header (segment) | Load commands (segment) |
| Code | .text | .text | `__TEXT`/`__text` |
| Dữ liệu chỉ đọc | .rdata | .rodata | `__TEXT`/`__cstring` |
| Import hàm ngoài | IAT | PLT/GOT | stubs / `__la_symbol_ptr` |
| Entry point | AddressOfEntryPoint | e_entry | LC_MAIN |
| Nhiều kiến trúc 1 file | Không | Không | Có (fat binary) |

Nhìn bảng này là thấy cả ba kể cùng một câu chuyện, chỉ đổi từ vựng. Học kỹ ELF thì đọc PE và Mach-O chỉ là tra lại tên gọi.

## Lab tự làm

Lab ở [labs/1.8/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/1.8). Bạn sẽ tự tay dùng `readelf`, `objdump`, `nm` để mổ một binary ELF, tìm entry point, liệt kê segment, và quan sát PLT/GOT. Có file hello world để build và một writeup mẫu để đối chiếu. Nếu không có máy Linux, chạy trong WSL hoặc một VM nhẹ là đủ.

## Checklist ghi nhớ
- ELF magic `7F 'E' 'L' 'F'`, Mach-O `FEEDFACE/FACF`, fat binary `CAFEBABE`.
- ELF có hai bảng: program header (segment, để loader chạy) và section header (section, để phân tích). Segment để chạy, section để đọc.
- PLT/GOT là cách Linux gọi hàm thư viện, lazy binding điền địa chỉ thật vào GOT lần gọi đầu.
- Stripped cắt `.symtab` (hàm nội bộ thành sub_xxx) nhưng `.dynsym` vẫn còn nên tên hàm import vẫn thấy.
- Mach-O có thể là fat binary chứa nhiều kiến trúc, dùng `lipo` để tách.
- Ba định dạng PE/ELF/Mach-O cùng ý tưởng, chỉ khác tên gọi.
