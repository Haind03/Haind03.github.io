---
title: "Bài 8.3: String, slice, interface và goroutine của Go trong assembly"
date: 2026-10-06 09:01:00 +0700
categories: ["Technique Reverse", "Phần 8 · Go"]
tags: [reverse-engineering, golang]
render_with_liquid: false
---
Bài trước bạn đã biết cách khôi phục tên hàm Go nhờ pclntab. Nhưng đọc được tên hàm mới là một nửa. Nửa còn lại là hiểu các kiểu dữ liệu đặc trưng của Go, vì chúng không giống C chút nào. Chuỗi Go không kết thúc bằng byte 0, slice là một bộ ba, interface giấu con trỏ kiểu ở đâu đó, và mỗi `go func` biến thành một lời gọi runtime. Không nắm mấy cái này, bạn nhìn disassembly Go mà cứ ngỡ đang đọc thứ bị hỏng.

Mọi đoạn asm và số liệu trong bài là output thật, build bằng Go 1.22 trên Linux x64, lấy ra bằng `go tool objdump` và `go tool nm`.

## Go string: con trỏ cộng độ dài, không có byte 0

Đây là khác biệt làm người quen C vấp ngay. Trong C, chuỗi là một dãy byte kết thúc bằng `\x00`, nên bạn cứ đọc tới khi gặp 0 là hết. Go thì khác: một string value là một struct hai trường:

```
type string struct {
    data *byte   // con trỏ tới byte đầu
    len  int     // độ dài, tính bằng byte
}
```

Không có terminator. Độ dài nằm riêng trong một trường. Hệ quả cực kỳ quan trọng cho reverse: **các chuỗi literal trong binary Go bị gộp thành một khối dài dính liền nhau, không có gì phân tách.** Compiler nhét tất cả vào một blob rồi mỗi chỗ dùng chỉ giữ con trỏ và độ dài trỏ vào đúng đoạn của mình.

Nhìn tận mắt cái blob đó trong binary demo của bài này:

```
secret length:1907348632812595367431640625unexpected EOFunsafe...
sum:true3125-Inf+Inffileboolint8uintchanfunccall...
```

Thấy chưa? Chuỗi `"secret length:"` chạy thẳng vào `"1907348..."` rồi `"unexpected EOF"` mà không có byte 0 nào ngăn cách. Nếu bạn mở cái này trong IDA và để nó tự dò chuỗi kiểu C, nó sẽ gộp cả cụm thành một chuỗi khổng lồ vô nghĩa, hoặc cắt sai chỗ.

Cách xử lý: đừng tin ranh giới chuỗi mà IDA tự đoán. Thay vào đó đi theo chỗ code nạp chuỗi, vì ở đó compiler luôn nạp kèm cả con trỏ lẫn độ dài. Nhìn đoạn asm thật nạp chuỗi `"GopherReverse"` (13 ký tự):

```asm
LEAQ 0x78bd(IP), CX        ; CX = con trỏ tới data của chuỗi
MOVQ CX, 0x98(SP)          ; lưu con trỏ
MOVL $0xd, AX              ; AX = 0xd = 13 = độ dài "GopherReverse"
```

`0xd` chính là 13, đúng độ dài `"GopherReverse"`. Mẹo vàng: thấy một `LEAQ` nạp con trỏ vào blob chuỗi, ngay cạnh là một hằng số nhỏ nạp vào register khác, hằng số đó gần như chắc là độ dài chuỗi. Lấy con trỏ, cộng độ dài, bạn cắt đúng chuỗi ra khỏi blob.

## Slice: con trỏ, len, cap

Slice Go là struct ba trường, 24 byte trên x64:

```
type slice struct {
    data *T   // con trỏ tới mảng nền
    len  int  // số phần tử đang dùng
    cap  int  // sức chứa
}
```

Khi bạn tạo một slice literal, compiler dựng mảng nền rồi nhồi các giá trị vào. Nhìn `[]int{3, 8, 15, 16, 23, 42}` build ra asm thật:

```asm
MOVQ $0x3,  0x30(SP)       ; phần tử 0 = 3
MOVQ $0x8,  0x38(SP)       ; phần tử 1 = 8
MOVQ $0xf,  0x40(SP)       ; phần tử 2 = 15 (0xf)
MOVQ $0x10, 0x48(SP)       ; phần tử 3 = 16
MOVQ $0x17, 0x50(SP)       ; phần tử 4 = 23 (0x17)
MOVQ $0x2a, 0x58(SP)       ; phần tử 5 = 42 (0x2a)
```

