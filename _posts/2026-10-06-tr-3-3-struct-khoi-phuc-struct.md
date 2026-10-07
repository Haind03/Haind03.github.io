---
title: "Bài 3.3: Struct trong assembly và nghệ thuật khôi phục nó"
date: 2026-10-06 08:27:00 +0700
categories: ["Technique Reverse", "Phần 3 · C: ngôn ngữ gốc của mọi thứ"]
tags: [reverse-engineering, c]
render_with_liquid: false
---
Có một khoảnh khắc trong đời reverser mà bạn sẽ nhớ mãi: lần đầu bạn gán một struct vào con trỏ trong IDA, và cả một hàm pseudocode đang rối như tơ vò bỗng biến thành code đọc được như sách. `*(a1 + 8)` trở thành `player->score`, `*(a1 + 16)` thành `player->name`. Khôi phục struct là một trong những kỹ năng cho lợi tức cao nhất khi reverse code C/C++. Bài này dạy bạn nhận ra struct và dựng lại nó.

## Struct trông như thế nào trong assembly

CPU không biết struct là gì. Với nó, một struct chỉ là một khối byte liền nhau, và truy cập một field là lấy địa chỉ gốc cộng thêm một offset cố định. Đó chính là dấu vân tay bạn cần tìm.

Giả sử có struct C này:

```c
struct Player {
    int   id;        // offset 0, 4 byte
    int   score;     // offset 4, 4 byte
    char  name[16];  // offset 8, 16 byte
    int   level;     // offset 24, 4 byte
};
```

Một hàm nhận con trỏ `Player*` và đọc các field sẽ ra assembly kiểu này:

```asm
; rcx = con trỏ Player (tham số đầu trên Windows x64)
mov  eax, [rcx]          ; đọc id      -> offset 0
mov  edx, [rcx+4]        ; đọc score   -> offset 4
lea  r8,  [rcx+8]        ; lấy địa chỉ name -> offset 8
mov  r9d, [rcx+18h]      ; đọc level   -> offset 24 (0x18)
```

Để ý cái pattern: cùng một thanh ghi nền (`rcx`) được cộng với **các hằng số cố định** `+0`, `+4`, `+8`, `+0x18`. Đó là chữ ký của struct. Mỗi offset là một field.

## Phân biệt struct với mảng

Người mới hay nhầm hai thứ này, nhưng chúng khác nhau rõ ở cách tính địa chỉ.

- **Mảng**: index nhân với kích thước phần tử, offset là biến. Bạn thấy `[base + index*scale]`, trong đó `index` là một thanh ghi thay đổi trong vòng lặp, `scale` là 1/2/4/8.
  ```asm
  mov eax, [rsi+rcx*4]   ; arr[rcx], mảng int
  ```
- **Struct**: offset là hằng số, mỗi field một kiểu có thể khác nhau. Bạn thấy `[base + hằng_số]`.
  ```asm
  mov eax, [rsi+8]       ; some_struct->field_at_8
  ```

Quy tắc nhanh: **thấy nhân với index (`*4`, `*8`) thì nghĩ mảng; thấy cộng hằng số cố định và các field kiểu khác nhau thì nghĩ struct.** Mảng của struct thì kết hợp cả hai: `[base + index*sizeof_struct + field_offset]`, ví dụ `[rsi + rcx*32 + 4]` là `players[rcx].score` khi struct rộng 32 byte.

## Cái bẫy padding và alignment

![Bố cục struct trong bộ nhớ có padding](/assets/img/technique-reverse/assets/phan-03/struct-layout.svg)

Đừng mong các field nằm sát nhau. Compiler chèn byte đệm (padding) để mỗi field nằm ở địa chỉ chia hết cho kích thước của nó (alignment). Ví dụ:

```c
struct Messy {
    char  a;    // offset 0
    int   b;    // offset 4  (KHÔNG phải 1, vì int cần căn 4)
    char  c;    // offset 8
    // 7 byte padding ở đây
    double d;   // offset 16 (double cần căn 8)
};  // sizeof = 24, không phải 14
```

