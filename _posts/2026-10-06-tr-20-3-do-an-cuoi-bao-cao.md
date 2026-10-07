---
title: "Bài 20.3: Đồ án cuối, reverse trọn một chương trình và viết báo cáo"
date: 2026-10-06 10:01:00 +0700
categories: ["Technique Reverse", "Phần 20 · Thực chiến"]
tags: [reverse-engineering, ctf]
render_with_liquid: false
---
Đây là bài cuối của cả series. Mọi thứ bạn học từ Phần 0 tới giờ, đọc assembly, dựng lại struct, unpack, vượt anti-debug, viết keygen, trích config, bây giờ gom lại thành một việc duy nhất: cầm một chương trình bạn chưa từng thấy bên trong, và nói cho người khác biết nó hoạt động thế nào. Không phải một crackme mười phút, mà một mục tiêu đủ lớn để bạn phải lên kế hoạch, ghi chép nhiều ngày, rồi viết lại thành một báo cáo mà người khác đọc là hiểu.

Giải crackme là chạy nước rút. Đồ án này là chạy đường dài. Kỹ năng khác nhau, và nghề RE thật sự sống ở đường dài.

## Chọn mục tiêu cho đúng

Chọn sai mục tiêu là hỏng cả đồ án, hoặc quá dễ nên không học được gì, hoặc quá khó nên bỏ cuộc giữa chừng. Vài lựa chọn hợp lý và hợp pháp:

- **Một chương trình của chính bạn**, build rồi vứt source đi, tự reverse lại. Nghe hơi giả, nhưng bạn có đáp án để tự chấm, rất tốt cho lần đầu.
- **Một crackme nhiều tầng** từ crackmes.one cấp 4 trở lên, loại có cả thuật toán serial lẫn một lớp bảo vệ.
- **Một challenge CTF rev cỡ lớn**, ví dụ một bài Flare-On cuối mùa (bài 7 tới 10 thường là cả một chương trình thật).
- **Một phần mềm mã nguồn mở**, reverse rồi so với source để kiểm chứng mình đọc đúng không.

Nhắc lại ranh giới ở [Bài 0.2](/posts/tr-0-2-phap-ly-dao-duc/): đừng chọn một sản phẩm thương mại rồi crack, đừng đụng hệ thống của người khác khi chưa được phép. Đồ án này để chứng minh kỹ năng, không phải để gây rắc rối.

Một dấu hiệu mục tiêu vừa tầm: bạn triage xong trong một buổi tối và vẫn còn tò mò, chứ không phải nản.

## Quy trình đồ án

Đây là [quy trình bốn bước](/posts/tr-0-4-quy-trinh-reverse/) ở Phần 0, nhưng kéo giãn ra cho một mục tiêu lớn.

### 1. Xác định phạm vi và câu hỏi

Đừng nói "tôi sẽ reverse hết chương trình này". Chương trình thật có hàng nghìn hàm, phần lớn là thư viện và boilerplate, bạn không cần đọc hết. Thay vào đó viết ra vài câu hỏi cụ thể, ví dụ:

- Chương trình kiểm tra license bằng thuật toán gì?
- Nó lưu dữ liệu ở đâu, định dạng ra sao?
- Nó nói chuyện với server nào, giao thức gì?
- Có cơ chế chống phân tích nào không?

Câu hỏi rõ thì bạn biết khi nào xong. Không có câu hỏi, bạn sẽ đọc assembly tới sáng mà chẳng để làm gì.

### 2. Triage

Áp [Bài 2.1](/posts/tr-2-1-triage-die-strings-pebear/): loại file, ngôn ngữ, compiler, packed hay không, 32 hay 64 bit, chuỗi đáng chú ý, import. Kết quả triage quyết định bạn dùng bộ công cụ nào (dnSpy cho .NET, JADX cho Android, IDA/Ghidra cho native, GoReSym cho Go...). Ghi lại ngay hash của file để sau này đối chiếu.

### 3. Lập bản đồ chức năng

Trước khi đào sâu, vẽ bản đồ tổng thể. Tìm `main` thật ([Bài 3.1](/posts/tr-3-1-hello-world-tim-main-that/)), đi từ các chuỗi và import quan trọng để khoanh vùng những khối chức năng lớn (khởi tạo, giao diện, xử lý dữ liệu, mạng, bảo vệ). Đổi tên và ghi chú ngay trong IDA/Ghidra khi hiểu tới đâu. Mục tiêu bước này không phải hiểu từng dòng, mà biết "chỗ thú vị ở đâu" để bước sau đào đúng chỗ.

Mẹo: một sơ đồ khối đơn giản vẽ tay hoặc trong file ghi chú, mỗi khối một dòng, kéo bạn ra khỏi cảm giác lạc trong biển hàm.

### 4. Phân tích sâu các thành phần chính

Giờ mới đào. Với mỗi câu hỏi ở bước 1, đi vào đúng khối đã khoanh vùng và áp kỹ thuật phù hợp:

