---
title: "Bài 3.2: Biến, con trỏ, mảng, chuỗi dưới dạng assembly"
date: 2026-10-06 08:26:00 +0700
categories: ["Technique Reverse", "Phần 3 · C: ngôn ngữ gốc của mọi thứ"]
tags: [reverse-engineering, c]
render_with_liquid: false
---
Code C xoay quanh bốn thứ: biến, con trỏ, mảng, chuỗi. Compiler biến tất cả thành các kiểu truy cập bộ nhớ na ná nhau, nên nhìn thoáng qua dễ lẫn. Nhưng mỗi loại có một dấu vân tay riêng trong assembly. Học nhận ra chúng là bạn đọc được phần lớn code C mà không cần source.

Mọi đoạn asm dưới đây là output thật của `gcc -O0` trên file [labs/3.2/src/datatypes.c](https://github.com/Haind03/Technique-Reverse/blob/main/labs/3.2/src/datatypes.c), cú pháp Intel, System V (Linux). Trên Windows thứ tự thanh ghi tham số khác (rcx, rdx...) nhưng ý tưởng y hệt.

## Biến cục bộ và biến toàn cục nằm ở hai nơi khác nhau

Đây là phân biệt quan trọng nhất và dễ nhất. Chỗ biến nằm cho bạn biết nó là loại gì.

**Biến cục bộ** sống trên stack, luôn truy cập qua `rbp` (hoặc `rsp`) với một offset:

```asm
mov    DWORD PTR [rbp-0x4], 0x0     ; một biến int cục bộ = 0
```

Thấy `[rbp-cái gì đó]` là gần như chắc chắn biến cục bộ. IDA đặt tên chúng `var_4`, `var_8`; Ghidra gọi `local_...`.

**Biến toàn cục** sống ở địa chỉ cố định trong section `.data` (có giá trị ban đầu) hoặc `.bss` (khởi tạo 0). Trên x64 chúng được truy cập qua địa chỉ tương đối với `rip` (RIP-relative):

```asm
mov    edx, DWORD PTR [rip+0x2db1]   ; # 4010 <g_initialized>   đọc biến toàn cục
mov    DWORD PTR [rip+0x2dbe], eax   ; # 4028 <g_zero>          ghi biến toàn cục
```

Để ý comment `<g_initialized>` và `<g_zero>` mà objdump tự thêm: đó là tên symbol vì file này chưa strip. Trong binary thật đã strip bạn chỉ thấy `[rip+offset]` trỏ tới một địa chỉ trong `.data`, và đó là tín hiệu "biến toàn cục". IDA hiển thị thành `dword_xxxx`.

Tóm lại một câu: `[rbp-x]` là cục bộ, `[rip+x]` (hay một địa chỉ tuyệt đối trong .data/.bss) là toàn cục.

## Con trỏ: giá trị là một địa chỉ

![Con trỏ và mảng trong bộ nhớ](/assets/img/technique-reverse/assets/phan-03/con-tro-mang.svg)

Con trỏ không có gì huyền bí: nó là một biến mà giá trị của nó là một địa chỉ. Điều làm người mới rối là bước dereference, tức lấy giá trị tại địa chỉ đó. Trong assembly, dereference luôn là một cặp hai bước: nạp con trỏ vào thanh ghi, rồi truy cập qua ngoặc vuông của thanh ghi đó.

Nhìn hàm `my_strlen`:

```asm
mov    rax, QWORD PTR [rbp-0x18]   ; rax = con trỏ s (đọc biến con trỏ)
movzx  eax, BYTE PTR [rax]         ; eax = *s   (dereference: đọc byte tại địa chỉ rax)
test   al, al                      ; so sánh byte đó với 0
jne    ...                         ; chưa phải '\0' thì lặp tiếp
```

Hai dòng đầu là trọng tâm: `[rbp-0x18]` là chính biến con trỏ `s` (con trỏ cũng là một biến cục bộ 8 byte), còn `[rax]` là thứ `s` trỏ tới. Phân biệt được "đọc con trỏ" với "đọc cái con trỏ trỏ tới" là qua ải con trỏ.

Con trỏ 8 byte nên dùng `QWORD PTR`. Thấy `QWORD PTR` khi nạp vào rồi ngay sau đó truy cập `[thanh ghi]` là mùi con trỏ rất rõ.

### Con trỏ tới con trỏ

Nghe đáng sợ nhưng chỉ là thêm một tầng. Hàm `retarget(char **pp, char *newtarget)` ghi `*pp = newtarget`:

```asm
mov    rax, QWORD PTR [rbp-0x8]    ; rax = pp (con trỏ ngoài)
mov    rdx, QWORD PTR [rbp-0x10]   ; rdx = newtarget
mov    QWORD PTR [rax], rdx        ; *pp = newtarget  (ghi vào ô mà pp trỏ tới)
```

Dòng cuối là mấu chốt: ghi `rdx` vào `[rax]`, tức ghi vào ô nhớ mà `pp` đang trỏ tới. Mỗi tầng con trỏ thêm một lần "nạp rồi truy cập qua ngoặc". Đếm số tầng ngoặc là đếm số dấu sao.

## Mảng: địa chỉ tính theo công thức base + index*scale

Mảng là chỗ `lea` toả sáng. Truy cập `arr[i]` thật ra là `*(arr + i)`, và vì mỗi phần tử rộng nhiều byte, index phải nhân với kích thước phần tử (scale). Nhìn vòng lặp cộng mảng int trong `sum_array`:

```asm
mov    eax, DWORD PTR [rbp-0x4]    ; eax = i
cdqe                               ; mở rộng i ra 64-bit
lea    rdx, [rax*4+0x0]            ; rdx = i*4   (4 = sizeof(int), đây là scale)
mov    rax, QWORD PTR [rbp-0x18]   ; rax = arr (địa chỉ gốc)
add    rax, rdx                    ; rax = arr + i*4
mov    eax, DWORD PTR [rax]        ; eax = arr[i]
add    DWORD PTR [rbp-0x8], eax    ; total += arr[i]
```

Dấu vân tay của mảng là `index * kích_thước_phần_tử` rồi cộng vào base. Thấy `*4` là mảng int (hoặc con trỏ 32-bit), `*8` là mảng long/con trỏ 64-bit, `*2` là mảng short. Nhiều khi compiler gộp tất cả vào một lệnh duy nhất kiểu `mov eax, [rax+rcx*4]`, nhìn phát ra ngay là "đang đọc phần tử mảng".

IDA/Ghidra thường nhận ra và hiển thị `arr[i]` cho bạn, nhưng khi nó đoán sai kiểu, chính con số scale `*4`, `*8` giúp bạn tự sửa lại.

## Chuỗi C: dãy byte kết thúc bằng 0

Chuỗi trong C không có trường độ dài. Nó chỉ là một mảng `char` kết thúc bằng byte `0x00` (null terminator). Hệ quả: mọi thao tác chuỗi đều là một vòng lặp chạy tới khi gặp byte 0. Đó là pattern bạn phải thuộc.

Nhìn lại `my_strlen` ở trên: vòng lặp đọc từng byte (`movzx eax, BYTE PTR [rax]`), `test al, al` để hỏi "byte này có phải 0 chưa", chưa thì tăng con trỏ (`add QWORD PTR [rbp-0x18], 1`) và đếm thêm. Cặp "đọc byte rồi test al, al" lặp lại là chữ ký của xử lý chuỗi.

Vài biến thể bạn sẽ gặp:
- So sánh hai chuỗi: hai con trỏ cùng tiến, so từng cặp byte, lệch là thoát. Đây chính là lõi của `strcmp`, và là chỗ password hay bị so sánh.
- Sao chép chuỗi (`strcpy`): đọc byte từ nguồn, ghi sang đích, dừng ở 0.
- Chuỗi hằng (literal) nằm ở `.rdata`/`.rodata`, truy cập qua `lea rax, [rip+offset]`. Objdump và IDA hiển thị luôn nội dung chuỗi, nên Strings window dẫn bạn tới đúng chỗ dùng nó.

Mẹo thực chiến: trong một crackme, tìm vòng lặp "đọc byte, test, nhảy" đặt ngay cạnh một chuỗi literal, đó thường là nơi so sánh input với đáp án.

## Cách để decompiler giúp bạn

Khi kiểu dữ liệu đúng, pseudocode của IDA/Ghidra đọc như C thật. Khi nó đoán sai (ví dụ hiện một con trỏ thành `int`), bạn tự gán lại kiểu:
- IDA: đặt con trỏ vào biến rồi nhấn `Y` để sửa type, hoặc `N` để đổi tên.
- Ghidra: `Ctrl+L` để retype, `L` để rename.

Mỗi lần bạn sửa một biến thành `char *` hay `int[5]`, decompiler tự cập nhật mọi chỗ dùng nó, và cả hàm sáng ra. Đây là vòng lặp làm việc thật: đọc, đoán kiểu, gán kiểu, đọc lại dễ hơn.

## Lab tự làm

Mã nguồn và hướng dẫn ở [labs/3.2/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/3.2). Tóm tắt: build `datatypes.c` với `-O0`, mở trong IDA hoặc Ghidra, rồi tự tay chỉ ra trong từng hàm đâu là biến toàn cục, biến cục bộ, chỗ dereference con trỏ, công thức truy cập mảng, và vòng lặp xử lý chuỗi. Writeup đối chiếu đầy đủ ở [labs/3.2/solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/3.2/solution.md), nhưng tự làm trước đã.

## Checklist ghi nhớ
- `[rbp-x]` là biến cục bộ, `[rip+x]` hoặc địa chỉ cố định trong .data/.bss là biến toàn cục.
- Con trỏ là biến chứa địa chỉ. Dereference luôn là nạp con trỏ vào thanh ghi rồi truy cập `[thanh ghi]`. Đếm tầng ngoặc là đếm số dấu sao.
- Mảng: dấu vân tay là `index * kích_thước_phần_tử` cộng vào base. `*4` là int, `*8` là con trỏ 64-bit.
- Chuỗi C kết thúc bằng byte 0. Pattern "đọc byte, test al,al, nhảy" là xử lý chuỗi.
- Gán đúng kiểu trong decompiler (`Y` ở IDA, `Ctrl+L` ở Ghidra) làm cả hàm dễ đọc hẳn.