Nên khi bạn thấy offset nhảy từ `+0` sang `+4` dù field đầu chỉ 1 byte, đừng hoảng: đó là padding. Khi dựng lại struct trong tool, bạn khai báo đúng kiểu từng field thì công cụ tự tính padding giúp. Nếu offset vẫn lệch, thường là bạn đoán sai kiểu của một field phía trước.

## Khôi phục struct trong IDA

Đây là quy trình thực tế, lặp đi lặp lại:

1. Mở decompiler (F5). Bạn thấy đống `*(a1 + N)` xấu xí.
2. Mở Local Types (Shift+F1) hoặc Structures (Shift+F9), tạo một struct mới. Có thể gõ thẳng khai báo C:
   ```c
   struct Player { int id; int score; char name[16]; int level; };
   ```
3. Quay lại pseudocode, click phải vào biến con trỏ (`a1`), chọn "Convert to struct pointer" hoặc đặt kiểu bằng phím `Y` rồi gõ `Player *`.
4. IDA lập tức đổi mọi `*(a1 + 8)` thành `a1->name`. Đọc lại, sửa tên field cho đúng ngữ nghĩa khi hiểu hơn.

Mẹo: nếu chưa biết struct có gì, dùng tính năng của IDA cho phép bạn vừa đọc vừa thêm field. Mỗi lần thấy một offset mới được truy cập, thêm field tại offset đó. IDA cũng có "Create new struct from this access" trên một số phiên bản để tự gom các offset đã thấy.

## Khôi phục struct trong Ghidra

Tương tự nhưng khác thao tác:

1. Mở Data Type Manager (cửa sổ dưới bên phải). Click phải vào archive của chương trình, New > Structure.
2. Thêm từng field với kiểu và tên, hoặc dùng "Auto Create Structure": trong Decompiler, click phải vào biến con trỏ, chọn Auto Fill in Structure / Auto Create Structure, Ghidra dò các truy cập và dựng struct nháp cho bạn.
3. Gán kiểu con trỏ cho biến (click phải > Retype Variable, hoặc Ctrl+L), Ghidra cập nhật pseudocode.
4. Tinh chỉnh tên field trong Data Type Manager, mọi nơi dùng struct cập nhật theo.

Ghidra mạnh ở chỗ Auto Create Structure khá thông minh với code tối ưu hóa, còn IDA cho trải nghiệm gõ khai báo C nhanh hơn. Dùng cái nào cũng được, quan trọng là thói quen: thấy con trỏ bị truy cập theo nhiều offset cố định thì dựng struct ngay.

## Trước và sau, vì sao đáng công

Trước khi gán struct, pseudocode:

```c
if ( *(a1 + 4) > 100 && *(_BYTE *)(a1 + 8) )
    *(a1 + 24) = *(a1 + 24) + 1;
```

Sau khi gán `Player *`:

```c
if ( player->score > 100 && player->name[0] )
    player->level++;
```

Cùng một code, nhưng cái sau bạn đọc hiểu trong hai giây. Nhân khác biệt đó với hàng trăm hàm trong một chương trình thật, bạn hiểu vì sao dân pro bỏ công dựng struct ngay từ đầu.

## Lab tự làm

Mã nguồn và hướng dẫn ở [labs/3.3/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/3.3). Tóm tắt: build một chương trình C dùng struct nhiều kiểu field, mở trong IDA hoặc Ghidra, đọc pseudocode thô, rồi dựng lại struct và so sánh trước/sau. File [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/3.3/solution.md) có layout struct và offset từng field để bạn đối chiếu, nhưng hãy tự dựng trước khi mở.

## Checklist ghi nhớ
- Struct trong assembly = địa chỉ gốc + offset hằng số. Mỗi offset là một field.
- Mảng dùng `[base + index*scale]` (index thay đổi); struct dùng `[base + hằng số]` (các kiểu khác nhau).
- Padding/alignment làm offset không liên tục, đó là bình thường, không phải lỗi.
- IDA: Local Types/Structures, gõ khai báo C, gán kiểu bằng `Y`.
- Ghidra: Data Type Manager, Auto Create Structure, retype bằng Ctrl+L.
- Dựng struct là một trong những việc cho lợi tức cao nhất khi đọc code C/C++.
