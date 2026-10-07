---
title: "Bài 14.1: Packer hoạt động thế nào, và làm sao nhận ra nó"
date: 2026-10-06 09:20:00 +0700
categories: ["Technique Reverse", "Phần 14 · Packer & Obfuscation"]
tags: [reverse-engineering, packer, obfuscation]
render_with_liquid: false
---
Có một khoảnh khắc ai làm RE cũng gặp: mở một file trong IDA, háo hức tìm logic, thì thấy đúng vài chục lệnh rồi một cú nhảy vào vùng toàn byte rác. Không strings có nghĩa, bảng import rỗng tuếch, đọc mãi không ra gì. Đó không phải bạn dốt. Đó là file đã bị pack, và thứ bạn đang nhìn chỉ là lớp vỏ.

Bài này giúp bạn nhận ra chuyện đó trong một phút, thay vì phí cả buổi tối đọc code không bao giờ chạy.

## Packer làm gì với chương trình

Ý tưởng của packer rất đơn giản. Lấy code gốc của chương trình, nén hoặc mã hoá nó thành một khối dữ liệu, rồi gắn thêm một đoạn code nhỏ gọi là stub (hay unpacking stub). Khi chạy, stub làm việc trước: nó giải nén/giải mã khối dữ liệu kia ra lại thành code gốc trong bộ nhớ, rồi nhảy tới đó để chương trình chạy bình thường.

```
File trên đĩa:               Khi chạy (trong bộ nhớ):
+------------------+          +------------------+
| unpacking stub   |  --->    | stub (đã chạy)   |
+------------------+          +------------------+
| code gốc đã nén/ |  giải    | code gốc ĐÃ HIỆN |  <- giờ mới đọc được
| mã hoá (rác)     |  nén ra  | rõ ở đây         |
+------------------+          +------------------+
```

