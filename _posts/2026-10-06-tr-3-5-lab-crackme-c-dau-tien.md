---
title: "Bài 3.5: Lab, giải crackme C đầu tiên từ đầu đến cuối"
date: 2026-10-06 08:29:00 +0700
categories: ["Technique Reverse", "Phần 3 · C: ngôn ngữ gốc của mọi thứ"]
tags: [reverse-engineering, c]
render_with_liquid: false
---
Tới giờ bạn đã có đủ mảnh ghép rời: đọc assembly (1.3), hiểu stack và tham số (1.4), nhận ra if/loop (1.5), dùng IDA/Ghidra (2.2, 2.3), dùng x64dbg (2.5). Bài này ghép tất cả lại trên một mục tiêu thật: một crackme nhỏ bằng C. Không có lý thuyết mới, chỉ có việc ngồi làm cho ra.

Crackme nằm ở `labs/3.5/`. Tôi khuyên bạn dừng đọc ở đây, sang đó tự giải trước, rồi mới quay lại so cách làm. Phần dưới tôi dẫn cả quy trình, nên nó là spoiler.

## Luật chơi

Crackme hỏi một password. Nhập đúng thì in `Correct!`, sai thì `Sai mat khau.`. Nhiệm vụ của bạn là tìm ra password đúng. Điểm xoắn: password không nằm thẳng trong file, nên chiến thuật "chạy strings rồi copy" sẽ thất bại. Bạn phải hiểu nó kiểm tra thế nào.

## Bước 1: triage

Thói quen đầu tiên, luôn luôn, là biết mình đang cầm cái gì. Kéo file vào Detect It Easy hoặc chạy `diec`:

```
$ diec crackme
PE64 / ELF64, compiler GCC (hoặc MSVC), not packed
```

Không packed, binary C bình thường. Tốt, đi thẳng vào đọc.

Chạy `strings` để nhặt manh mối:

```
$ strings crackme
Nhap password: 
Correct! Chuc mung.
Sai mat khau.
check_password
...
```

Hai điều rút ra. Một, có hàm tên `check_password`, quá tiện, đó là đích đến. Hai, không thấy password nào dạng plaintext. Nghĩa là nó được so sánh gián tiếp, phải đọc logic.

## Bước 2: static, đi từ chuỗi tới hàm check

Mở file trong Ghidra (hoặc IDA). Sau auto-analysis, dùng cửa sổ Defined Strings (Ghidra) hoặc Strings (Shift+F12 trong IDA), tìm chuỗi `Sai mat khau.`. Nhấn vào nó rồi xem xref (ai dùng chuỗi này). Xref dẫn tới `main`, nơi in kết quả dựa trên giá trị trả về của `check_password`. Nhảy vào `check_password` và F5 để decompile.

Pseudocode sẽ gần như thế này:

```c
int check_password(char *input) {
    if (strlen(input) != 10)
        return 0;
    int checksum = 0;
    for (int i = 0; i < 10; i++) {
        unsigned char t = input[i] ^ 0x5A;
        if (t != expected[i])
            return 0;
        checksum += input[i];
    }
    if (checksum != 0x39C)
        return 0;
    return 1;
}
```

Đọc từng tầng:

- **Tầng 0, độ dài.** Password phải đúng 10 ký tự. `strlen(input) != 10` trả 0 ngay. Đây là thứ bạn đã thấy y hệt ở bài 1.3.
- **Tầng 1, biến đổi từng ký tự.** Mỗi ký tự nhập vào bị XOR với `0x5A`, rồi so với một phần tử trong mảng `expected`. Đây là chỗ password "biến mất" khỏi strings: cái nằm trong file là mảng `expected` đã bị XOR, không phải password gốc.
- **Tầng 2, checksum.** Tổng mã ASCII của password phải bằng `0x39C`. Lớp này để chống việc mò bừa, nhưng với ta nó là quà: nếu giải tầng 1 đúng thì tầng 2 tự thoả.

