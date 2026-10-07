---
title: "Tài liệu học và nơi luyện tập"
date: 2026-10-06 14:03:00 +0700
categories: ["Technique Reverse", "Tài nguyên"]
tags: [reverse-engineering, resources]
render_with_liquid: false
---
> Chỗ để tự học thêm và quan trọng hơn là chỗ để luyện tay. RE không đọc mà giỏi được, phải ngồi gỡ binary thật. Mục cuối là các sân luyện, ưu tiên mấy cái đó.

## Sách nên đọc

Không cần đọc hết, chọn theo hướng của bạn.

| Sách | Dành cho | Ghi chú |
|---|---|---|
| **Practical Malware Analysis** (Sikorski & Honig) | Người theo malware | Kinh điển, thực hành nhiều, lab kèm theo rất tốt |
| **Practical Reverse Engineering** (Dang, Gazet, Bachaalany) | Trung cấp | x86/x64, kernel, anti-RE, VM |
| **The IDA Pro Book** (Chris Eagle) | Người dùng IDA | Vẫn là tài liệu IDA đầy đủ nhất |
| **Reversing: Secrets of Reverse Engineering** (Eldad Eilam) | Nhập môn nền tảng | Cũ nhưng phần nền tảng vẫn đúng |
| **The Ghidra Book** (Eagle & Nance) | Người dùng Ghidra | Đối trọng của IDA Pro Book |
| **Practical Binary Analysis** (Dennis Andriesse) | Thích tự động hoá, Linux | ELF, DBI, taint, symbolic |
| **Windows Internals** (Russinovich và cộng sự) | Chuyên Windows | Tra cứu khi cần hiểu sâu hệ điều hành |
| **Rootkits and Bootkits** | Nâng cao, kernel/firmware | Khi đã vững cơ bản |
| **Android Security Internals** / **OWASP MASTG** | Mảng mobile | MASTG kèm app luyện UnCrackable |

## Khoá học và tài liệu miễn phí

- **OpenSecurityTraining2** (ost2.fyi). Khoá học bài bản miễn phí về x86/x64, PE, debugging, hoàn toàn chất lượng.
- **Malware Unicorn RE101 / RE102**. Workshop nhập môn malware rất được yêu thích.
- **Nightmare** (guyinatuxedo). Khoá CTF pwn/RE qua ví dụ, github mở.
- **TryHackMe** mảng Reverse Engineering, **HackTheBox Academy**. Có hướng dẫn từng bước.
- **pwn.college**. Nền tảng học theo module, từ cơ bản tới nâng cao, miễn phí.
- **Tài liệu chính thức**: Ghidra docs, Frida handbook (learnfrida.info), tài liệu angr, x64dbg wiki.

## Kênh YouTube và blog

Kênh:
- **stacksmashing**, **LiveOverflow**, **OALabs**, **MalwareTech**, **John Hammond**, **GuidedHacking** (game), **HackerSploit**.

Blog và site:
- **OALabs**, **Hex-Rays blog**, **Binary Ninja blog**, **0x00sec**, **tuts4you** (diễn đàn RE lâu đời, nhiều tutorial unpacking).
- Writeup Flare-On các năm (fireeye/mandiant công bố lời giải chính thức sau mỗi mùa, học cực tốt).

## Nơi luyện tập, phần quan trọng nhất

Đọc mười bài không bằng tự gỡ một binary. Xếp theo độ khó tăng dần:

**Nhập môn, crackme nhẹ nhàng:**
- **crackmes.one**. Kho crackme khổng lồ, lọc theo độ khó 1 tới 6 và theo ngôn ngữ/nền tảng. Bắt đầu từ mức 1, đây là sân tập tốt nhất cho người mới.
- **Reversing.kr**. Bộ bài RE kinh điển, khó dần.
- **crackmes.de** (bản lưu trữ). Kho cũ nhưng còn nhiều bài hay.

**CTF và wargame:**
- **picoCTF**. Hướng giáo dục, có mục Reverse Engineering rất hợp người mới.
- **pwnable.kr / pwnable.tw**. Nghiêng pwn nhưng nhiều bài RE.
- **Root-Me** mục Cracking. Phân loại rõ ràng.
- **HackTheBox** mục Reversing. Khó hơn, cho người đã cứng.

**Giải đấu thật:**
- **Flare-On**. Giải RE thường niên của Mandiant, kéo dài vài tuần mỗi năm, từ dễ tới rất khó. Làm lại các mùa cũ là một giáo trình RE hoàn chỉnh miễn phí.
- Các CTF trên **CTFtime** có category rev.

**Malware mẫu (chỉ dùng trong lab cô lập, xem [Bài 0.3](/posts/tr-0-3-dung-lab-an-toan/)):**
- **MalwareBazaar** (abuse.ch), **vx-underground**, **theZoo**, **Malshare**. Tải mẫu thật để luyện phân tích. Cẩn trọng tuyệt đối, đây là mã độc sống.

**Mobile:**
- **OWASP UnCrackable Apps** (Android và iOS). Ba mức, kèm trong MASTG.
- **DIVA / InsecureBankv2**. App Android cố tình có lỗ hổng.

## Cộng đồng để hỏi

- Discord/subreddit **r/ReverseEngineering**, **r/malware**.
- Diễn đàn **tuts4you**, **0x00sec**.
- Hashtag và cộng đồng **#malware**, **#RE** trên các mạng xã hội kỹ thuật.

## Cách dùng trang này

Đừng cố nạp hết. Gợi ý lộ trình tự học song song với series:
1. Bắt đầu gỡ **crackmes.one mức 1** ngay từ khi học xong Phần 2.
2. Mỗi phần ngôn ngữ học xong, tìm một crackme đúng ngôn ngữ đó mà làm.
3. Khi thấy đủ tự tin, nhảy vào **picoCTF** rồi **Flare-On mùa cũ**.
4. Theo mảng nào thì đào sâu sách và sân luyện của mảng đó.
