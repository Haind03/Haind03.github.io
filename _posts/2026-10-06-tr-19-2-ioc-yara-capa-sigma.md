---
title: "Bài 19.2: IOC, YARA, capa và Sigma, biến một mẫu thành thứ phát hiện được"
date: 2026-10-06 09:56:00 +0700
categories: ["Technique Reverse", "Phần 19 · Phân tích mã độc cơ bản (phòng thủ)"]
tags: [reverse-engineering, malware]
render_with_liquid: false
---
Phân tích xong một mẫu malware mà để đó thì phí. Giá trị thật của việc reverse một mẫu là rút ra được thứ giúp bạn (và cả cộng đồng) nhận ra nó lần sau, nhận ra biến thể của nó, và nhận ra nó đang chạy trong hệ thống. Bài này nói về bốn thứ đó: IOC để chia sẻ dấu hiệu, YARA để quét file và bộ nhớ, capa để lập hồ sơ khả năng, Sigma để bắt hành vi trong log. Tất cả đều là công cụ phòng thủ.

## IOC: dấu hiệu để chia sẻ

IOC (Indicator of Compromise) là những mẩu dữ liệu cụ thể chỉ ra một hệ thống có thể đã bị xâm nhập. Khi phân tích một mẫu, bạn nhặt ra:

- **Hash** của file: MD5, SHA-1, SHA-256. Đây là IOC yếu nhất vì chỉ cần đổi một byte là hash khác, nhưng vẫn cần để tra cứu và chia sẻ.
- **Network**: IP, domain, URL của server điều khiển (C2), đường dẫn tải payload.
- **Host**: tên mutex (malware hay tạo mutex để không chạy trùng, xem lại Bài 1.11), tên file nó thả ra, khoá registry nó tạo để persistence, tên scheduled task.
- **Email**: địa chỉ gửi, tiêu đề, tên file đính kèm (với phishing).

IOC được chuẩn hoá để trao đổi tự động, phổ biến nhất là STIX (Structured Threat Information eXpression). Nhưng hãy nhớ: IOC là loại chỉ dấu dễ né nhất. Kẻ tấn công đổi domain, đổi hash trong vài giây. Thứ bền hơn nằm ở dưới.

## YARA: quét theo pattern

YARA là ngôn ngữ viết rule nhận diện file (và cả bộ nhớ tiến trình) theo mẫu byte và chuỗi. Nó bền hơn hash vì bắt vào những thứ kẻ tấn công khó đổi: chuỗi đặc trưng, đoạn code, hằng số thuật toán.

Một rule gồm hai phần chính: `strings` khai báo các mẫu cần tìm, `condition` nói khi nào thì coi là khớp.

```yara
rule FakeBot_Demo
{
    meta:
        description = "Nhan dien mau FakeBot gia lap"
        author = "blog"

    strings:
        $mutex = "Global\\FakeBot_Mutex_v1" ascii
        $c2    = "http://c2.example-fakebot.test/gate.php" ascii
        $key   = { 52 43 34 4B 65 79 31 32 33 }   // byte pattern "RC4Key123"

    condition:
        uint16(0) == 0x5A4D and          // 0x5A4D = "MZ", chi quet file PE
        2 of them                        // khop it nhat 2 trong cac string tren
}
```

Vài điều đáng nhớ khi viết rule:

- Chuỗi có thể là text (`ascii`, `wide` cho UTF-16, `nocase` không phân biệt hoa thường) hoặc **byte pattern** trong ngoặc nhọn, dùng được cho đoạn code hoặc hằng số. Byte pattern cho phép wildcard `??` (một byte bất kỳ) nên bắt được code dù vài byte thay đổi.
- `condition` là nơi đặt logic: `uint16(0) == 0x5A4D` lọc trước chỉ file PE, `2 of them` hay `3 of ($a, $b, $c)` cho phép khớp mềm, `$a at 0` buộc chuỗi ở offset cụ thể.
- Rule tốt là rule **đủ cụ thể để không báo nhầm file lành, đủ rộng để bắt biến thể**. Dựa vào 1 chuỗi dễ false positive hoặc dễ né; dựa vào tổ hợp vài dấu hiệu đặc trưng thì vừa.

