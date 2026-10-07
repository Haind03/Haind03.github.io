---
title: "Bài 17.5: Nhận diện process injection khi phân tích malware"
date: 2026-10-06 09:44:00 +0700
categories: ["Technique Reverse", "Phần 17 · Patch, Hook, Injection & Instrumentation"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
Bài này đứng hẳn ở ghế blue-team. Mục tiêu không phải viết injector mà là: khi bạn mở một mẫu malware và thấy nó đụng tới một tiến trình khác, bạn gọi tên được kỹ thuật, biết dùng tool nào xác nhận, và viết được dấu hiệu để săn tìm lại. Đây là nhóm hành vi malware dùng nhiều nhất để chạy code trong thân một tiến trình hợp pháp (svchost, explorer, một trình duyệt) nhằm trốn con mắt và qua mặt sản phẩm bảo mật.

Toàn bộ trình bày ở mức nhận diện và phát hiện. Không có cookbook từng bước, vì thứ bạn cần ở đây là con mắt phân tích.

## Vì sao malware thích chạy nhờ trong tiến trình khác

Một process lạ tên `invoice_2024.exe` ngốn CPU và nối ra một IP Nga thì ai cũng nghi. Nhưng nếu cùng hành vi đó diễn ra bên trong `explorer.exe`, nó lẫn vào nền hệ thống. Đó là động cơ của mọi kỹ thuật trong bài: mượn danh tính và mượn không gian địa chỉ của một tiến trình được tin tưởng.

Với người phân tích, điều này nghĩa là: đừng chỉ nhìn tiến trình của mẫu, hãy nhìn cả những tiến trình nó chạm vào.

## Bốn họ kỹ thuật, nhận ra bằng điều gì

Bạn không cần thuộc lòng cài đặt của chúng. Cần nhớ *chữ ký hành vi* để nhận ra khi gặp.

| Họ kỹ thuật | Chữ ký nhận ra | Dấu vết để lại |
|---|---|---|
| Remote thread injection | Mẫu mở handle tiến trình khác rồi tạo thread trong đó | Một thread có điểm vào nằm ngoài mọi module |
| APC injection | Chèn công việc vào một thread sẵn có thay vì tạo thread mới | Không có thread mới, nhưng xuất hiện vùng code lạ |
| Thread hijacking | Dừng một thread, đổi con trỏ lệnh của nó, cho chạy tiếp | Thread hợp pháp bỗng thực thi ngoài module gốc |
| Process hollowing | Tạo một tiến trình hợp pháp ở trạng thái treo rồi tráo nội dung | Image trên đĩa khác với image trong bộ nhớ của cùng tiến trình |

Điểm chung cả bốn: ở đâu đó trong tiến trình nạn nhân xuất hiện một vùng mã **không ứng với file nào trên đĩa**. Đó là sợi chỉ xuyên suốt mà mọi công cụ phát hiện bám vào.

## Cờ đỏ số một: vùng nhớ private, executable, không có module

Code hợp pháp nằm trong các section đã ánh xạ từ file .exe/.dll (memory có kiểu *image*, gắn tên module). Code bị tiêm nằm trong vùng *private* hoặc *mapped* mà lại có quyền thực thi. Khi mở một tiến trình nghi vấn:

- Trong **Process Hacker / System Informer**, tab Memory, lọc các vùng có quyền execute mà cột "Use" trống (không phải Image). Một vùng `Private` + `RX`/`RWX` là ứng viên hàng đầu.
- Trong tab Threads, xem **Start Address** từng thread. Thread hợp pháp trỏ vào một hàm có tên trong module. Thread trỏ vào một địa chỉ trần không tên là cờ đỏ.

Quyền **RWX** (vừa ghi vừa chạy) đặc biệt hiếm trong phần mềm sạch và rất hay gặp ở code tiêm, vì payload cần được ghi vào rồi chạy. Thấy RWX private là giỏng tai lên.

## Công cụ phát hiện chuyên dụng

Bạn không phải soi tay từng vùng nhớ. Có tool làm sẵn:

- **PE-sieve** (Hasherezade): quét một tiến trình đang chạy, so từng module với bản gốc trên đĩa, phát hiện vùng code lạ, phần bị hook, và dump chúng ra để phân tích tiếp. Đây là công cụ đi đầu khi nghi injection.
- **HollowsHunter**: chạy PE-sieve trên toàn bộ tiến trình của hệ thống một lượt, hợp để săn trên máy nghi nhiễm.
- **Moneta**: liệt kê bất thường bộ nhớ (private executable, image bị sửa, thiếu ánh xạ đĩa).
- **Process Hacker / System Informer**: quan sát thủ công thread, memory, handle, và dump vùng nghi ngờ.
- **Procmon** và **ETW / Sysmon**: ghi lại hành vi ở mức sự kiện. Sysmon Event ID 8 (CreateRemoteThread) và Event ID 25 (process tampering) là hai mục đáng theo dõi cho lớp hành vi này.

## Khi reverse tĩnh: nhìn vào import và chuỗi gọi

Mở mẫu trong IDA/Ghidra, phần import và capa cho bạn manh mối trước cả khi đọc code:

- **capa** (Mandiant) suy ra khả năng và thường gắn thẳng nhãn kiểu "inject into process" hay "spawn suspended process" kèm địa chỉ hàm liên quan. Chạy capa trước là đường tắt tốt.
- Trong danh sách import, các API thao tác bộ nhớ và thread của tiến trình *khác* (phiên bản có hậu tố Ex, các hàm Nt tương ứng trong ntdll) là chỉ điểm. Một chương trình bình thường hiếm khi cần ghi vào bộ nhớ tiến trình khác.
- Malware tinh vi che các API này (resolve động qua hashed API, nối lại Bài 1.13), nên nếu import *quá sạch* mà hành vi lại khả nghi, đó cũng là một tín hiệu.

Khi muốn thấy tận mắt, đặt breakpoint tại các API ghi bộ nhớ tiến trình để bắt đúng khoảnh khắc payload được chuyển sang, rồi dump payload đó ra. Đây là cách lấy được shellcode/PE tầng sau mà không cần dựng lại toàn bộ logic.

## Process hollowing: nhận ra qua sự lệch đĩa và bộ nhớ

Hollowing đáng nói riêng vì nó giả dạng tinh vi nhất: tiến trình trông đúng tên, đúng đường dẫn, nhưng ruột đã bị thay. Dấu hiệu đặc trưng:

- Một tiến trình con được tạo ở trạng thái treo (suspended) rồi mới chạy, thấy trong log Procmon/Sysmon.
- **Image trong bộ nhớ khác image trên đĩa** của cùng đường dẫn. PE-sieve so sánh đúng điểm này và báo "replaced/hollowed".
- Base address hoặc entry point trong bộ nhớ không khớp với file gốc.

Cây tiến trình cũng kể chuyện: một tiến trình hệ thống có parent vô lý (ví dụ `svchost.exe` sinh ra bởi một file Office) là bất thường, xem bằng Process Explorer hoặc trong EDR.

## Biến hành vi thành dấu hiệu săn tìm

Phân tích xong một mẫu, hãy chắt ra thứ tái dùng được:

- Ghi lại tiến trình nạn nhân mục tiêu, chuỗi API quan sát được, và đặc điểm vùng nhớ (kích thước, quyền).
- Viết YARA cho phần loader nếu có pattern ổn định, và một quy tắc hành vi (Sigma) cho chuỗi sự kiện tạo remote thread / process tampering.
- Lưu hash payload tầng sau dump được làm IOC. Nối sang Phần 19 về IOC và YARA.

## Checklist ghi nhớ
- Mọi kỹ thuật tiêm để lại một dấu chung: vùng code trong tiến trình nạn nhân không ứng với file nào trên đĩa.
- Cờ đỏ: vùng nhớ private executable (nhất là RWX), thread có start address không thuộc module nào.
- PE-sieve / HollowsHunter / Moneta tự động phát hiện code tiêm và hollowing; Process Hacker để soi tay.
- capa và danh sách import cho manh mối tĩnh; đặt breakpoint tại API ghi bộ nhớ tiến trình để dump payload tầng sau.
- Hollowing lộ ra ở chỗ image trong bộ nhớ lệch với image trên đĩa, và ở cây tiến trình vô lý.
- Chắt kết quả thành YARA/Sigma/IOC để săn lại lần sau.
