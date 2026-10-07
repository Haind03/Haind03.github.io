---
title: "Bài 2.4: Binary Ninja, Cutter và radare2, khi IDA và Ghidra không phải lựa chọn duy nhất"
date: 2026-10-06 08:20:00 +0700
categories: ["Technique Reverse", "Phần 2 · Làm quen bộ công cụ"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
Hỏi mười người làm RE dùng tool gì, chín người nhắc IDA hoặc Ghidra. Nhưng dừng ở đó là bỏ sót cả một hệ sinh thái, và đôi khi chính cái tool "không phổ biến" lại hợp việc của bạn hơn. Bài này điểm qua ba cái tên đáng có trong túi đồ nghề: Binary Ninja, Cutter, và radare2/rizin. Không phải để bạn bỏ IDA, mà để biết khi nào với sang cái khác.

Lưu ý nhỏ trước khi vào: tôi không cố thuyết phục bạn "cái nào tốt nhất". Tool tốt nhất là cái bạn thạo và hợp bài toán. Mục tiêu ở đây là cho bạn đủ thông tin để thử và tự quyết.

## Binary Ninja, kẻ thách thức trẻ

Binary Ninja (hay gọi tắt BN) là disassembler thương mại ra sau, nên nó học được bài của đàn anh và làm UI gọn gàng, mượt mà hơn hẳn. Nhưng điểm khiến dân kỹ thuật mê nó không nằm ở giao diện, mà ở **BNIL**, hệ thống trung gian nhiều tầng (intermediate language).

Ý tưởng của IL là thế này: assembly thô rất rối và khác nhau giữa các kiến trúc. BN dịch assembly lên nhiều tầng trừu tượng dần:

- **LLIL** (Low Level IL): sát assembly nhưng đã chuẩn hoá, bỏ bớt rác đặc thù kiến trúc.
- **MLIL** (Medium Level IL): có biến, tham số, bỏ chi tiết thanh ghi và stack.
- **HLIL** (High Level IL): gần như pseudocode kiểu C, dễ đọc.

Bạn chuyển qua lại giữa các tầng để nhìn cùng một hàm ở độ chi tiết khác nhau. Khi cần soi từng lệnh thì xuống LLIL, khi muốn nắm logic tổng thể thì lên HLIL. Đây là thứ làm việc viết script phân tích tự động trên BN rất dễ chịu, vì API Python của nó thao tác thẳng trên các tầng IL này thay vì trên assembly thô.

Vài điểm thực tế về BN:
- Có bản thương mại (trả tiền một lần, cập nhật theo năm) và một bản **cloud miễn phí** chạy trên trình duyệt, đủ để bạn thử nghiệm và học mà không tốn đồng nào. Người mới cứ vào bản cloud nghịch trước.
- API Python được khen là sạch và dễ dùng nhất trong các disassembler, hợp nếu bạn định tự động hoá nhiều.
- Decompiler (ra HLIL) tốt, tuy độ "chín" của việc nhận diện kiểu phức tạp vẫn sau Hex-Rays của IDA một bậc.

Chọn BN khi: bạn muốn UI hiện đại, hay viết script phân tích, và thích làm việc trên IL nhiều tầng.

## radare2 và rizin, sức mạnh của dòng lệnh

radare2 (viết tắt r2) là bộ công cụ RE mã nguồn mở hoàn toàn, điều khiển bằng dòng lệnh. Nó nổi tiếng vừa mạnh vừa khó học, vì cú pháp lệnh ngắn tới mức khó nhớ. **rizin** là một nhánh (fork) tách ra từ r2, dọn dẹp lại cho nhất quán và dễ tiếp cận hơn, nên nếu mới bắt đầu bạn có thể cân nhắc rizin.

Triết lý của r2 là mọi thứ là một lệnh ngắn, ghép lại thành phiên làm việc. Nghe đáng sợ nhưng bạn chỉ cần thuộc chừng năm lệnh là làm được việc cơ bản:

| Lệnh | Tác dụng |
|---|---|
| `aaa` | Phân tích toàn bộ file (analyze all). Gần như luôn chạy đầu tiên |
| `afl` | Liệt kê các hàm đã tìm được (analyze function list) |
| `s <địa chỉ hoặc tên>` | Seek, nhảy con trỏ tới đó, ví dụ `s main` |
| `pdf` | Print disassembly of function, in disassembly của hàm hiện tại |
| `VV` | Vào chế độ graph view trực quan (nhấn `q` để thoát) |

Cách đọc tên lệnh giúp đỡ nhớ nhiều: chữ đầu là nhóm (`a` analyze, `p` print, `s` seek, `V` visual), các chữ sau thu hẹp dần. `pdf` là print (p), disassembly (d), function (f). Hiểu quy luật này thì không phải học thuộc.

Điểm mạnh của r2/rizin:
- Hoàn toàn miễn phí và mở, chạy ở mọi nơi kể cả qua SSH trên server không có GUI.
- Kịch bản hoá cực mạnh, ghép với shell và pipe thoải mái.
- Có `r2pipe` để điều khiển r2 từ Python, C, nhiều ngôn ngữ.

Điểm yếu: đường học dốc, và khi phân tích file lớn bằng mắt thì dòng lệnh thuần mệt hơn GUI.

Chọn r2/rizin khi: bạn thích dòng lệnh, cần làm trên môi trường không GUI, hoặc muốn tự động hoá bằng script nhỏ nhanh gọn.

## Cutter, bộ mặt đồ hoạ của rizin

Nếu bạn thích sức mạnh của rizin nhưng không chịu nổi dòng lệnh, Cutter là câu trả lời. Đây là GUI chính thức xây trên rizin, cho bạn cửa sổ disassembly, graph, hex, strings, imports giống IDA, nhưng engine bên dưới là rizin và hoàn toàn miễn phí.

Điểm đáng giá nhất: Cutter tích hợp sẵn **decompiler jsdec** (và cắm được decompiler của Ghidra), nên bạn có pseudocode mà không tốn tiền. Với người mới ngại cả r2 lẫn giá IDA, Cutter là điểm vào rất hợp lý: giao diện quen thuộc, công cụ mở, lại vẫn gõ được lệnh rizin ở ô command khi cần.

Chọn Cutter khi: bạn muốn trải nghiệm GUI miễn phí đầy đủ, hoặc muốn dùng rizin nhưng thích chuột hơn bàn phím.

## Vậy cuối cùng chọn gì

Không có câu trả lời đúng tuyệt đối, nhưng đây là cách tôi hay khuyên:

- Người mới, ít tiền: bắt đầu bằng **Ghidra** (bài 2.3) hoặc **Cutter**, cả hai miễn phí và có decompiler.
- Thích UI đẹp, hay viết script, có ngân sách hoặc dùng bản cloud: thử **Binary Ninja**.
- Dân dòng lệnh, làm nhiều trên server, mê tự động hoá: **radare2/rizin**.
- Môi trường chuyên nghiệp, cần Hex-Rays mạnh nhất: **IDA Pro** (bài 2.2).

Điều quan trọng hơn chọn tool nào: đừng nhảy tool liên tục khi mới học. Chọn một cái, dùng cho thạo tới mức phím tắt thành bản năng, rồi mới thử cái khác. Nhảy qua nhảy lại là cách chắc chắn để không giỏi cái nào.

## Lab tự làm

Xem [labs/2.4/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/2.4). Bạn sẽ mổ cùng một binary nhỏ bằng radare2 dòng lệnh với chuỗi lệnh `aaa`, `afl`, `pdf`, rồi mở lại trong Cutter để thấy cùng dữ liệu đó dưới dạng GUI, và nếu có điều kiện thì thử bản Binary Ninja cloud. Mục tiêu là thấy ba tool nhìn cùng một file theo ba cách khác nhau.

## Checklist ghi nhớ
- Binary Ninja: UI hiện đại, IL nhiều tầng (LLIL/MLIL/HLIL), API Python đẹp, có bản cloud free để thử.
- radare2/rizin: dòng lệnh, miễn phí, mạnh về tự động hoá. Năm lệnh cốt lõi: `aaa`, `afl`, `s`, `pdf`, `VV`.
- Tên lệnh r2 có quy luật (nhóm + thu hẹp), hiểu quy luật đỡ phải học thuộc.
- Cutter: GUI miễn phí trên nền rizin, có decompiler jsdec, hợp người mới ngại dòng lệnh.
- Chọn một tool và dùng cho thạo trước khi đổi, đừng nhảy liên tục.
