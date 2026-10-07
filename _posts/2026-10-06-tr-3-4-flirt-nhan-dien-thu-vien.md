---
title: "Bài 3.4: FLIRT và nhận diện hàm thư viện, đừng đọc code không phải của tác giả"
date: 2026-10-06 08:28:00 +0700
categories: ["Technique Reverse", "Phần 3 · C: ngôn ngữ gốc của mọi thứ"]
tags: [reverse-engineering, c]
render_with_liquid: false
---
Mở một binary C nhỏ xíu trong IDA mà thấy bảng Functions có hơn 1500 hàm, bạn sẽ hoảng. Nhưng bình tĩnh lại: tác giả chỉ viết dăm hàm, 1490 cái còn lại là `printf`, `malloc`, `strlen` và cả bộ ruột của libc bị nhét thẳng vào file. Nhiệm vụ của bài này là tách nhanh hai nhóm đó, để bạn chỉ đọc phần người ta thật sự viết.

## Vì sao binary phình to: static linking

Khi bạn `gcc hello.c -o hello`, trình linker có hai cách ghép code thư viện vào:

- **Dynamic linking** (mặc định): binary chỉ giữ một danh sách "tôi cần `printf` từ `libc.so`", còn code `printf` nằm trong thư viện hệ thống, nạp lúc chạy. File gọn, bảng hàm sạch.
- **Static linking** (`gcc -static`): toàn bộ code libc được copy thẳng vào file. Binary tự chạy không cần thư viện ngoài, nhưng phình lên hàng trăm KB tới vài MB, và bảng Functions ngập hàng nghìn hàm thư viện.

Malware và các binary CTF rất hay static link, một phần để chạy ở mọi máy, một phần để làm khó người phân tích bằng cách chôn code thật giữa biển code thư viện. Phân biệt được đâu là code libc là kỹ năng tiết kiệm thời gian nhất ở giai đoạn này.

## FLIRT, khi IDA tự gọi tên hàm quen

![FLIRT signature: trước và sau khi áp](/assets/img/technique-reverse/assets/phan-03/flirt.svg)

FLIRT (Fast Library Identification and Recognition Technology) là cơ chế của IDA để nhận ra một hàm thư viện đã biết và tự đặt lại tên cho nó. Ý tưởng đơn giản: mỗi hàm libc đã biên dịch có một "vân tay" byte đặc trưng (pattern các byte đầu hàm, bỏ qua phần địa chỉ sẽ thay đổi khi relocate). IDA giữ sẵn một kho signature cho nhiều phiên bản compiler và libc. Khi phân tích, nó so từng hàm với kho, khớp cái nào thì đổi `sub_401A20` thành `strlen` và tô màu khác.

Kết quả: thay vì 1500 hàm vô danh, bạn thấy đa số đã mang tên thật, còn lại một nhúm nhỏ `sub_xxxx` chính là code tác giả. Bạn khoanh vùng xong trong vài giây.

### Áp signature trong IDA

IDA tự nạp một số signature khi mở file, nhưng không phải lúc nào cũng đúng bộ. Cách áp thủ công:

1. Mở menu `View > Open subviews > Signatures` (hoặc `Shift+F5`).
2. Nhấn `Ins` (Insert) để mở danh sách signature có sẵn.
3. Chọn bộ khớp với compiler của file. Ví dụ libc GCC trên Linux thường là các bộ tên `libc_*`, còn MSVC là `vc32*` / `vc64*` / `vcseh`.
4. IDA quét lại và đặt tên các hàm khớp. Cột "Applied" cho biết khớp được bao nhiêu.

Mẹo thực tế: nếu quét xong mà vẫn nhiều `sub_`, thử bộ signature của phiên bản compiler khác. Khớp sai bộ thì không có hàm nào được đặt tên, không hại gì, cứ thử bộ khác.

### Tự tạo signature với FLAIR

Khi bạn gặp một thư viện tĩnh lạ (ví dụ một SDK game, một thư viện crypto đóng gói `.lib` / `.a`), IDA không có sẵn signature. Bộ công cụ FLAIR của Hex-Rays cho phép tự sinh:

```text
pelf / pcf / plb / pmsvc   -> tạo file pattern (.pat) từ .a / .lib / .obj
sigmake                    -> biến .pat thành .sig dùng được trong IDA
```

