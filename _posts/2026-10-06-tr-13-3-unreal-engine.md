---
title: "Bài 13.3: Reverse game Unreal Engine"
date: 2026-10-06 09:17:00 +0700
categories: ["Technique Reverse", "Phần 13 · Game: Unity, Unreal, Lua"]
tags: [reverse-engineering, game-hacking]
render_with_liquid: false
---
Unity cho bạn file DLL đọc gần như ra source. Unreal thì không hào phóng thế. Unreal Engine viết bằng C++, biên dịch thẳng ra native, nên toàn bộ logic nằm trong một file exe to đùng mà bạn phải mở bằng IDA/Ghidra như một chương trình C++ bình thường (quay lại Phần 4 là vừa). Bù lại, UE có hệ thống phản chiếu (reflection) riêng và một hệ sinh thái tool cộng đồng rất mạnh, nên vẫn có nhiều đường vào. Bài này vẽ bản đồ đó.

Phạm vi: nội dung dành cho game offline/single-player của chính bạn, mục đích học và nghiên cứu. Đụng vào game online nhiều người chơi là chuyện anti-cheat và điều khoản dịch vụ, không nằm trong phạm vi series.

## Nhận ra một game Unreal

Trước khi làm gì, xác nhận đây đúng là Unreal. Các dấu hiệu gần như không lẫn được:

- File chạy thường tên dạng `GameName-Win64-Shipping.exe`, nằm trong `GameName/Binaries/Win64/`.
- Có thư mục `Content/Paks/` chứa các file `.pak` (đôi khi `.utoc` và `.ucas` với định dạng IoStore mới).
- Asset rời (nếu chưa đóng pak) có đuôi `.uasset`, `.umap`.
- Trong strings của exe đầy chuỗi kiểu `/Game/`, `/Engine/`, tên class bắt đầu bằng `U`, `A`, `F` (UObject, AActor, FVector), và chuỗi phiên bản engine.

Biết được phiên bản UE (UE4.x hay UE5.x) rất quan trọng vì tool cộng đồng gắn chặt với phiên bản. Chuỗi trong exe hoặc file `.version` thường nói rõ.

## Ba thế giới của một game Unreal

Khi reverse Unreal, bạn làm việc trên ba mặt trận khác nhau, chọn mặt trận theo thứ bạn cần:

1. **Asset trong file .pak**: model, texture, âm thanh, và quan trọng với reverser là Blueprint và DataTable. Dùng FModel/UModel.
2. **Code C++ native trong exe**: logic lõi, hàm engine, chống phân tích. Dùng IDA/Ghidra, hỗ trợ bởi SDK dump.
3. **Runtime**: inject vào game đang chạy để gọi hàm, đọc object, scripting. Dùng UE4SS.

### File .pak và chuyện mã hoá AES

`.pak` là archive gói toàn bộ asset. Nhiều game để nguyên không mã hoá, khi đó FModel/UModel mở thẳng. Nhưng không ít game mã hoá index (và đôi khi cả nội dung) bằng **AES-256**. Lúc đó bạn cần **AES key** mới duyệt được.

Key đó nằm đâu đó trong exe, được nạp vào lúc chạy. Hai cách lấy phổ biến:

- Dùng tool quét exe tìm key (các AES key finder cho UE, chúng tìm pattern 32 byte ở vùng hay chứa key).
- Dump key từ bộ nhớ lúc game chạy, hoặc đặt breakpoint tại hàm giải mã pak.

Có key rồi, nạp vào FModel là duyệt được cây asset như duyệt thư mục.

### FModel và UModel

- **FModel**: trình duyệt asset hiện đại, hỗ trợ cả định dạng IoStore (.utoc/.ucas) của UE mới, xem preview, export texture/model/âm thanh, và đọc được DataTable (bảng dữ liệu game, nơi hay chứa chỉ số vật phẩm, công thức, v.v.). Đây là nơi bắt đầu tốt nhất.
- **UModel (UE Viewer)**: lâu đời, mạnh về trích model và texture để xem/chuyển định dạng.

Với reverser, DataTable và Blueprint trong pak thường trả lời được nhiều câu hỏi mà không cần mở exe.

### Blueprint

