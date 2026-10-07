---
title: "Bài 12.1: Objective-C, khi mọi lời gọi đều đi vòng qua runtime"
date: 2026-10-06 09:12:00 +0700
categories: ["Technique Reverse", "Phần 12 · Swift / Objective-C (macOS, iOS)"]
tags: [reverse-engineering, ios, swift]
render_with_liquid: false
---
Mở một app macOS hay iOS viết bằng Objective-C trong IDA lần đầu, bạn sẽ thấy một thứ lạ: gần như không có lời gọi hàm trực tiếp nào. Thay vào đó là `call objc_msgSend` lặp đi lặp lại hàng nghìn lần. Nếu không hiểu chuyện gì đang xảy ra, bạn sẽ tưởng cả chương trình chỉ gọi đúng một hàm. Bài này giải thích cơ chế đó và vì sao nó thật ra là tin tốt cho người reverse.

## Objective-C không gọi method, nó gửi message

Trong C hay C++, gọi một hàm là `call` thẳng tới địa chỉ của nó. Objective-C làm khác hẳn: mọi lời gọi method được dịch thành một message gửi qua một hàm trung gian duy nhất tên là `objc_msgSend`.

Một dòng Objective-C quen thuộc:

```objc
[account checkPassword:input];
```

thực ra được compiler biến thành:

```objc
objc_msgSend(account, @selector(checkPassword:), input);
```

Nghĩa là: "gửi cho đối tượng `account` một message tên `checkPassword:`, kèm tham số `input`". Runtime của Objective-C lúc chạy mới tra xem class của `account` có method nào tên `checkPassword:` rồi nhảy tới đó. Đây là dynamic dispatch, và nó là lý do bạn thấy `objc_msgSend` khắp nơi.

## Đọc objc_msgSend trong assembly

Vì mọi thứ đi qua `objc_msgSend`, chìa khoá là đọc hai tham số đầu của nó. Theo calling convention macOS/iOS (System V trên x64, hoặc AAPCS trên ARM64), tham số nằm ở các thanh ghi đã quen từ [Bài 1.3](/posts/tr-1-3-assembly-1-thanh-ghi-lenh-co-ban/):

- Tham số 1 (`rdi` trên x64, `x0` trên ARM64): **receiver**, đối tượng nhận message.
- Tham số 2 (`rsi` trên x64, `x1` trên ARM64): **selector**, tên method dạng chuỗi.
- Tham số 3 trở đi (`rdx`/`x2`...): các tham số thật của method.

Một đoạn x64 điển hình trông thế này:

```asm
lea  rsi, selRef_checkPassword_   ; rsi = selector "checkPassword:"
mov  rdi, rbx                     ; rdi = receiver (đối tượng account)
mov  rdx, r14                     ; rdx = tham số input
call objc_msgSend
```

Mấu chốt: **nhìn `rsi` (hoặc `x1`) để biết đang gọi method gì.** IDA và Ghidra thường tự chú thích selector cạnh lời gọi, nên bạn đọc được `objc_msgSend(account, "checkPassword:", input)` gần như một dòng code gốc. Khi tool không tự làm, bạn tự lần `rsi` về vùng `__objc_selrefs` để lấy tên.

Trên ARM64 cũng vậy, chỉ đổi thanh ghi:

```asm
adrp x1, selRef_checkPassword_@PAGE
...
mov  x0, x19                      ; receiver
bl   _objc_msgSend
```

## Vì sao đây là tin tốt: metadata còn nguyên tên

Điều khiến Objective-C dễ reverse hơn C++ nhiều: runtime cần biết tên class, tên method, kiểu tham số để dispatch lúc chạy, nên compiler **nhúng toàn bộ thông tin đó vào file Mach-O**. Nối lại [Bài 1.8](/posts/tr-1-8-elf-va-mach-o/) về Mach-O, bạn sẽ thấy các section chuyên dụng:

- `__objc_classlist`: danh sách class trong binary.
- `__objc_methname`: tên tất cả method (dạng selector).
- `__objc_classname`: tên class.
- `__objc_selrefs`: tham chiếu selector mà code dùng.

Nói cách khác, tên `checkPassword:`, `AccountManager`, `validateLicense` vẫn nằm trần trong binary, chưa bị mangling kiểu C++ hay xoá sạch kiểu C native. Bạn gần như có một bản mục lục của chương trình.

## class-dump: lấy lại toàn bộ interface

Vì metadata còn đủ, có một công cụ dựng lại gần như nguyên vẹn các file header: `class-dump` (và bản hỗ trợ Swift là `class-dump-swift`). Chạy nó trên một Mach-O ObjC:

```
class-dump /path/to/MyApp.app/Contents/MacOS/MyApp
```

Kết quả là các khai báo `@interface` đầy đủ: mỗi class, danh sách method, property, biến instance. Giống như có lại file `.h` của chương trình. Từ đó bạn biết ngay class nào đáng quan tâm (ví dụ `LicenseManager`) và method nào là mục tiêu (`-isValidLicense:`), rồi mới mở IDA/Ghidra đọc phần thân.

## Quy trình thực tế

Ghép lại thành nhịp làm việc:

1. Nhận diện: file Mach-O, có các section `__objc_*`, import `objc_msgSend`. Đây là app Objective-C.
2. Chạy `class-dump` lấy interface, đọc để khoanh vùng class/method đáng chú ý.
3. Mở IDA/Ghidra, nhảy tới method mục tiêu (IDA đặt tên method kiểu `-[AccountManager checkPassword:]`).
4. Đọc thân method, mỗi `objc_msgSend` thì nhìn selector ở `rsi`/`x1` để biết nó gọi gì.
5. Lần theo chuỗi message để hiểu logic, đổi tên biến khi hiểu như thói quen đã học ở [Bài 0.4](/posts/tr-0-4-quy-trinh-reverse/).

## Vài cạm bẫy

- `objc_msgSend` có họ hàng: `objc_msgSendSuper` (gọi lên superclass), `objc_msgSend_stret` (method trả về struct), `objc_msgSend_fpret` (trả về float). Gặp biến thể thì cách đọc selector vẫn như cũ.
- Selector chỉ là tên, không phải địa chỉ. Hai class khác nhau có thể cùng selector `init`, phải nhìn cả receiver mới biết method nào thực sự chạy.
- App có thể gọi method qua chuỗi động (`NSSelectorFromString`), lúc đó selector không hiện tĩnh, phải quan sát runtime.
- Code bị obfuscate có thể đổi tên selector thành vô nghĩa, nhưng đa số app thương mại bình thường thì tên còn rất rõ.

## Checklist ghi nhớ
- Objective-C dispatch qua `objc_msgSend(receiver, selector, args)`, không call thẳng.
- Đọc selector ở `rsi` (x64) hoặc `x1` (ARM64) để biết đang gọi method nào; receiver ở `rdi`/`x0`.
- Metadata ObjC nhúng trong Mach-O (`__objc_classlist`, `__objc_methname`...) giữ nguyên tên class/method.
- `class-dump` trích lại toàn bộ `@interface`, coi như có lại file header.
- Quy trình: class-dump khoanh vùng, rồi đọc thân method trong IDA/Ghidra theo selector.
