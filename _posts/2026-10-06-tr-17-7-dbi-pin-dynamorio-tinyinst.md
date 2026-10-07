---
title: "Bài 17.7: Dynamic Binary Instrumentation, cho binary tự kể nó chạy những đâu"
date: 2026-10-06 09:46:00 +0700
categories: ["Technique Reverse", "Phần 17 · Patch, Hook, Injection & Instrumentation"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
Debugger cho bạn dừng và soi từng điểm. Frida cho bạn hook vài hàm. Nhưng khi bạn muốn hỏi một câu kiểu "trong lần chạy này, chương trình đã thực thi đúng những lệnh nào", hoặc "nhập sai với nhập đúng thì luồng khác nhau ở chỗ nào", thì cả hai đều đuối. Đó là lúc cần Dynamic Binary Instrumentation (DBI).

## DBI là gì

DBI là kỹ thuật chèn mã phân tích (instrumentation) vào luồng thực thi của một binary ngay lúc nó chạy, mà không cần source code và không sửa file trên đĩa. Công cụ DBI đọc từng basic block sắp chạy, dịch lại nó kèm theo các đoạn code quan sát của bạn, rồi mới cho CPU chạy bản đã chèn.

Nói cách khác, bạn viết một đoạn kiểu "mỗi khi có một lệnh chạy, cộng biến đếm lên một", hoặc "mỗi khi ghi vào bộ nhớ, ghi lại địa chỉ", và công cụ DBI gắn đoạn đó vào mọi lệnh/mọi lần ghi của chương trình đích. Chương trình không hề biết mình đang bị quan sát ở mức này.

Khác biệt với các công cụ đã học:

| Công cụ | Mức can thiệp | Hợp khi |
|---|---|---|
| Debugger (x64dbg) | dừng tại breakpoint, thủ công | soi sâu một điểm |
| Frida ([Bài 17.2](/posts/tr-17-2-frida-toan-tap/)) | hook ở mức hàm | đọc/sửa tham số, quan sát API |
| DBI (Pin, DynamoRIO...) | ở mức từng lệnh/block, toàn chương trình | coverage, trace diện rộng, taint |

DBI nặng hơn Frida (chạy chậm hơn nhiều vì dịch lại mọi block) nhưng chi tiết hơn hẳn: nó thấy từng lệnh, không chỉ ranh giới hàm.

## Bốn công cụ hay dùng

- **Intel Pin.** Lâu đời, mạnh, miễn phí (không mã nguồn mở). Bạn viết một pintool bằng C++, đăng ký callback cho từng lệnh (INS), từng block (BBL), từng ảnh được nạp (IMG). Dùng nhiều cho instruction count, memory trace, và taint analysis.
- **DynamoRIO.** Mã nguồn mở, kiến trúc client, API gọn. Có sẵn các tool mẫu như drcov (lấy coverage) và drltrace (trace lời gọi thư viện). Nhiều người thích vì mở và nhanh hơn Pin trong một số tác vụ.
- **QBDI** (QuarksLab). DBI nhúng được vào chương trình khác, API Python và C++ đẹp, hợp để viết script phân tích nhanh thay vì dựng cả một pintool.
- **TinyInst.** Nhẹ, thiên về coverage cho fuzzing, không dịch lại toàn bộ như Pin/DynamoRIO mà chỉ instrument chỗ cần, nên nhanh và ổn định với binary lớn trên Windows/macOS.

Người mới nên bắt đầu với một tool có sẵn (drcov của DynamoRIO) trước khi tự viết pintool.

## Ứng dụng đắt giá nhất: coverage diffing

Đây là chiêu khiến DBI đáng học. Ý tưởng rất đơn giản nhưng mạnh:

1. Chạy chương trình với một input **sai**, lấy tập các basic block đã thực thi (coverage A).
2. Chạy lại với một input **gần đúng** hoặc **đúng**, lấy coverage B.
3. So sánh. Những block chỉ xuất hiện ở B mà không có ở A chính là code chạy khi bạn đi sâu hơn vào logic kiểm tra.

Với một crackme, cách này khoanh vùng hàm kiểm tra serial mà không cần đọc hiểu trước gì cả: bạn để chương trình tự chỉ cho bạn chỗ nó rẽ hướng khi input tốt hơn. Kết hợp coverage với fuzzing là nền của fuzzing hiện đại (AFL dùng chính ý tưởng coverage để dẫn đường).

Các ứng dụng khác:

- **Instruction count / trace thực thi.** Hiểu một hàm obfuscated làm gì bằng cách nhìn chuỗi lệnh thật sự chạy, bỏ qua junk code không bao giờ thực thi (hữu ích với anti-disassembly ở [Bài 15.6](/posts/tr-15-6-anti-disassembly/)).
- **Memory trace.** Ghi lại mọi lần đọc/ghi bộ nhớ để lần theo một giá trị đi đâu.
- **Taint analysis.** Đánh dấu input là "bẩn" rồi theo dõi nó lan qua các thanh ghi và ô nhớ, thấy input ảnh hưởng tới quyết định nào.

## DBI và anti-debug

Một điểm thú vị: nhiều kỹ thuật anti-debug ở Phần 15 nhắm vào debugger (kiểm tra PEB, debug port, breakpoint 0xCC). DBI không dùng debugger và không đặt breakpoint 0xCC, nên một phần các check đó không bắt được nó. Tuy vậy DBI để lại dấu vết riêng (thời gian chạy chậm bất thường, vùng code dịch lại, một số artefact của Pin/DynamoRIO), nên malware tinh vi có cả anti-DBI. Nó không phải viên đạn bạc, nhưng là một góc tiếp cận khác khi debugger bị chặn.

## Khi nào dùng DBI

Dùng khi câu hỏi của bạn mang tính "toàn cục và định lượng": coverage, đếm, trace diện rộng, taint. Đừng dùng khi bạn chỉ cần soi một hàm (debugger nhanh hơn) hay hook vài API (Frida nhẹ hơn). DBI đổi tốc độ lấy tầm nhìn: chương trình chạy chậm đi nhiều lần, bù lại bạn thấy mọi thứ.

## Lab tự làm

Xem [labs/17.7/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/17.7): dùng một DBI tool lấy coverage của một chương trình với input đúng và input sai, rồi so sánh để tự khoanh vùng hàm kiểm tra.

## Checklist ghi nhớ
- DBI chèn mã quan sát vào từng lệnh/block lúc chạy, không cần source, không sửa file đĩa.
- Pin (C++, mạnh), DynamoRIO (mã nguồn mở, có drcov sẵn), QBDI (nhúng, API đẹp), TinyInst (nhẹ cho coverage/fuzzing).
- Chiêu mạnh nhất: coverage diffing giữa input sai và đúng để tìm hàm kiểm tra.
- Nặng hơn Frida nhưng chi tiết tới từng lệnh; dùng cho câu hỏi toàn cục, không phải soi điểm.
- Né được một phần anti-debug (không dùng debugger, không 0xCC) nhưng có anti-DBI riêng.
