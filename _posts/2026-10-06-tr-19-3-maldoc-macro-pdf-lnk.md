---
title: "Bài 19.3: Phân tích maldoc và loader, nơi cuộc tấn công bắt đầu"
date: 2026-10-06 09:57:00 +0700
categories: ["Technique Reverse", "Phần 19 · Phân tích mã độc cơ bản (phòng thủ)"]
tags: [reverse-engineering, malware]
render_with_liquid: false
---
Phần lớn các vụ nhiễm không mở màn bằng một file `.exe` đập thẳng vào mặt nạn nhân. Nó mở màn bằng một thứ trông vô hại: một file Word đính kèm email, một PDF hoá đơn, một shortcut `.lnk` giả làm thư mục. Những thứ này không phải malware thật sự, chúng là loader, nhiệm vụ duy nhất là kéo payload tầng sau về và chạy. Reverse được khâu này là bạn chặn được cuộc tấn công từ gốc, nên đây là kỹ năng blue team dùng hằng ngày.

Cả bài này đứng ở góc phòng thủ: ta phân tích để hiểu và phát hiện, mọi ví dụ đều lành tính và chạy trong lab cô lập (xem [Bài 0.3](/posts/tr-0-3-dung-lab-an-toan/)).

## Bốn loại loader hay gặp

Trước khi mổ, biết mình cầm cái gì. Dùng `file`, đọc magic, nhìn phần mở rộng thật:

- **Office macro** trong `.doc/.docm/.xls/.xlsm`: VBA nhúng, tự chạy khi mở.
- **PDF độc**: JavaScript nhúng hoặc launch action gọi lệnh ngoài.
- **LNK độc**: shortcut giấu một dòng lệnh dài trong trường arguments.
- **Script loader**: PowerShell, JS, HTA, VBS, thường obfuscate nhiều tầng.

Cả bốn có chung một khuôn: một mồi (file người dùng mở) kéo theo một chuỗi lệnh bị che, chuỗi đó tải payload thật về. Việc của bạn là lột từng lớp cho tới khi thấy URL hoặc payload tầng sau.

## Office macro, kẻ kinh điển

File Office hiện đại (`.docx`) là ZIP chứa XML. Nhưng bản có macro (`.docm`, hoặc `.doc` cũ dạng OLE) nhúng VBA. Bộ công cụ số một là **oletools** (Python):

```
olevba mau.doc        # trích toàn bộ macro VBA ra text
oleid mau.doc         # tóm tắt dấu hiệu khả nghi
mraptor mau.doc       # chấm điểm khả năng độc (auto-exec + ghi + chạy)
```

Khi đọc macro, tìm ba thứ:

1. **Auto-exec trigger**: `AutoOpen`, `Document_Open`, `Workbook_Open`, `AutoClose`. Đây là hàm chạy ngay khi mở file mà không cần người dùng bấm gì. olevba đánh dấu sẵn các hàm này.
2. **Chuỗi bị obfuscate**: tác giả hay nối chuỗi (`"po" & "wer" & "shell"`), `Chr()` từng ký tự, hoặc base64. olevba có cờ trích các chuỗi này ra.
3. **Lệnh chạy ngoài**: `Shell`, `CreateObject("WScript.Shell").Run`, `WMI`, thường kết thúc bằng một lời gọi `powershell` tải payload.

Mẹo: olevba còn có tính năng giải mã một số encode phổ biến ngay trong output. Nhưng obfuscation tuỳ biến thì bạn phải tự gỡ, chép đoạn VBA ra, thay `Shell`/`Run` bằng một lệnh in ra (hoặc dịch sang Python) để lấy chuỗi cuối mà không thực thi.

## PDF độc

PDF là một chuỗi object đánh số, nối bằng cross-reference table. Phần nguy hiểm nằm ở:

- **JavaScript nhúng** (`/JS`, `/JavaScript`): chạy khi mở, thường khai thác lỗ hổng reader hoặc decode một payload.
- **Launch action** (`/Launch`, `/OpenAction`, `/AA`): gọi một chương trình ngoài.
- **Embedded file** (`/EmbeddedFile`): giấu payload ngay trong PDF.

Công cụ: **pdf-parser** (liệt kê object, lọc theo từ khoá) và **peepdf**:

```
pdf-parser.py --stats mau.pdf          # thống kê loại object
pdf-parser.py --search JavaScript mau.pdf
pdf-parser.py --object 12 --filter mau.pdf   # giải stream của object 12
```

Quy trình: tìm `/OpenAction` trỏ tới object nào, mở object đó, giải stream (nhiều stream nén FlateDecode nên cần `--filter`), đọc JavaScript, giải tiếp nếu nó encode.

