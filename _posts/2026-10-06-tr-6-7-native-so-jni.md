---
title: "Bài 6.7: Thư viện native .so và JNI, nơi logic trốn khỏi JADX"
date: 2026-10-06 08:50:00 +0700
categories: ["Technique Reverse", "Phần 6 · Java / Kotlin / Android (JADX)"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
Bạn mở APK trong JADX, tìm hàm kiểm tra license, và thấy nó chỉ có đúng một dòng: `public native boolean checkLicense(String s);`. Hết. Không có thân hàm để đọc. Logic thật đã bị đẩy xuống một thư viện native `lib/arm64-v8a/libcheck.so`, nơi JADX bó tay vì đó là machine code ARM64 chứ không còn là bytecode Java. Đây là cách phổ biến nhất để làm khó người reverse app Android: cái gì quan trọng thì viết bằng C/C++.

Tin tốt: bạn đã học ARM64 ở [Bài 1.9](/posts/tr-1-9-arm-arm64-co-ban/). Phần còn lại chỉ là biết cách bắc cầu từ method Java sang đúng hàm trong file .so.

## JNI là cây cầu giữa Java và native

![JNI bắc cầu từ Java sang hàm native trong file .so](/assets/img/technique-reverse/assets/phan-06/jni-bridge.svg)

JNI (Java Native Interface) là cơ chế cho Java gọi code C/C++. Luồng cơ bản:

1. Lớp Java nạp thư viện: `System.loadLibrary("check")` sẽ nạp `libcheck.so`.
2. Khai báo method là `native`, không có thân: `public native boolean checkLicense(String s);`.
3. Trong `libcheck.so` có một hàm C cài đặt thật sự cho method đó.

Khi Java gọi `checkLicense`, runtime tìm hàm native tương ứng và nhảy vào. Việc của bạn là tìm ra hàm native đó trong file .so.

## Hai cách Java tìm được hàm native

Đây là chỗ mấu chốt, và cũng là nơi tác giả app hay giở trò.

### Cách 1: đặt tên theo quy ước (static linking)

Mặc định, JNI tìm hàm C theo một cái tên dài dằng dặc ghép từ package + class + method:

```
Java_<package>_<class>_<method>
```

Ví dụ method `checkLicense` trong class `com.example.app.Native` sẽ ứng với hàm C tên:

```
Java_com_example_app_Native_checkLicense
```

Dấu chấm trong package thành dấu gạch dưới. Cái hay là bạn mở .so trong Ghidra, vào danh sách export/symbol, gõ tìm `Java_` là ra ngay tất cả hàm native, kèm tên đầy đủ nói rõ nó thuộc method Java nào. Rất dễ.

### Cách 2: đăng ký động qua RegisterNatives (khó hơn)

Tác giả muốn giấu thì không dùng tên quy ước. Thay vào đó, trong hàm đặc biệt `JNI_OnLoad` (chạy ngay khi thư viện được nạp), họ gọi `RegisterNatives` để tự tay ánh xạ tên method Java sang một con trỏ hàm bất kỳ:

```c
JNIEXPORT jint JNI_OnLoad(JavaVM *vm, void *reserved) {
    // ... lấy JNIEnv ...
    JNINativeMethod methods[] = {
        { "checkLicense", "(Ljava/lang/String;)Z", (void*)sub_1234 }
    };
    (*env)->RegisterNatives(env, clazz, methods, 1);
    return JNI_VERSION_1_6;
}
```

Lúc này hàm thật tên gì cũng được (ví dụ `sub_1234`), không có `Java_` để tìm. Quy trình xử lý:

1. Tìm `JNI_OnLoad` trong .so (nó luôn là export, luôn có mặt nếu app dùng cách này).
2. Đọc code trong đó, tìm lời gọi `RegisterNatives`.
3. `RegisterNatives` nhận một mảng struct `JNINativeMethod`, mỗi phần tử gồm: con trỏ tới tên method, con trỏ tới chuỗi signature, và con trỏ tới hàm cài đặt. Đọc mảng đó là biết method `checkLicense` ứng với hàm nào.

Mẹo đọc signature JNI: `(Ljava/lang/String;)Z` nghĩa là nhận một String, trả về boolean (`Z`). Bảng kiểu: `Z`=boolean, `I`=int, `J`=long, `[`=mảng, `L...;`=object.

## Hai tham số đầu luôn là của JNI

Dù tìm theo cách nào, mọi hàm JNI đều có hai tham số ẩn đứng trước tham số của bạn:

```c
jboolean checkLicense(JNIEnv *env, jobject thiz, jstring s)
```

- `env` (tham số 1, nằm ở `x0` trên ARM64): con trỏ tới bảng hàm JNI, dùng để gọi ngược lại Java (lấy chuỗi, gọi method...).
- `thiz` (tham số 2, `x1`): chính là object Java gọi method (giống `this`).
- Tham số thật của bạn bắt đầu từ `x2`.

Nên khi mở hàm trong Ghidra, đừng bối rối khi thấy hai tham số đầu không liên quan logic. Tham số chuỗi `s` nằm ở `x2`. Muốn đọc nội dung chuỗi đó, native gọi `env->GetStringUTFChars`, bạn sẽ thấy một lời gọi gián tiếp qua bảng `env` (dạng `ldr` từ `x0` rồi `blr`), đó là dấu hiệu nó đang rút chuỗi ra để xử lý.

## Quy trình đưa .so vào Ghidra

1. APK là file ZIP, giải nén lấy `lib/arm64-v8a/lib<ten>.so` (ưu tiên arm64-v8a, là ABI phổ biến nhất hiện nay).
2. Kéo file .so vào Ghidra, auto-analysis. Ghidra nhận diện ELF ARM64 (nối lại [Bài 1.8](/posts/tr-1-8-elf-va-mach-o/) và [1.9](/posts/tr-1-9-arm-arm64-co-ban/)).
3. Mở Symbol Tree, lọc `Java_` để tìm hàm theo quy ước. Không có thì tìm `JNI_OnLoad`.
4. Đọc decompiler, nhớ bỏ qua hai tham số JNI đầu.

## Checklist ghi nhớ
- Method Java khai báo `native` nghĩa là logic nằm trong một file `.so`, không đọc được bằng JADX.
- Hàm JNI theo quy ước tên `Java_package_Class_method`, tìm chuỗi `Java_` trong .so là ra.
- Nếu không thấy, tìm `JNI_OnLoad` rồi đọc `RegisterNatives` để biết method ánh xạ sang hàm nào.
- Mọi hàm JNI có hai tham số ẩn đầu: `JNIEnv* env` (x0) và `jobject thiz` (x1). Tham số thật bắt đầu từ x2.
- Signature JNI đọc theo bảng kiểu: `Z` boolean, `I` int, `L...;` object, `[` mảng.
- Phân tích .so chính là reverse ARM64 bình thường, xem lại Bài 1.9.

## Lab tự làm
Xem [labs/6.7/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/6.7): trích .so từ một APK, mở trong Ghidra, tìm hàm JNI theo cả hai cách, và đối chiếu một ví dụ C JNI tự viết.
