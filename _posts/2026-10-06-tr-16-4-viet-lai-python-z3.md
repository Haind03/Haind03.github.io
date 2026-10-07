---
title: "Bài 16.4: Viết lại thuật toán bằng Python, và để Z3 giải hộ"
date: 2026-10-06 09:39:00 +0700
categories: ["Technique Reverse", "Phần 16 · Crypto & thuật toán"]
tags: [reverse-engineering, crypto]
render_with_liquid: false
---
Tới đây bạn đã đọc được thuật toán kiểm tra trong binary. Câu hỏi tiếp theo: làm sao tìm ra input hợp lệ? Có hai cấp độ. Cấp một, thuật toán đơn giản thì viết lại bằng Python rồi đảo ngược hoặc brute-force. Cấp hai, logic là một mớ ràng buộc chằng chịt giữa các byte, giải tay thì phát điên, lúc đó ta giao cho Z3, một SMT solver, nó tự tìm input thoả mọi điều kiện. Bài này đi qua cả hai, và lab cuối là một crackme giải trọn bằng Z3 đã chạy thật.

## Cấp một: viết lại bằng Python

Phần lớn crackme sau khi đọc xong hàm check là bạn thấy ngay một phép biến đổi có thể đảo. Ví dụ hay gặp: chương trình lấy từng ký tự input, biến đổi, rồi so với một mảng hằng.

```c
// đọc được trong binary
for (int i = 0; i < 10; i++)
    if (((input[i] ^ 0x5A) + i) != target[i]) return 0;
```

Viết lại và đảo ngược bằng Python trong ba dòng:

```python
target = [0x12, 0x34, ...]   # lấy từ binary
flag = bytes((target[i] - i) ^ 0x5A for i in range(len(target)))
print(flag)
```

Phép biến đổi khả nghịch (xor, cộng, trừ, hoán vị) thì luôn đảo được kiểu này. Khi nó một chiều một phần nhưng không gian nhỏ (ví dụ 4 ký tự, mỗi ký tự in được) thì brute-force:

```python
import itertools, string
for cand in itertools.product(string.printable, repeat=4):
    if check(''.join(cand)): print(cand)
```

Viết lại bằng Python là kỹ năng nền. Nhưng có loại check mà viết lại thôi chưa đủ.

## Khi nào Python tay bó tay

Xét một hàm check không biến đổi từng ký tự độc lập, mà ràng buộc chúng với nhau:

```c
if (f[0] ^ f[1] != 0x41) return 0;
if ((3*f[2] + f[3]) & 0xff != 0x5E) return 0;
if (f[0] + f[1] + ... + f[11] != 988) return 0;
// ... thêm chục ràng buộc đan nhau
```

Mỗi điều kiện liên quan nhiều byte, các byte lại xuất hiện trong nhiều điều kiện. Đảo ngược tay thành giải hệ phương trình, brute-force thì không gian 95^12 là quá lớn. Đây đúng là bài toán cho SMT solver.

## Z3 là gì và vì sao nó hợp

Z3 (Microsoft Research) là một SMT solver: bạn mô tả bài toán bằng các biến và ràng buộc, nó tự tìm một gán giá trị thoả tất cả, hoặc báo vô nghiệm. Với RE, ta mô hình mỗi byte input thành một biến, dịch mỗi phép cmp/xor/add/so sánh trong binary thành một constraint, rồi gọi solver. Nó trả về flag.

Điểm hợp với RE: Z3 có kiểu `BitVec` mô phỏng đúng số nguyên n-bit với tràn số (wrap-around) và toán bit, y hệt CPU. `xor`, `+`, `&`, `*` trên BitVec hành xử đúng như trong binary, kể cả khi tràn 8-bit.

Khung một lời giải Z3 luôn gồm bốn phần:

