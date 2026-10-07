---
title: "Bài 12.3: Reverse app iOS, từ file IPA tới hook runtime"
date: 2026-10-06 09:14:00 +0700
categories: ["Technique Reverse", "Phần 12 · Swift / Objective-C (macOS, iOS)"]
tags: [reverse-engineering, ios, swift]
render_with_liquid: false
---
Reverse iOS khác Android ở một điểm làm nản lòng người mới: bạn không chỉ cần hiểu Mach-O và Objective-C/Swift, mà trước đó phải vượt qua một lớp mã hoá của Apple và gần như luôn cần một thiết bị đã jailbreak. Bài này đi từ file IPA tới lúc bạn hook được method đang chạy, và nói thẳng chỗ nào cần thiết bị thật.

Nhắc lại ranh giới ở [Bài 0.2](/posts/tr-0-2-phap-ly-dao-duc/): mọi thứ dưới đây là để kiểm thử bảo mật trên app của chính bạn hoặc app bạn được phép, không phải để bẻ khoá app của người khác.

## IPA chỉ là một file ZIP

Giống APK bên Android, file `.ipa` thực ra là ZIP. Đổi đuôi thành `.zip` rồi giải nén là thấy cấu trúc:

```
Payload/
  TenApp.app/
    TenApp            <- Mach-O binary, phần quan trọng nhất
    Info.plist        <- metadata: bundle id, phiên bản, quyền, URL scheme
    embedded.mobileprovision  <- profile ký
    Assets.car        <- asset đã biên dịch
    *.nib, *.storyboardc, *.lproj ...
```

File đáng quan tâm là Mach-O binary cùng tên với app (không có đuôi). `Info.plist` đọc trước để biết bundle identifier, minimum iOS version, các permission (NSCameraUsageDescription...) và URL scheme. Nó giống vai trò của AndroidManifest.

## Rào cản: mã hoá FairPlay

Đây là chỗ iOS khác hẳn. Binary tải từ App Store bị Apple mã hoá bằng FairPlay DRM: phần `__TEXT` (chứa code) được mã hoá, chỉ giải mã trong bộ nhớ lúc chạy trên thiết bị có đúng license. Cột `cryptid` trong load command `LC_ENCRYPTION_INFO` bằng 1 là dấu hiệu binary còn mã hoá.

Hệ quả thực tế: nếu bạn kéo thẳng binary từ IPA App Store vào IDA/Ghidra, phần code chỉ là rác đã mã hoá. Phải lấy bản đã giải mã trước.

Cách lấy bản giải mã là để thiết bị tự giải mã trong RAM (như nó vẫn làm khi chạy app) rồi dump vùng nhớ đó ra:

- **frida-ios-dump**: script Python chạy qua Frida, phổ biến nhất hiện nay. Nó chạy app, đọc vùng `__TEXT` đã giải mã trong bộ nhớ, ghi đè vào binary rồi đặt `cryptid` về 0, đóng lại thành IPA giải mã.
- **bagbak**: tool mới hơn, cùng ý tưởng, dựa Frida.
- **Clutch**: tool cũ, nhiều khi hỏng trên iOS mới, chỉ nhắc để bạn nhận ra tên.

Tất cả đều cần thiết bị **đã jailbreak** (hoặc một môi trường tương đương) vì phải đọc bộ nhớ tiến trình của app khác. Đây là điểm chặn lớn nhất với người học iOS: không có thiết bị jailbreak thì gần như không đi tiếp được với app App Store. App do chính bạn build và cài qua Xcode thì không bị FairPlay, dùng để học thì tiện hơn nhiều.

## Sau khi giải mã: phân tích như Mach-O

Khi đã có binary giải mã (`cryptid` = 0), phần còn lại chính là những gì đã học:

- Đây là Mach-O, nhắc lại [Bài 1.8](/posts/tr-1-8-elf-va-mach-o/). Nhớ kiểm tra fat binary và kiến trúc arm64.
- Nếu app viết Objective-C: đọc theo `objc_msgSend` và selector như [Bài 12.1](/posts/tr-12-1-objc-runtime-class-dump/), chạy class-dump lấy header.
- Nếu app viết Swift: demangle và đọc metadata như [Bài 12.2](https://github.com/Haind03/Technique-Reverse/blob/main/phan-12-swift-objc-apple/12.2-swift-metadata-demangle.md).
- Code là ARM64, xem lại [Bài 1.9](/posts/tr-1-9-arm-arm64-co-ban/).

Nói cách khác, FairPlay chỉ là một cánh cửa. Qua được rồi thì công cụ và tư duy y như phân tích một Mach-O bình thường.

## Hook runtime với Frida và objection

Phân tích tĩnh cho bạn bản đồ, nhưng iOS rất hợp với phân tích động vì ObjC runtime cho phép can thiệp sạch sẽ. Cài frida-server trên thiết bị jailbreak, chạy frida/objection trên máy host.

**objection** là lớp tự động hoá trên Frida, làm nhanh các việc hay gặp mà không phải viết script:

```
objection -g com.example.myapp explore
# trong shell objection:
ios hooking list classes                 # liệt kê class
ios hooking watch class LoginViewController   # theo dõi method của class
ios hooking set return_value "...:isJailbroken" false   # ép trả về
ios sslpinning disable                    # tắt SSL pinning để xem traffic
ios jailbreak disable                     # bypass jailbreak detection
```

Khi cần kiểm soát kỹ hơn thì viết script Frida. ObjC method hook qua `ObjC.classes`:

```js
if (ObjC.available) {
  var LoginVC = ObjC.classes.LoginViewController;
  Interceptor.attach(LoginVC['- checkPassword:'].implementation, {
    onEnter: function (args) {
      // args[0]=self, args[1]=selector, args[2]=tham số đầu
      var pw = new ObjC.Object(args[2]);
      console.log('[+] checkPassword gọi với: ' + pw.toString());
    },
    onLeave: function (retval) {
      console.log('[+] trả về: ' + retval);
      retval.replace(ptr(1));   // ép trả về true
    }
  });
}
```

Hai tình huống kinh điển trong kiểm thử bảo mật app của mình:

- **Jailbreak detection**: app tự từ chối chạy khi thấy thiết bị jailbreak. Hook hàm kiểm tra (thường trả về BOOL) cho trả về false, hoặc dùng `ios jailbreak disable`.
- **SSL pinning**: app chỉ chấp nhận đúng certificate nên proxy như Burp không đọc được traffic. Tắt pinning để phân tích lưu lượng của chính app mình, phục vụ kiểm thử.

## Cạm bẫy hay gặp

- Quên app App Store còn mã hoá FairPlay, cứ thế mở IDA và tưởng binary hỏng. Luôn kiểm `cryptid` trước.
- Không có thiết bị jailbreak mà cố phân tích app App Store: gần như bế tắc. Hãy bắt đầu bằng app bạn tự build.
- Lệch phiên bản giữa frida-server trên thiết bị và frida trên host làm hook im lặng không chạy.
- Swift method nhiều khi không lộ selector đẹp như ObjC, phải demangle và dựa metadata.

## Lab tự làm

Xem [labs/12.3/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/12.3). Cần một thiết bị iOS đã jailbreak và một app do chính bạn làm (hoặc được phép). Nhiệm vụ: dump binary giải mã, xác nhận `cryptid` về 0, phân tích Mach-O, rồi hook một method bằng objection. File `src/hook.js` có script Frida iOS mẫu.

## Checklist ghi nhớ
- IPA là ZIP, binary quan trọng là Mach-O cùng tên app, đọc Info.plist trước.
- App Store binary bị FairPlay mã hoá `__TEXT`, kiểm `cryptid` = 1, phải dump bản giải mã từ bộ nhớ.
- Dump bằng frida-ios-dump/bagbak, cần thiết bị jailbreak. App tự build không bị mã hoá.
- Sau giải mã thì phân tích như Mach-O ObjC/Swift (Bài 12.1, 12.2), code ARM64 (Bài 1.9).
- Frida/objection để hook runtime, bypass jailbreak detection và SSL pinning khi kiểm thử app của mình.
