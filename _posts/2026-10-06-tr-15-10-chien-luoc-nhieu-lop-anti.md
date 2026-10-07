---
title: "Bài 15.10: Khi nhiều lớp anti chồng lên nhau, đánh thế nào"
date: 2026-10-06 09:35:00 +0700
categories: ["Technique Reverse", "Phần 15 · Anti-Reverse chuyên sâu và cách vượt qua"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
Chín bài trước mỗi bài mổ một kỹ thuật anti riêng lẻ. Thực tế phũ phàng hơn: một mẫu malware hay một protector thương mại không bao giờ dùng đúng một chiêu. Nó chồng lớp. Một mẫu điển hình có thể là UPX hoặc packer tuỳ biến ở ngoài, anti-debug đặt trong TLS callback chạy trước cả main, anti-VM gọi CPUID ngay khi vào, một integrity check tự băm code section, và phần lõi thì bị virtualize. Bạn gỡ xong lớp này lại đụng lớp khác. Bài này không dạy thêm chiêu mới, nó dạy thứ tự và tư duy để không chết đuối.

## Nguyên tắc số một: bóc từ ngoài vào trong

Các lớp anti xếp theo thời điểm chạy, và bạn phải tôn trọng thứ tự đó. Thứ chạy sớm nhất phải xử lý đầu tiên, vì nếu không bạn còn chẳng tới được chỗ có lớp sau.

Thứ tự thời gian chạy điển hình:

```
1. Packer stub          (chạy đầu tiên, giải nén code thật)
2. TLS callback         (chạy trước entry point, hay giấu anti-debug ở đây)
3. Entry point / CRT
4. Anti-VM, anti-sandbox (ngay khi vào main)
5. Anti-debug API + PEB  (rải khắp)
6. Integrity check       (định kỳ hoặc trước đoạn nhạy cảm)
7. Virtualized core      (lõi logic được bảo vệ nặng nhất)
```

Sai lầm kinh điển của người mới là lao thẳng vào lõi logic trong khi packer còn chưa gỡ, nên đọc toàn rác. Cứ bóc tuần tự: unpack trước (Bài 14.2, 14.3), rồi lo anti-debug, rồi mới tới logic.

## Dựng môi trường một lần cho tử tế

Trước khi đụng mẫu nhiều lớp, bỏ công dựng môi trường để không phải đánh nhau với từng check lẻ:

- VM trông giống máy thật: đủ nhân CPU và RAM, có file người dùng, đổi tên máy, gỡ bớt artefact VM dễ lộ (Bài 15.5).
- ScyllaHide (user mode) cắm vào x64dbg để nuốt gọn phần lớn anti-debug API và PEB cùng lúc, đỡ phải patch tay từng cái (Bài 15.9).
- TitanHide hoặc HyperHide khi ScyllaHide không đủ, vì chúng ẩn ở tầng sâu hơn.
- Bật tuỳ chọn dừng ở TLS callback và system breakpoint trong x64dbg, để attach đủ sớm trước khi anti-debug trong TLS kịp chạy (Bài 15.4).

Dựng một lần, snapshot lại, dùng cho mọi mẫu về sau.

## Khi static bị chặn, chuyển sang dynamic

Anti-disassembly (Bài 15.6) và virtualization (Bài 14.5) làm disassembler tĩnh vô dụng hoặc sai. Lúc đó đừng cố đọc tĩnh cho bằng được. Chạy động và quan sát: giá trị thật lộ ra trong thanh ghi, chuỗi giải mã hiện trong bộ nhớ, luồng thật thấy rõ khi single-step. Nhiều lớp anti được thiết kế để đánh người đọc tĩnh, và sập ngay khi bạn cho chạy rồi nhìn.

## Chia để trị: cô lập từng check

Đừng cố vượt mọi lớp cùng lúc. Với mỗi check, làm đủ ba việc: tìm ra nó, hiểu nó quyết định điều gì, vô hiệu đúng điểm quyết định đó. Thường điểm quyết định là một lệnh rẽ nhánh (`cmp` rồi `je/jne`) sau khi check chạy xong. Patch đúng nhánh đó, hoặc sửa giá trị thanh ghi lúc chạy, là qua, mà không cần hiểu trọn vẹn cơ chế check.

Với integrity check (Bài 15.8), nhớ bài học ngược đời: đừng sửa code bị kiểm, hãy vô hiệu chính hàm kiểm. Sửa code là tự châm ngòi.

## Vũ khí hạng nặng: emulation bỏ qua cả đống anti

Đây là ý quan trọng nhất của bài. Rất nhiều anti-debug dựa vào việc có một debugger thật và một hệ điều hành thật: PEB.BeingDebugged, NtQueryInformationProcess, timing RDTSC, hardware breakpoint. Nếu bạn không dùng debugger thật mà **emulate** đoạn code bằng Unicorn hoặc Qiling (Bài 18.2), toàn bộ nhóm anti-debug đó trở nên vô nghĩa, vì không có debugger nào để phát hiện, và bạn kiểm soát mọi giá trị trả về của mọi API.

Emulation hợp nhất khi bạn cần chạy một hàm tách biệt (ví dụ routine giải mã chuỗi, hàm sinh serial) mà không muốn kéo theo cả bộ máy anti-debug của chương trình. Cô lập hàm, nạp vào emulator, cho input, lấy output.

## Khi nào ngừng gỡ và tiếp cận hộp đen

Không phải lúc nào cũng cần hiểu mọi lớp. Nếu mục tiêu của bạn chỉ là "input nào làm nó in Correct", nhiều khi không cần devirtualize cái lõi VProtect làm gì cho mệt. Tiếp cận hộp đen: coi phần được bảo vệ như một cái hộp, chỉ quan sát quan hệ input và output, hoặc dùng symbolic execution (Bài 18.3) để solver tự tìm input thoả điều kiện ở đầu ra. Virtualization bảo vệ cách tính, nhưng thường không giấu được điều kiện cuối cùng phải đúng.

Luôn hỏi lại câu hỏi gốc (Bài 0.4): tôi thật sự cần biết gì? Trả lời được thì biết lớp nào đáng gỡ, lớp nào bỏ qua.

## Ghi chép, nếu không bạn sẽ gỡ lại từ đầu

Mẫu nhiều lớp có thể ngốn nhiều ngày. Ghi lại từng lớp đã nhận ra, địa chỉ của từng check, cái gì đã vô hiệu và vô hiệu bằng cách nào. Một bảng đơn giản "lớp, địa chỉ, cách vượt" tiết kiệm cho bạn hàng giờ khi phải chạy lại hoặc khi mẫu reset sau một lần sai.

## Một thứ tự mẫu để bám theo

```
1. Triage (DIE, strings, entropy): nhận ra lớp ngoài cùng là gì
2. Dựng môi trường: VM giống thật + ScyllaHide + attach sớm
3. Unpack: tới OEP, dump, rebuild IAT
4. Trung hoà anti-debug/anti-VM: ScyllaHide lo phần lớn, patch phần còn lại
5. Vô hiệu integrity check (vô hiệu hàm check, không sửa code bị kiểm)
6. Với lõi virtualized: cân nhắc hộp đen / symbolic / emulation thay vì devirtualize trọn
7. Ghi chép mọi bước
```

Không có mẫu nào giống hệt mẫu nào, nhưng khung này giữ bạn đi đúng hướng thay vì loay hoay.

## Checklist ghi nhớ
- Bóc lớp theo thứ tự thời gian chạy: packer, TLS, anti-VM, anti-debug, integrity, lõi.
- Dựng môi trường một lần cho chuẩn (VM thật + ScyllaHide + attach sớm) rồi snapshot.
- Static bị chặn thì chuyển dynamic, đừng cố đọc tĩnh cái đã bị anti-disasm.
- Cô lập từng check, vô hiệu đúng điểm quyết định, không ôm đồm.
- Emulation (Unicorn/Qiling) vô hiệu hoá cả nhóm anti-debug vì không có debugger thật.
- Biết khi nào chuyển sang hộp đen hoặc symbolic thay vì gỡ trọn.
- Ghi chép từng lớp, nếu không sẽ phải làm lại từ đầu.
