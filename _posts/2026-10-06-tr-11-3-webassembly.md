---
title: "Bài 11.3: WebAssembly, đọc bytecode chạy trong trình duyệt"
date: 2026-10-06 09:11:00 +0700
categories: ["Technique Reverse", "Phần 11 · JavaScript, Electron, WebAssembly"]
tags: [reverse-engineering, javascript, wasm]
render_with_liquid: false
---
Khi một trang web làm việc nặng (game, crypto, mã hoá, xử lý ảnh) mà JavaScript thuần không kham nổi, người ta đẩy phần đó xuống WebAssembly (WASM). Với dân reverse, WASM vừa quen vừa lạ: quen vì nó là bytecode của một máy ảo stack-based, giống JVM hay CPython bạn gặp ở Phần 6 và 7, lạ vì nó không giữ tên biến và nhiều khi cố tình giấu logic quan trọng. Bài này dạy bạn mở một file `.wasm` ra đọc.

## WASM là gì, dưới góc nhìn reverse

WASM là một định dạng bytecode nhỏ gọn, chạy trong một sandbox trên trình duyệt (hoặc runtime như wasmtime, Node). Hai điều cần nhớ ngay:

- Nó là **stack-based**: lệnh đẩy và lấy toán hạng trên một stack, giống bytecode Python. Không có thanh ghi kiểu x86.
- Nó có **hai dạng**: `.wasm` là binary (thứ trình duyệt tải về), `.wat` là text tương đương mà con người đọc được. Công việc đầu tiên của bạn gần như luôn là biến `.wasm` thành `.wat`.

Khác với native, WASM không truy cập bộ nhớ hệ thống tuỳ tiện. Nó có một vùng **linear memory** (một mảng byte phẳng, lớn dần theo trang 64KB), một **table** (mảng tham chiếu hàm, dùng cho gọi gián tiếp), và giao tiếp với JavaScript qua **import/export**. Hàm được export ra chính là cửa vào mà bạn nên bắt đầu đọc.

## Lấy file .wasm từ web

Nếu mục tiêu là một trang web, mở DevTools của trình duyệt:

- Tab **Network**: lọc theo `wasm` hoặc tìm request có đuôi `.wasm`, bấm chuột phải để lưu.
- Tab **Sources**: Chrome liệt kê module WASM đã nạp, có thể xem và lưu từ đây.

Lưu được file `.wasm` rồi là có thể làm việc offline, không cần trang web nữa.

## Bộ công cụ wabt, món phải có

**wabt** (WebAssembly Binary Toolkit) là bộ dao chính. Những lệnh dùng nhiều nhất:

```bash
wasm2wat app.wasm -o app.wat      # binary sang text đọc được (bước đầu tiên)
wasm-objdump -x app.wasm          # xem header: import, export, section, type
wasm-decompile app.wasm -o app.dcmp  # sinh giả C, dễ đọc hơn WAT nhiều
wasm2c app.wasm -o app.c          # sang C, để biên dịch lại hoặc phân tích sâu
```

Trong đó `wasm2wat` cho bạn sự thật từng lệnh, còn `wasm-decompile` cho bạn một bản giả C gần với logic cấp cao. Người có kinh nghiệm đọc cả hai: dùng bản decompile để nắm ý, tụt xuống WAT khi cần chính xác.

Nếu muốn đồ nặng hơn, **Ghidra** có plugin WASM (nạp `.wasm` như một kiến trúc riêng, dùng decompiler quen thuộc), và có các tool như **wasmdec**. Nhưng với phần lớn bài web và CTF, wabt là đủ.

## Đọc một đoạn WAT

Giả sử một challenge web kiểm tra key bằng WASM. Sau `wasm2wat`, bạn thấy đại loại:

```wat
(module
  (func $check (param $p0 i32) (result i32)   ;; nhận con trỏ tới chuỗi, trả 0/1
    (local $i i32)
    ...
    local.get $p0
    i32.load8_u            ;; đọc 1 byte từ linear memory tại địa chỉ $p0
    i32.const 42
    i32.xor                ;; byte XOR 42
    i32.const 0x5b
    i32.eq                 ;; so với 0x5b
    ...
  )
  (export "check" (func $check))   ;; đây là cửa vào
  (memory (export "memory") 1)
)
```

Cách đọc không khác gì bytecode Python hay Java bạn đã quen:

- `local.get $p0` đẩy tham số lên stack.
- `i32.load8_u` lấy địa chỉ trên đỉnh stack, đọc 1 byte từ linear memory tại đó, đẩy giá trị lên.
- `i32.const 42` rồi `i32.xor`: byte vừa đọc XOR với 42.
- `i32.const 0x5b` rồi `i32.eq`: so sánh với 0x5b, đẩy kết quả 0/1.

Dịch ra ý: với mỗi ký tự, `char ^ 42 == 0x5b`, tức `char == 0x5b ^ 42 == 0x71 == 'q'`. Vừa đọc WASM vừa suy ra ký tự đúng, đó chính là reverse. Thấy pattern XOR trong một vòng lặp là gần như chắc đang gặp routine kiểm tra hoặc giải mã chuỗi, đúng như kinh nghiệm từ Bài 1.1.

## Mẹo khi logic nằm trong linear memory

Chuỗi và hằng số thường không nằm trong lệnh mà ở **data section**, được nạp sẵn vào linear memory. `wasm-objdump -x` liệt kê các đoạn data kèm offset. Khi code làm `i32.load` tại một offset cố định, tra offset đó trong data section để biết nó đọc chuỗi gì. Đây là bước hay bị bỏ sót khiến người mới bế tắc.

## Checklist ghi nhớ
- WASM là bytecode stack-based, giống bytecode Python/JVM về cách đọc.
- Việc đầu tiên: `wasm2wat` để có text, rồi `wasm-decompile` để có giả C.
- Lấy `.wasm` từ DevTools tab Network hoặc Sources.
- Bắt đầu từ hàm được **export**, đó là cửa vào.
- Chuỗi và hằng số nằm trong data section của linear memory, tra bằng `wasm-objdump -x`.
- Pattern XOR trong vòng lặp thường là kiểm tra hoặc giải mã chuỗi.

## Lab tự làm
Mã và hướng dẫn: [labs/11.3/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/11.3). Tóm tắt: lấy một file `.wasm`, chạy `wasm2wat` đọc, tìm hàm export kiểm tra key, dùng `wasm-decompile` để đối chiếu, rồi suy ra key.
