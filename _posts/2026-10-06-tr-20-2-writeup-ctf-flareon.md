---
title: "Bài 20.2: Giải RE challenge trong CTF và viết write-up tử tế"
date: 2026-10-06 10:00:00 +0700
categories: ["Technique Reverse", "Phần 20 · Thực chiến"]
tags: [reverse-engineering, ctf]
render_with_liquid: false
---
Sau mười chín phần, bạn có đủ công cụ và kỹ thuật. Thiếu một thứ: nhịp làm bài thật dưới áp lực, khi không ai nói trước đề dùng ngôn ngữ gì, packer nào, giấu flag ở đâu. CTF là nơi rèn cái đó, và write-up là cách biến một lần giải thành kiến thức giữ được. Bài này nói về cả hai.

## Chơi ở đâu

Không phải sân nào cũng hợp người mới. Xếp theo độ khó và mục đích:

- **picoCTF.** Hướng giáo dục, category Reverse Engineering rất hợp để bắt đầu. Bài có gợi ý, cộng đồng write-up đông. Đây là chỗ đầu tiên nên vào sau khi học xong Phần 2.
- **crackmes.one.** Không phải CTF theo kiểu giải đấu, nhưng là kho luyện vô tận, lọc theo độ khó 1 tới 6 và theo ngôn ngữ. Mỗi phần ngôn ngữ trong series này nên đi kèm vài bài crackmes.one đúng ngôn ngữ đó.
- **Flare-On.** Giải RE thường niên của Mandiant, kéo dài vài tuần mỗi năm, khó dần qua từng challenge, trải đủ nền tảng (Windows native, .NET, Go, shellcode, obfuscation, đôi khi cả mobile và hardware). Điểm vàng: sau mỗi mùa Mandiant công bố lời giải chính thức. Làm lại các mùa cũ cùng write-up chính thức là một giáo trình RE hoàn chỉnh và miễn phí.
- **HackTheBox, Root-Me, các CTF trên CTFtime.** Khó hơn, dành cho khi đã cứng.

Lời khuyên thật: đừng nhảy vào một CTF đang diễn ra khi chưa quen tay. Làm Flare-On mùa cũ trước, có đáp án để đối chiếu, học nhanh hơn nhiều so với ngồi kẹt một mình vào bài live.

## Phương pháp luận khi mở một challenge rev

Mỗi bài rev về bản chất hỏi một câu: "input nào làm chương trình chấp nhận". Quy trình dưới đây áp cho gần như mọi bài, và nó chính là [quy trình reverse](/posts/tr-0-4-quy-trinh-reverse/) ở Bài 0.4 bóp lại cho hoàn cảnh thi.

**1. Đọc đề và liệt kê file.** Nghe hiển nhiên nhưng nhiều người bỏ qua. Đề nói "nhập đúng flag", "tìm password", hay "giải mã file"? Có file kèm nào ngoài binary không (một file đã mã hoá, một capture mạng)? Format flag thường cho sẵn (`flag{...}`, `CTF{...}`), biết nó để nhận ra khi đã tới gần.