Blueprint là visual scripting của Unreal, biên dịch thành một dạng bytecode chạy trên VM của engine (Kismet bytecode). Nó không phải native code, nằm trong asset Blueprint. Đọc Blueprint bytecode khó chịu và tool còn hạn chế, nhưng nhiều logic gameplay nằm ở đây thay vì trong C++. FModel xem được cấu trúc Blueprint ở mức nào đó; để đọc sâu bytecode thì cần tool chuyên và kiên nhẫn.

## SDK dump: chìa khoá đọc exe

Mở exe Unreal trong IDA mà không chuẩn bị gì thì bạn chết chìm: hàng trăm nghìn hàm, không tên. Cứu cánh là hệ thống **reflection** của Unreal. Engine lưu thông tin về mọi UClass, UProperty, UFunction trong bộ nhớ lúc chạy (để serialize, để Blueprint gọi C++, để editor hoạt động). Một **SDK dumper** duyệt các cấu trúc đó và sinh ra header C++ mô tả toàn bộ class, offset field, và địa chỉ hàm của game cụ thể này.

Có SDK rồi, bạn biết:
- Struct của các object quan trọng (vị trí người chơi nằm ở offset nào trong AActor, máu ở đâu).
- Tên và địa chỉ các UFunction, map ngược vào IDA để đặt tên hàm.

Các dumper hoạt động bằng cách đi từ GObjects (mảng toàn cục mọi UObject) và GNames (bảng tên), hai global mà bạn phải tìm offset cho đúng phiên bản game. Cộng đồng có sẵn nhiều dumper, phổ biến nhất hiện nay tích hợp trong UE4SS.

## UE4SS: dao đa năng runtime

**UE4SS** (Unreal Engine Scripting System) là một DLL inject vào game, cho bạn:

- **Dump SDK** tự động (C++ header và cả dạng cho các tool khác).
- **Live property viewer**: duyệt cây UObject đang sống, xem và sửa property trực tiếp.
- **Scripting bằng Lua**: viết script gọi UFunction, hook hàm, thay đổi hành vi mà không cần patch exe. Rất mạnh để thử nghiệm nhanh.
- Console và nhiều tiện ích modding.

Workflow điển hình: inject UE4SS, dump SDK, mở live viewer tìm object và property bạn quan tâm, rồi hoặc viết Lua script để can thiệp, hoặc mang offset/địa chỉ hàm sang IDA để phân tích tĩnh sâu hơn.

## Quy trình đặt cạnh nhau

```
   Nhận diện UE (tên exe, Content/Paks, phiên bản)
            |
   +--------+-----------------------------+
   |                                      |
  Asset?                               Logic?
   |                                      |
  FModel/UModel                   UE4SS inject
  (lấy AES key nếu cần)           dump SDK
   |                                      |
  DataTable, Blueprint,          live viewer +
  texture, model                 Lua script, hoặc
                                 mang offset sang IDA/Ghidra
                                 đọc C++ native (Phần 4)
```

Điểm mấu chốt cần nhớ: Unreal khó hơn Unity vì không có bước "mở DLL đọc source". Nhưng hệ thống reflection của chính engine là điểm yếu bạn khai thác: nó buộc phải mô tả mọi class và hàm trong bộ nhớ để engine chạy, và SDK dumper chỉ việc đọc lại mô tả đó.

## Lab tự làm

Xem [labs/13.3/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/13.3). Nhiệm vụ: với một game Unreal offline của bạn, duyệt `.pak` bằng FModel (lấy AES key nếu bị mã hoá), rồi inject UE4SS để dump SDK và tìm một class trong live viewer.

## Checklist ghi nhớ
- Unreal là C++ native: logic trong exe to, mở bằng IDA/Ghidra như chương trình C++ (Phần 4).
- Nhận diện qua `-Shipping.exe`, `Content/Paks/*.pak`, chuỗi `/Game/`, class U/A/F.
- Asset trong .pak: FModel/UModel duyệt, cần AES key nếu index bị mã hoá.
- Reflection của engine là điểm vào: SDK dumper đọc GObjects/GNames sinh header C++ với offset và địa chỉ hàm.
- UE4SS inject runtime: dump SDK, live property viewer, scripting Lua.
- Blueprint là bytecode riêng nằm trong asset, không phải native code.
