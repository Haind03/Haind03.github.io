---
title: "Bài 6.6: Frida trên Android, sửa hành vi app lúc nó đang chạy"
date: 2026-10-06 08:49:00 +0700
categories: ["Technique Reverse", "Phần 6 · Java / Kotlin / Android (JADX)"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
Đọc tĩnh một APK trong JADX cho bạn biết app định làm gì. Nhưng nhiều lúc bạn muốn tận mắt thấy một giá trị lúc runtime, hoặc thử đổi kết quả một hàm để xem app phản ứng ra sao mà không phải patch rồi đóng gói lại cả APK. Đó là lúc Frida vào cuộc. Nó cho bạn chen vào bất kỳ method Java nào lúc app chạy, đọc tham số, đổi giá trị trả về, tất cả bằng vài dòng JavaScript.

Nói thẳng về ranh giới trước: những gì trong bài này là kỹ thuật kiểm thử bảo mật (security testing). Dùng trên app của chính bạn, app bạn được phép kiểm thử, hoặc app luyện tập như OWASP UnCrackable. Hook để qua mặt kiểm tra bản quyền của app người khác, hay gian lận trong game online, là chuyện khác và không nằm trong phạm vi series. Công cụ trung lập, mục đích mới quyết định.

## Frida hoạt động thế nào

Frida là một dynamic instrumentation toolkit. Trên Android, mô hình gồm hai phần:

- **frida-server**: một binary chạy trên thiết bị (thường cần root) hoặc trên emulator. Nó là cánh tay nối dài, chịu trách nhiệm chèn code vào tiến trình app.
- **frida / objection**: công cụ chạy trên máy tính của bạn (host), nói chuyện với frida-server qua USB hoặc TCP, nạp script của bạn vào app.

Script bạn viết bằng JavaScript. Frida tiêm một JS engine vào tiến trình app, và từ trong đó script của bạn gọi được vào runtime của Android, nắm lấy class và method Java như thể bạn đang viết Java vậy.

## Dựng môi trường

Các bước tối thiểu, giả định bạn đã có một emulator hoặc thiết bị đã root:

```bash
# trên host
pip install frida-tools

# tải frida-server đúng kiến trúc thiết bị (vd arm64) từ GitHub của Frida
# đẩy lên thiết bị và chạy
adb push frida-server /data/local/tmp/
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "su -c /data/local/tmp/frida-server &"

# kiểm tra host thấy thiết bị
frida-ps -U        # liệt kê tiến trình qua USB
```

`frida-ps -U` liệt kê được app là môi trường đã thông. Phiên bản frida-server phải khớp phiên bản frida-tools trên host, lệch version là lỗi ngay, đây là cái bẫy số một của người mới.

## Hook method Java: ba mẫu bạn dùng mãi

Mọi script Android bắt đầu bằng `Java.perform`, bên trong lấy class bằng `Java.use`, rồi ghi đè implementation của method. Ba việc hay làm nhất:

### 1. Đổi giá trị trả về

Giả sử app có `SecurityCheck.isRooted()` trả về `true` khi phát hiện máy đã root, và app từ chối chạy. Bạn hook để nó luôn trả `false`:

```javascript
Java.perform(function () {
    var SecurityCheck = Java.use("com.example.app.SecurityCheck");
    SecurityCheck.isRooted.implementation = function () {
        console.log("[*] isRooted() bị gọi, ép trả về false");
        return false;   // bỏ qua giá trị thật, trả cái ta muốn
    };
});
```

### 2. Log tham số và kết quả thật

Khi muốn hiểu một hàm nhận gì và trả gì mà không đổi hành vi, gọi method gốc rồi in ra:

```javascript
Java.perform(function () {
    var Checker = Java.use("com.example.app.LicenseChecker");
    Checker.validate.implementation = function (input) {
        console.log("[*] validate() input = " + input);
        var ret = this.validate(input);   // gọi bản gốc
        console.log("[*] validate() trả về = " + ret);
        return ret;
    };
});
```

Mẹo quan trọng: `this.validate(input)` gọi lại chính method gốc. Nhờ vậy bạn quan sát mà không phá logic, rất hợp để lần ra thuật toán kiểm tra.

### 3. Method bị overload

Nếu một method có nhiều overload, Frida bắt bạn chỉ rõ chữ ký, nếu không nó báo lỗi ambiguous:

```javascript
var Util = Java.use("com.example.app.Util");
Util.check.overload("java.lang.String", "int").implementation = function (s, n) {
    return true;
};
```

Chạy script:

```bash
frida -U -f com.example.app -l hook.js        # spawn app kèm script
# hoặc attach vào app đang chạy:
frida -U com.example.app -l hook.js
```

`-f` spawn app từ đầu (bắt được cả code chạy sớm), còn attach thì gắn vào tiến trình đang sống.

## JADX sinh sẵn snippet cho bạn

Không cần gõ tay class name dài loằng ngoằng. Trong JADX-GUI (bài [6.3](/posts/tr-6-3-jadx-gui-chuyen-sau/)), chuột phải vào một method rồi chọn **Copy as Frida snippet**. Nó sinh sẵn khung `Java.use(...).implementation` đúng class và chữ ký, bạn chỉ việc dán vào script và điền phần thân. Đây là cách nhanh nhất để đi từ "tìm thấy hàm trong decompiler" sang "hook được nó".

## SSL pinning và vì sao cần vượt qua khi kiểm thử

Nhiều app ghim chứng chỉ (SSL pinning) để từ chối mọi kết nối không đúng certificate định sẵn. Tốt cho bảo mật, nhưng khi bạn kiểm thử chính app của mình và muốn xem traffic qua Burp/mitmproxy, pinning chặn luôn cả bạn. Giải pháp trong kiểm thử là hook lớp kiểm tra chứng chỉ để nó chấp nhận proxy của bạn.

Cách nhanh nhất là dùng objection, lớp tự động hoá dựng trên Frida:

```bash
pip install objection
objection -g com.example.app explore
# trong shell objection:
android sslpinning disable
android root disable
```

Hai lệnh này gói sẵn hàng loạt hook phổ biến cho pinning và root detection, đỡ phải tự viết. Khi objection không xử lý được cơ chế lạ, bạn quay lại viết hook Frida tay cho đúng lớp đó.

## Cạm bẫy hay gặp

- **Lệch version** giữa frida-server và frida-tools: lỗi khó hiểu, luôn kiểm tra trước.
- **Class chưa được nạp** lúc bạn hook: dùng `-f` để spawn sớm, hoặc hook ClassLoader.
- **Tên method sau obfuscation**: nếu app bị R8/ProGuard (bài [6.8](/posts/tr-6-8-obfuscation-android/)) đổi tên, class name trong snippet cũng là tên rối, cứ dùng đúng tên rối đó.
- **Phát hiện Frida**: app phòng thủ có thể dò frida-server qua cổng 27042 hoặc tên tiến trình. Khi đó cần chạy frida-server đổi tên/đổi cổng, hoặc dùng gadget nhúng.

## Lab tự làm

Xem [labs/6.6/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/6.6). Bạn sẽ hook một method trong app luyện tập của chính mình để đổi giá trị trả về, và quan sát app đổi hành vi theo. File `src/hook.js` là script mẫu để bạn sửa.

## Checklist ghi nhớ
- Frida gồm frida-server trên thiết bị và frida/objection trên host, version hai bên phải khớp.
- Mẫu cốt lõi: `Java.perform` rồi `Java.use("class").method.implementation = function(){...}`.
- Gọi `this.method(...)` để chạy bản gốc, dùng khi chỉ muốn log mà không đổi hành vi.
- Method overload phải chỉ rõ bằng `.overload(...)`.
- JADX Copy as Frida snippet sinh sẵn khung hook đúng chữ ký.
- objection gói sẵn hook cho SSL pinning và root detection.
- Chỉ dùng trên app của mình hoặc được phép, đây là kiểm thử bảo mật chứ không phải gian lận.
