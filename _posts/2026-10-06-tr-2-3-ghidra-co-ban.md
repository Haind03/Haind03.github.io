---
title: "Bài 2.3: Ghidra cơ bản, con dao miễn phí mà đắt tiền"
date: 2026-10-06 08:19:00 +0700
categories: ["Technique Reverse", "Phần 2 · Làm quen bộ công cụ"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
Ghidra là bộ reverse do NSA viết rồi mở mã nguồn năm 2019, và câu hỏi đầu tiên ai cũng hỏi là "đồ miễn phí thì làm được gì". Trả lời ngắn: nó có một decompiler biến assembly thành pseudocode kiểu C, chạy được trên gần như mọi kiến trúc, và bạn không mất một xu. Với người mới, đây là lý do rất chính đáng để bắt đầu bằng Ghidra thay vì chờ tiền mua IDA Pro.

Bài này đưa bạn đi hết một vòng từ lúc mở Ghidra tới lúc đọc được pseudocode của một hàm. Phím tắt đầy đủ nằm ở [cheatsheet](/posts/tr-tai-nguyen-cheatsheet/), ở đây tôi chỉ nhắc cái nào dùng tới.

## Project, không phải mở thẳng file

Khác IDA (kéo file vào là chạy), Ghidra bắt bạn tạo một project trước. Nghe phiền nhưng có lý do: một project gom nhiều file liên quan vào một chỗ, giữ lại toàn bộ ghi chú và phân tích của bạn, và cho phép so sánh nhiều binary với nhau sau này.

Các bước:
1. Mở Ghidra, chọn File > New Project, chọn Non-Shared Project (bạn làm một mình), đặt tên và nơi lưu.
2. Kéo file cần phân tích vào cửa sổ project, hoặc File > Import File. Ghidra tự nhận định dạng (PE, ELF, Mach-O) và kiến trúc. Thường cứ để mặc định rồi OK.
3. Double-click file vừa import để mở CodeBrowser, cửa sổ làm việc chính.
4. Ghidra hỏi "Analyze now?", chọn Yes. Bảng analyzer hiện ra, cứ để mặc định rồi Analyze.

Auto-analysis là bước Ghidra quét toàn file: tìm hàm, dựng cross-reference, nhận diện chuỗi, đoán kiểu dữ liệu. File nhỏ xong trong vài giây, file to thì chờ chút. Thanh tiến trình chạy xong là bắt đầu được.

## CodeBrowser, bốn cửa sổ bạn sống trong đó

Giao diện CodeBrowser nhìn rối lúc đầu, nhưng thực ra chỉ có bốn chỗ bạn dùng suốt:

- **Listing** (giữa màn hình): disassembly, tức assembly kèm địa chỉ, comment, nhãn. Đây là bản gốc chính xác nhất.
- **Decompiler** (thường bên phải): pseudocode kiểu C của hàm đang chọn. Mở bằng cách click vào một hàm, hoặc nhấn Ctrl+E. Đây là chỗ người mới đọc nhiều nhất vì dễ nuốt hơn assembly.
- **Symbol Tree** (bên trái): danh sách hàm (Functions), import, export, nhãn. Chỗ để nhảy nhanh tới một hàm theo tên.
- **Data Type Manager** (dưới bên trái): kho kiểu dữ liệu. Khi bạn muốn áp một struct hay một kiểu Windows vào biến, bạn lấy từ đây.

Listing và Decompiler luôn đồng bộ: click một dòng bên này, bên kia nhảy theo. Thói quen tốt là đọc Decompiler để nắm ý, rồi liếc Listing khi cần độ chính xác từng lệnh.

## Đi từ chuỗi, kỹ thuật vào việc nhanh nhất

Giống mọi công cụ RE, cách nhanh nhất để tìm "chỗ thú vị" trong Ghidra là đi ngược từ một chuỗi. Mở Window > Defined Strings. Một bảng mọi chuỗi trong file hiện ra. Thấy chuỗi đáng ngờ kiểu "Wrong password" hay "Access granted"? Double-click vào nó để nhảy tới nơi nó nằm trong Listing, rồi xem cái gì tham chiếu tới nó.

Để xem tham chiếu, đặt con trỏ lên chuỗi (hoặc hàm, biến) rồi nhấn Ctrl+Shift+F (Find References To). Ghidra liệt kê mọi nơi dùng tới nó. Nơi tham chiếu chuỗi "Wrong password" gần như chắc chắn là hàm kiểm tra mật khẩu. Double-click là bạn đã đứng ngay trong hàm cần tìm, bỏ qua được cả nghìn dòng khởi tạo runtime.

## Rename và retype, biến rác thành đọc được

Sau auto-analysis, hàm chưa có tên sẽ tên kiểu `FUN_00401000`, biến là `local_8`, `uVar1`. Khó đọc. Khác biệt giữa người làm chậm mà chắc với người ngập trong `FUN_xxx` nằm ở chỗ: hiểu cái gì thì đặt tên ngay cái đó.

- **Rename**: đặt con trỏ lên hàm hoặc biến, nhấn **L**, gõ tên mới. Ví dụ `FUN_00401000` hoá ra băm chuỗi thì đổi thành `hash_string`.
- **Retype**: nhấn **Ctrl+L** để đổi kiểu một biến. Biến Ghidra đoán là `undefined4` mà bạn biết là `int` hay một con trỏ struct thì sửa lại, decompiler sẽ hiển thị đẹp hơn hẳn.
- **Comment**: nhấn **;** để ghi chú ngay tại dòng.

Mỗi cái tên bạn đặt làm hàm kế tiếp dễ đọc hơn, vì Ghidra lan tên đó ra mọi nơi gọi tới. Đây không phải việc làm cho đẹp, nó là cách bạn giữ đầu óc tỉnh táo khi hàm chồng hàm.

## Navigation, đừng lạc đường

- Double-click một tên hàm hay địa chỉ để nhảy tới nó.
- Nút mũi tên back/forward trên thanh công cụ (hoặc Alt+Mũi tên trái/phải) để quay lại chỗ vừa rời, y như trình duyệt. Dùng liên tục khi bạn lần theo một chuỗi call.
- Phím **G** để nhảy thẳng tới một địa chỉ cụ thể.

## Ghidra so với IDA, và vài chỗ hay vấp

Nếu bạn đến từ IDA, phần lớn khái niệm giống nhau nhưng tên gọi và phím tắt khác, đây là chỗ làm người ta bực lúc đầu:

| Việc | IDA | Ghidra |
|---|---|---|
| Rename | N | L |
| Decompile | F5 | Ctrl+E (hoặc click hàm) |
| Xref tới | X | Ctrl+Shift+F |
| Danh sách chuỗi | Shift+F12 | Window > Defined Strings |
| Nhảy địa chỉ | G | G |

Vài điểm người quen IDA hay vấp:
- Ghidra **không** tự mở decompiler bằng F5. Decompiler là một panel luôn hiện, bạn chỉ cần click vào hàm.
- Undo/Redo trong Ghidra là Ctrl+Z/Ctrl+Y và nó nhớ cả thao tác phân tích, mạnh hơn IDA ở điểm này.
- Ghidra lưu tự động vào project, nhưng nhớ File > Save (Ctrl+S) trước khi đóng cho chắc.

Về sức mạnh: decompiler của IDA (Hex-Rays) thường ra code mượt hơn chút, nhất là với code tối ưu nặng, nhưng Ghidra miễn phí mà chất lượng rất gần, và phần scripting (Java hoặc Python) để tự động hoá thì cực mạnh, nói ở [Bài 18.1](https://github.com/Haind03/Technique-Reverse/tree/main/phan-18-nang-cao). Với người học, Ghidra không thua thiệt gì đáng kể.

## Lab tự làm

Bài tập thực hành và writeup nằm ở [labs/2.3/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/2.3). Bạn sẽ import cùng một crackme nhỏ vào Ghidra, chạy auto-analysis, đi từ Defined Strings tới hàm kiểm tra, rename và retype để pseudocode đọc được, rồi so sánh cảm giác với IDA ở [Bài 2.2](/posts/tr-2-2-ida-co-ban/). Làm cả hai công cụ trên cùng một binary là cách nhanh nhất để thấy chúng giống và khác chỗ nào.

## Checklist ghi nhớ
- Ghidra bắt tạo project trước, rồi import, rồi Analyze (auto-analysis) mới dùng được.
- Bốn cửa sổ chính: Listing (asm), Decompiler (pseudocode), Symbol Tree (hàm), Data Type Manager (kiểu).
- Vào việc nhanh: Window > Defined Strings, double-click chuỗi, Ctrl+Shift+F để xref tới hàm dùng nó.
- Rename bằng L, retype bằng Ctrl+L, comment bằng dấu chấm phẩy. Hiểu gì đặt tên nấy ngay.
- So với IDA: khái niệm giống, phím khác. Decompiler luôn hiện, không cần F5.
