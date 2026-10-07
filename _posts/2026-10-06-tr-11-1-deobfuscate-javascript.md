---
title: "Bài 11.1: Deobfuscate JavaScript, bóc từng lớp cho tới khi đọc được"
date: 2026-10-06 09:09:00 +0700
categories: ["Technique Reverse", "Phần 11 · JavaScript, Electron, WebAssembly"]
tags: [reverse-engineering, javascript, wasm]
render_with_liquid: false
---
JavaScript không biên dịch ra machine code, nó chạy ngay dạng text. Nghe thì tưởng dễ reverse nhất đời, nhưng chính vì là text nên người ta đổ công sức vào obfuscation: đổi tên biến thành rác, giấu chuỗi trong mảng mã hoá, bẻ vụn luồng điều khiển. Malware JS, skimmer thẻ tín dụng trên web, script chặn adblock, tất cả đều obfuscate. Bài này dạy bóc từng lớp theo đúng thứ tự.

Điểm mấu chốt cần nhớ trước: **obfuscation không mã hoá logic, chỉ làm nó khó đọc.** Code vẫn phải chạy được, nên mọi thứ bạn cần đều ở đó, chỉ bị che. Công việc của bạn là lột lớp che.

## Bốn mức, từ nhẹ tới nặng

Gặp một file JS lạ, nó rơi vào một trong bốn mức, và cách xử lý khác nhau:

1. **Minified**: chỉ bị nén (xoá khoảng trắng, rút tên biến thành `a`, `b`). Không phải obfuscation thật, chỉ để file nhỏ. Beautify là đọc được gần như ngay.
2. **Obfuscated**: cố tình làm khó bằng string array, control flow flattening, dead code. Đây là mức tốn công nhất.
3. **Bundled**: webpack/rollup gộp nhiều module thành một file khổng lồ. Cần tách module ra.
4. **Compiled**: Electron (bytecode V8) hoặc WebAssembly. Đây là bài [11.2](https://github.com/Haind03/Technique-Reverse/blob/main/phan-11-javascript-electron-wasm/11.2-electron-asar-v8.md) và [11.3](/posts/tr-11-3-webassembly/).

## Mức 1: beautify, việc đầu tiên luôn làm

Dù file ở mức nào, bước đầu tiên luôn là format lại cho xuống dòng thụt lề. Một file minified một dòng dài 50KB là không thể đọc, nhưng sau khi beautify thì cấu trúc hiện ra.

```bash
npx js-beautify minified.js
# hoặc Prettier, hoặc nút Format trong DevTools của trình duyệt ({})
```

Với file chỉ minified (không obfuscate), beautify là xong. Bạn đọc được logic ngay, chỉ tên biến hơi xấu. Nhiều "mã bị giấu" thực ra chỉ minified, đừng dùng dao mổ trâu.

## Mức 2: nhận diện obfuscator trước khi gỡ

Đây là chỗ người mới hay sai: lao vào gỡ bằng tay trước khi biết nó bị obfuscate bằng tool gì. Phần lớn code obfuscated ngoài đời sinh ra từ **obfuscator.io** (thư viện `javascript-obfuscator`), và nó để lại dấu vân tay rất dễ nhận:

- Một **string array**: một hàm trả về mảng chuỗi dài, mọi chuỗi trong code được thay bằng lời gọi kiểu `_0x4ae3eb(0xc4)`.
- Một **rotate function**: đoạn IIFE có vòng `while(true)` với `parseInt` và `push/shift`, dùng để xoay mảng chuỗi về đúng thứ tự lúc chạy.
- **Control flow flattening**: thân hàm biến thành `while` + `switch` với thứ tự case lộn xộn, điều khiển bằng một chuỗi kiểu `"4|2|3|0|1"[split]`.
- Tên biến dạng `_0x` hex.

Nhận ra bốn dấu này là biết ngay: đây là obfuscator.io, và có tool gỡ sẵn.

## Mức 2: chạy tool gỡ

Hai tool chủ lực, nên thử theo thứ tự:

- **webcrack**: mạnh nhất hiện nay cho obfuscator.io và cả webpack bundle. `npx webcrack obf.js -o out`. Nó giải string array, unflatten control flow, inline, tách module.
- **synchrony** (gói `deobfuscator`): `npx deobfuscator file.js`, chuyên obfuscator.io, gỡ string array và đơn giản hoá biểu thức.

Thực tế một tool không phải lúc nào cũng gỡ sạch 100%. webcrack chạy code trong sandbox để giải string array, nên đôi khi vướng môi trường (ví dụ isolated-vm trên máy nào đó). synchrony có thể chỉ gỡ được một phần: đổi hằng số hex sang decimal, đơn giản hoá, nhưng vẫn để lại control flow flattening. Không sao. **Bạn không cần tool gỡ sạch, chỉ cần nó gỡ đủ để bạn đọc được logic.**

Ngay cả khi vẫn còn `switch`-case lộn xộn, bạn đọc từng case là ra logic gốc. Trong lab của bài này, sau khi chạy synchrony, hàm check vẫn còn flattening nhưng các case lộ rõ: một case `split('-')`, một case kiểm tra số phần ttử, một case cộng `charCodeAt`, một case `return` so sánh tổng với một hằng số. Ghép lại là hiểu trọn.

## Mức 2 nâng cao: tự viết AST transform

Khi gặp obfuscator tuỳ biến mà không tool nào gỡ được, bạn tự viết transform. JavaScript có lợi thế lớn: nó tự parse được chính nó. Dùng **Babel** để biến code thành AST (cây cú pháp), sửa cây, rồi in lại.

Quy trình: dán code vào **AST Explorer** (astexplorer.net) để nhìn cây, tìm pattern lặp lại (ví dụ mọi lời gọi `_0xabc(0x1f)`), viết một visitor thay nó bằng giá trị thật.

```js
// Ví dụ: thay mọi lời gọi hàm decode bằng chuỗi thật
const { parse } = require("@babel/parser");
const traverse = require("@babel/traverse").default;
const generate = require("@babel/generator").default;

const ast = parse(code);
traverse(ast, {
  CallExpression(path) {
    if (path.node.callee.name === "_0x4ae3eb") {
      const idx = path.node.arguments[0].value;
      path.replaceWithSourceString(JSON.stringify(decode(idx)));
    }
  },
});
console.log(generate(ast).code);
```

Đây là cách mạnh nhất và cũng là cách các tool trên hoạt động bên trong. Học viết AST transform là bạn gỡ được thứ chưa có tool.

## Quy trình gọn

```
1. Beautify (js-beautify / Prettier / nút {} trong DevTools)
2. Chỉ minified?  -> đọc luôn, xong.
3. Nhận diện: thấy string array + rotate + _0x + switch flattening -> obfuscator.io
4. Chạy webcrack, nếu vướng thì synchrony
5. Còn sót control flow -> đọc từng case, hoặc tự viết Babel transform
6. Bundle webpack -> webcrack tách module rồi lặp lại từ bước 1 cho từng module
```

## Một lưu ý về malware JS

Malware JS hay thêm một lớp nữa: `eval`, `Function()`, hoặc `atob` (giải base64) để chạy payload sinh ra lúc runtime. Đừng chạy mù. Thay `eval(x)` bằng `console.log(x)` để in payload ra thay vì thực thi, đó là cách "giải" an toàn nhất. Làm trong môi trường cô lập theo [Bài 0.3](/posts/tr-0-3-dung-lab-an-toan/).

## Checklist ghi nhớ
- Obfuscation chỉ che logic, không mã hoá nó. Code chạy được nghĩa là mọi thứ bạn cần đều ở đó.
- Luôn beautify trước. Nhiều thứ "bị giấu" thực ra chỉ minified.
- Nhận diện obfuscator trước khi gỡ: string array + rotate + `_0x` + switch flattening là obfuscator.io.
- webcrack mạnh nhất, synchrony là phương án hai. Không cần gỡ sạch, chỉ cần đọc được logic.
- Tool bó tay thì tự viết Babel/AST transform, đó cũng là cách tool hoạt động bên trong.
- Payload trong `eval`/`Function` thì in ra bằng `console.log`, đừng chạy.

## Lab
Xem [labs/11.1/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/11.1). Có sẵn một license checker, bản minified, bản obfuscated bằng obfuscator.io thật, và kết quả sau khi beautify và chạy synchrony. Nhiệm vụ: bóc ngược về logic gốc và tìm license key hợp lệ.
