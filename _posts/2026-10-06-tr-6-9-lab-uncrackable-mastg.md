---
title: "Bài 6.9: Lab lớn, giải OWASP UnCrackable Level 1 tới 3"
date: 2026-10-06 08:52:00 +0700
categories: ["Technique Reverse", "Phần 6 · Java / Kotlin / Android (JADX)"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
Đây là bài gom lại mọi thứ của Phần 6. Thay vì một crackme tôi tự nặn ra, lần này ta chơi với bộ bài chuẩn mà cả ngành dùng để luyện: OWASP UnCrackable App for Android, nằm trong MASTG (Mobile Application Security Testing Guide). Ba level, khó dần, mỗi level dạy đúng một nhóm kỹ thuật bạn vừa học.

Vì sao dùng bộ này mà không phải app ngoài kia: nó hợp pháp tuyệt đối. Mã nguồn mở, làm ra để học, OWASP khuyến khích bạn bẻ. Không có chuyện vi phạm bản quyền hay điều khoản dịch vụ như khi đụng vào app thương mại. Đây là sân tập đúng nghĩa.

Tải chính thức từ kho MASTG (link trong [labs/6.9/README.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/6.9/README.md)). Đừng tải APK trôi nổi ở nơi khác, bản chính thức mới sạch và đúng đề.

## Luật chơi chung

Cả ba app đều hiện một ô nhập, bạn gõ đúng secret thì nó báo thành công. Nhiệm vụ: tìm ra secret, hoặc làm cho app tin là bạn đã nhập đúng. Có hai trường phái, và một reverser giỏi biết cả hai:

- **Tĩnh (static):** mở app trong JADX, đọc code, moi thẳng secret hoặc hiểu thuật toán kiểm tra rồi tính ngược. Không cần chạy app.
- **Động (dynamic):** chạy app trên máy/emulator, dùng Frida hook vào đúng hàm kiểm tra để đọc giá trị thật hoặc ép nó trả về đúng.

Level càng cao, hướng tĩnh càng đuối và bạn càng phải dựa vào động, đặc biệt khi secret bị đẩy xuống native hoặc app chủ động chống lại bạn.

## Level 1: root detection và secret trong Java

Mở `UnCrackable-Level1.apk` bằng JADX-GUI. Đọc `AndroidManifest.xml` tìm launcher activity (nhớ lại [Bài 6.2](/posts/tr-6-2-cau-truc-apk/)), từ đó lần vào `MainActivity`.

Hai thứ đập vào mắt ngay:

1. **Root detection.** Trong `onCreate`, app gọi vài hàm kiểu `c.a()`, `c.b()`, `c.c()` kiểm tra thiết bị có root không (tìm file `su`, kiểm `test-keys`, thư mục Superuser). Nếu phát hiện, nó bật một dialog rồi thoát. Đây là lớp phòng thủ đầu tiên, và nó yếu.

2. **Hàm verify.** Khi bạn bấm nút, app gọi một hàm (thường là `a.a(input)`) so chuỗi bạn nhập với một secret. Theo đúng nếp đi-từ-chuỗi và find usage (`x`) trong JADX (nhắc lại [Bài 6.3](/posts/tr-6-3-jadx-gui-chuyen-sau/)), bạn lần tới hàm so sánh.

### Hướng tĩnh
Hàm kiểm tra giải mã secret bằng AES với key cứng nhúng trong code, rồi so với input. Vì key và ciphertext đều nằm trong app, bạn chép thuật toán ra, chạy lại bằng Python hoặc một đoạn Java nhỏ, in ra secret. Đọc xong là có đáp án, không cần cài app.

### Hướng động
Nếu lười giải AES, cho app chạy rồi hook. Nhưng app thoát ngay vì root detection, nên trước hết phải vô hiệu hóa nó. Dùng Frida hook các hàm detection trả về false, và hook luôn `System.exit` cho chắc. Sau đó hook hàm verify để in ra chuỗi mà nó đem so, chính là secret. Script mẫu nằm trong [labs/6.9/solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/6.9/solution.md).

Điểm rút ra của Level 1: root detection chỉ là cái khóa cửa giấy. Nó chặn người dùng thường, không chặn được người cầm Frida.

## Level 2: secret chui xuống native .so

Level 2 nhìn giống Level 1, nhưng khi bạn tìm hàm verify trong JADX, nó khai báo `native`:

```java
public native boolean bar(byte[] bar);
```

Nghĩa là logic kiểm tra không còn trong Java nữa, nó nằm trong `lib/arm64-v8a/libfoo.so`. Đây đúng tình huống của [Bài 6.7](/posts/tr-6-7-native-so-jni/).

### Hướng tĩnh
Trích `libfoo.so` ra (giải nén APK), mở trong Ghidra ở chế độ AArch64 (ôn lại [Bài 1.9](/posts/tr-1-9-arm-arm64-co-ban/)). Tìm hàm JNI theo tên `Java_sg_vantagepoint_uncrackable2_..._bar` hoặc, nếu nó đăng ký động, đi qua `JNI_OnLoad` và `RegisterNatives`. Đọc hàm đó, bạn thấy nó so byte input với một chuỗi cứng trong `.so`. Moi chuỗi đó ra là xong.

### Hướng động
Native thì hook khó hơn Java một chút nhưng vẫn làm được. Hai cách:
- Hook hàm `strcmp`/`memcmp` của libc, in hai toán hạng khi app so sánh. Secret lộ ra trần trụi, giống hệt mẹo đọc hai toán hạng `cmp` trong [Bài 2.5](/posts/tr-2-5-x64dbg/) nhưng ở tầng native.
- Hook thẳng hàm `bar` native bằng `Interceptor.attach` tại địa chỉ của nó trong module.

Điểm rút ra của Level 2: đẩy secret xuống native làm chậm người đọc tĩnh, nhưng runtime thì byte vẫn phải đi qua một phép so sánh, và chỗ so sánh luôn là nơi phục kích tốt.

## Level 3: thêm anti-tampering và anti-Frida

Level 3 là Level 2 cộng thêm phòng thủ chủ động, đúng tinh thần [Bài 6.8](/posts/tr-6-8-obfuscation-android/) và báo trước cho cả Chặng 3 về anti-reverse:

- **Anti-tampering:** app kiểm tra chữ ký APK và checksum của chính nó. Nếu bạn repack bằng apktool rồi ký lại (cách của [Bài 6.4](/posts/tr-6-4-smali-apktool-repack/)), chữ ký đổi, app phát hiện và từ chối chạy. Nên hướng repack tĩnh vấp ngay ở đây.
- **Anti-Frida:** app dò xem có frida-server đang chạy không (quét cổng 27042, tìm chuỗi "frida" trong maps, kiểm tên tiến trình). Nếu thấy, nó thoát.

### Cách tiếp cận
Đây là lúc bạn phải gỡ từng lớp theo thứ tự:

1. **Qua anti-Frida trước.** Hook sớm (early instrumentation, dùng `frida -f` để spawn chứ không attach muộn) các hàm dò Frida và cho chúng trả về âm tính. Hoặc dùng frida-server đổi tên, đổi cổng để né cách dò ngây thơ.
2. **Qua anti-tampering.** Hook hàm kiểm chữ ký trả về đúng giá trị của app gốc, hoặc hook hàm so checksum.
3. **Rồi mới tới verify**, xử lý y như Level 2 (phân tích .so hoặc hook so sánh).

Thứ tự quan trọng: bạn không hook được verify nếu app đã thoát vì phát hiện Frida. Gỡ phòng thủ ngoài cùng trước, đi dần vào trong. Đây chính là tư duy xử lý nhiều lớp anti kết hợp mà [Bài 15.10](https://github.com/Haind03/Technique-Reverse/tree/main/phan-15-anti-reverse) sẽ nói kỹ.

Điểm rút ra của Level 3: khi app chống lại công cụ của bạn, trận đấu chuyển thành gỡ-lớp. Kiên nhẫn, mỗi lần một lớp, và luôn để dành chỗ so sánh cuối cùng làm điểm phục kích.

## Chọn hướng nào

| Tình huống | Nên ưu tiên |
|---|---|
| Secret là chuỗi cứng trong Java | Tĩnh, đọc thẳng trong JADX |
| Có thuật toán kiểm tra rõ ràng | Tĩnh, tính ngược (như keygen Bài 3.6) |
| Secret trong native .so | Tĩnh đọc .so, hoặc động hook strcmp |
| App chống lại bạn (anti-*) | Động, gỡ từng lớp bằng Frida |

Phần lớn người mới nhảy ngay vào Frida vì thấy ngầu. Lời khuyên thật lòng: thử đọc tĩnh trước. Rất nhiều lần secret nằm ngay đó, năm phút đọc JADX nhanh hơn nửa tiếng vật lộn với frida-server.

## Checklist ghi nhớ
- UnCrackable (MASTG) là bộ luyện Android hợp pháp, tải từ kho chính thức.
- Level 1: root detection yếu + secret trong Java, đọc tĩnh hoặc hook là xong.
- Level 2: secret trong native .so, phân tích .so hoặc hook strcmp/memcmp runtime.
- Level 3: thêm anti-tampering và anti-Frida, phải gỡ từng lớp từ ngoài vào trong.
- Luôn cân nhắc hướng tĩnh trước, nhiều khi nhanh hơn hẳn động.
- Chỗ so sánh cuối cùng luôn là điểm phục kích tốt nhất, dù ở tầng Java hay native.