Hệ quả quan trọng nhất cho người làm RE: **code thật chỉ tồn tại ở dạng đọc được trong bộ nhớ lúc chạy, không có trên đĩa.** Nên phân tích tĩnh (mở bằng IDA/Ghidra đọc file) sẽ chỉ thấy stub và một đống rác. Muốn thấy code thật, bạn phải để nó tự giải nén rồi chộp lấy, đó là chuyện của bài [14.2](https://github.com/Haind03/Technique-Reverse/blob/main/phan-14-packer-obfuscation/14.2-unpack-upx.md) và [14.3](https://github.com/Haind03/Technique-Reverse/blob/main/phan-14-packer-obfuscation/14.3-dump-rebuild-iat.md).

## OEP: đích đến của mọi cuộc unpack

Stub chạy xong phần giải nén thì nó phải nhảy về điểm bắt đầu thật của chương trình. Điểm đó gọi là OEP (Original Entry Point), chính là entry point mà chương trình sẽ có nếu không bị pack.

Cả nghề unpack thủ công quy về một câu: tìm cho ra OEP. Tới được OEP nghĩa là stub đã giải nén xong, code gốc đã nằm đầy đủ trong bộ nhớ, và đây là thời điểm vàng để dump ra. Nhớ từ OEP này, nó quay lại liên tục trong cả Phần 14.

## Nhận ra file bị pack trong một phút

Không cần unpack mới biết file có bị pack hay không. Vài dấu hiệu lộ liễu:

### 1. Entropy cao

Entropy là thước đo độ "ngẫu nhiên" của dữ liệu, thang từ 0 tới 8. Code và text bình thường có entropy tầm 5 tới 6.5. Dữ liệu đã nén hoặc mã hoá trông gần như ngẫu nhiên, nên entropy vọt lên sát 8.0. Thấy một section có entropy 7.8 trở lên là gần như chắc nó bị nén hoặc mã hoá.

Detect It Easy (DIE, có sẵn trong repo này tại thư mục cha `die_win64_portable_3.08_x64`) có nút Entropy vẽ biểu đồ entropy theo từng vùng file. Một file sạch có đường entropy gập ghềnh vừa phải. Một file packed có một khối phẳng lì ở sát mức 8.

### 2. Bảng import nghèo nàn một cách đáng ngờ

Một chương trình Windows bình thường gọi hàng chục tới hàng trăm hàm API, nên bảng import (IAT) dài. File bị pack thì khác: stub chưa cần API gì nhiều, nó chỉ cần vài hàm để tự dựng lại import sau khi giải nén, điển hình là `LoadLibraryA` và `GetProcAddress`. Nên khi bạn thấy một file exe đầy đủ chức năng mà bảng import chỉ có dăm ba hàm, trong đó có `LoadLibrary` và `GetProcAddress`, đó là dấu hiệu rất mạnh của packer.

### 3. Tên section lạ

Packer hay đặt tên section theo thương hiệu của nó. Vài cái quen mặt:

| Tên section | Packer/protector |
|---|---|
| `UPX0`, `UPX1` | UPX |
| `.vmp0`, `.vmp1` | VMProtect |
| `.themida`, `.winlice` | Themida/WinLicense |
| `.aspack`, `.adata` | ASPack |
| `.petite` | Petite |
| `.enigma1` | Enigma Protector |

Section chuẩn của compiler là `.text`, `.data`, `.rdata`, `.rsrc`. Thấy tên lạ là nghi ngay.

### 4. Section vừa ghi vừa thực thi

Code bình thường nằm trong section chỉ-đọc-và-thực-thi (R-X). Nhưng stub phải ghi code đã giải nén vào một vùng rồi chạy nó, nên vùng đó cần cả quyền ghi lẫn thực thi (RWX hoặc một section có cả WRITE và EXECUTE). Một section vừa ghi được vừa chạy được là cờ đỏ, hiếm thấy trong phần mềm sạch (xem lại [Bài 1.2](/posts/tr-1-2-bo-nho-tien-trinh/)).

### 5. Rất ít strings có nghĩa

Chuỗi trong code gốc (thông báo, URL, path) bị nén/mã hoá nên biến mất khỏi output `strings`. Cái còn lại thường chỉ là chuỗi của stub. Một exe to mà `strings` ra gần như trống là đáng ngờ.

## Packer với protector: cùng họ, khác mục đích

Hai từ này hay bị dùng lẫn, nên phân biệt cho rõ:

- **Packer** chủ yếu để **nén** (giảm kích thước) hoặc che code ở mức cơ bản. UPX là ví dụ kinh điển, vốn sinh ra để nén exe. Packer đơn thuần tương đối dễ gỡ.
- **Protector** nhắm tới **chống phân tích**. Ngoài việc nén/mã hoá, nó thêm anti-debug, anti-VM, anti-dump, kiểm tra toàn vẹn, và nặng nhất là virtualization (biến code thành bytecode của một VM riêng). Themida, VMProtect, Enigma thuộc nhóm này. Gỡ protector khó hơn nhiều bậc.

Ranh giới không tuyệt đối (nhiều packer hiện đại kèm chút bảo vệ), nhưng biết mình đang đối đầu loại nào quyết định bạn bỏ ra một giờ hay một tuần. Anti-debug và anti-VM là nội dung Phần 15, virtualization là [Bài 14.5](https://github.com/Haind03/Technique-Reverse/blob/main/phan-14-packer-obfuscation/14.5-virtualization.md).

## Quy trình triage packer

Gói lại thành thói quen, mỗi khi nghi một file bị pack:

1. Kéo file vào DIE, xem nó nhận ra packer gì không (DIE có signature cho hầu hết packer phổ biến).
2. Bấm nút Entropy, nhìn có khối nào phẳng sát 8.0 không.
3. Xem bảng import, có nghèo nàn bất thường và chỉ có `LoadLibrary`/`GetProcAddress` không.
4. Xem tên section, có tên lạ không.
5. Kết luận: packed hay không, nếu có thì loại gì, packer hay protector.

Xong bước này bạn biết mình đang cầm cái gì và chọn chiến thuật: UPX thì `upx -d` một phát (bài 14.2), packer tuỳ biến thì unpack thủ công tìm OEP, protector mạnh thì cân nhắc có đáng không.

## Checklist ghi nhớ
- Packer nén/mã hoá code gốc, kèm stub giải nén lúc chạy. Code thật chỉ hiện trong bộ nhớ runtime, không có trên đĩa.
- OEP (Original Entry Point) là đích của mọi cuộc unpack: tới đó là code gốc đã sẵn sàng trong bộ nhớ.
- Năm dấu hiệu packed: entropy sát 8.0, import nghèo (LoadLibrary/GetProcAddress), tên section lạ, section vừa ghi vừa chạy, ít strings.
- Dùng Detect It Easy để nhận diện nhanh (signature + entropy).
- Packer để nén, protector để chống phân tích (thêm anti-debug/anti-VM/virtualization). Biết loại nào để chọn công sức.