Quy trình gọn: chạy công cụ parser (`plb` cho `.lib`, `pelf` cho `.a`) để xuất `.pat`, rồi `sigmake tên.pat tên.sig`. Nếu có xung đột (hai hàm cùng vân tay), sigmake xuất file `.exc` để bạn quyết định giữ cái nào. Chép `.sig` vào thư mục `sig/` của IDA là áp được. Có signature của chính thư viện mà mục tiêu dùng, bạn tiết kiệm hàng giờ.

## Bên Ghidra: FunctionID

Ghidra có cơ chế tương đương tên là FunctionID. Nó cũng dựa trên hash đặc trưng của hàm để nhận diện thư viện đã biết. Ghidra kèm sẵn vài bộ FID cho các runtime phổ biến (Visual Studio, một số libc). Bạn bật qua `Tools > Function ID`, và có thể tự tạo FID database từ binary thư viện đã biết. Độ phủ của FID mặc định không rộng bằng FLIRT, nên trên Ghidra bạn sẽ dựa vào nhận diện bằng mắt nhiều hơn một chút.

## Khi không có signature: nhận ra hàm chuẩn bằng mắt

Nhiều khi bạn không có bộ signature khớp. Lúc đó vài hàm libc hay gặp vẫn có hình dáng rất dễ nhận:

`strlen` thủ công là một vòng quét tới byte 0:

```asm
    xor  eax, eax           ; i = 0
loop:
    cmp  byte [rdi+rax], 0  ; s[i] == 0 ?
    je   done
    inc  rax                ; i++
    jmp  loop
done:
    ret                     ; trả về độ dài trong rax
```

Dịch ra C:

```c
size_t strlen(const char *s) {
    size_t i = 0;
    while (s[i] != 0) i++;
    return i;
}
```

Thấy một vòng lặp quét từng byte cho tới khi gặp 0 rồi trả về số đếm, gần như chắc đó là `strlen` hoặc họ hàng của nó.

`strcmp` là so sánh song song hai con trỏ, dừng khi khác nhau hoặc gặp 0:

```asm
loop:
    mov  al, [rdi]
    cmp  al, [rsi]
    jne  diff
    test al, al          ; đã tới cuối chuỗi?
    je   equal
    inc  rdi
    inc  rsi
    jmp  loop
```

Hai con trỏ chạy song song, so từng byte, có kiểm tra byte 0: đó là chữ ký hình học của `strcmp`/`memcmp`. `memcpy` thì là vòng chép theo khối lớn (thường dùng thanh ghi rộng, movups/rep movsb). Quen mặt vài hàm này là đủ để không lạc.

Một manh mối miễn phí khác: nhìn chuỗi định dạng. Một hàm nhận một chuỗi có `%d`, `%s` rồi gọi lòng vòng gần như chắc liên quan tới họ `printf`.

## Nhịp làm việc rút ra

Mở một binary C, trước khi đọc bất cứ hàm nào:

1. Xem file static hay dynamic (DIE hoặc kích thước file, số lượng import). Static thì chuẩn bị tinh thần nhiều hàm.
2. Áp FLIRT (IDA) hoặc FID (Ghidra) ngay. Để tool đặt tên giúp phần libc.
3. Những hàm còn lại là `sub_` sau khi đã áp signature chính là nơi đáng đọc. Bắt đầu từ đó, kết hợp đi từ chuỗi và từ main (Bài 3.1).

## Lab tự làm

Xem [labs/3.4/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/3.4). Bạn sẽ build cùng một chương trình ở hai dạng static và dynamic, mở bản static trong IDA để thấy rừng hàm, rồi áp FLIRT libc và đếm xem bao nhiêu hàm được đặt tên, so với bản dynamic gọn gàng.

## Checklist ghi nhớ
- Static linking nhét code libc vào file, làm bảng hàm phình lên hàng nghìn. Đa số không phải code tác giả.
- FLIRT (IDA) tự nhận diện và đặt tên hàm thư viện theo vân tay byte. Áp qua `Shift+F5`, chọn bộ khớp compiler.
- Khớp sai bộ thì không đặt được tên nào, vô hại, cứ thử bộ khác.
- FLAIR (`pelf`/`plb` + `sigmake`) để tự tạo signature cho thư viện lạ.
- Ghidra dùng FunctionID, độ phủ hẹp hơn, nên luyện nhận dạng bằng mắt.
- Nhớ hình dáng `strlen` (quét tới byte 0), `strcmp` (hai con trỏ song song), `memcpy` (chép khối), họ `printf` (có chuỗi định dạng).
