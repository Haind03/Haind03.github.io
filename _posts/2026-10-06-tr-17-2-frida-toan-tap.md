---
title: "Bài 17.2: Frida toàn tập, soi và sửa chương trình lúc nó đang chạy"
date: 2026-10-06 09:41:00 +0700
categories: ["Technique Reverse", "Phần 17 · Patch, Hook, Injection & Instrumentation"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
Có những lúc đọc code tĩnh mãi không ra, mà đặt breakpoint trong debugger thì chậm và dễ bị anti-debug phát hiện. Frida sinh ra cho đúng tình huống đó: bạn tiêm một đoạn JavaScript nhỏ vào tiến trình đang chạy, bảo nó "mỗi khi hàm này được gọi, in cho tôi tham số ra", và thế là xong. Không cần sửa file trên đĩa, không cần recompile, chạy được trên Windows, Linux, macOS, Android, iOS với cùng một bộ API.

Bài này là Frida ở mức bạn dùng được ngay cho RE. Phạm vi: phân tích hành vi, kiểm thử bảo mật phần mềm của chính mình, giải crackme/CTF. Dùng để quan sát và hiểu, không phải để phá.

## Frida nhìn từ trên xuống

Về bản chất Frida nhét một engine tên là **gum** vào tiến trình đích, rồi engine đó chạy đoạn script JavaScript (gọi là agent) của bạn ngay bên trong không gian địa chỉ của tiến trình. Vì script chạy *bên trong* tiến trình nên nó thấy mọi hàm, mọi vùng nhớ, mọi thanh ghi như chính tiến trình thấy.

Hai cách đưa script vào:
- **attach**: gắn vào một tiến trình đang chạy sẵn. Dùng khi chương trình đã khởi động và bạn muốn soi từ giữa chừng.
- **spawn**: Frida tự khởi chạy chương trình trong trạng thái tạm dừng, nạp script, rồi mới cho chạy. Dùng khi cần hook thứ gì đó xảy ra rất sớm (trước main, trong hàm khởi tạo).

Công cụ dòng lệnh đi kèm bạn sẽ gõ nhiều:
- `frida-ps -U` liệt kê tiến trình (cờ `-U` cho thiết bị USB như Android, bỏ đi là máy local).
- `frida -l hook.js -f ./target` spawn `target` và nạp `hook.js`.
- `frida -l hook.js target` attach vào tiến trình tên `target`.
- `frida-trace` sinh hook tự động (nói ở cuối bài).

## Interceptor, trái tim của Frida

99% việc hook của bạn đi qua `Interceptor.attach`. Nó nhận một địa chỉ hàm và hai callback: `onEnter` chạy khi vào hàm (lúc này đọc được tham số), `onLeave` chạy khi hàm sắp return (lúc này đọc và sửa được giá trị trả về).

Tìm địa chỉ hàm thế nào? Nếu hàm được export (như API hệ thống) thì dùng tên:

```javascript
// Hook CreateFileW trên Windows để xem chương trình mở file nào
const pCreateFileW = Module.findExportByName("kernel32.dll", "CreateFileW");

Interceptor.attach(pCreateFileW, {
    onEnter(args) {
        // Tham số đầu của CreateFileW là lpFileName (con trỏ chuỗi UTF-16)
        this.name = args[0].readUtf16String();
        console.log("[CreateFileW] mo file: " + this.name);
    },
    onLeave(retval) {
        // retval là HANDLE trả về; INVALID_HANDLE_VALUE = -1
        console.log("   -> handle: " + retval);
    }
});
```

Vài điều quan trọng trong đoạn trên:
- `args` là mảng tham số. **Frida tự lo calling convention cho bạn**: `args[0]` là tham số đầu bất kể trên Windows nó nằm ở rcx hay Linux nằm ở rdi. Đây là lý do cùng một script chạy đa nền.
- Mỗi `args[i]` là một `NativePointer`, nên bạn phải tự diễn giải: `.readUtf16String()` cho chuỗi Windows wide, `.readCString()` cho chuỗi C, `.toInt32()` cho số.
- `this` dùng chung giữa `onEnter` và `onLeave`, nên lưu giá trị ở onEnter để dùng lại ở onLeave (như `this.name`).

### Sửa tham số và giá trị trả về

Hook không chỉ để xem, bạn sửa được. Ví dụ bắt một hàm kiểm tra license luôn trả về "hợp lệ":

```javascript
Interceptor.attach(pCheckLicense, {
    onLeave(retval) {
        console.log("check tra ve that: " + retval);
        retval.replace(1);   // ep tra ve 1 (hop le)
    }
});
```

Hoặc sửa tham số trước khi hàm xử lý, trong onEnter:

```javascript
onEnter(args) {
    // ep tham so thu 2 (do kho) ve 0
    args[1] = ptr(0);
}
```

### Interceptor.replace, thay nguyên hàm

Khi muốn thay hẳn toàn bộ hàm bằng cài đặt của mình (không chỉ xem/sửa), dùng `Interceptor.replace`:

```javascript
const origStrcmp = new NativeFunction(pStrcmp, 'int', ['pointer', 'pointer']);
Interceptor.replace(pStrcmp, new NativeCallback((a, b) => {
    console.log("strcmp: " + a.readCString() + " vs " + b.readCString());
    return origStrcmp(a, b);   // van goi ban goc
}, 'int', ['pointer', 'pointer']));
```

## NativeFunction và NativePointer, gọi ngược vào tiến trình

Đôi khi bạn không chỉ muốn hook mà muốn *chủ động gọi* một hàm có sẵn trong tiến trình, ví dụ để thử hàm giải mã với input của mình. `NativeFunction` bọc một địa chỉ thành hàm gọi được từ JS:

```javascript
const decrypt = new NativeFunction(ptr("0x401500"), 'pointer', ['pointer', 'int']);
const buf = Memory.allocUtf8String("du lieu ma hoa");
const result = decrypt(buf, 14);
console.log("giai ma: " + result.readCString());
```

`NativePointer` (viết tắt `ptr(...)`) là kiểu con trỏ của Frida, có đủ `.readByteArray()`, `.writeUtf8String()`, `.add(offset)`, `.readPointer()` để bạn đọc ghi bộ nhớ thoải mái. `Memory.alloc` cấp vùng nhớ mới trong tiến trình khi cần truyền buffer.

## Stalker, trace từng lệnh

`Interceptor` hook tại ranh giới hàm. Khi bạn cần theo dõi *luồng thực thi bên trong* một hàm (mỗi basic block, mỗi lệnh nào chạy, đo code coverage), đó là việc của `Stalker`. Nó theo một thread và báo lại từng block được thực thi. Dùng nhiều cho fuzzing và để tìm "code nào chạy khi tôi nhập serial đúng so với sai":

```javascript
Stalker.follow(Process.getCurrentThreadId(), {
    events: { block: true },
    onReceive(events) {
        // danh sach block vua chay, dung de do coverage
    }
});
```

Stalker mạnh nhưng nặng và phức tạp hơn Interceptor nhiều, nên để dành cho khi thật sự cần coverage, không dùng cho hook thông thường.

## frida-trace, lười mà hiệu quả

Không muốn viết script tay? `frida-trace` sinh sẵn handler cho bạn:

```
frida-trace -f ./target -i "strcmp" -i "CreateFileW"
```

Cờ `-i` chọn hàm theo tên (có wildcard, ví dụ `-i "str*"` bắt mọi hàm bắt đầu bằng str). Frida tạo một file JS cho mỗi hàm trong thư mục `__handlers__`, bạn mở ra sửa để in thêm tham số. Đây là cách nhanh nhất để có cái nhìn tổng thể "chương trình gọi những API nào".

## Trên Android thì sao

Nền tảng giống hệt, chỉ khác bạn hook method Java qua `Java.perform` và `Java.use` thay vì hàm native. Phần đó đã nói kỹ ở [Bài 6.6](/posts/tr-6-6-frida-android-hook/). Với thư viện native `.so` trong app Android thì lại quay về `Interceptor.attach` như bài này. Nhớ cần `frida-server` chạy trên thiết bị và dùng cờ `-U`.

## Vài cạm bẫy hay gặp

- **Lệch phiên bản**: Frida host và frida-server (trên Android/iOS) phải cùng version, lệch là lỗi khó hiểu.
- **Hook quá sớm**: nếu module chưa được nạp, `Module.findExportByName` trả null. Dùng `spawn` hoặc chờ module trong một số trường hợp.
- **Anti-Frida**: phần mềm bảo vệ có thể dò cổng 27042, chuỗi "frida", hoặc thread lạ. Gặp vậy thì xem [Bài 15.7](/posts/tr-15-7-anti-attach-dump-hook/) về anti-hook và cân nhắc Frida ở chế độ ẩn hơn.
- **Đọc sai kiểu con trỏ**: `args[0]` là con trỏ, in thẳng ra địa chỉ chứ không phải nội dung. Phải gọi `.readUtf8String()` hay tương tự.

## Lab tự làm

Xem [labs/17.2/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/17.2). Nhiệm vụ: dùng Frida hook hàm so sánh của một chương trình nhỏ để lộ chuỗi đúng mà nó đang so với input của bạn, rồi thử ép giá trị trả về cho qua check. File `hook.js` mẫu có sẵn trong `src/`.

## Checklist ghi nhớ
- Frida tiêm agent JS vào tiến trình đang chạy, thấy mọi thứ từ bên trong, chạy đa nền.
- `Interceptor.attach` với `onEnter` (tham số) và `onLeave` (giá trị trả về) là công cụ chính.
- `args[i]` đánh số theo thứ tự tham số logic, Frida tự lo calling convention. Mỗi cái là NativePointer, phải tự diễn giải kiểu.
- `retval.replace(x)` sửa giá trị trả về, gán `args[i]` sửa tham số.
- `NativeFunction` để tự gọi hàm trong tiến trình; `Stalker` để trace từng block; `frida-trace` để sinh hook nhanh.
- Android hook Java qua `Java.use` (Bài 6.6), native `.so` vẫn dùng Interceptor.