**2. Triage.** Kéo vào Detect It Easy: loại file, ngôn ngữ, packed hay chưa, 32 hay 64-bit. Chạy `strings`. Bước này quyết định bạn đi hướng nào, và đây là lúc toàn bộ chặng ngôn ngữ của series phát huy. Thấy `.NET` thì mở dnSpy ([Phần 5](https://github.com/Haind03/Technique-Reverse/tree/main/phan-05-csharp-dotnet)), thấy Go thì chuẩn bị GoReSym ([Phần 8](https://github.com/Haind03/Technique-Reverse/tree/main/phan-08-go)), thấy `.pyc` thì pycdc ([Phần 7](https://github.com/Haind03/Technique-Reverse/tree/main/phan-07-python)), thấy entropy cao thì unpack trước ([Phần 14](https://github.com/Haind03/Technique-Reverse/tree/main/phan-14-packer-obfuscation)).

**3. Tìm điều kiện thắng.** Đi ngược từ chuỗi "Correct" hay "Wrong" tới hàm so sánh, hoặc từ hàm in flag. Đây là kỹ thuật đi-từ-chuỗi của [Bài 0.4](/posts/tr-0-4-quy-trinh-reverse/), hiệu quả tới mức giải được phần lớn bài mức dễ chỉ bằng nó.

**4. Chọn kỹ thuật theo hình dạng bài.**
- Logic check đọc thẳng ra được: đọc tĩnh rồi đảo ngược bằng tay hoặc Python ([Bài 16.4](/posts/tr-16-4-viet-lai-python-z3/)).
- Nhiều ràng buộc trên các byte input: ném cho Z3 hoặc angr ([Bài 18.3](/posts/tr-18-3-symbolic-execution-angr-triton/)).
- Một hàm biến đổi phức tạp nhưng tách rời được: emulate bằng Unicorn ([Bài 18.2](/posts/tr-18-2-emulation-unicorn-qiling/)) thay vì đọc hiểu.
- Anti-debug chặn đường: chuyển hướng theo [Phần 15](https://github.com/Haind03/Technique-Reverse/tree/main/phan-15-anti-reverse), hoặc emulate để né debugger thật.
- Bí quá: chạy động, đặt breakpoint ở chỗ so sánh cuối, nhiều khi flag đúng lộ ra trần trụi trên thanh ghi.

**5. Biết khi nào dừng một hướng.** Kẹt 30 phút ở một cách thì đổi cách, đừng cố đấm. Người giải nhanh không phải người thông minh hơn mà là người bỏ hướng sai sớm hơn.

## Viết write-up, phần biến lần giải thành kiến thức

Giải xong rồi quên là phí. Write-up là cách ghim lại, và viết tốt còn giúp người khác học. Một write-up tử tế có mấy phần:

- **Đề và môi trường.** Tên bài, file, hash, công cụ dùng. Để người đọc tái hiện được.
- **Triage.** Bạn nhận ra gì ở bước đầu và vì sao chọn hướng đó.
- **Quá trình, gồm cả chỗ sai.** Đây là phần quý nhất và hay bị bỏ. Đừng chỉ chép đường đi thẳng tới đáp án. Viết cả hướng bạn thử mà hỏng và vì sao hỏng. Người đọc (và chính bạn sau này) học từ ngã rẽ sai nhiều hơn từ lời giải bóng bẩy.
- **Lời giải và flag.** Code script nếu có, để chạy lại được.
- **Bài học rút ra.** Một hai câu: lần sau gặp dạng này mình sẽ làm gì khác.

Một write-up chỉ ghi "mở IDA, thấy flag, xong" thì vô dụng. Một write-up ghi "tôi tưởng nó là AES vì thấy một bảng 256 byte, hoá ra là RC4 vì bảng được khởi tạo 0..255 rồi hoán vị, nhận ra nhờ Bài 16.2" thì dạy được người khác.

## Thực tế về đường đi

Bài Flare-On số 1 mỗi mùa thường giải trong mười phút. Bài số 10, 11 có thể ngốn cả tuần của người giỏi. Bình thường. Mục tiêu không phải giải hết ngay mà là mỗi bài học thêm một kỹ thuật. Năm nay kẹt ở bài 7, sang năm bạn qua nó trong một buổi, đó là tiến bộ đo được.

Và đừng ngại đọc write-up của người khác sau khi đã tự vật lộn đủ. Xem cách một người giỏi tiếp cận cùng bài bạn vừa giải chật vật là một trong những cách học nhanh nhất của nghề này.

## Lab tự làm
- Thư mục: `labs/20.2/`.
- Nhiệm vụ: chọn một challenge Flare-On mùa cũ (hoặc một bài picoCTF category Reverse Engineering), tự giải, rồi viết write-up theo mẫu trong `labs/20.2/solution.md`. So với lời giải chính thức sau khi đã tự làm xong.

## Checklist ghi nhớ
- Mọi bài rev hỏi cùng một câu: input nào được chấp nhận.
- Luôn triage trước để biết dùng hướng ngôn ngữ/kỹ thuật nào, đây là lúc cả series hội tụ.
- Đi từ chuỗi thắng/thua ngược về hàm kiểm tra là cách vào bài nhanh nhất.
- Chọn kỹ thuật theo hình dạng bài: đọc tay, Z3/angr, emulation, hay debug.
- Kẹt một hướng thì đổi, đừng cố đấm.
- Write-up phải ghi cả chỗ sai, đó là phần dạy được nhiều nhất.