Sáu phần tử int, mỗi cái 8 byte, xếp liền nhau trên stack cách nhau đúng 8. Đây là cách nhận ra một slice literal: một loạt `MOVQ` ghi các giá trị vào vị trí stack liên tiếp. Khi slice được truyền vào hàm, bạn sẽ thấy ba thứ đi cùng nhau: con trỏ, len, cap.

## Interface: hai con trỏ

Một interface value cũng là struct hai trường:

```
type iface struct {
    tab  *itab   // con trỏ tới bảng kiểu (itab), cho biết kiểu động và method
    data *T      // con trỏ tới dữ liệu thật
}
```

`itab` chứa thông tin kiểu và bảng method, giống vai trò của vtable trong C++ (xem lại Bài 4.2). Khi gọi một method qua interface, Go đọc con trỏ hàm từ itab rồi gọi gián tiếp, y như virtual call. Trong asm bạn thấy một `MOVQ` lấy con trỏ hàm từ offset trong itab rồi `CALL` nó. Thấy `go:itab.*os.File,io.Writer` trong disassembly (có thật trong demo) là dấu hiệu rõ ràng của interface: nó ghép kiểu cụ thể `*os.File` với interface `io.Writer`.

## Goroutine: go func thành runtime.newproc

Đây là chỗ Go trông lạ nhất. Khi bạn viết `go f(x)`, compiler không gọi `f` trực tiếp. Nó đóng gói hàm và tham số rồi gọi `runtime.newproc`, và scheduler của Go lo chạy nó trên một goroutine riêng. Trong demo, nm xác nhận:

```
main.main.func1              ; thân của goroutine (closure)
main.main.gowrap1            ; wrapper Go sinh ra
main.main.func1.deferwrap1   ; wrapper cho defer bên trong
runtime.newproc              ; hàm tạo goroutine
```

Nên khi bạn thấy một `CALL runtime.newproc` trong code, hiểu ngay: ở đây có một `go func(...)`. Thân thật của goroutine nằm ở một hàm riêng tên kiểu `main.xxx.funcN`. Muốn biết goroutine làm gì, nhảy vào hàm funcN đó.

Tương tự, `defer` biến thành `deferwrap`/`runtime.deferproc` và được chạy lúc hàm return (`runtime.deferreturn`). Channel thành các lời gọi `runtime.chansend`/`runtime.chanrecv`. Map thành `runtime.makemap`, `runtime.mapaccess`, `runtime.mapassign`. Nhận ra các tên runtime này là bạn đọc được ý đồ code cấp cao mà không cần lần từng lệnh.

## Nhận ra lời gọi runtime, la bàn của bạn

Điểm chung của mọi thứ trên: Go đẩy rất nhiều việc cho runtime, và các hàm runtime đều có tên rõ ràng (sau khi bạn khôi phục symbol ở Bài 8.2). Học thuộc vài cái hay gặp là đọc Go nhanh hẳn:

| Thấy lời gọi | Nghĩa là |
|---|---|
| `runtime.newproc` | có một `go func(...)` |
| `runtime.deferproc` / `deferreturn` | có `defer` |
| `runtime.makemap` / `mapaccess` / `mapassign` | thao tác map |
| `runtime.makeslice` / `growslice` | tạo/mở rộng slice |
| `runtime.chansend` / `chanrecv` | gửi/nhận trên channel |
| `runtime.convT64` / `convTstring` | đóng gói giá trị vào interface |
| `runtime.stringtoslicebyte` | đổi string sang []byte |
| `runtime.concatstrings` | nối chuỗi |

## Lab tự làm

Mã nguồn và hướng dẫn trong [labs/8.3/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/8.3). Bạn sẽ build chính chương trình Go của bài này, soi cái string blob dính liền, và lần theo cách code nạp chuỗi bằng con trỏ cộng độ dài.

## Checklist ghi nhớ
- Go string là (con trỏ, độ dài), KHÔNG kết thúc bằng byte 0. Chuỗi literal gộp thành một blob dính liền.
- Để cắt đúng chuỗi, đi theo chỗ code nạp nó: một `LEAQ` con trỏ cạnh một hằng số nhỏ chính là độ dài.
- Slice = (data, len, cap), 24 byte. Slice literal là một loạt MOVQ vào stack liên tiếp.
- Interface = (itab, data), gọi method qua itab giống virtual call.
- `go func` thành `runtime.newproc`, thân thật nằm ở hàm `funcN` riêng.
- Học tên các hàm runtime (newproc, deferproc, makemap, chansend) để đọc ý đồ cấp cao nhanh.