## LNK độc

File `.lnk` là shortcut Windows, nhưng trường target và arguments chứa được một dòng lệnh dài mà người dùng không thấy (Explorer cắt bớt phần hiển thị). Kẻ tấn công nhét cả một lệnh PowerShell vào đó, icon thì giả làm PDF hay folder.

Phân tích bằng **lnkparse** (Python) hoặc **LECmd** (Eric Zimmerman):

```
lnkparse mau.lnk      # in target, arguments, working dir, icon
```

Nhìn vào `arguments`: nếu thấy `powershell -enc ...` hoặc `cmd /c ... & start ...` thì rõ là loader. Chuỗi trong đó lại thường base64, gỡ tiếp theo mục dưới.

## Script loader và gỡ obfuscation từng tầng

Dù đi qua macro, PDF hay LNK, điểm cuối gần như luôn là một script bị che nhiều tầng. Pattern hay gặp nhất là PowerShell với `-EncodedCommand` (hay `-enc`): tham số đằng sau là chuỗi UTF-16LE đã base64.

Nguyên tắc gỡ: **lột từng lớp, mỗi lớp decode rồi đọc, không bao giờ thực thi.** Các lớp hay gặp:

- `base64` (PowerShell encoded command dùng UTF-16LE, khác base64 thường).
- `gzip`/`deflate` nén bên trong base64.
- `XOR` với một khoá nhỏ.
- `-join`, `Reverse`, replace ký tự, format string.

Thấy `IEX` (Invoke-Expression), `DownloadString`, `DownloadFile`, `New-Object Net.WebClient`, `Start-BitsTransfer` là bạn đang tới gần URL payload. Thay `IEX` bằng `Write-Output` (hoặc chép sang Python) để in ra tầng tiếp theo thay vì chạy nó.

Ví dụ gỡ một tầng base64 UTF-16LE bằng Python (an toàn, chỉ in):

```python
import base64
enc = "VwByAGkAdABlAC0ASABvAHMAdAAg..."   # chuỗi sau -enc
print(base64.b64decode(enc).decode("utf-16-le"))
```

Nếu tầng trong lại là base64 + gzip:

```python
import base64, gzip
print(gzip.decompress(base64.b64decode(enc)).decode())
```

Lab [19.3](https://github.com/Haind03/Technique-Reverse/tree/main/labs/19.3) có chuỗi mẫu lành tính để bạn luyện đúng hai pattern này.

## Quy trình gọn

```
1. Nhận diện loại file (file, magic, phần mở rộng thật)
2. Trích phần thực thi:
     macro -> olevba        PDF -> pdf-parser/peepdf
     LNK   -> lnkparse      script -> mở bằng editor
3. Gỡ obfuscation từng tầng (decode, KHÔNG execute)
4. Tìm IOC tầng sau: URL, IP, tên file payload, mutex
5. Ghi IOC và viết rule phát hiện (YARA/Sigma, xem Bài 19.2)
```

Thứ bạn săn ở cuối chuỗi là URL tải payload và cách nó chạy payload đó. Có hai thứ này là đủ để chặn và truy vết, chưa cần đụng tới payload tầng sau.

## Checklist ghi nhớ
- Loader (maldoc/LNK/script) khác payload: nó chỉ kéo payload về, mổ nó là chặn từ gốc.
- Macro: olevba trích, tìm AutoOpen/Document_Open, chuỗi obfuscate, Shell/Run.
- PDF: pdf-parser/peepdf, soi /OpenAction, /JS, /Launch, giải stream FlateDecode.
- LNK: lnkparse đọc arguments, lệnh thật giấu ở đó.
- Script: gỡ từng tầng (base64 UTF-16LE, gzip, XOR), thay IEX bằng in ra, không chạy.
- Luôn làm trong lab cô lập, mục tiêu là lấy URL/IOC tầng sau.

## Cạm bẫy thường gặp
- Quên PowerShell `-enc` dùng UTF-16LE chứ không phải UTF-8, decode base64 thường ra chữ dính cách.
- Vô tình chạy script khi "thử cho nhanh", luôn thay execute bằng print.
- Dừng ở tầng đầu, nhiều loader lồng ba bốn tầng mới lộ URL.

## Đọc thêm
- Tài liệu oletools (decalage.info), didierstevens.com (pdf-parser, base64dump).
- CyberChef để gỡ nhanh nhiều tầng encode bằng giao diện kéo thả (bài [tài nguyên công cụ](/posts/tr-tai-nguyen-cong-cu/)).
