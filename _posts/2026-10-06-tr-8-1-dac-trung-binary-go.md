---
title: "Bài 8.1: Đặc trưng binary Go, và vì sao pclntab là món quà"
date: 2026-10-06 08:59:00 +0700
categories: ["Technique Reverse", "Phần 8 · Go"]
tags: [reverse-engineering, golang]
render_with_liquid: false
---
Lần đầu mở một binary Go trong IDA, cảm giác giống như lạc vào một thành phố lạ: hàng chục nghìn hàm, phần lớn tên là `runtime.*`, một file hello world bé xíu mà nặng gần 2 MB. Nhưng Go dễ thở hơn nhiều so với C++ bị strip, vì Go gói sẵn trong binary một thứ quý giá: bảng tên hàm. Bài này chỉ cho bạn nhận ra một binary Go và khai thác thứ bảng đó.

Mọi con số và đoạn asm dưới đây lấy từ một binary build thật bằng Go 1.22.0 trên Linux x64, bạn làm lại trong lab sẽ ra tương tự.

## Vì sao binary Go to và nhiều hàm đến thế

Build một hello world Go rồi so với C:

```
hello world C   (gcc, dynamic):   ~16 KB
hello world Go  (go build):       ~1.9 MB
```

Chênh hơn trăm lần. Lý do: Go **static-link mặc định**, và quan trọng hơn, nó nhét luôn cả **runtime** vào mỗi binary. Runtime đó gồm bộ lập lịch goroutine, garbage collector, quản lý bộ nhớ, reflection. Vì thế bạn thấy rừng hàm `runtime.*`, `fmt.*`, `sync.*` dù chương trình của bạn chỉ in một dòng.

Hệ quả thực tế cho người reverse: **đừng cố đọc hết.** 95% số hàm là runtime và thư viện chuẩn. Code của tác giả nằm trong các hàm tên `main.*` và package riêng của họ. Việc đầu tiên luôn là khoanh vùng cái `main.*`, bỏ qua phần còn lại. Nghe quen chứ, đây chính là tư duy "tìm main thật" ở [Bài 3.1](/posts/tr-3-1-hello-world-tim-main-that/), chỉ khác quy mô lớn hơn.

## pclntab: tại sao Go không bao giờ thực sự "stripped"

![Binary Go: runtime to, pclntab sống sót qua strip](/assets/img/technique-reverse/assets/phan-08/go-binary.svg)

Đây là điểm quan trọng nhất của bài. Go nhúng vào mỗi binary một cấu trúc gọi là **pclntab** (program counter line table). Mục đích gốc của nó là để runtime in stack trace có tên hàm và số dòng khi panic. Nhưng với người reverse, nó là một bảng ánh xạ địa chỉ sang tên hàm, nằm sẵn trong file.

Điều tuyệt vời: pclntab **sống sót qua cả khi strip**. Thử nghiệm thật:

```
go build            -> 1.9 MB, có symbol table
go build -ldflags="-s -w"  -> 1.2 MB, "stripped"
```

Bản `-s -w` làm `nm` không còn liệt kê được symbol thường. Nhưng pclntab vẫn nằm nguyên đó (trong thí nghiệm, magic của nó ở cùng một offset `0x4030b` trước và sau khi strip). Nghĩa là các tool chuyên dụng vẫn phục hồi được tên hàm từ một binary Go "đã strip". Đây là lý do dân RE hay nói đùa binary Go không bao giờ strip thật sự.

Magic number của pclntab theo phiên bản Go (4 byte đầu bảng), nhận ra nó là biết chắc đây là Go:

| Magic | Phiên bản Go |
|---|---|
| `fb ff ff ff` | Go 1.2 tới 1.15 |
| `fa ff ff ff` | Go 1.16, 1.17 |
| `f0 ff ff ff` | Go 1.18 tới 1.19 |
| `f1 ff ff ff` | Go 1.20 trở lên |