```python
from z3 import *
f = [BitVec(f'f{i}', 8) for i in range(12)]   # 1. biến: 12 byte
s = Solver()
s.add([And(c >= 0x20, c <= 0x7e) for c in f]) # 2. ràng buộc miền (printable)
s.add(f[0] ^ f[1] == 0x41)                    # 3. ràng buộc từ binary
# ... thêm các constraint khác
print(s.check())                              # 4. giải: sat / unsat
m = s.model()
print(bytes(m[c].as_long() for c in f))
```

Vài mẹo quan trọng:
- Dùng đúng độ rộng: byte là `BitVec(name, 8)`. Khi cộng dồn thành tổng lớn, mở rộng bằng `ZeroExt(24, c)` để lên 32-bit, tránh tràn ngoài ý muốn.
- Khớp wrap-around: nếu binary tính `(unsigned char)(3*f[i] + f[i+1])` thì trong Z3 là `(3*f[i] + f[i+1]) & 0xff` trên BitVec 8-bit (vốn đã tự wrap).
- Kiểm tra nghiệm duy nhất: sau khi có `m`, thêm `s.add(Or([c != m[c] for c in f]))` rồi `check()` lại. Nếu `unsat` thì nghiệm là duy nhất, yên tâm đó là flag thật.

## Lab: crackme giải trọn bằng Z3

Lab ở [labs/16.4/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/16.4) là một crackme cố ý ràng buộc 12 byte input với nhau: một chuỗi phương trình `A[i]*f[i] + f[i+1] == C[i]`, hai ràng buộc xor chéo, và một ràng buộc tổng. Không có phép nào so input với flag trực tiếp, nên không moi flag từ bộ nhớ hay từ strings được. Bạn đọc hệ ràng buộc trong binary, chép sang Z3, bấm giải.

Lời giải tham chiếu `solve_z3.py` dựng đúng hệ đó và chạy ra flag trong chớp mắt. Kết quả kiểm thật trong môi trường này (gcc 11.4, Python 3.11, z3 5.1.0):

```text
$ python3 solve_z3.py
FLAG: Z3_Rul3s_RE!

$ python3 solve_z3.py | sed -n 's/FLAG: //p' | ./crackme
Nhap flag: Correct! Flag hop le.
```

Z3 vừa tìm ra `Z3_Rul3s_RE!` chỉ từ các hằng số ràng buộc, và chính crackme xác nhận nó hợp lệ. Mình cũng đã kiểm nghiệm là nghiệm duy nhất, nên không có flag thứ hai.

Chi tiết từng bước nằm trong [labs/16.4/solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/16.4/solution.md), gồm cả cách đối chiếu mỗi dòng C với một constraint Z3.

## Khi nào Z3 không phải câu trả lời

Z3 mạnh nhưng không phải phép màu. Nó đuối khi:
- Ràng buộc đi qua hàm một chiều thật sự (hash như SHA-256): không có cấu trúc đại số để solver khai thác, nó sẽ chạy mãi.
- Không gian trạng thái quá lớn với loop phụ thuộc dữ liệu dài: cân nhắc kết hợp với symbolic execution (angr, Bài 18.3) để tự sinh constraint từ việc chạy.
- Ràng buộc dạng float phức tạp: được hỗ trợ nhưng chậm.

Quy tắc: nếu check là một hệ phương trình/bất phương trình trên các byte (cộng, xor, nhân, so sánh), Z3 ăn đứt. Nếu check là "băm rồi so hash", Z3 vô dụng, phải tấn công cách khác.

## Checklist ghi nhớ
- Biến đổi khả nghịch thì viết lại Python rồi đảo; không gian nhỏ thì brute-force.
- Hệ ràng buộc đan nhau giữa nhiều byte: giao cho Z3 thay vì giải tay.
- Khung Z3: biến BitVec, ràng buộc miền, ràng buộc từ binary, check và model.
- Dùng BitVec đúng độ rộng và ZeroExt khi cộng dồn, để khớp wrap-around của CPU.
- Kiểm nghiệm duy nhất bằng cách block nghiệm cũ rồi check lại.
- Z3 bó tay trước hash một chiều; lúc đó đổi hướng tấn công.
