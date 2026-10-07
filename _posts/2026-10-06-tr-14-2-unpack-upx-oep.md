---
title: "Bài 14.2: Unpack UPX, tự động và thủ công"
date: 2026-10-06 09:21:00 +0700
categories: ["Technique Reverse", "Phần 14 · Packer & Obfuscation"]
tags: [reverse-engineering, packer, obfuscation]
render_with_liquid: false
---
UPX là packer bạn gặp nhiều nhất, và cũng là nơi tốt nhất để học quy trình unpack thủ công vì nó đơn giản, mã nguồn mở, không có anti-debug. Hiểu UPX là hiểu khung sườn của mọi packer: một đoạn code nhỏ (stub) giải nén phần code thật vào bộ nhớ rồi nhảy tới điểm vào gốc. Bài này đi từ cách lười nhất (một dòng lệnh) tới cách phải tự tay làm khi packer chống lại bạn.

## Packer làm gì, nói lại cho gọn

Một file đã pack gồm hai phần: dữ liệu nén (code gốc của bạn, đã bị nén lại nên không đọc được) và một stub giải nén đặt ở entry point. Khi chạy, stub bung phần nén ra bộ nhớ, dựng lại bảng import, rồi nhảy về OEP (Original Entry Point, điểm vào thật của chương trình gốc). Từ OEP trở đi chính là chương trình ban đầu đang chạy.

Mục tiêu của unpack: bắt đúng khoảnh khắc stub vừa bung xong và sắp nhảy về OEP, rồi chụp lại (dump) bộ nhớ lúc đó. Bản dump đó là code gốc.

## Cách lười: upx -d

Nếu file được pack bằng UPX chuẩn và chưa ai đụng vào, chỉ cần:

```
upx -d -o output.exe packed.exe
```

UPX tự nhận ra định dạng của chính nó và bung ngược lại. Đây là trường hợp đẹp nhất và cũng là lý do UPX một mình nó không phải biện pháp bảo vệ nghiêm túc: ai cũng gỡ được trong một giây.

Một phiên làm việc thật trên Linux để bạn thấy con số:

```
$ gcc -O2 -static -o hello_s hello.c      # 900368 byte
$ upx --best -o hello_s.upx hello_s
   900368 ->    352616   39.16%   linux/amd64   hello_s.upx
$ upx -d -o hello_s.unp hello_s.upx
Unpacked 1 file.
$ ./hello_s.unp UPX_s3cr3t
Correct!
```

Nén còn 39% kích thước, và bản giải nén chạy y hệt bản gốc. Xong.

## Khi upx -d từ chối

Vấn đề là kẻ đóng gói biết tới `upx -d`. Mẹo chống phổ biến nhất: sửa vài byte trong header để UPX không nhận ra file của chính nó nữa. UPX đánh dấu các khối của nó bằng magic bốn byte `UPX!`. Chỉ cần đổi các dấu này đi, `upx -d` sẽ bó tay, nhưng stub vẫn chạy bình thường vì nó không dựa vào magic đó để giải nén.

Vẫn phiên làm việc trên, sau khi đổi cả bốn dấu `UPX!` thành rác:

```
$ upx -d -o out hello_s.broken
upx: hello_s.broken: NotPackedException: not packed by UPX
Unpacked 0 files.
$ ./hello_s.broken UPX_s3cr3t
Correct!
```

UPX nói "không phải file do UPX đóng gói", nhưng file vẫn chạy ra "Correct!". Đây chính là lúc bạn phải tự unpack. Tin tốt: dù header bị sửa, cơ chế giải nén không đổi, nên kỹ thuật thủ công vẫn hiệu quả.

## Giải phẫu stub UPX

Stub UPX trên Windows bắt đầu bằng một thao tác rất đặc trưng: nó lưu toàn bộ thanh ghi, làm việc giải nén, rồi khôi phục thanh ghi trước khi nhảy về OEP.

```asm
pushad                    ; lưu tất cả thanh ghi lên stack
mov  esi, <địa chỉ nguồn> ; nguồn: dữ liệu nén
mov  edi, <địa chỉ đích>  ; đích: nơi đặt code đã giải nén
...                       ; vòng lặp giải nén
popad                     ; khôi phục tất cả thanh ghi
jmp  <OEP>                ; tail jump: nhảy về điểm vào gốc
```

Hai chi tiết vàng ở đây:
- `pushad` đẩy 8 thanh ghi lên stack cùng lúc. Ngay sau `pushad`, con trỏ stack (ESP) trỏ vào khối vừa lưu.
- Cuối stub là `popad` rồi một `jmp` nhảy xa, gọi là tail jump, đưa thẳng về OEP.

Hai chi tiết này cho ta hai cách tìm OEP.

## Cách 1: ESP trick (stack restore)

Đây là kỹ thuật kinh điển, nhanh và gần như luôn hiệu quả với UPX.