Bài [8.2](https://github.com/Haind03/Technique-Reverse/blob/main/phan-08-go/8.2-khoi-phuc-ten-ham-go.md) sẽ dùng GoReSym và plugin IDA/Ghidra để đọc pclntab và tự đặt lại tên cho hàng nghìn hàm chỉ bằng một cú chạy.

## Nhận ra một binary là Go

Trước khi xử lý, phải biết chắc đó là Go. Vài dấu hiệu, kiểm trong vài giây:

- **Kích thước**: một CLI nhỏ mà nặng 1 tới 5 MB là đáng nghi.
- **Chuỗi build info**: Go nhúng dòng phiên bản. Chạy lệnh chính thức:
  ```
  go version hello        ->  hello: go1.22.0
  go version -m hello     ->  kèm GOARCH, GOOS, build flags, module path
  ```
  Không có Go toolchain thì `strings` cũng thấy chuỗi kiểu `go1.22.0`.
- **Strings đặc trưng**: `runtime.`, `runtime.gopanic`, `fmt.`, tên package. Chạy `strings hello | grep '^go1\.'` hoặc `grep 'runtime\.'`.
- **DIE** (xem [Bài 2.1](/posts/tr-2-1-triage-die-strings-pebear/)) thường nhận ra luôn "Go build ID".

## Calling convention: cái bẫy phiên bản

Đây là chỗ người reverse hay vấp nếu quen C. Go đổi cách truyền tham số giữa các phiên bản:

- **Trước Go 1.17**: mọi tham số và giá trị trả về đi qua **stack**, không dùng register như C. Đọc code Go cũ bạn sẽ thấy nó đẩy tham số lên stack rồi hàm con đọc từ stack ra, khác hẳn thói quen `rcx/rdx` của Win64.
- **Từ Go 1.17 trở đi (ABIInternal)**: chuyển sang truyền qua **register**, nhưng thứ tự register KHÁC với C. Go dùng `RAX, RBX, RCX, RDI, RSI, R8, R9, R10, R11` cho tham số (9 register đầu), không phải `RDI, RSI, RDX...` của System V.

Nhìn hàm `add(a, b int) int` thật, build bằng Go 1.22 (register ABI):

```asm
TEXT main.add(SB)
    PUSHQ BP
    MOVQ  SP, BP
    SUBQ  $0x8, SP
    MOVQ  AX, 0x18(SP)     ; a vào từ AX  (không phải RDI)
    MOVQ  BX, 0x20(SP)     ; b vào từ BX  (không phải RSI)
    ADDQ  BX, AX           ; AX = a + b
    MOVQ  AX, 0(SP)
    ...
    RET                    ; trả về trong AX
```

Dịch ra: `a` đến trong `AX` (tức RAX), `b` trong `BX` (RBX), kết quả trả về cũng trong `AX`. Nếu bạn áp luật System V (`a` ở RDI) thì đọc sai toàn bộ. Luôn tự hỏi binary này build bằng Go phiên bản nào, rồi áp đúng ABI. IDA và Ghidra bản mới đã nhận ra Go ABI, nhưng bản cũ thì bạn phải tự biết.

Lưu ý cú pháp: `go tool objdump` dùng dạng Plan 9 (`AX`, `MOVQ`), còn IDA/Ghidra hiển thị Intel (`rax`, `mov`). Cùng một thứ, chỉ khác tên gọi.

## Những thứ Go để lại trong code

Vài pattern sẽ gặp nhiều, nói kỹ ở [Bài 8.3](/posts/tr-8-3-string-slice-interface-goroutine/), ở đây điểm danh để bạn khỏi bỡ ngỡ:

- **String không null-terminated**: Go string là cặp (con trỏ, độ dài), nên một chuỗi trong Go thường nằm dính liền với chuỗi khác trong một blob lớn, cắt ra theo độ dài. Thấy một khối text khổng lồ dính liền nhau là đặc trưng Go.
- **Kiểm tra bounds**: Go chèn check chỉ số mảng khắp nơi, nên code có nhiều lệnh so sánh rồi nhảy tới `runtime.panicIndex`.
- **Goroutine**: lời gọi `go f()` biến thành `runtime.newproc`.
- **Nhiều giá trị trả về**: hàm Go trả nhiều giá trị, trong register ABI là trả qua nhiều register.

## Checklist ghi nhớ
- Binary Go to vì static-link cộng runtime và GC đi kèm. Đừng đọc rừng `runtime.*`, tập trung `main.*`.
- pclntab là bảng tên hàm nhúng sẵn, sống sót qua strip, nên Go gần như không bao giờ strip thật. Tool phục hồi tên từ đó (Bài 8.2).
- Magic pclntab cho biết phiên bản Go: `f1 ff ff ff` là Go 1.20+.
- Nhận ra Go qua kích thước, build info (`go version -m`), chuỗi `runtime.`/`go1.x`.
- Calling convention đổi theo phiên bản: trước 1.17 qua stack, từ 1.17 qua register nhưng thứ tự là `RAX, RBX, RCX, RDI, RSI...`, khác System V. Trả về trong AX.