YARA quét được cả file tĩnh lẫn bộ nhớ tiến trình đang chạy, nên rất hợp để bắt malware đã unpack trong RAM (nối lại Bài 14 và 17.5). **yarGen** sinh rule tự động từ một tập mẫu (nó loại các chuỗi phổ biến trong file sạch rồi giữ lại chuỗi hiếm), là điểm khởi đầu tốt rồi bạn tinh chỉnh tay.

## capa: hỏi "nó làm được gì"

Trong khi YARA hỏi "đây có phải mẫu X không", capa (Mandiant) hỏi một câu khác: "binary này có những **khả năng** gì". Nó chạy một bộ rule mô tả hành vi dựa trên API, chuỗi, hằng số, và trả về những câu như:

- "communicate over HTTP"
- "encrypt data using RC4"
- "inject code into another process"
- "persist via registry run key"

capa cực hữu ích ở bước triage: chưa cần đọc code, bạn đã có bản tóm tắt binary làm gì, biết chỗ nào đáng đọc trước. Nó còn map sang MITRE ATT&CK để bạn nói chuyện cùng ngôn ngữ với đội phòng thủ. Kết hợp đẹp với [capa trong triage ở Bài 2.1](/posts/tr-2-1-triage-die-strings-pebear/).

## Sigma: bắt hành vi trong log

YARA và capa nhìn vào file. Sigma nhìn vào **log**. Nó là định dạng rule chung cho SIEM và log hệ thống (Windows Event Log, Sysmon, EDR): mô tả một hành vi đáng ngờ theo cách không phụ thuộc hãng SIEM nào, rồi convert sang truy vấn của Splunk, Elastic, Sentinel...

Ví dụ một ý tưởng Sigma: "process `winword.exe` sinh ra `powershell.exe`" là mẫu macro độc điển hình. Hay "có process ghi vào vùng nhớ của process khác rồi tạo remote thread" (nối lại dấu hiệu injection ở [Bài 17.4/17.5](https://github.com/Haind03/Technique-Reverse/tree/main/phan-17-patch-hook-frida)). Sigma bắt được những thứ YARA không thấy, vì nó theo dõi **hành vi lúc chạy** chứ không phải nội dung file.

Bốn công cụ, bốn tầng: IOC (dữ liệu cụ thể, dễ né), YARA (nội dung file/bộ nhớ), capa (khả năng), Sigma (hành vi). Càng xuống dưới càng khó né, vì kẻ tấn công đổi domain thì dễ, đổi hẳn cách hành xử thì tốn công.

## Quy trình thực tế

Sau khi reverse một mẫu, bạn thường làm theo mạch này:

1. Tính hash, nhặt network/host IOC (domain, mutex, registry, file thả ra).
2. Chạy capa để có hồ sơ khả năng, biết nó inject/mã hoá/persist ra sao.
3. Viết YARA rule dựa trên tổ hợp chuỗi và byte pattern đặc trưng (ưu tiên thứ khó đổi), test với cả mẫu và một bộ file sạch để tránh false positive.
4. Viết Sigma rule cho hành vi quan sát được (process tree, ghi registry, network), để đội SOC phát hiện cả khi hash đã đổi.
5. Chia sẻ IOC/YARA/Sigma cho cộng đồng hoặc nội bộ.

## Lab tự làm

Tới `labs/19.2/`. Bạn sẽ viết một YARA rule, tạo một file mẫu lành tính chứa các chuỗi marker, rồi chạy `yara` (hoặc `yara-python`) để thấy rule khớp đúng chuỗi nào ở offset nào. Rule mẫu và kết quả chạy thật có trong `solution.md`.

## Checklist ghi nhớ

- IOC = dấu hiệu cụ thể (hash, domain, mutex, registry), dễ chia sẻ nhưng dễ né nhất.
- YARA quét file và bộ nhớ theo `strings` + `condition`, dùng byte pattern để bắt cả biến thể.
- Rule tốt dựa trên tổ hợp dấu hiệu khó đổi, test với file sạch để tránh false positive.
- capa trả lời "binary làm được gì" và map sang ATT&CK, tuyệt cho triage.
- Sigma bắt hành vi trong log, khó né hơn vì theo dõi lúc chạy.
- Thang độ bền: IOC < YARA < capa < Sigma.