Ý tưởng: `pushad` ghi 8 thanh ghi vào stack, `popad` sẽ đọc lại đúng vùng đó. Nếu bạn đặt một hardware breakpoint theo dõi việc đọc vùng stack mà `pushad` vừa ghi, thì breakpoint đó bật đúng lúc `popad` chạy, tức là ngay trước tail jump về OEP.

Các bước trong x64dbg (32-bit thì x32dbg):
1. Mở file trong debugger, nó dừng ở entry point (chính là đầu stub).
2. Bước qua lệnh `pushad` đầu tiên (F8 một lần).
3. Nhìn vào thanh ghi ESP, nó vừa giảm đi sau pushad. Nhấn chuột phải vào ESP, chọn "Follow in Dump".
4. Trong cửa sổ Dump, chọn 4 byte đầu, chuột phải, Breakpoint, Hardware, Access.
5. Nhấn F9 (Run). Debugger sẽ dừng khi `popad` đọc lại vùng đó.
6. Lúc này bạn đang ở ngay trước tail jump. Bước vài lệnh (F8) tới khi thấy một `jmp` nhảy tới một địa chỉ xa, khác hẳn vùng stub. Đó là tail jump.
7. Bước qua tail jump. Bạn đã ở OEP.

Khi tới OEP, code trông "sạch": một prologue hàm bình thường (hoặc với chương trình thật là CRT startup, xem [Bài 3.1](/posts/tr-3-1-hello-world-tim-main-that/)), không còn giống stub nén nữa.

## Cách 2: tìm tail jump trực tiếp

Nếu quen mắt, bạn có thể cuộn xuống cuối stub tìm luôn cặp `popad` + `jmp xa`. Đặt breakpoint tại tail jump đó, chạy tới, rồi bước qua. Cách này nhanh nhưng cần biết mặt stub. ESP trick an toàn hơn cho người mới.

## Cách 3: breakpoint trên section gốc

Một hướng khác: section chứa code gốc ban đầu rỗng (vì code nằm ở dạng nén). Đặt memory breakpoint "execute" trên section đó. Khi stub giải nén xong và CPU bắt đầu chạy code trong section gốc, breakpoint bật, và bạn đang ở gần OEP. Hữu ích khi stub phức tạp làm ESP trick khó.

## Tới OEP rồi, giờ dump

Tới OEP mới xong một nửa. Code đã giải nén nằm trong bộ nhớ, nhưng bạn cần lưu nó thành một file chạy được. Đây là việc của Scylla (thường đi kèm x64dbg dưới dạng plugin):

1. Mở Scylla, chọn đúng tiến trình đang debug.
2. Đặt OEP bạn vừa tìm được vào ô OEP.
3. Nhấn "IAT Autosearch" rồi "Get Imports": Scylla dò và dựng lại bảng import (vì stub đã resolve import trong bộ nhớ, nhưng file dump thô chưa có bảng import đúng).
4. "Dump" để lưu bộ nhớ ra file.
5. "Fix Dump" để vá bảng import vào file vừa dump.

Chi tiết phần rebuild IAT, vì sao cần nó và các cạm bẫy, nằm ở [Bài 14.3](/posts/tr-14-3-dump-rebuild-iat-scylla/). Không rebuild IAT thì file dump mở được trong IDA để đọc tĩnh nhưng thường không chạy được.

## Khi nào UPX không còn là UPX

Cẩn thận: nhiều packer và malware dùng UPX làm lớp ngoài rồi bọc thêm lớp bảo vệ riêng, hoặc sửa stub nặng tới mức không còn pushad/popad chuẩn. Lúc đó ESP trick có thể trượt. Nguyên tắc chung vẫn đúng (chạy stub, tìm OEP, dump), nhưng cách tìm OEP phải linh hoạt. UPX chỉ là bài tập nhập môn cho tư duy unpack áp dụng được cho mọi packer.

## Checklist ghi nhớ
- Thử `upx -d` trước, nhiều khi xong ngay.
- Nếu header bị sửa (đổi magic `UPX!`), `upx -d` báo NotPackedException nhưng file vẫn chạy, phải unpack thủ công.
- Stub UPX: `pushad` đầu, `popad` + tail jump cuối. Đó là hai mốc để tìm OEP.
- ESP trick: hardware breakpoint trên stack ngay sau `pushad`, bật lại khi `popad` chạy, gần tail jump.
- Tới OEP thì dump bằng Scylla và rebuild IAT (Bài 14.3).
- UPX là bài nhập môn, tư duy này áp dụng cho mọi packer.

## Lab tự làm
Thư mục [labs/14.2/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/14.2) có chương trình mẫu, lệnh pack, và cách tự tay làm header hỏng để luyện unpack thủ công. Writeup đầy đủ với số liệu thật trong [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/14.2/solution.md).
