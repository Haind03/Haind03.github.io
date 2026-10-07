---
title: "Bài 6.3: JADX-GUI chuyên sâu, công cụ số một để mổ APK"
date: 2026-10-06 08:46:00 +0700
categories: ["Technique Reverse", "Phần 6 · Java / Kotlin / Android (JADX)"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
Nếu reverse .NET có dnSpy thì reverse Android có JADX. Mở một APK lên, chờ vài giây, và bạn có gần như toàn bộ source Java hiện ra. Nhưng phần lớn người mới chỉ dùng JADX ở mức "mở ra rồi cuộn đọc", bỏ phí những tính năng làm nên khác biệt giữa ngồi cả buổi và tìm ra chỗ cần trong mười phút. Bài này là những tính năng đó.

JADX đã có sẵn trong repo này tại `jadx-gui-1.5.1-win`, chạy `jadx-gui.exe` là xong, không cần cài gì.

## Mở cái gì được

JADX nuốt khá nhiều định dạng, kéo thả vào là chạy:

- **APK**: nó tự giải nén, gộp mọi `classes.dex` (kể cả multidex), decompile ra Java, và parse luôn `AndroidManifest.xml` cùng resource.
- **DEX**: file bytecode Android trần.
- **JAR / .class**: bytecode JVM thường.
- **AAB, ZIP, XAPK**: các dạng đóng gói khác.

Với APK, việc đầu tiên nên làm là mở `AndroidManifest.xml` trong cây **Resources**, tìm activity có `android.intent.action.MAIN` để biết màn hình khởi động, đó là điểm vào của app. Thói quen này giống như tìm `main` khi reverse native.

## Cây bên trái và hai cách nhìn code

Panel trái có hai nhánh chính: **Source code** (các package Java đã decompile) và **Resources** (manifest, string, layout, file trong assets). Click một class, panel phải hiện Java.

Điều nhiều người không biết: bạn xem được **smali song song**. Chuột phải vào class, chọn xem bytecode/smali, hoặc bật chế độ hiển thị cả hai. Khi JADX decompile sai (gặp code rối hoặc obfuscated), smali là sự thật, Java chỉ là bản dịch có thể lỗi. Lúc nghi ngờ, tụt xuống smali đối chiếu.

## Ba phím tắt làm nên tốc độ

Giống bộ ba `N`/`X`/comment trong IDA, JADX có bộ phím của nó. Xem thêm [cheatsheet](/posts/tr-tai-nguyen-cheatsheet/).

- **Tìm kiếm toàn cục (Ctrl+Shift+F)**: tìm text trong toàn bộ code đã decompile. Đây là vũ khí số một. Thấy app hiện "License invalid"? Search chuỗi đó, nhảy thẳng tới class dùng nó.
- **Find usage (x)**: đặt con trỏ lên một method/field/class rồi nhấn `x` để xem mọi nơi dùng nó. Đây chính là xref của JADX, cách bạn lần ngược từ một hàm tới nơi gọi nó.
- **Rename (n)**: đổi tên class/method/field/biến cho dễ đọc. JADX nhớ tên bạn đặt trong suốt phiên, và mỗi cái tên tốt làm code quanh nó sáng ra. Với app bị obfuscate thành `a.a.a`, rename là cách duy nhất giữ cho đầu bạn không nổ.

## Đi từ chuỗi, kỹ thuật vào việc nhanh nhất

Giống mọi nền tảng khác, cách nhanh nhất tìm logic quan trọng là đi từ chuỗi người dùng thấy. Trên Android chuỗi thường nằm hai nơi:

- Hard-code trong code: search thẳng bằng Ctrl+Shift+F.
- Trong `res/values/strings.xml`: nếu chuỗi hiển thị là một resource, tìm tên resource (ví dụ `login_failed`), lấy resource ID, rồi search ID đó (dạng `R.string.login_failed` hoặc giá trị hex `0x7f...`) trong code.

Tìm được chuỗi "Sai mật khẩu" hay "Premium activated" là tìm được gần đúng chỗ kiểm tra. Từ đó nhấn `x` lần ngược lên hàm gọi.

## Deobfuscation tự động

App thật gần như luôn chạy qua R8/ProGuard, biến tên thành `a`, `b`, `c`. JADX có tính năng đổi tên tự động: vào Preferences, bật **Deobfuscation**, đặt ngưỡng độ dài tên tối thiểu/tối đa. JADX sẽ sinh tên giả nhất quán (như `C0001a`) thay cho các tên một ký tự trùng nhau, giúp phân biệt được chúng. Nó không trả lại tên gốc (tên gốc đã mất khi build), nhưng làm code bớt loạn và cho phép bạn rename dần.

Mức obfuscation nặng hơn (string encryption, control flow) thì JADX bó tay phần đó, phải sang hướng động (Frida, xem [Bài 6.6](https://github.com/Haind03/Technique-Reverse/blob/main/phan-06-java-kotlin-android/6.6-frida-android-hook-bypass.md)) hoặc công cụ khác. Chi tiết các loại obfuscation ở [Bài 6.8](https://github.com/Haind03/Technique-Reverse/blob/main/phan-06-java-kotlin-android/6.8-obfuscation-android-r8-packer.md).

## Copy as Frida snippet, cầu nối sang hook động

Đây là tính năng JADX mà dân mobile rất thích. Chuột phải vào một method, chọn **Copy as Frida snippet**, JADX sinh sẵn đoạn JavaScript hook method đó bằng Frida, đúng tên class, đúng signature tham số. Bạn chỉ việc dán vào script Frida, thêm logic in tham số hoặc đổi giá trị trả về.

Ví dụ nó sinh ra khung kiểu:

```javascript
Java.perform(function () {
    var LoginActivity = Java.use("com.example.app.LoginActivity");
    LoginActivity.checkPassword.implementation = function (input) {
        console.log("checkPassword được gọi với: " + input);
        var ret = this.checkPassword(input);
        console.log("trả về: " + ret);
        return ret;
    };
});
```

Đây là cách nối tĩnh (JADX đọc code) với động (Frida quan sát/sửa lúc chạy). Tìm hàm trong JADX, sinh snippet, hook để xem giá trị thật hoặc ép nó trả về `true`.

## Xuất source ra để grep

Khi muốn tìm kiếm mạnh hơn tìm trong GUI, hoặc muốn mở trong editor quen thuộc, dùng **File > Save all** (Ctrl+Shift+S) để JADX xuất toàn bộ source Java ra thư mục. Sau đó `grep -r` thoải mái, hoặc mở bằng VS Code để điều hướng. Rất tiện khi muốn tìm pattern phức tạp (ví dụ mọi nơi gọi `Cipher.getInstance`).

## Lab tự làm

Làm trong [labs/6.3/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/6.3): mở một APK bằng JADX-GUI, đi từ một chuỗi tới code, rename cho dễ đọc, sinh Frida snippet cho một method, và xuất source ra để grep.

## Checklist ghi nhớ
- JADX mở APK/DEX/JAR/AAB, tự gộp multidex và parse manifest.
- Mở AndroidManifest tìm MAIN activity để biết điểm vào app.
- Ba phím chủ lực: Ctrl+Shift+F (search toàn cục), `x` (find usage, chính là xref), `n` (rename).
- Đi từ chuỗi người dùng thấy, qua resource ID nếu cần, rồi `x` lần ngược tới hàm kiểm tra.
- Bật Deobfuscation để làm dịu tên một ký tự, nhưng tên gốc đã mất.
- Copy as Frida snippet để nối sang hook động.
- Save all để xuất source ra grep ngoài GUI.
- Khi Java decompile trông sai, đối chiếu smali.
