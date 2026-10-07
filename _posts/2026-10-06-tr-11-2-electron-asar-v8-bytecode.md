---
title: "Bài 11.2: Mổ một app Electron, từ app.asar tới V8 bytecode"
date: 2026-10-06 09:10:00 +0700
categories: ["Technique Reverse", "Phần 11 · JavaScript, Electron, WebAssembly"]
tags: [reverse-engineering, javascript, wasm]
render_with_liquid: false
---
Rất nhiều app desktop bạn dùng hằng ngày (Discord, VS Code, Slack, Postman) thật ra là một trình duyệt Chromium đóng gói kèm Node.js, gọi là Electron. Tin vui cho người reverse: phần lớn logic của chúng là JavaScript, và JavaScript thì gần như đọc được nguyên bản. Tin kém vui: vài app bọc code bằng V8 bytecode để làm khó bạn. Bài này đi từ dễ tới khó.

## Electron là cái gì dưới lớp vỏ

Một app Electron gồm ba mảnh:

- **Chromium**: phần render giao diện, chính là một trình duyệt.
- **Node.js**: cho phép code truy cập file, mạng, hệ thống như một chương trình desktop thật.
- **Code app của bạn**: viết bằng JavaScript (đôi khi TypeScript đã transpile), chia làm main process (chạy trên Node) và renderer process (chạy trong Chromium).

Điểm mấu chốt để reverse: code app không bị biên dịch sang machine code. Nó chỉ được gói lại. Nhiệm vụ của bạn phần lớn là tìm gói đó và mở ra.

## Tìm code: resources/app.asar

Cài một app Electron rồi vào thư mục cài đặt, bạn sẽ thấy một thư mục `resources/`. Bên trong thường có một trong hai thứ:

- `app.asar`: một file archive gói toàn bộ source JS, HTML, CSS, JSON.
- hoặc một thư mục `app/` để nguyên không đóng gói (còn dễ hơn, đọc thẳng).

`asar` chỉ là định dạng đóng gói đơn giản của Electron, không mã hoá gì cả, chỉ nối các file lại kèm một header JSON mô tả vị trí. Nghĩa là mở nó ra dễ như giải nén.

Nhận ra một app là Electron: có `resources/app.asar`, có các file `*.pak` của Chromium, có `ffmpeg.dll`/`libffmpeg`, và kích thước cài đặt lớn bất thường (cả trăm MB cho một app đơn giản).

## Giải nén app.asar

Cách chuẩn, dùng công cụ chính chủ:

```bash
# cài asar nếu chưa có
npm install -g asar

# giải nén
asar extract app.asar app_extracted/

# hoặc liệt kê nội dung trước khi giải
asar list app.asar
```

Không có Node cũng không sao, `app.asar` mở được bằng 7-Zip (có plugin), hoặc bạn tự parse header JSON ở đầu file. Nhưng `asar extract` là nhanh và sạch nhất.

Giải xong bạn có một cây thư mục JS đọc được. Mở `package.json` tìm trường `main`, đó là file điểm vào của main process (thường `main.js` hoặc `index.js`). Từ đó lần ra logic: nơi kiểm tra license, nơi gọi API, nơi xử lý dữ liệu. Nếu code bị minify (dồn một dòng, tên biến một chữ), dùng Prettier hoặc js-beautify làm đẹp lại, rồi mới đọc (chi tiết deobfuscation JS ở Bài 11.1).

## Sửa và đóng gói lại

Vì là JS thuần, bạn sửa thẳng file rồi gói lại:

```bash
# sửa file trong app_extracted/ bằng editor bất kỳ
asar pack app_extracted/ app.asar
```

Ghi đè `app.asar` cũ (nhớ sao lưu bản gốc trước). Lần chạy sau, Electron nạp code đã sửa của bạn. Đây là lý do patch app Electron nhiều khi chỉ là sửa vài dòng JS, không cần đụng tới assembly. Cách này dùng cho kiểm thử bảo mật app của chính mình hoặc được phép, không phải để qua mặt license thương mại.

## Khi gặp V8 bytecode (.jsc)

Một số app bọc code kỹ hơn bằng **bytenode**: biên dịch JavaScript sang V8 bytecode, lưu thành file `.jsc`, rồi nạp bytecode đó lúc chạy. Mở ra bạn không thấy JS nữa mà là một khối nhị phân. Đây là nấc khó hơn hẳn.

Vài điều cần biết về V8 bytecode:

- Nó **không ổn định giữa các phiên bản V8/Node**: một file `.jsc` build cho Node 18 chưa chắc chạy trên Node 20. Nghĩa là để chạy/phân tích, bạn cần đúng phiên bản V8 mà app dùng.
- Bytecode này **không giữ source gốc**, nhưng vẫn giữ nhiều thông tin: tên hàm, chuỗi literal, tên biến trong nhiều trường hợp. Chạy `strings` lên file `.jsc` thường lộ ra kha khá manh mối.

Hướng tiếp cận, theo thứ tự nên thử:

1. **Lấy chuỗi và constant trước.** `strings file.jsc` thường cho thấy tên hàm, chuỗi thông báo, endpoint. Nhiều khi bấy nhiêu đã đủ hiểu logic.
2. **Dump từ runtime.** Đây là cách mạnh nhất. Vì cuối cùng V8 vẫn phải thực thi code, bạn có thể hook vào quá trình nạp để lấy lại source hoặc AST. Dùng chính Node đúng phiên bản để nạp file `.jsc` rồi chặn ở tầng `vm`/`Module._compile`, hoặc dùng các tool cộng đồng chuyên dump bytenode.
3. **Disassemble bytecode.** Node có cờ nội bộ `--print-bytecode` in ra bytecode V8 ở dạng đọc được. Kết hợp tài liệu về opcode V8 để đọc thủ công. Cực nhọc, chỉ làm khi thật cần.

Thực tế, với bytenode hướng số 2 (dump runtime) gần như luôn thắng, vì bytenode chỉ che chứ không mã hoá mạnh: code phải chạy được thì bạn phải lấy lại được.

## Checklist ghi nhớ
- App Electron = Chromium + Node.js + code JavaScript được gói, không biên dịch ra native.
- Code nằm trong `resources/app.asar`, giải nén bằng `asar extract` hoặc 7-Zip, không có mã hoá.
- Đọc `package.json` trường `main` để tìm điểm vào, beautify nếu bị minify.
- Sửa thẳng JS rồi `asar pack` để đóng gói lại.
- Gặp `.jsc` (bytenode, V8 bytecode): thử strings trước, dump từ runtime là cách thắng, disassemble là phương án cuối.

## Lab tự làm
Xem [labs/11.2/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/11.2): tìm và giải nén `app.asar` của một app Electron, đọc code, thử sửa và đóng gói lại.
