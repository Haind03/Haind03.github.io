---
title: "Bài 19.4: Trích config và C2, moi ra bộ não của malware"
date: 2026-10-06 09:58:00 +0700
categories: ["Technique Reverse", "Phần 19 · Phân tích mã độc cơ bản (phòng thủ)"]
tags: [reverse-engineering, malware]
render_with_liquid: false
---
Gần như mọi malware có khả năng điều khiển từ xa đều mang theo một mẩu config: địa chỉ server điều khiển (C2), port, khoá mã hoá, campaign id, tên mutex, danh sách lệnh. Trích được mẩu config đó là bạn cầm trong tay bản đồ hạ tầng của kẻ tấn công. Đây là một trong những việc có giá trị threat intel cao nhất mà người phân tích làm được, và nó dựa thẳng vào kỹ năng crypto ở Phần 16.

## Vì sao đáng công

Một C2 domain rút ra từ một mẫu không chỉ giúp bạn chặn đúng mẫu đó. Nó mở ra:

- **Detection diện rộng.** Viết rule chặn domain/IP đó bảo vệ cả tổ chức, không chỉ một máy.
- **Pivoting.** Từ một C2 lần ra các mẫu khác cùng hạ tầng, cùng campaign, cùng nhóm.
- **Takedown.** Báo domain/IP cho registrar hoặc nhà cung cấp để gỡ.
- **Phân loại họ malware.** Cấu trúc config thường đặc trưng cho từng family (Emotet, AgentTesla, Cobalt Strike...), nhận ra config là nhận ra họ.

Nói ngắn gọn: một hash chỉ nhận diện một file, một C2 nhận diện cả một chiến dịch.

## Config nằm ở đâu và vì sao không đọc thẳng được

Nếu malware để C2 domain dạng chuỗi trần trong binary thì `strings` đã moi ra, và mọi antivirus cũng vậy. Nên tác giả gần như luôn giấu nó. Các kiểu hay gặp:

- **Blob mã hoá** trong một section dữ liệu (thường XOR, RC4, AES, xem Phần 16), giải lúc chạy ngay trước khi dùng.
- **Nén** (zlib, LZ) rồi mới mã hoá.
- **Stack string** dựng từng ký tự bằng lệnh `mov` để tránh nằm liền thành chuỗi.
- **Resolve lúc chạy** từ một thuật toán (DGA, domain generation algorithm) thay vì lưu sẵn.

Điểm chung: trên đĩa config là một đống byte vô nghĩa, chỉ thành chuỗi đọc được trong bộ nhớ, trong khoảnh khắc ngắn trước khi malware dùng nó. Nhiệm vụ của bạn là lấy nó ra, bằng con đường tĩnh hoặc động.

## Ba con đường trích

### Con đường tĩnh: hiểu thuật toán rồi tự giải

Đây là cách sạch nhất và cho hiểu biết sâu nhất. Các bước:

1. **Tìm blob config.** Dấu hiệu: một vùng dữ liệu entropy cao hơn xung quanh, hoặc có magic/marker, hoặc được hàm khởi tạo trỏ tới. Nhiều family đặt một marker ngắn trước blob (ví dụ bốn byte nhận dạng).
2. **Tìm hàm giải mã.** Lần xref tới blob đó. Hàm chạm vào nó đầu tiên thường là decryptor. Đọc để nhận thuật toán: vòng lặp `xor` từng byte là XOR, mảng 256 byte hoán vị là RC4, S-box là AES (nhận diện theo Bài 16.1 tới 16.3).
3. **Lấy key.** Key có thể là hằng số ngay trong code, hoặc tính từ một chuỗi, hoặc nằm cạnh blob.
4. **Viết lại bằng Python.** Chép thuật toán và key sang Python rồi giải, đúng tinh thần Bài 16.2 và 16.4. Kết quả là config dạng đọc được.

Ưu điểm: không cần chạy mẫu, an toàn tuyệt đối, và script tái dùng được cho mọi mẫu cùng family. Một config extractor tốt là tài sản lâu dài.

### Con đường động: để malware tự giải rồi chộp

Khi thuật toán quá rối để giải tĩnh (nhiều lớp, obfuscated), hãy để chính malware làm việc nặng:

1. Chạy mẫu trong lab cô lập (Bài 0.3), dưới debugger.
2. Đặt breakpoint ngay **sau** hàm decrypt, hoặc tại hàm hay nhận config đã giải (ví dụ hàm kết nối mạng nhận domain làm tham số).
3. Khi dừng, đọc vùng bộ nhớ chứa config đã giải, dump ra.

Nhanh, không cần hiểu trọn thuật toán. Nhược điểm: phải chạy mẫu thật nên cần lab kín, và anti-debug/anti-VM (Phần 15) có thể cản.

### Con đường tự động: sandbox và config extractor

- **CAPE/CAPEv2** có sẵn config extractor cho rất nhiều họ malware phổ biến: nạp mẫu vào, nó tự unpack, tự giải và in config ra. Luôn thử trước khi làm tay.
- Khi gặp family chưa có extractor, bạn **viết một cái** (thường bằng Python, theo đúng con đường tĩnh ở trên) rồi đóng góp lại. Đây là cách cộng đồng mở rộng CAPE.

## Ví dụ quy trình trên một blob XOR rồi RC4

Giả sử bạn đã reverse và thấy decryptor làm hai tầng: RC4 với một khoá chuỗi, rồi XOR từng byte với một byte. Để giải, bạn làm ngược thứ tự tác giả mã hoá. Trong lab đi kèm, blob 157 byte bắt đầu bằng marker `CFG0` rồi tới độ dài 4 byte little-endian, rồi dữ liệu mã hoá. Extractor Python chạy thật cho ra:

```
[+] Config C2 trich duoc:
{
  "c2": ["cdn.example-fake.test", "203.0.113.45"],
  "port": 8443,
  "campaign": "DEMO-2024-01",
  "mutex": "Global\\FakeMwDemoMutex",
  "sleep": 60
}
```

Từ đống byte `43 46 47 30 95 00 00 00 f3 56 96 16 ...` thành một bộ IOC hoàn chỉnh. Đó là toàn bộ giá trị của bài này. (Config trong lab hoàn toàn bịa ra và vô hại, domain dùng dải TEST-NET không routable.)

## Hiểu luôn giao thức C2

Có config rồi, bước tiếp là hiểu malware **nói chuyện** với C2 ra sao: khung dữ liệu, mã hoá trên đường truyền, lệnh và phản hồi. Đây chính là reverse giao thức ở Bài 18.7, áp lên luồng mạng của malware. Hiểu giao thức cho phép viết detection mạng, thậm chí giả làm C2 để quan sát (sinkhole), hoặc giải mã traffic đã bắt được.

## Chia sẻ IOC có trách nhiệm

IOC rút ra nên được chia sẻ để cộng đồng cùng phòng thủ, nhưng đúng cách:

- Đăng lên nền tảng threat intel (MISP, VirusTotal, abuse.ch) với ngữ cảnh rõ ràng.
- Phân biệt C2 thật với domain hợp pháp bị lạm dụng (nhiều malware dùng dịch vụ cloud/CDN thật làm trung gian, chặn bừa là chặn nhầm dịch vụ lành).
- Không công bố thông tin giúp kẻ tấn công biết mình đã bị lộ quá sớm nếu đang có hoạt động takedown phối hợp.

Tinh thần giống disclosure có trách nhiệm ở Bài 0.2: chia sẻ để bảo vệ, không để khoe.

## Lab tự làm

Trong `labs/19.4/` có `build_sample.py` tạo một blob config C2 giả (vô hại) bị XOR rồi RC4, và `extractor.py` giải ngược ra config kèm danh sách IOC. Nhiệm vụ: chạy build rồi tự viết lại extractor từ đầu dựa trên việc đọc thuật toán, không chép sẵn. Chi tiết trong `labs/19.4/README.md`.

## Checklist ghi nhớ
- Config (C2, key, mutex, campaign) là mục tiêu threat intel giá trị nhất, một C2 nhận diện cả chiến dịch.
- Config thường bị mã hoá/nén trong binary, chỉ đọc được trong bộ nhớ lúc chạy.
- Ba con đường: tĩnh (hiểu thuật toán rồi giải bằng Python, sạch và tái dùng), động (dump sau khi malware tự giải), tự động (CAPE hoặc tự viết extractor).
- Nhận thuật toán giải mã theo Phần 16, lấy key, viết lại Python.
- Hiểu giao thức C2 theo Bài 18.7 để viết detection mạng.
- Chia sẻ IOC có trách nhiệm, phân biệt C2 thật với dịch vụ hợp pháp bị lạm dụng.
