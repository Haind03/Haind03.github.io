---
title: "Bài 2.7: Hex editor và template, khi bạn cần nhìn tận byte"
date: 2026-10-06 08:23:00 +0700
categories: ["Technique Reverse", "Phần 2 · Làm quen bộ công cụ"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
Disassembler cho bạn cái nhìn ở mức lệnh, debugger cho bạn cái nhìn lúc chạy. Nhưng có những lúc bạn chỉ muốn mở toạc file ra và nhìn thẳng từng byte một: sửa một magic number bị hỏng, vá một byte để qua check, hay đọc một định dạng file lạ hoắc chẳng ai viết parser. Đó là lúc hex editor lên tiếng. Nó là con dao mổ thô nhất nhưng cũng trung thực nhất trong bộ đồ nghề.

Bài này không dạy bạn thuộc từng nút của ba phần mềm. Nó chỉ cho bạn biết khi nào cần hex editor, chọn cái nào, và quan trọng nhất là khái niệm template/pattern biến một đống byte thành cấu trúc đọc được.

## Khi nào thật sự cần hex editor

Phần lớn thời gian bạn không mở hex editor, vì IDA và x64dbg đã có cửa sổ hex riêng. Nhưng có vài tình huống mà một hex editor độc lập nhanh và gọn hơn hẳn:

- **Patch byte trực tiếp trên file.** Bạn đã tìm ra trong debugger rằng cần đổi một `jne` (opcode `75`) thành `je` (opcode `74`), giờ muốn sửa thẳng vào file trên đĩa để bản vá tồn tại vĩnh viễn. Mở hex editor, nhảy tới offset, gõ đè, lưu. Xong. Chi tiết patch ở [Bài 17.1](https://github.com/Haind03/Technique-Reverse/tree/main/phan-17-patch-hook-frida).
- **Sửa magic number hoặc header.** Một file bị hỏng vài byte đầu, hoặc ai đó cố tình đổi magic để giấu loại file. Bạn khôi phục bằng tay.
- **Đọc định dạng file không ai biết.** Một file cấu hình nhị phân, một save game, một container tự chế. Không có parser, bạn tự lần cấu trúc qua hex.
- **Kiểm tra nhanh một file.** Bốn byte đầu là gì? `4D 5A` là PE, `7F 45 4C 46` là ELF, `50 4B` là ZIP. Nhiều khi chỉ cần liếc đầu file là biết.

## Ba lựa chọn, chọn theo nhu cầu

### HxD, nhẹ và đủ xài

HxD là hex editor Windows miễn phí, nhẹ, mở nhanh. Nó làm tốt những việc cơ bản: xem, sửa byte, tìm kiếm chuỗi hex hoặc text, so sánh hai file, mở cả ổ đĩa và bộ nhớ tiến trình. Nếu bạn chỉ cần vá vài byte hay soi nhanh một file, HxD là đủ và không có gì phải nghĩ thêm. Điểm yếu: nó không hiểu cấu trúc, với nó mọi thứ chỉ là byte.

### 010 Editor, vua của Binary Template

010 Editor là phần mềm thương mại (có bản dùng thử), và thứ làm nó đáng tiền là **Binary Template**. Đây là tính năng để đời. Thay vì nhìn byte trần, bạn chạy một template (một script mô tả cấu trúc file) và 010 sẽ phân rã file thành các trường có tên, có kiểu, có màu. File PE trở thành một cây gồm DOS header, NT headers, section table, mỗi trường ghi rõ giá trị. Cộng đồng đã viết template cho hàng trăm định dạng (PE, ELF, ZIP, PNG, PCAP...), tải về chạy là xong.

Nếu công việc của bạn hay phải đọc cấu trúc file, 010 tiết kiệm hàng giờ dò byte thủ công.

### ImHex, dành riêng cho reverser và miễn phí

ImHex là hex editor mã nguồn mở, sinh ra cho dân RE. Nó có gần hết thứ hay của 010 mà không tốn tiền:

- **Pattern language** tương đương Binary Template, mô tả cấu trúc file bằng cú pháp giống C.
- **Data inspector**: đặt con trỏ tại một byte, nó hiện ngay giá trị nếu diễn giải thành u8/u16/u32, float, thời gian, ở cả little và big endian. Cực tiện để đoán kiểu dữ liệu.
- **Disassembler tích hợp**, biểu đồ entropy, xem nhiều kiểu encoding.
- Giao diện node để xử lý dữ liệu, và kho pattern có sẵn tải trong app.

Với người mới không muốn chi tiền, ImHex là lựa chọn mặc định tốt nhất. Phần còn lại của bài dùng ImHex làm ví dụ.

## Template/pattern: biến byte thành cấu trúc

Đây là ý tưởng quan trọng nhất của bài. Một file nhị phân thực ra là các trường có kiểu xếp liền nhau: một số 4 byte ở đây, một chuỗi ở kia, một mảng struct phía sau. Mắt thường nhìn hex khó mà tách ra. Template là cách bạn nói cho công cụ biết bố cục đó, rồi nó tô màu và gắn nhãn giúp.

Lấy phần đầu một file PE làm ví dụ. Chuẩn PE bắt đầu bằng DOS header, trong đó hai trường quan trọng là magic `MZ` ở offset 0 và `e_lfanew` ở offset 0x3C (trỏ tới NT headers). Bằng pattern language của ImHex, bạn mô tả như sau:

```c
// Pattern ImHex rút gọn cho phần đầu PE
struct DosHeader {
    char     magic[2];   // phải là "MZ"
    u8       rest[58];    // bỏ qua phần giữa
    u32      e_lfanew;    // offset tới NT headers
};

struct NtHeaders {
    char     signature[4];   // "PE\0\0"
    u16      machine;        // 0x8664 = x64, 0x14C = x86
    u16      numberOfSections;
};

DosHeader dos @ 0x00;              // đặt DosHeader tại offset 0
NtHeaders nt  @ dos.e_lfanew;      // đặt NtHeaders tại offset mà e_lfanew chỉ ra
```

Chạy pattern này trên một file `.exe`, ImHex sẽ hiện `dos.magic = "MZ"`, `dos.e_lfanew = 0x100` (chẳng hạn), rồi nhảy tới đó đọc `nt.signature = "PE"`, `nt.machine = 0x8664`. Bạn vừa đọc được loại kiến trúc và số section mà không phải đếm byte bằng tay. Cú pháp `@ địa_chỉ` là nét duyên của pattern language: bạn đặt một struct tại đúng offset, kể cả offset lấy từ một trường khác.

Hiểu được ý này rồi, bạn áp cho mọi định dạng: tự viết pattern cho một save game, một file config nhị phân, và công cụ sẽ phân rã giúp. Đây chính là bước đầu của reverse định dạng file, chủ đề [Bài 18.7](https://github.com/Haind03/Technique-Reverse/tree/main/phan-18-nang-cao).

## So sánh nhanh ba tool

| | HxD | 010 Editor | ImHex |
|---|---|---|---|
| Giá | free | thương mại | free, mã nguồn mở |
| Nền tảng | Windows | đa nền | đa nền |
| Template/pattern | không | Binary Template (mạnh, nhiều sẵn) | Pattern language (mạnh, miễn phí) |
| Data inspector | cơ bản | có | rất tốt |
| Disasm/entropy | không | một phần | có |
| Hợp với | vá byte nhanh | đọc cấu trúc chuyên nghiệp | reverser nói chung, người mới |

Lời khuyên gọn: cài HxD để vá nhanh, cài ImHex làm chủ lực. 010 chỉ cần khi bạn làm nhiều với định dạng file và muốn kho template khổng lồ của nó.

## Lab tự làm

Bài tập và writeup ở [labs/2.7/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/2.7). Bạn sẽ dùng ImHex (hoặc 010) parse header một file PE bằng pattern, vá một byte trong file nhỏ rồi quan sát thay đổi, và tự viết pattern cho một định dạng file đơn giản.

## Checklist ghi nhớ
- Hex editor dùng khi cần nhìn và sửa tận byte: vá byte, sửa magic/header, đọc định dạng lạ.
- Nhận diện nhanh đầu file: `4D 5A` = PE, `7F 45 4C 46` = ELF, `50 4B` = ZIP.
- HxD nhẹ cho việc vá nhanh, ImHex miễn phí và mạnh cho reverser, 010 Editor mạnh nhất về template nhưng trả phí.
- Template/pattern biến byte trần thành trường có tên và kiểu, đây là chìa khoá đọc cấu trúc file.
- Cú pháp `@ offset` của ImHex cho bạn đặt struct tại đúng vị trí, kể cả vị trí lấy từ trường khác.
