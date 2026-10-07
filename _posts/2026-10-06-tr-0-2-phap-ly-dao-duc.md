---
title: "Bài 0.2: Pháp lý và đạo đức, phần ai cũng muốn bỏ qua"
date: 2026-10-06 08:01:00 +0700
categories: ["Technique Reverse", "Phần 0 · Nhập môn"]
tags: [reverse-engineering, nhap-mon]
render_with_liquid: false
---
Tôi biết bạn muốn nhảy thẳng vào IDA. Nhưng bài này quyết định bạn làm nghề này được lâu hay sớm dính rắc rối, nên đọc một lần cho xong.

Kỹ thuật RE trung lập. Cùng một thao tác unpack, hook, patch, dùng để phân tích malware bảo vệ công ty thì là việc tốt, dùng để bẻ khoá phần mềm bán lại thì phạm luật. Khác nhau nằm ở **mục đích và sự cho phép**, không nằm ở công cụ.

## Ranh giới nói chung

Không có một bộ luật chung cho cả thế giới, mỗi nước mỗi khác, nên đây chỉ là nguyên tắc định hướng chứ không phải tư vấn pháp lý.

**Thường được chấp nhận:**
- Reverse phần mềm **của chính bạn**, hoặc bạn được chủ sở hữu cho phép bằng văn bản.
- Phân tích **malware** để phòng thủ, nghiên cứu, ứng cứu sự cố.
- Chơi **CTF**, giải **crackme**, dùng binary làm ra để học.
- Nghiên cứu nhằm **tương thích** (interoperability), ở nhiều nơi được luật miễn trừ có điều kiện.
- Tìm lỗ hổng rồi **báo cáo có trách nhiệm** (coordinated disclosure) qua chương trình bug bounty hoặc liên hệ nhà sản xuất.

**Dễ dính rắc rối:**
- Bẻ khoá, vá license, chia sẻ bản crack của phần mềm thương mại.
- Vượt qua DRM rồi phát tán nội dung.
- Reverse hệ thống của người khác khi chưa được phép, kể cả "chỉ để xem".
- Phá điều khoản sử dụng (EULA/ToS), nhất là mảng game online và dịch vụ cloud.
- Công bố 0-day kèm exploit chạy được mà chưa cho nhà sản xuất cơ hội vá.

Cụm "chỉ để học thôi mà" không phải lá chắn pháp lý. Phát tán công cụ hoặc bản vá mới là chỗ ranh giới bị vượt, chứ không phải lúc bạn ngồi đọc code một mình.

## Vài khung luật nên biết tên

Không cần thuộc, chỉ cần nghe tên là biết tra ở đâu khi cần:

- **DMCA (Mỹ), mục 1201** cấm vượt qua biện pháp bảo vệ kỹ thuật, nhưng có các ngoại lệ cho nghiên cứu bảo mật, tương thích, giáo dục. Ngoại lệ được rà soát định kỳ.
- **CFAA (Mỹ)** về truy cập trái phép vào hệ thống máy tính.
- **EU Software Directive** cho phép decompile nhằm tương thích trong điều kiện nhất định.
- Việt Nam và nhiều nước có luật sở hữu trí tuệ và an ninh mạng riêng. Reverse để học thì không ai bắt, nhưng phát tán bản crack thì vi phạm bản quyền rõ ràng.

Thông điệp không phải "luật phức tạp nên thôi khỏi học", mà là "biết mình đang đứng ở đâu".

## Đạo đức nghề, thứ luật không ghi

Luật đặt mức sàn. Người làm nghề tử tế tự đặt mức cao hơn:

- **Có phép trước khi đụng vào hệ thống của người khác.** Email xin phép còn lưu lại là bạn bè tốt nhất của bạn.
- **Giữ sạch chuỗi lây nhiễm khi phân tích malware.** Lab cô lập, không để mẫu thoát ra mạng thật. Bài [0.3](/posts/tr-0-3-dung-lab-an-toan/) nói kỹ.
- **Tìm được lỗ hổng thì báo, đừng bán cho chợ đen, đừng đăng khoe kèm exploit.** Cho nhà sản xuất thời gian vá (thường 90 ngày) rồi mới công bố chi tiết.
- **Đừng dạy người khác làm điều bạn sẽ không dám ký tên vào.**

## Series này đứng ở đâu

Tất cả bài thực hành trong series dùng một trong các loại sau, không có ngoại lệ:

- crackme và binary CTF do chính tôi hoặc cộng đồng tạo ra để học,
- chương trình nhỏ do chúng ta tự viết rồi tự reverse,
- mẫu malware công khai dùng trong lab cô lập, cho mục đích phòng thủ.

Không có bài nào hướng dẫn bẻ khoá một sản phẩm thương mại cụ thể. Nếu bạn định dùng kỹ năng học được ở đây để crack phần mềm bán lại, phần còn lại của series không dành cho bạn, và tôi cũng không giúp được gì khi có chuyện.

## Checklist ghi nhớ
- Kỹ thuật trung lập, mục đích và sự cho phép quyết định đúng sai.
- Reverse đồ của mình, CTF, malware phòng thủ: an toàn. Phát tán crack, vượt DRM để phát tán: phạm luật.
- Tìm lỗ hổng thì báo cáo có trách nhiệm, đừng vội công bố exploit.
- Khi nghi ngờ, xin phép bằng văn bản trước.
