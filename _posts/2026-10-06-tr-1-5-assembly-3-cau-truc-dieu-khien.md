---
title: "Bài 1.5: Assembly x86/x64 (3), nhận ra if, loop, switch, mảng và struct"
date: 2026-10-06 08:08:00 +0700
categories: ["Technique Reverse", "Phần 1 · Nền tảng máy tính cho RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Bài 1.3 cho bạn bộ lệnh. Bài 1.4 cho bạn stack frame. Giờ tới phần thú vị nhất: lắp chúng lại để đọc ra **cấu trúc cấp cao**. Compiler lấy một câu `for` gọn gàng của bạn và nghiền nó thành một mớ `cmp`, `jmp`, `inc`. Việc của reverser là làm ngược: nhìn mớ đó và nhận ra "à, đây là vòng lặp".

Tin tốt: compiler rất máy móc. Nó dịch mỗi cấu trúc theo vài khuôn cố định. Thuộc khuôn là đọc được, giống như học thuộc mặt chữ vậy. Bài này là bộ khuôn đó.

## if / else: một cú nhảy bỏ qua một khối

Cấu trúc đơn giản nhất, bạn đã gặp ở bài 1.3. Mấu chốt: compiler nhảy **qua** khối lệnh khi điều kiện không thoả. Để ý logic thường bị đảo: `if (a == b)` trong C lại dịch thành "nếu a KHÁC b thì nhảy đi".

```asm
    mov  eax, [rbp-4]     ; eax = x
    cmp  eax, 5
    jne  else_branch      ; x != 5 thì nhảy xuống else
    mov  dword [rbp-8], 1 ; y = 1  (thân if)
    jmp  end_if
else_branch:
    mov  dword [rbp-8], 2 ; y = 2  (thân else)
end_if:
```

Dịch ra C:

```c
if (x == 5)
    y = 1;
else
    y = 2;
```

Khuôn nhận dạng: một `cmp`/`test`, một nhảy có điều kiện tới nhãn "else", cuối thân if có một `jmp` vô điều kiện nhảy qua khối else. Thấy cái `jmp` cuối khối là dấu hiệu có `else`. Không có nó thường là `if` trơn.

### if lồng nhau

if trong if chỉ là nhiều tầng khuôn trên chồng lên nhau, với nhiều nhãn nhảy hơn. Đừng cố đọc một mạch, hãy đi theo từng cặp cmp/jump một. IDA và Ghidra vẽ graph view giúp bạn thấy các khối rẽ nhánh rõ hơn nhiều so với đọc text tuần tự, dùng nó.

## Vòng lặp: cú nhảy ngược về trên

Đây là chữ ký không thể nhầm của vòng lặp: **một lệnh nhảy trỏ ngược lên một địa chỉ phía trước nó.** Code bình thường chạy xuôi xuống dưới, thấy nhảy lên trên là gần như chắc chắn có loop.

Một `for (i = 0; i < n; i++)` điển hình:

```asm
    mov  dword [rbp-4], 0   ; i = 0
loop_check:
    mov  eax, [rbp-4]
    cmp  eax, [rbp-8]       ; so i với n
    jge  loop_end          ; i >= n thì thoát
    ; ----- thân vòng lặp ở đây -----
    mov  eax, [rbp-4]
    inc  eax
    mov  [rbp-4], eax      ; i++
    jmp  loop_check        ; <--- NHẢY NGƯỢC LÊN, dấu hiệu vòng lặp
loop_end:
```

Dịch ra C:

```c
for (int i = 0; i < n; i++) {
    // thân vòng lặp
}
```

Cách đọc một vòng lặp cho nhanh, tìm bốn mảnh:
1. **Khởi tạo** biến đếm trước nhãn (ở đây `i = 0`).
2. **Điều kiện** ở đầu (cmp + nhảy thoát).
3. **Thân** ở giữa.
4. **Tăng/giảm** biến đếm rồi **jmp ngược** về điều kiện.

`while` và `for` dịch ra gần như y hệt, chỉ khác chỗ có hay không có phần khởi tạo và phần tăng biến. `do...while` thì đặt điều kiện ở **cuối**, nên nó thậm chí còn gọn hơn (không cần jmp vô điều kiện đầu vòng). Thấy điều kiện kiểm ở dưới đáy khối lặp là `do...while`.

## switch-case: khi compiler dùng jump table

`switch` nhỏ với vài case thì compiler nhiều khi dịch thành một chuỗi if/else if (cmp lần lượt từng giá trị). Nhưng khi case nhiều và giá trị liền nhau (0, 1, 2, 3...), nó dùng chiêu nhanh hơn nhiều: **jump table**, một bảng địa chỉ. Thay vì so sánh từng cái, nó lấy giá trị làm chỉ số tra thẳng vào bảng rồi nhảy.

```asm
    mov  eax, [rbp-4]      ; eax = giá trị switch
    cmp  eax, 3
    ja   default_case     ; lớn hơn 3 (không dấu) thì về default
    ; eax dùng làm chỉ số vào bảng địa chỉ
    lea  rcx, [jump_table]
    mov  rcx, [rcx + rax*8] ; lấy địa chỉ case thứ eax (mỗi mục 8 byte trên x64)
    jmp  rcx              ; nhảy tới case

jump_table:
    dq case_0
    dq case_1
    dq case_2
    dq case_3
```

Dịch ra C:

```c
switch (x) {
    case 0: ...; break;
    case 1: ...; break;
    case 2: ...; break;
    case 3: ...; break;
    default: ...;
}
```

Khuôn nhận dạng: một `cmp` chặn biên trên kèm `ja` về default, rồi một lệnh nhảy gián tiếp dạng `jmp [table + index*8]`. Thấy `jmp` tới một thanh ghi (không phải nhãn cố định) đi kèm phép `*4` hoặc `*8` là gần như chắc chắn jump table. Tin vui: IDA và Ghidra tự nhận ra jump table và hiển thị luôn các case cho bạn, khỏi dò tay.

## Truy cập mảng: nhân với kích thước phần tử

Mảng trong bộ nhớ là các phần tử xếp liền nhau. Để lấy `arr[i]`, CPU tính `địa chỉ gốc + i * kích_thước_phần_tử`. Chính cái phép nhân đó tố cáo đây là mảng, và còn cho biết kích thước mỗi phần tử.

```asm
    mov  rax, [rbp-8]      ; rax = con trỏ gốc của mảng
    mov  ecx, [rbp-4]      ; ecx = i
    mov  edx, [rax + rcx*4] ; edx = arr[i], mỗi phần tử 4 byte -> int
```

Dịch ra C:

```c
int x = arr[i];   // arr là int*, nên nhân 4
```

Đọc hệ số nhân là đọc ra kiểu:
- `*1`: mảng byte (char, uint8).
- `*2`: short (16 bit).
- `*4`: int hoặc float (32 bit).
- `*8`: long long, double, hoặc con trỏ trên x64.

Cú pháp đầy đủ của một toán hạng bộ nhớ x86 là `[base + index*scale + displacement]`, ví dụ `[rax + rcx*4 + 0x10]`. Mỗi thành phần có ý nghĩa, và phần tiếp theo sẽ cho thấy cái `displacement` đó hay là dấu hiệu của struct.

## Truy cập struct: cộng một offset cố định

Struct cũng là các trường xếp liền nhau, nhưng khác mảng ở chỗ: bạn truy cập bằng **offset cố định** (vị trí trường trong struct) chứ không phải chỉ số nhân với kích thước. Thấy một con trỏ bị cộng thêm các hằng số khác nhau (0, 4, 8, 0x10...) để lấy ra các giá trị, đó là struct.

```asm
    mov  rax, [rbp-8]     ; rax = con trỏ tới struct
    mov  ecx, [rax]        ; đọc trường tại offset 0
    mov  edx, [rax+4]      ; đọc trường tại offset 4
    mov  r8,  [rax+8]      ; đọc trường tại offset 8
```

Dịch ra C:

```c
struct Thing {
    int   a;   // offset 0
    int   b;   // offset 4
    void *c;   // offset 8
};
int x = t->a;
int y = t->b;
void *z = t->c;
```

Phân biệt nhanh mảng với struct: **mảng dùng chỉ số thay đổi nhân kích thước (`rcx*4`), struct dùng offset hằng số (`+4`, `+8`).** Mảng là "cùng một kiểu, nhiều phần tử", struct là "nhiều kiểu khác nhau, mỗi cái một chỗ cố định".

Trong IDA bạn có thể khai báo struct (phím `Y` để đặt kiểu, hoặc tạo struct trong Local Types) rồi gán cho con trỏ, lập tức `[rax+8]` biến thành `t->c` đọc sướng mắt. Bài [3.3](https://github.com/Haind03/Technique-Reverse/tree/main/phan-03-c) đào kỹ việc khôi phục struct.

## Tổng kết bộ khuôn

Dán cái này cạnh màn hình lúc mới học:

| Thấy gì trong asm | Nhiều khả năng là |
|---|---|
| `cmp`/`test` + nhảy có điều kiện + `jmp` qua một khối | if / else |
| Nhảy **ngược lên** một địa chỉ phía trên | vòng lặp |
| Biến bị `inc`/`dec` rồi so sánh ở đầu/cuối khối | biến đếm của loop |
| `jmp` tới thanh ghi + `index*4` hoặc `*8` từ một bảng | switch với jump table |
| `[base + index*scale]`, scale là 1/2/4/8 | truy cập mảng, scale cho biết kiểu |
| `[base + hằng số]` với nhiều hằng số khác nhau | truy cập struct, hằng số là offset trường |

Đừng học vẹt. Cách chắc nhất là tự viết code C, build ra, rồi mở trong Ghidra/IDA xem compiler đã biến nó thành gì. Đó chính là lab dưới đây.

## Lab tự làm

Thư mục [`labs/1.5/`](https://github.com/Haind03/Technique-Reverse/tree/main/labs/1.5) có một file C gói đủ cả năm cấu trúc trên. Build nó (hướng dẫn trong README của lab), mở binary trong Ghidra hoặc IDA, rồi tự tay chỉ ra chỗ nào là if lồng, chỗ nào là loop, chỗ nào là switch jump table, chỗ nào là mảng. Làm xong hãy đối chiếu với [`labs/1.5/solution.md`](https://github.com/Haind03/Technique-Reverse/blob/main/labs/1.5/solution.md).

Thử cả hai mức tối ưu: build với `-O0` (dễ đọc, sát khuôn) rồi build lại với `-O2` (compiler tối ưu, biến dạng nhiều hơn). So hai bản để thấy tối ưu hoá làm code khó đọc thế nào, đây là bài học thực tế quý hơn mọi lý thuyết.

## Checklist ghi nhớ
- if/else: cmp + nhảy có điều kiện qua một khối, có `jmp` cuối thân if thì thường có else. Logic điều kiện hay bị đảo.
- Vòng lặp: dấu hiệu chắc chắn là **nhảy ngược lên trên**. Tìm 4 mảnh: khởi tạo, điều kiện, thân, tăng biến.
- do...while đặt điều kiện ở cuối khối.
- switch nhiều case liền nhau: jump table, nhận ra qua `jmp` gián tiếp + `index*8`. IDA/Ghidra tự dựng các case.
- Mảng: `[base + index*scale]`, scale (1/2/4/8) cho biết kích thước phần tử.
- Struct: `[base + offset hằng số]`, mỗi offset là một trường.
- Build code của mình rồi soi là cách học nhanh nhất.
