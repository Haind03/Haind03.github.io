---
title: "Bài 10.3: Script đóng thành exe, mở lại nhanh hơn bạn tưởng"
date: 2026-10-06 09:08:00 +0700
categories: ["Technique Reverse", "Phần 10 · Ngôn ngữ legacy: Delphi, VB6, AutoIt, AHK"]
tags: [reverse-engineering, legacy]
render_with_liquid: false
---
Có một nhóm "exe" mà nếu bạn lôi thẳng vào IDA thì phí cả buổi tối: đó là các script được gói vào một file chạy. Bên trong không phải code C được biên dịch, mà là một đoạn AutoIt, AutoHotkey, hay một bộ cài NSIS, kèm theo một cái stub chỉ làm mỗi việc bung script ra rồi chạy. Reverse đúng cách là không đọc assembly của stub, mà trích lại script gốc. Nhiều khi bạn lấy lại gần như nguyên văn mã nguồn.

Đây không phải kiến thức bên lề. Malware rất chuộng AutoIt và NSIS vì gói nhanh, khó bị diệt theo chữ ký, và trông vô hại. Biết moi script ra là một kỹ năng dùng thật.

## Nguyên tắc chung: nhận diện trước, trích sau

Mọi loại trong bài này theo cùng một nhịp. Đầu tiên nhận diện loại wrapper bằng Detect It Easy (DIE) và `strings`, vì mỗi loại để lại dấu vết rất rõ. Sau đó dùng đúng công cụ trích cho loại đó. Đừng bao giờ nhảy vào disassembler trước khi loại trừ khả năng đây chỉ là script được gói.

Dấu hiệu nhanh trong `strings` hoặc DIE:

| Loại | Dấu vết hay thấy |
|---|---|
| AutoIt | chuỗi `AU3!`, `>>>AUTOIT SCRIPT<<<`, `AutoIt v3` |
| AutoHotkey | resource `RCDATA` tên `>AUTOHOTKEY SCRIPT<`, chuỗi `AutoHotkey` |
| NSIS | chuỗi `Nullsoft Install System`, `NSIS` |
| Inno Setup | chuỗi `Inno Setup`, section `JR.` trong resource |
| PyInstaller | chuỗi `MEI`, `pyi` (xem lại Bài 7.4) |

## AutoIt

AutoIt là ngôn ngữ script tự động hoá cho Windows. Khi compile, nó nhúng mã script (dạng đã token hoá, không phải text thuần) vào một stub interpreter. Điều may mắn: token hoá không phải mã hoá mạnh, nên tool giải lại được gần hết.

Công cụ:
- **Exe2Aut**: kéo thả exe vào, nó bung ra file `.au3` gốc. Chạy trên Windows, đơn giản nhất.
- **AutoIt-Ripper** (Python): chạy được đa nền, trích script từ exe hoặc từ dump bộ nhớ.

Với các biến thể AutoIt mới có mã hoá thêm, Exe2Aut đôi khi phải chạy chính file đó (nguy hiểm nếu là malware) để bắt lúc script được giải trong bộ nhớ. Khi phân tích mẫu độc, làm trong VM cô lập theo [Bài 0.3](/posts/tr-0-3-dung-lab-an-toan/).

## AutoHotkey

AutoHotkey (AHK) còn dễ hơn. Script được nhúng gần như nguyên văn vào một resource kiểu `RCDATA`, thường tên `>AUTOHOTKEY SCRIPT<`. Bạn không cần tool chuyên dụng:

- Mở exe bằng **Resource Hacker** hoặc **CFF Explorer**, tìm resource RCDATA, export ra là có script `.ahk`.
- Với AHK v2 hoặc bản nén, có thể cần giải nén resource trước, nhưng cách tiếp cận không đổi.

Vì script nằm dạng text, nhiều khi bạn chỉ cần `strings` là đã thấy lấp ló nội dung.

## NSIS installer

NSIS (Nullsoft Scriptable Install System) là bộ tạo installer rất phổ biến. Bên trong là một archive chứa các file sẽ cài, cộng với script cài đặt đã biên dịch.

- **7-Zip** (bản hỗ trợ NSIS) mở thẳng file `.exe` NSIS như một archive, cho bạn xem và trích các file bên trong. Đây là cách nhanh nhất để lấy payload mà installer sẽ thả ra.
- Lưu ý 7-Zip đời mới đã bỏ bớt hỗ trợ xem script `.nsi`, nhưng vẫn trích được các file. Muốn đọc lại logic script thì dùng các fork chuyên như **nsisunbz** hoặc bản 7-Zip cũ.

Với malware, NSIS thường chỉ là lớp vỏ: trích ra rồi bạn sẽ thấy payload thật (một exe/dll/script khác) để phân tích tiếp.

## Inno Setup

Inno Setup là một bộ tạo installer phổ biến khác. Khác NSIS ở định dạng nên 7-Zip không mở được tử tế.

- **innounp** (Inno Setup Unpacker): dòng lệnh, `innounp -x setup.exe` để trích toàn bộ file và cả script `install_script.iss` đã decompile.
- **UniExtract2** gói sẵn nhiều trình trích, nhận diện tự động cả NSIS lẫn Inno lẫn vài loại khác, tiện khi bạn lười nhớ tool nào cho loại nào.

## Các wrapper khác

- **BAT to EXE** (batch gói thành exe): thường trích được bằng các tool như `Batch2Exe` ngược, hoặc đơn giản là dump chuỗi/temp file lúc chạy.
- **Các packer script tự chế**: khi không có tool sẵn, cách tổng quát luôn đúng là chạy trong VM rồi bắt file tạm hoặc dump bộ nhớ lúc script được giải (dùng Procmon xem file nó ghi ra `%TEMP%`, xem lại [Bài 2.8](/posts/tr-2-8-giam-sat-he-thong/)).

## Vì sao nên thử hướng này đầu tiên

Một mẫu malware được báo là "khó", kéo vào IDA thấy toàn code lạ, hoá ra chỉ là stub AutoIt. Trích script ra là đọc được ý đồ trong vài phút, thay vì lội assembly cả ngày. Thói quen tốt: trước khi than phiền binary khó, hãy loại trừ khả năng nó chỉ là một script được gói. DIE và `strings` cho bạn câu trả lời trong mười giây.

## Checklist ghi nhớ
- Nhiều "exe" thật ra là script (AutoIt/AHK) hoặc installer (NSIS/Inno) được gói. Đừng đọc assembly của stub.
- Luôn nhận diện trước bằng DIE và `strings`, mỗi loại có dấu vết rất rõ.
- AutoIt: Exe2Aut hoặc AutoIt-Ripper. AHK: trích resource RCDATA bằng Resource Hacker.
- NSIS: 7-Zip. Inno: innounp. Lười thì UniExtract2 lo cả hai.
- Malware chuộng AutoIt và NSIS, trích script/payload là kỹ năng thực tế.
- Khi không có tool, chạy trong VM cô lập rồi bắt file tạm hoặc dump bộ nhớ.