Chìa khoá nằm ở phép XOR. Nhớ tính chất từ bài 1.1: `a ^ k ^ k == a`. Nếu `input[i] ^ 0x5A == expected[i]`, thì `input[i] == expected[i] ^ 0x5A`. Chỉ cần lấy mảng `expected` XOR ngược lại `0x5A` là ra password.

## Bước 3: lấy mảng expected ra

Trong Ghidra, double-click vào `expected` để tới địa chỉ của nó, đọc 10 byte. Giá trị (trong lab này) là:

```
08 3F 2C 3F 28 29 3F 05 6A 6B
```

Giờ XOR từng byte với `0x5A`. Làm tay thì lâu, để Python làm:

```python
exp = [0x08,0x3F,0x2C,0x3F,0x28,0x29,0x3F,0x05,0x6A,0x6B]
print(''.join(chr(b ^ 0x5A) for b in exp))
# Reverse_01
```

Password là `Reverse_01`. Nhập thử vào crackme, nó in `Correct!`. Bạn vừa giải một crackme hoàn toàn bằng đọc tĩnh, không cần chạy lần nào.

## Bước 4: con đường dynamic, thấy tận mắt

Giả sử bạn không muốn tính tay, hoặc logic rối hơn và bạn muốn nhìn giá trị thật. Đây là lúc x64dbg vào cuộc.

Mở crackme trong x64dbg, đặt breakpoint tại `check_password` (hoặc tại lệnh `cmp` so sánh trong vòng lặp). Nhập một password bừa đủ 10 ký tự, ví dụ `AAAAAAAAAA`. Khi dừng ở vòng lặp, bạn thấy:

- Thanh ghi chứa `t = input[i] ^ 0x5A` (giá trị bạn nhập sau khi XOR).
- Toán hạng kia của `cmp` là `expected[i]`, lộ ngay trong register hoặc trong Dump.

Nhìn hai bên của `cmp` tại từng vòng, bạn đọc được mảng `expected` mà không cần tìm nó trong static. Từ đó vẫn XOR ngược như trên. Dynamic ở đây không thay thế static, nó xác nhận và cho bạn mảng hằng số tận tay.

Có một mẹo còn nhanh hơn cho crackme kiểu này: đặt breakpoint tại tầng checksum hoặc ngay trước `return 1`, rồi khi đã biết độ dài và pattern, đôi khi bạn chỉ cần patch nhánh `jne` thành `je` để qua check. Nhưng patch chỉ làm nó chấp nhận mọi input, không cho bạn password thật. Với crackme, mục tiêu thường là tìm password, nên XOR ngược mới là lời giải đẹp. Chuyện patch để dành cho Phần 17.

## Vì sao làm theo thứ tự này

Để ý nhịp: triage trước để khỏi phí công đọc file packed, static để hiểu logic và khoanh vùng, dynamic để xác nhận khi cần. Đây đúng là vòng lặp ở bài 0.4, lần này áp vào mục tiêu thật. Người mới hay nhảy thẳng vào debug và step từng lệnh từ đầu chương trình, lạc trong CRT startup cả buổi. Người quen việc đọc tĩnh tới chỗ đáng ngờ rồi mới đặt một breakpoint đúng chỗ.

## Checklist ghi nhớ
- Luôn triage rồi strings trước. Tên hàm như `check_password` là quà, chuỗi `Correct` dẫn thẳng tới logic.
- Password không có trong strings nghĩa là nó bị biến đổi, phải đọc cách kiểm tra.
- XOR là hai chiều: `input = expected ^ key`. Gặp vòng lặp XOR từng byte rồi so mảng hằng là nghĩ tới XOR ngược.
- Đọc tĩnh ra lời giải là đẹp nhất. Dynamic để xác nhận hoặc khi logic phức tạp.
- Patch jump làm nó "luôn đúng" nhưng không cho bạn password thật.
