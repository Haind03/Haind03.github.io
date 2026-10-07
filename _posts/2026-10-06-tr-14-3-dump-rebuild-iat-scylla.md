---
title: "Bài 14.3: Dump tiến trình và rebuild IAT bằng Scylla"
date: 2026-10-06 09:22:00 +0700
categories: ["Technique Reverse", "Phần 14 · Packer & Obfuscation"]
tags: [reverse-engineering, packer, obfuscation]
render_with_liquid: false
---
Ở [bài 14.2](/posts/tr-14-2-unpack-upx-oep/) bạn đã lần được tới OEP, nghĩa là stub giải nén đã chạy xong và code gốc đang nằm nguyên vẹn trong bộ nhớ. Bước tự nhiên tiếp theo là lấy nó ra thành một file chạy được. Nghe đơn giản: cứ dump vùng nhớ ra đĩa là xong chứ gì. Thử đi, rồi bạn sẽ thấy file dump ra chạy là crash ngay. Bài này giải thích vì sao, và cách Scylla sửa nó.

## Vì sao dump thô không chạy được

Vấn đề nằm ở IAT (Import Address Table), bảng chứa địa chỉ các hàm API mà chương trình gọi.

Khi Windows nạp một file PE bình thường, loader đọc import directory (danh sách "tôi cần hàm `MessageBoxA` từ `user32.dll`"), tự tìm địa chỉ thật của từng hàm rồi điền vào IAT. Lúc chạy, chương trình gọi API qua bảng này.

Giờ xét file đã unpack trong bộ nhớ:

- IAT trong bộ nhớ đã chứa **địa chỉ thật** rồi, vì stub giải nén đã resolve xong lúc chạy.
- Nhưng cái import directory mô tả "cần hàm nào từ DLL nào" thì packer đã vứt đi hoặc làm hỏng, vì nó không cần nữa.

Nên khi bạn dump thô ra đĩa và chạy lại, trên máy khác (hoặc sau khi ASLR đổi base DLL), những địa chỉ thật trong IAT trở thành vô nghĩa, mà loader lại không có import directory để resolve lại. Chương trình gọi vào địa chỉ rác và chết.

Tóm lại: dump có **giá trị IAT** nhưng mất **bản mô tả để tái tạo IAT**. Việc của Scylla là dựng lại bản mô tả đó.

## Scylla làm gì

Scylla (phiên bản x64 là Scylla x64, hay dùng kèm plugin trong x64dbg) đi theo đúng logic trên:

1. **Attach** vào tiến trình đang dừng ở OEP (hoặc chọn nó từ danh sách process). Lưu ý tiến trình phải đang sống và dừng đúng chỗ, đừng để nó chạy tiếp hay thoát.
2. **Đặt OEP**: điền địa chỉ OEP bạn vừa tìm được vào ô OEP. Đây sẽ là entry point của file mới.
3. **IAT Autosearch**: Scylla quét bộ nhớ quanh vùng code để tìm ra bảng IAT (một dãy con trỏ trỏ vào các DLL hệ thống). Nó đoán điểm đầu và kích thước.
4. **Get Imports**: từ mỗi con trỏ trong IAT, Scylla tra ngược xem địa chỉ đó thuộc hàm nào của DLL nào, dựng lại danh sách import đầy đủ. Đây là bước tái tạo "bản mô tả" đã mất.
5. **Dump**: ghi vùng nhớ của module ra file.
6. **Fix Dump**: ghép file dump vừa tạo với import directory mới dựng, thêm một section chứa bảng import, và sửa PE header (đặt lại entry point về OEP, trỏ Import Directory tới bảng mới).

Kết quả là một file PE chạy độc lập, loader Windows resolve import lại được như một file bình thường.

## Đọc kết quả Get Imports

Sau khi Get Imports, Scylla hiện một cây: mỗi DLL và các hàm của nó. Thứ cần để ý là các dòng được đánh dấu đỏ hoặc "not found". Chúng là con trỏ trong IAT mà Scylla không map được về hàm nào. Vài khả năng:

- **IAT Autosearch bắt dư**: vùng nó đoán là IAT lẫn cả dữ liệu không phải con trỏ import. Thu hẹp lại điểm đầu hoặc kích thước.
- **Redirected imports**: một số protector không để IAT trỏ thẳng vào DLL mà trỏ vào một đoạn stub trung gian của riêng nó (thunk che import), rồi stub mới nhảy vào hàm thật. Scylla thấy con trỏ trỏ vào vùng của packer chứ không vào user32/kernel32 nên chịu. Scylla có tuỳ chọn "Trace redirected imports" cố đi xuyên qua stub, nhưng với IAT bị che tinh vi thì phải sửa tay hoặc dùng công cụ khác.

Nguyên tắc: xoá các entry rác (right-click, cut thunk) trước khi Fix Dump, nếu không bảng import mới sẽ chứa mục hỏng và file vẫn không chạy.

## Khi Autosearch không ra

Nếu IAT Autosearch tìm không đúng, bạn tự xác định IAT bằng cách nhìn trong x64dbg: tới một lời gọi API trong code đã unpack (ví dụ `call [0x00407120]`), thì `0x00407120` chính là một ô trong IAT. Follow địa chỉ đó trong dump, cuộn lên xuống để thấy ranh giới của dãy con trỏ trỏ vào DLL, rồi điền thủ công điểm đầu và kích thước vào Scylla.

## Quy trình gọn

```
x64dbg: unpack tới OEP (bài 14.2)
   |
Scylla: Attach process
   |
đặt OEP = địa chỉ OEP
   |
IAT Autosearch  ->  Get Imports
   |
dọn các entry đỏ / redirected
   |
Dump  ->  Fix Dump
   |
chạy thử file _dump_SCY.exe
```

## Cạm bẫy thường gặp

- **Dump trước khi tới OEP**: code chưa giải nén xong, dump ra là rác. Luôn chắc chắn đã ở OEP.
- **Quên Fix Dump**: file Dump thô vẫn thiếu import, phải Fix Dump mới ghép bảng import vào.
- **Sai OEP vài byte**: entry point lệch, chương trình chạy sai ngay từ đầu. OEP phải là đúng lệnh đầu của code gốc (thường là prologue chuẩn hoặc call tới CRT init).
- **Section không đủ quyền**: đôi khi phải chỉnh characteristics của section cho đúng (readable/executable) nếu file dump bị lỗi quyền.

## Checklist ghi nhớ
- Dump thô không chạy vì có giá trị IAT nhưng mất import directory để loader tái tạo.
- Scylla: Attach, đặt OEP, IAT Autosearch, Get Imports, Dump, Fix Dump.
- Dọn các entry đỏ và xử lý redirected imports trước khi Fix Dump.
- Nếu Autosearch sai, tìm IAT thủ công từ một `call [address]` trong code đã unpack.
- Luôn dump ở đúng OEP, sai OEP là hỏng cả file.

## Lab tự làm
Xem [labs/14.3/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/14.3/README.md). Tiếp nối file đã unpack thủ công ở lab 14.2, dùng Scylla để dump và fix IAT thành file chạy độc lập.
