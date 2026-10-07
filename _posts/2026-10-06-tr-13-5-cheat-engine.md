---
title: "Bài 13.5: Cheat Engine, học bộ nhớ runtime qua trò chơi"
date: 2026-10-06 09:19:00 +0700
categories: ["Technique Reverse", "Phần 13 · Game: Unity, Unreal, Lua"]
tags: [reverse-engineering, game-hacking]
render_with_liquid: false
---
Trước khi đi tiếp, một câu dứt khoát: mọi thứ trong bài này chỉ dành cho game **offline, single-player của chính bạn**, hoặc cho Cheat Engine Tutorial đi kèm. Đụng vào game online là gian lận, vi phạm ToS, và ở nhiều nơi là phạm pháp. Ngoài ra anti-cheat sẽ ban bạn. Lý do ta học Cheat Engine không phải để ăn gian, mà vì nó là cách thực hành memory analysis trực quan nhất: bạn thấy giá trị trong RAM đổi theo thời gian thực, lần ra địa chỉ, rồi lần ra code đụng vào địa chỉ đó. Kỹ năng này dùng lại y nguyên khi phân tích malware hay bất kỳ tiến trình nào.

Cheat Engine (CE) là một memory scanner cộng debugger cho Windows. Nó gắn vào một tiến trình đang chạy rồi cho bạn tìm kiếm, theo dõi, và sửa bộ nhớ của tiến trình đó.

## Scan: tìm địa chỉ của một giá trị

Vấn đề cốt lõi: bạn thấy "máu = 100" trên màn hình, nhưng con số đó nằm ở địa chỉ nào trong hàng trăm MB bộ nhớ của game? CE giải bằng cách quét nhiều lần và lọc dần.

Hai kiểu quét hay dùng nhất:

**Exact value (biết giá trị).** Máu đang là 100, bạn gõ 100 rồi First Scan. CE trả về có khi hàng nghìn địa chỉ đang chứa 100 (trùng ngẫu nhiên). Bạn vào game cho máu tụt xuống 90, quay ra gõ 90 rồi Next Scan. CE chỉ giữ lại các địa chỉ vừa đổi từ 100 thành 90. Lặp vài lần là còn một hai địa chỉ, đó chính là máu thật.

**Unknown initial value (không biết giá trị).** Dùng khi con số bị mã hoá hoặc không hiện rõ (ví dụ thanh máu chỉ là hình). First Scan chọn "Unknown initial value". Rồi mỗi khi giá trị tăng bạn chọn **Increased value**, khi giảm chọn **Decreased value**, khi không đổi chọn **Unchanged**. Đây là lọc theo xu hướng thay đổi thay vì theo con số, cực mạnh cho giá trị ẩn.

Chọn đúng kiểu dữ liệu cũng quan trọng: 4 Bytes (int) là mặc định cho phần lớn giá trị game, nhưng có khi là Float (máu lẻ), Double, hoặc 2 Bytes. Sai kiểu thì không bao giờ ra.

Tìm xong, double-click địa chỉ để đưa xuống bảng dưới, rồi tick **Active** để freeze (đóng băng) giá trị, game không trừ máu được nữa.

## Vấn đề: địa chỉ đổi mỗi lần chạy

Bạn freeze máu thành công, tắt game, mở lại, và địa chỉ cũ trỏ vào rác. Vì object máu nằm trên heap, mỗi lần chạy nó được cấp ở chỗ khác (cộng thêm ASLR, xem lại Bài 1.2). Địa chỉ tuyệt đối vô dụng qua các phiên.

Lời giải là **pointer path**: thay vì nhớ địa chỉ cuối, bạn tìm một chuỗi con trỏ xuất phát từ một địa chỉ cố định (base của module game, không đổi tương đối) đi qua vài offset tới được giá trị. Dạng `[[base + 0x10] + 0x8] + 0x4C`. Chuỗi này ổn định giữa các lần chạy vì nó bám vào cấu trúc chương trình chứ không bám vào chỗ heap ngẫu nhiên.

CE có **Pointer Scan** để tự tìm: chuột phải địa chỉ máu, Pointer scan for this address, CE dò ngược xem con trỏ nào dẫn tới đó. Bạn chạy pointer scan, khởi động lại game, rồi rescan với địa chỉ mới để loại bớt path sai. Vài vòng là ra một pointer path dùng lại được.

## Find out what accesses this address

Đây là tính năng biến CE từ đồ chơi thành công cụ reverse thật sự. Chuột phải địa chỉ máu, chọn **Find out what accesses this address**. CE đặt một hardware breakpoint và liệt kê mọi lệnh đụng vào địa chỉ đó. Bạn sẽ thấy dòng kiểu:

```
mov [rax+4C], ecx      ; lệnh ghi máu mới
sub [rbx+4C], edx      ; lệnh trừ máu khi trúng đòn
```

Lệnh `sub [rbx+4C], edx` chính là nơi game trừ máu. Giờ bạn biết chính xác code nào xử lý máu, và có thể xem thanh ghi rbx để biết địa chỉ base của object nhân vật, từ đó suy ra cả struct. Đây đúng là tư duy "đi từ dữ liệu tới code" của Bài 0.4, chỉ khác là làm trên bộ nhớ sống.

## Auto Assembler và code injection

Khi đã tìm thấy lệnh trừ máu, bạn có thể vô hiệu hoá nó. Đơn giản nhất là NOP (xem Bài 17.1): chuột phải lệnh, Replace with code that does nothing, CE ghi đè bằng nop, máu không trừ nữa. Nhưng NOP thô có thể hỏng logic khác dùng chung lệnh đó.

Cách sạch hơn là **code injection** qua **Auto Assembler (AA) script**. Ý tưởng giống code cave: bạn chèn một jump từ lệnh gốc tới một vùng trống, làm thêm việc của mình ở đó (ví dụ chỉ bỏ qua trừ máu khi là nhân vật của người chơi chứ không phải địa chỉ khác), rồi nhảy về. CE sinh sẵn khung script qua menu Auto Assemble, template "Code injection". Một AA script điển hình:

```
[ENABLE]
aobscanmodule(hpInj, game.exe, 29 50 4C)   // tìm chuỗi byte của lệnh sub [rax+4C],edx
alloc(newmem, 256, hpInj)

newmem:
  cmp rax, [playerBase]     // chỉ chặn nếu là object người chơi
  jne originalcode
  jmp return                // bỏ qua lệnh trừ máu
originalcode:
  sub [rax+4C], edx
return:

hpInj:
  jmp newmem

[DISABLE]
hpInj:
  db 29 50 4C               // trả lại lệnh gốc
```

`aobscanmodule` (array-of-bytes scan) tìm lệnh theo chuỗi byte thay vì địa chỉ cứng, nên script sống sót qua các lần chạy và cả vài bản cập nhật nhỏ. Đây là pattern bạn gặp lại khi viết hook (Bài 17.3).

## ReClass.NET: dựng lại struct trong bộ nhớ

Khi `find out what accesses` cho bạn địa chỉ base của object nhân vật, bạn sẽ muốn biết cả struct: máu ở offset 0x4C, mana ở đâu, toạ độ ở đâu. **ReClass.NET** làm đúng việc đó: bạn trỏ nó vào địa chỉ base, nó hiển thị vùng nhớ dạng bảng và cho bạn gán kiểu cho từng offset (int, float, con trỏ, chuỗi, struct lồng nhau). Dần dần bạn dựng lại được định nghĩa struct của object giống hệt việc khôi phục struct trong IDA ở Bài 3.3, chỉ là làm trên bộ nhớ sống thay vì trên binary tĩnh. Struct dựng xong export ra C++ header, dùng lại khi viết tool.

## Vì sao bài này quan trọng ngoài game

Gỡ bỏ lớp áo game đi, bạn vừa học: quét bộ nhớ để định vị dữ liệu, lần pointer path để có địa chỉ ổn định qua ASLR, hardware breakpoint để tìm code đụng vào dữ liệu, code injection qua AOB scan, và dựng lại struct runtime. Cả năm kỹ năng đó là bánh mì bơ của phân tích malware và của mọi dynamic analysis. Cheat Engine chỉ tình cờ là cách vui nhất để luyện chúng.

## Lab tự làm
Xem [labs/13.5/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/13.5). Dùng Cheat Engine Tutorial đi kèm (hợp pháp, làm ra để học) hoặc một game offline của bạn: tìm giá trị bằng exact và unknown scan, dựng pointer path qua một lần khởi động lại, dùng find out what accesses để tìm lệnh xử lý, và thử một AA script đơn giản.

## Checklist ghi nhớ
- Chỉ dùng cho game offline/single-player của mình. Online là gian lận và phạm pháp.
- Exact value scan khi biết số, unknown + increased/decreased khi giá trị ẩn. Chọn đúng kiểu (4 Bytes, Float...).
- Địa chỉ heap đổi mỗi lần chạy, phải tìm pointer path bám vào base module mới ổn định.
- Find out what accesses this address đặt hardware breakpoint để tìm code đụng vào dữ liệu, đây là đi từ data tới code.
- Code injection qua AA script + aobscanmodule sạch và bền hơn NOP thô.
- ReClass.NET dựng lại struct runtime, giống khôi phục struct trong IDA nhưng trên bộ nhớ sống.
- Các kỹ năng này dùng lại nguyên vẹn cho malware analysis và mọi dynamic analysis.
