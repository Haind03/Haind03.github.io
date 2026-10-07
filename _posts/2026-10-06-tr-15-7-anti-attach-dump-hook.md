---
title: "Bài 15.7: Anti-attach, anti-dump, anti-hook, ba lớp chống công cụ của bạn"
date: 2026-10-06 09:32:00 +0700
categories: ["Technique Reverse", "Phần 15 · Anti-Reverse chuyên sâu và cách vượt qua"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
Ba bài trước nói về anti-debug: làm sao chương trình biết nó đang bị debug. Bài này đi một bước xa hơn, về những thủ thuật nhắm thẳng vào ba thao tác cụ thể bạn hay làm: attach debugger vào một tiến trình đang chạy, dump bộ nhớ ra file, và hook API. Mỗi thứ chặn một công cụ khác nhau, nên hiểu riêng từng cái mới gỡ đúng.

Như mọi bài trong phần này, góc nhìn ở đây là của người phân tích: hiểu cơ chế để nhận ra và vượt qua khi gặp trong mẫu của mình, chứ không phải để đi gài vào phần mềm người khác.

## Anti-attach: khóa cửa sau khi vào nhà

Bình thường bạn có hai cách đưa debugger vào một chương trình: chạy nó từ debugger ngay từ đầu (spawn), hoặc để nó chạy rồi mới attach vào sau. Anti-attach nhắm vào cách thứ hai.

Mẹo kinh điển nhất dựa trên một giới hạn của Windows: **một tiến trình chỉ có đúng một debugger tại một thời điểm.** Nếu chương trình tự debug chính nó (hoặc đẻ ra một tiến trình con rồi để con debug lại cha), thì cái slot debugger đã bị chiếm. Debugger thật của bạn attach vào sẽ bị từ chối với lỗi kiểu "a debugger is already attached". Kỹ thuật self-debugging này đã nói ở [Bài 15.4](/posts/tr-15-4-anti-debug-selfdebug-tls/), ở đây nó phục vụ mục đích anti-attach.

Cách thứ hai tinh hơn: khi Windows attach một debugger, nó gọi `DbgUiRemoteBreakin` trong `ntdll` để tạo thread breakin trong tiến trình đích. Chương trình chỉ cần vá hàm này (ghi đè đầu hàm bằng một lời gọi `ExitProcess` hoặc một `ret` làm hỏng logic) là mỗi lần có ai cố attach, tiến trình tự thoát thay vì dừng lại cho bạn. Tương tự với `DbgBreakPoint`.

Cách thứ ba đơn giản mà phiền: **kiểm tra định kỳ.** Một thread chạy nền cứ vài giây lại chạy lại toàn bộ các check anti-debug ở ba bài trước (BeingDebugged, NtQueryInformationProcess...). Bạn attach sạch sẽ xong, vài giây sau nó phát hiện và thoát.

Cách vượt chung cho anti-attach:
- **Attach sớm, hoặc đừng attach.** Nếu có thể, chạy chương trình thẳng từ debugger ngay từ đầu (spawn) thay vì attach sau. Lúc đó slot debugger là của bạn trước khi code anti-attach kịp chạy.
- **Vô hiệu hóa vòng kiểm tra định kỳ.** Tìm thread làm việc đó, patch hàm check trả về "không có debugger", hoặc dùng ScyllaHide/TitanHide che luôn (xem [Bài 15.9](https://github.com/Haind03/Technique-Reverse/blob/main/phan-15-anti-reverse/15.9-vuot-qua-scyllahide-titanhide.md)).
- **Khôi phục `DbgUiRemoteBreakin`** về nguyên bản trong bộ nhớ trước khi attach, nếu nó bị vá.

## Anti-dump: làm cho bản dump thành rác

Khi bạn unpack một mẫu bằng cách chạy tới OEP rồi dump bộ nhớ (quy trình ở [Bài 14.3](/posts/tr-14-3-dump-rebuild-iat-scylla/)), tool dump như Scylla đọc PE header trong bộ nhớ để biết section nằm đâu, kích thước bao nhiêu, dựng lại file. Anti-dump phá chính cái header đó.

Những chiêu hay gặp:
- **Xóa chữ ký MZ và PE.** Sau khi loader đã nạp xong và không cần header nữa, chương trình ghi đè hai byte `4D 5A` ("MZ") ở đầu và chữ ký `50 45` ("PE") bằng số 0 hoặc rác. Tool dump quét bộ nhớ không còn thấy một PE hợp lệ để bám vào.
- **Làm sai SizeOfImage.** Sửa trường `SizeOfImage` trong Optional Header thành một giá trị khổng lồ hoặc quá nhỏ. Tool dump tin theo rồi dump thiếu hoặc dump tràn sang vùng rác.
- **Bôi bẩn section table.** Sửa số section, địa chỉ ảo, kích thước thô của các section để việc dựng lại file sai bố cục.
- **Giữ code quan trọng ở vùng cấp phát động** (VirtualAlloc) không thuộc image chính, để một bản dump image thường bỏ sót.

Nhận ra anti-dump không khó: bạn dump ra một file, mở bằng PE-bear hay CFF Explorer thì nó báo header hỏng, hoặc file dump không chạy dù bạn chắc chắn đã tới đúng OEP.

Cách vượt:
- **Dựng lại header bằng tay.** Bạn biết ImageBase (từ Memory Map trong debugger) và biết PE header gốc trông thế nào. Chép lại hai byte MZ, chữ ký PE, và sửa SizeOfImage về giá trị đúng. Scylla có tùy chọn rebuild giúp phần này.
- **Dump sớm hơn.** Nếu code xóa header chạy sau OEP, đặt breakpoint ngay tại OEP và dump trước khi nó kịp phá.
- **Lấy header từ một nguồn sạch.** Với một số packer, header gốc còn nằm đâu đó trong bộ nhớ trước khi bị ghi đè, hoặc bạn có thể vá nhánh thực hiện việc xóa (NOP nó đi) rồi mới để chạy tiếp.
- **PE-sieve** thường tự xử lý được nhiều trường hợp header hỏng khi dump module bị unpack.

## Anti-hook: soi gương xem có bị sờ vào không

Khi bạn hook một API bằng inline hook (Detours, MinHook) hay khi Frida/một EDR gắn vào, cách phổ biến nhất là ghi đè vài byte đầu của hàm (prologue) bằng một lệnh `jmp` nhảy sang code của bạn. Anti-hook lợi dụng chính điều đó: nó tự kiểm tra xem đầu các hàm quan trọng có còn nguyên vẹn không.

Cơ chế:
- **So prologue với giá trị mong đợi.** Chương trình biết `NtProtectVirtualMemory` hay `VirtualProtect` bình thường bắt đầu bằng những byte nào. Nó đọc mấy byte đầu hàm lúc chạy, nếu thấy một `jmp` (`E9 ...`) hay `push/ret` lạ thì biết đang bị hook.
- **So với bản sạch trên đĩa.** Tinh hơn: nó tự đọc file `ntdll.dll` từ đĩa, map lại một bản sạch, rồi so từng byte prologue giữa bản trong bộ nhớ (có thể đã bị hook) với bản sạch trên đĩa. Khác là có hook.
- **Đếm tầng.** Một số mẫu còn so cả `kernel32` gọi xuống `ntdll` để phát hiện hook nằm ở tầng nào.

Đây chính là cách nhiều malware phát hiện EDR, và cũng là cách một chương trình phát hiện Frida đang gắn vào.

Cách vượt:
- **Hook ẩn hơn.** Thay vì inline hook ghi đè prologue, dùng **hardware breakpoint** (thanh ghi DR0 tới DR3) để bắt lời gọi mà không sửa một byte nào của code. Không có gì để so sánh nên anti-hook kiểu prologue-check mù.
- **Hook sâu hơn tầng bị kiểm.** Nếu nó chỉ check prologue `kernel32`, hook ở tầng `ntdll` hoặc ngược lại.
- **Vô hiệu hóa chính hàm check.** Tìm hàm so sánh prologue, patch nó luôn báo "sạch".
- **Khôi phục prologue trước khi check, hook lại sau.** Phức tạp hơn, ít dùng.

Để ý mối liên hệ: anti-hook kiểm tra prologue chính là lý do dân RE thích hardware breakpoint. Nó mạnh vì không để lại dấu vết trong code.

## Ba thứ này hay đi cùng nhau

Trong một protector nghiêm túc (Themida, VMProtect với full option), bạn sẽ gặp cả ba lớp cùng lúc, chồng lên anti-debug ở các bài trước. Thứ tự xử lý hợp lý:
1. Vượt anti-debug cơ bản trước để chạy được dưới debugger (ScyllaHide).
2. Spawn thay vì attach để né anti-attach.
3. Hook bằng hardware breakpoint để né anti-hook.
4. Tới OEP thì dump sớm và dựng lại header để né anti-dump.

Chiến lược tổng khi gặp nhiều lớp sẽ nói kỹ ở [Bài 15.10](/posts/tr-15-10-chien-luoc-nhieu-lop-anti/).

## Checklist ghi nhớ
- Anti-attach chặn việc attach sau khi chạy: tự chiếm debug slot, vá `DbgUiRemoteBreakin`, hoặc check định kỳ. Vượt bằng spawn thay vì attach.
- Anti-dump phá PE header trong bộ nhớ (xóa MZ/PE, sai SizeOfImage) để bản dump thành rác. Vượt bằng dump sớm và dựng lại header (Scylla/PE-sieve).
- Anti-hook so prologue API với bản sạch trên đĩa để phát hiện inline hook/EDR/Frida. Vượt bằng hardware breakpoint (không sửa byte nào).
- Hardware breakpoint là bạn thân khi gặp anti-hook, vì nó không để lại dấu trong code.
- Protector mạnh gộp cả ba lớp, xử lý theo thứ tự anti-debug, anti-attach, anti-hook, anti-dump.
