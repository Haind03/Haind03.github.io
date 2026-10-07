---
title: "Bài 8.2: Khôi phục tên hàm và kiểu trong binary Go"
date: 2026-10-06 09:00:00 +0700
categories: ["Technique Reverse", "Phần 8 · Go"]
tags: [reverse-engineering, golang]
render_with_liquid: false
---
Mở một binary Go trong IDA lần đầu, bạn sẽ thấy một biển hàm `sub_xxxxxx` và cảm giác tuyệt vọng quen thuộc. Nhưng Go có một bí mật dễ chịu: ngay cả khi binary bị strip, phần lớn tên hàm vẫn còn nằm đâu đó bên trong, chỉ là công cụ chưa biết cách đọc. Bài này chỉ cho bạn lấy chúng ra.

## Vì sao Go stripped vẫn khôi phục được

Go runtime cần tự biết tên hàm lúc chạy, để in stack trace khi panic. Nghĩa là compiler buộc phải nhúng sẵn một bảng ánh xạ từ địa chỉ sang tên hàm ngay trong binary, bất kể bạn có strip hay không. Bảng đó tên là **pclntab** (program counter line table).

Thêm nữa, Go lưu cả thông tin kiểu (type) cho reflection và garbage collector trong một cấu trúc gọi là **moduledata**. Gộp lại, một binary Go mang theo nhiều metadata hơn hẳn một binary C stripped. Strip chỉ bỏ symbol table ELF/PE tiêu chuẩn, chứ không đụng tới pclntab và moduledata. Đó là lý do công cụ chuyên dụng lấy lại được rất nhiều.

Điểm mấu chốt cần nhớ: với Go, đừng vội nản khi thấy stripped. Chạy đúng tool trước đã.

## GoReSym, con dao chính

**GoReSym** (của Mandiant) là công cụ đáng chạy đầu tiên. Nó parse pclntab và moduledata để lấy lại:

- tên hàm (cả hàm người viết lẫn hàm thư viện chuẩn),
- thông tin kiểu (type),
- build info: phiên bản Go, danh sách module/package, đôi khi cả đường dẫn source.

Chạy cơ bản:

```
GoReSym.exe -t -d -p target_go.exe > symbols.json
```

- `-t` trích type, `-d` lấy luôn các package mặc định của Go, `-p` lấy path/build info.
- Kết quả là JSON chứa tên hàm kèm địa chỉ, rồi bạn nạp ngược vào IDA/Ghidra bằng script để đổi tên hàng loạt.

Riêng việc biết phiên bản Go đã quý: cú pháp calling convention của Go đổi ở Go 1.17 (từ truyền tham số qua stack sang truyền qua register, ABIInternal), nên biết version giúp bạn đọc đúng tham số. Chuyện này đã nói ở bài trước của phần.

## Plugin cho IDA và Ghidra

Nếu thích làm gọn trong một công cụ thay vì qua JSON trung gian:

- **IDAGolangHelper** và **golang_loader_assist**: script IDA (IDAPython) dò pclntab ngay trong IDA và đổi tên hàm tại chỗ. Tiện khi bạn đã ở sẵn trong IDA.
- **GolangAnalyzerExtension** (GOA): extension cho Ghidra. Sau khi cài, nó tự nhận binary Go, khôi phục tên hàm, dựng lại type, nhận diện string của Go (vốn không null-terminated mà là con trỏ kèm độ dài, nên tool mặc định hay đọc sai).
- **redress**: công cụ dòng lệnh cho thông tin build và cấu trúc package của binary Go, hữu ích để triage nhanh.

Trong thực tế nhiều người chạy GoReSym để lấy JSON (ổn định, không phụ thuộc version IDA), rồi mới nạp vào công cụ yêu thích. Plugin thì nhanh nhưng đôi khi kén phiên bản Go mới.

## Chuỗi trong Go, một cái bẫy riêng

Kể cả sau khi có tên hàm, chuỗi vẫn làm bạn vấp. String trong Go không kết thúc bằng byte 0 như C. Nó là một struct hai trường: con trỏ tới dữ liệu và độ dài. Các chuỗi hằng còn bị gộp chung thành một khối lớn liền nhau trong `.rodata`, không có dấu phân cách.

Hậu quả: cửa sổ Strings mặc định của IDA/Ghidra sẽ hiển thị cả khối dính liền thành một chuỗi khổng lồ vô nghĩa. GolangAnalyzerExtension và các script Go xử lý được việc này, cắt đúng từng chuỗi theo độ dài. Nếu không có tool, bạn phải nhìn cách code nạp cặp (con trỏ, độ dài) để biết ranh giới chuỗi thật.

## Quy trình gọn

1. Nhận diện đây là binary Go (DIE, hoặc thấy chuỗi `go:buildid`, section `.gopclntab`, pattern runtime Go).
2. Chạy GoReSym lấy symbols.json, đọc luôn phiên bản Go và package list.
3. Nạp symbol vào IDA/Ghidra (script import JSON) hoặc chạy plugin tương ứng.
4. Cài thêm xử lý string Go (GOA hoặc script) để chuỗi hiện đúng.
5. Giờ mới bắt đầu đọc code: tập trung vào package của tác giả (thường là `main.*`), bỏ qua runtime và thư viện chuẩn.

Bước 5 là chỗ tiết kiệm thời gian lớn nhất: sau khi khôi phục tên, hàm `main.main`, `main.validateLicense` hiện ra rõ ràng giữa hàng nghìn hàm runtime, và bạn đi thẳng tới chỗ cần.

## Lab tự làm

Xem [labs/8.2/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/8.2). Bạn sẽ chạy GoReSym trên một binary Go, so sánh cửa sổ hàm trong Ghidra trước và sau khi có symbol, để thấy tận mắt khác biệt mà pclntab mang lại.

## Checklist ghi nhớ
- Binary Go stripped vẫn khôi phục được nhiều tên hàm nhờ pclntab (runtime cần nó để in stack trace).
- GoReSym là tool chạy đầu tiên: lấy tên hàm, type, build info, phiên bản Go.
- Plugin thay thế: IDAGolangHelper (IDA), GolangAnalyzerExtension (Ghidra), redress (CLI).
- Biết phiên bản Go để đọc đúng calling convention (đổi ở Go 1.17).
- String Go là (con trỏ, độ dài), không null-terminated, cần tool cắt đúng kẻo đọc sai.
- Sau khi khôi phục, tập trung vào package `main.*`, bỏ qua runtime.