- Thuật toán kiểm tra hoặc crypto: nhận diện hằng số ([Bài 16.1](/posts/tr-16-1-nhan-dien-hang-so-crypto/)), viết lại bằng Python hoặc giải bằng Z3 ([Bài 16.4](/posts/tr-16-4-viet-lai-python-z3/)).
- Lớp bảo vệ: unpack ([Phần 14](https://github.com/Haind03/Technique-Reverse/tree/main/phan-14-packer-obfuscation)), vượt anti-debug ([Phần 15](https://github.com/Haind03/Technique-Reverse/tree/main/phan-15-anti-reverse)).
- Định dạng dữ liệu hoặc giao thức: dựng lại spec ([Bài 18.7](/posts/tr-18-7-reverse-giao-thuc-dinh-dang-file/)).
- Xác nhận giả thuyết bằng dynamic: đặt breakpoint, xem giá trị thật, hoặc hook bằng Frida ([Bài 17.2](/posts/tr-17-2-frida-toan-tap/)).

Cứ lặp static rồi dynamic rồi ghi chép cho tới khi trả lời xong các câu hỏi.

### 5. Tổng hợp phát hiện

Khi đã trả lời đủ, dừng đào và bắt đầu viết. Gom các ghi chú rời rạc thành một câu chuyện mạch lạc: chương trình này là gì, hoạt động ra sao, điểm đáng chú ý nằm đâu.

## Cấu trúc một báo cáo RE tốt

Báo cáo là phần nhiều người bỏ qua và cũng là phần phân biệt người làm nghề với người chỉ nghịch tool. Một hàm bạn hiểu mà không viết lại được thì ba tháng sau coi như chưa từng hiểu. Dàn ý chuẩn:

1. **Tóm tắt điều hành (executive summary).** Vài đoạn ngắn cho người không đọc kỹ thuật: đây là cái gì, kết luận chính, mức độ quan trọng. Viết phần này sau cùng nhưng đặt lên đầu.
2. **Phương pháp và công cụ.** Bạn dùng gì, chạy trong môi trường nào (nhắc lab cô lập nếu là malware), để người khác tái hiện được.
3. **Thông tin mẫu.** Tên file, kích thước, hash (MD5/SHA-256), loại file, compiler, phiên bản. Đây là danh tính của mục tiêu.
4. **Kiến trúc chương trình.** Bản đồ tổng thể các thành phần và cách chúng liên kết. Một sơ đồ ở đây đáng giá nghìn dòng chữ.
5. **Phát hiện chi tiết.** Phần ruột. Mỗi phát hiện kèm bằng chứng cụ thể: địa chỉ hàm, ảnh chụp pseudocode, đoạn assembly then chốt, giá trị quan sát được lúc chạy. Người đọc phải lần theo được.
6. **IOC (nếu là malware).** Hash, domain, IP, mutex, khoá registry, đường dẫn file, kèm YARA/Sigma nếu có ([Bài 19.2](/posts/tr-19-2-ioc-yara-capa-sigma/)).
7. **Kết luận và khuyến nghị.** Trả lời lại các câu hỏi ban đầu, nêu điểm còn bỏ ngỏ, và khuyến nghị (vá lỗi, chặn IOC, hoặc hướng phân tích tiếp).

Nguyên tắc vàng: **mọi khẳng định phải có bằng chứng.** "Chương trình mã hoá bằng RC4" là một câu nói suông cho tới khi bạn chỉ ra hàm KSA tại địa chỉ nào. Đừng đoán rồi viết như đã chứng minh.

Template đầy đủ để điền nằm ở [labs/20.3/bao-cao-mau.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/20.3/bao-cao-mau.md).

## Checklist ghi nhớ
- Chọn mục tiêu vừa tầm và hợp pháp, không quá dễ cũng không quá khó.
- Bắt đầu bằng câu hỏi cụ thể, không ôm đồm "reverse hết".
- Triage, lập bản đồ, rồi mới đào sâu đúng chỗ, lặp static và dynamic.
- Viết báo cáo có cấu trúc, mọi khẳng định kèm bằng chứng (địa chỉ, pseudocode, giá trị runtime).
- Báo cáo viết được thì mới thật sự là đã hiểu.

## Lời kết

Bạn đã đi từ chỗ mở IDA lên và hoảng vì biển assembly, tới chỗ tự tay unpack, vượt anti-debug, viết keygen, trích config C2 và viết được một báo cáo hoàn chỉnh. Đó là một chặng đường dài và bạn nên tự hào.

RE không có đích cuối. Luôn có một packer mới, một kiến trúc mới, một protector tinh vi hơn. Từ đây bạn chọn hướng đào sâu: phân tích malware và threat intel, nghiên cứu lỗ hổng và exploit, hay mảng mobile và game. Mỗi hướng là một series riêng đáng cả năm trời. Cứ giữ thói quen luyện đều ở [crackmes.one và Flare-On](/posts/tr-tai-nguyen-tai-lieu-hoc/), và quan trọng nhất là giữ cái tò mò đã kéo bạn tới tận đây.

Và nhớ lại [Bài 0.2](/posts/tr-0-2-phap-ly-dao-duc/): kỹ năng này mạnh, dùng nó cho việc tử tế. Chúc bạn reverse vui.

## Cạm bẫy thường gặp
- Đào quá sâu vào code thư viện không liên quan tới câu hỏi, tốn hàng giờ vô ích.
- Không ghi chép, tới lúc viết báo cáo phải làm lại từ đầu.
- Kết luận không có bằng chứng, báo cáo mất giá trị.
- Chọn mục tiêu quá tham vọng rồi bỏ cuộc.
