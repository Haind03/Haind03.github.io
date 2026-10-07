---
title: "Bài 6.4: Smali và apktool, sửa app Android rồi đóng gói lại"
date: 2026-10-06 08:47:00 +0700
categories: ["Technique Reverse", "Phần 6 · Java / Kotlin / Android (JADX)"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
JADX cho bạn đọc code Android dưới dạng Java đẹp đẽ, nhưng nó chỉ để đọc. Khi muốn thật sự sửa hành vi của app rồi cài lại, bạn không sửa cái Java đó được. Lý do đơn giản: không có đường ngược sạch sẽ từ Java đã decompile về lại DEX. Thứ sửa được, và đóng gói lại được, là smali. Bài này là quy trình patch kinh điển mà gần như bài crackme Android nào cũng dùng tới.

## Smali là gì, vì sao phải học

Android không chạy JVM bytecode mà chạy DEX bytecode (Dalvik/ART). Smali là ngôn ngữ assembly cho DEX: mỗi lệnh smali ứng với một lệnh bytecode, một đổi một. Nó là mức thấp nhất mà con người còn đọc và sửa thoải mái.

Khác biệt cần nhớ so với assembly x86 ở các bài trước: DEX là register-based chứ không stack-based. Nghĩa là thay vì push/pop lên stack, mỗi method có sẵn một dãy thanh ghi ảo đánh số, và lệnh thao tác trực tiếp trên chúng.

Có hai nhóm thanh ghi:
- `p0, p1, p2...` là tham số (parameter) truyền vào method. Với method không static, `p0` chính là `this`.
- `v0, v1, v2...` là thanh ghi cục bộ (local) để tính toán.

Đầu mỗi method khai báo cần bao nhiêu thanh ghi local, ví dụ `.registers 4` hoặc `.locals 2`.

## Cú pháp smali cơ bản

Không cần thuộc hết, chỉ cần nhận ra nhóm hay gặp:

```smali
.method public check(Ljava/lang/String;)Z   # nhận String, trả về boolean (Z)
    .registers 3                              # p0=this, p1=tham số, v0=local

    const-string v0, "secret123"              # v0 = "secret123"
    invoke-virtual {p1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0                            # lấy kết quả equals() vào v0
    return v0                                 # trả về v0
.end method
```

Đối chiếu Java:

```java
public boolean check(String input) {
    return input.equals("secret123");
}
```

Mấy chữ viết tắt kiểu `Z`, `Ljava/lang/String;` là type descriptor của DEX: `Z`=boolean, `I`=int, `V`=void, `Ljava/lang/String;`=class String. Quen dần là đọc trôi.

Nhóm lệnh hay đụng khi patch:
- `const/4 v0, 0x1` nạp hằng số nhỏ (ở đây 1) vào v0.
- `const/4 v0, 0x0` nạp 0.
- `invoke-virtual {...}, ...` gọi method.
- `move-result v0` lấy giá trị trả về của lời gọi vừa rồi vào v0 (giống "rax là giá trị trả về" ở assembly x86).
- `if-eqz v0, :label` nhảy tới label nếu v0 bằng 0 (equal zero). `if-nez` là khác 0.
- `return v0` / `return-void` trả về.

Nhận ra cặp `invoke` rồi `move-result` rồi `if-eqz` là bạn đang nhìn đúng một câu if dựa trên kết quả hàm, y như cặp `cmp`/`je` bên x86.

## Quy trình patch kinh điển

![Quy trình patch APK: apktool d, sửa smali, apktool b, ký lại](/assets/img/technique-reverse/assets/phan-06/smali-patch-flow.svg)

Giả sử app có một hàm kiểm tra license trả về boolean, false là chặn. Mục tiêu: bắt nó luôn trả true.

Bốn bước, nhớ là làm được:

1. Giải APK ra smali:
   ```
   apktool d target.apk -o target_out
   ```
   apktool dịch classes.dex thành cây thư mục `.smali`, và giải mã luôn AndroidManifest về dạng đọc được.

2. Tìm hàm kiểm tra. Dùng JADX đọc Java để biết tên class/method trước, rồi mở đúng file smali tương ứng trong `target_out/smali/...`. Grep tên method cho nhanh.

3. Sửa smali để hàm luôn trả true. Cách sạch nhất là thay toàn bộ thân hàm bằng trả về 1:
   ```smali
   .method public isLicensed()Z
       .registers 2
       const/4 v0, 0x1      # ép v0 = true
       return v0            # trả về true luôn
   .end method
   ```
   Hoặc nếu chỉ muốn đảo một nhánh, tìm chỗ `if-eqz`/`if-nez` và đổi qua lại, hoặc đổi `const/4 v0, 0x0` thành `const/4 v0, 0x1` ngay trước return. Giữ số thanh ghi khai báo đủ lớn kẻo build lỗi.

4. Build lại và ký. Đây là chỗ người mới hay quên:
   ```
   apktool b target_out -o patched.apk
   ```
   APK vừa build CHƯA ký, Android từ chối cài app không chữ ký. Phải ký lại:
   ```
   apksigner sign --ks my.keystore patched.apk
   ```
   hoặc dùng `uber-apk-signer -a patched.apk` cho nhanh (nó tự tạo key debug). Ký xong mới `adb install patched.apk` được.

Cái bẫy lớn nhất của cả quy trình không nằm ở smali mà ở chữ ký: quên ký là cài không nổi, và nếu app có kiểm tra chữ ký của chính nó (anti-tamper) thì ký lại bằng key khác sẽ bị phát hiện. Chuyện vượt anti-tamper để bài obfuscation [6.8](/posts/tr-6-8-obfuscation-android/) và phần Frida lo.

## Khi nào patch smali, khi nào dùng Frida

Patch smali cho ra một APK sửa vĩnh viễn, cài là chạy, không cần công cụ lúc runtime. Nhược điểm: phải build và ký lại, và vướng anti-tamper.

Frida (bài [6.6](/posts/tr-6-6-frida-android-hook/)) hook lúc chạy, không cần sửa file, linh hoạt hơn nhiều khi thử nghiệm, nhưng cần Frida server chạy trên máy/thiết bị. Dân Android RE dùng cả hai: Frida để nghiên cứu nhanh, patch smali khi muốn bản sửa đứng một mình.

## Lab tự làm

Xem [labs/6.4/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/6.4). Bạn sẽ lấy một APK có hàm kiểm tra, dùng apktool giải nó ra smali, tìm và patch hàm đó luôn trả true, build lại, ký, rồi kiểm. Lời giải ở `solution.md`.

## Checklist ghi nhớ
- Android chạy DEX (register-based), không phải JVM bytecode. Smali là assembly cho DEX.
- Sửa smali chứ không sửa Java decompiled, vì không có đường ngược sạch từ Java về DEX.
- Thanh ghi: `p0` là this (method không static), `p1...` là tham số, `v0...` là local.
- `move-result` lấy giá trị trả về của lời gọi vừa rồi, giống rax bên x86.
- Patch "luôn trả true": `const/4 v0, 0x1` rồi `return v0`.
- Quy trình: `apktool d`, sửa smali, `apktool b`, rồi BẮT BUỘC ký lại (apksigner/uber-apk-signer).
