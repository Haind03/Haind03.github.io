---
title: "Bài 6.2: Giải phẫu một file APK"
date: 2026-10-06 08:45:00 +0700
categories: ["Technique Reverse", "Phần 6 · Java / Kotlin / Android (JADX)"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
Lần đầu người ta đưa bạn một file `.apk` và bảo "xem thử app này làm gì", phản xạ hay gặp là kéo ngay vào JADX rồi lạc trong hàng nghìn class. Khoan. APK là một cái hộp có bố cục rõ ràng, và nhìn vào đúng chỗ trước sẽ tiết kiệm cả buổi. Bài này mở cái hộp đó ra xem bên trong có gì.

## APK thật ra chỉ là một file ZIP

![Bên trong một file APK: manifest, classes.dex, lib, resources, assets, META-INF](/assets/img/technique-reverse/assets/phan-06/apk-structure.svg)

Điều đầu tiên làm nhiều người ngạc nhiên: APK không có định dạng bí ẩn nào cả, nó là một file ZIP đổi tên. Bạn đổi đuôi `.apk` thành `.zip` rồi giải nén bằng công cụ bất kỳ là thấy hết ruột gan. Thử ngay với bất kỳ app nào trên máy.

Bên trong một APK điển hình:

```
app.apk  (ZIP)
├── AndroidManifest.xml     khai báo app: component, permission, entry
├── classes.dex             bytecode Java/Kotlin (có thể có classes2.dex...)
├── resources.arsc          bảng tài nguyên đã biên dịch (string, layout id...)
├── res/                    tài nguyên: layout, drawable, values
├── lib/                    thư viện native .so, chia theo ABI
│   ├── arm64-v8a/
│   ├── armeabi-v7a/
│   └── x86_64/
├── assets/                 file thô app tự đọc (model, config, script...)
└── META-INF/               chữ ký và manifest của chính file ZIP
```

Không phải cái nào cũng đáng xem như nhau. Khi triage, thứ tự tôi nhìn là: AndroidManifest trước (để biết điểm vào), rồi classes.dex (logic chính), rồi lib/ nếu thấy có native (logic nhạy cảm hay bị đẩy xuống đây), cuối cùng assets/ khi nghi có dữ liệu giấu trong đó.

## AndroidManifest.xml, đọc cái này trước tiên

Manifest là bản khai báo của app: nó gồm những component gì, xin những quyền gì, và quan trọng nhất với người reverse, **màn hình nào chạy đầu tiên**.

Có một bẫy: manifest trong APK không phải XML chữ thường mà là binary XML (AXML) đã được mã hoá nhị phân, mở bằng text editor sẽ ra ký tự rác. Phải dùng công cụ giải mã:
- Kéo APK vào **JADX**, nó tự hiển thị manifest dạng đọc được.
- Hoặc `apktool d app.apk`, apktool giải manifest và tài nguyên về dạng text.

Thứ cần tìm trong manifest:
- **Launcher activity**: activity có intent-filter với `android.intent.action.MAIN` và `android.intent.category.LAUNCHER`. Đây là màn hình mở đầu, là nơi bắt đầu lần theo luồng.
- **Application class** (thuộc tính `android:name` trong thẻ `<application>`): nếu có, class này chạy trước cả activity đầu, nhiều app đặt khởi tạo và cả chống phân tích ở đây.
- **Permission**: `<uses-permission>` kể app đụng tới gì (internet, SMS, danh bạ, vị trí). Danh sách quyền cho bạn hình dung nhanh app thuộc loại gì, giống như đọc import của một PE vậy.
- **Exported component**: component có `android:exported="true"` là bề mặt có thể bị gọi từ ngoài, đáng chú ý khi đánh giá bảo mật.

## classes.dex, nơi logic nằm

Code Java và Kotlin sau khi biên dịch không nằm trong các file `.class` rời như trên máy tính để bàn, mà được gộp và chuyển thành một file duy nhất: `classes.dex`, chứa DEX bytecode (Dalvik Executable).

Điểm khác cốt lõi so với JVM bytecode thường:
- **.class của JVM là stack-based**: lệnh đẩy toán hạng lên một stack rồi thao tác.
- **DEX là register-based**: lệnh làm việc trực tiếp trên các register ảo (v0, v1, v2...). Gần với assembly thật hơn, và gọn hơn.

Bạn hiếm khi đọc DEX thô. Chuỗi công cụ thông thường là DEX được decompiler (JADX, CFR...) dựng ngược về Java gần như đọc được. Khi cần sửa, người ta xuống mức trung gian smali (dạng text của DEX bytecode), nói ở Bài 6.4.

### Multidex

Một file DEX có giới hạn lịch sử khoảng 65536 method (giới hạn của chỉ số tham chiếu method 16-bit). App lớn vượt qua bằng multidex: `classes.dex`, `classes2.dex`, `classes3.dex`... Khi phân tích, nhớ là code có thể nằm rải ở nhiều file dex, đừng chỉ nhìn cái đầu. JADX gộp tất cả lại cho bạn nên thường không phải lo, nhưng khi dùng apktool thủ công thì phải để ý.

## lib/, khi logic trốn xuống native

Thư mục `lib/` chứa thư viện native dạng `.so` (ELF shared object, giống Linux), chia theo kiến trúc CPU (ABI): `arm64-v8a` cho điện thoại 64-bit hiện nay, `armeabi-v7a` cho máy cũ, `x86_64` cho emulator.

Vì sao người reverse quan tâm: logic nhạy cảm (kiểm tra license, mã hoá, chống gian lận, phần lõi của game) hay được viết bằng C/C++ qua JNI và nhét vào `.so` để khó đọc hơn Java nhiều. Thấy app có `.so` lớn là biết phần thú vị có thể không nằm trong Java mà ở native. Lúc đó bạn chuyển file `.so` sang IDA hoặc Ghidra và reverse như một binary ARM bình thường (nhớ lại Bài 1.9 về ARM64). Cầu nối Java gọi xuống native là JNI, chủ đề của Bài 6.7.

## assets/ và resources, đừng bỏ qua

`assets/` chứa file thô app tự đọc lúc chạy: cấu hình, model machine learning, script, đôi khi cả một dex/so thứ cấp được nạp động (dấu hiệu của packer, xem Bài 6.8). `res/` và `resources.arsc` chứa tài nguyên giao diện và chuỗi; chuỗi trong `res/values/strings.xml` nhiều khi chứa URL, key, thông báo lỗi hữu ích cho việc lần theo.

## META-INF, chữ ký

`META-INF/` chứa chữ ký của APK (file `.RSA`/`.SF`/`.MF` với scheme v1, còn v2 trở lên ký trong block riêng của file ZIP). Bạn không đọc để hiểu logic, nhưng nhớ một điều quan trọng: **mọi APK cài lên máy đều phải được ký**. Khi bạn sửa app rồi đóng gói lại (Bài 6.4), chữ ký cũ hỏng, phải ký lại bằng key của mình thì mới cài được. Đó là lý do có bước re-sign.

## Lab tự làm

Thực hành ở `labs/6.2/`. Tóm tắt nhiệm vụ: lấy một APK bất kỳ (app miễn phí tải về, hoặc APK bạn tự build), giải nén nó như file ZIP, nhận diện từng thành phần, mở AndroidManifest bằng JADX hoặc apktool để tìm launcher activity và danh sách permission, rồi liệt kê các native lib trong `lib/`. Mục tiêu là quen tay với bố cục trước khi lao vào đọc code.

## Checklist ghi nhớ
- APK là file ZIP, giải nén ra xem được hết thành phần.
- Đọc AndroidManifest trước: tìm launcher activity, application class, permission.
- Manifest là binary XML, phải mở bằng JADX/apktool chứ không phải text editor.
- classes.dex chứa code, là DEX bytecode register-based (khác JVM stack-based); app lớn dùng multidex.
- lib/ chứa `.so` native theo ABI, logic nhạy cảm hay trốn xuống đây, chuyển sang IDA/Ghidra.
- Mọi APK phải được ký; sửa xong phải ký lại mới cài được.
