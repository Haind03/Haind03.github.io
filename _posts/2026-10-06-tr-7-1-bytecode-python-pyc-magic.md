---
title: "Bài 7.1: Bytecode Python và file .pyc"
date: 2026-10-06 08:53:00 +0700
categories: ["Technique Reverse", "Phần 7 · Python (pycdc)"]
tags: [reverse-engineering, python]
render_with_liquid: false
---
Sau native C++ và managed .NET, Python là một luồng gió mát. Ở đây reverse gần như là đọc lại source, vì Python giữ lại gần hết mọi thứ: tên hàm, tên biến, tên hằng, cả số dòng. Hiểu cách Python biên dịch và cái file `.pyc` chứa gì là bạn nắm được vì sao nó dễ đến thế, và vì sao đôi khi vẫn khó (phiên bản).

## Python cũng biên dịch, chỉ là bạn không để ý

Nhiều người tưởng Python là ngôn ngữ thông dịch thuần, chạy thẳng từ text. Không hẳn. Khi bạn chạy một file `.py`, CPython biên dịch nó sang bytecode trước, rồi mới cho một máy ảo (CPython VM) chạy bytecode đó. Máy ảo này stack-based, giống JVM: các lệnh đẩy và lấy giá trị trên một stack.

Bytecode này không biến mất. Với module được import, CPython lưu lại thành file `.pyc` trong thư mục `__pycache__/` để lần sau khỏi biên dịch lại. Và `.pyc` chính là thứ bạn hay phải reverse, vì nhiều chương trình Python đóng gói chỉ phát hành `.pyc` chứ không kèm `.py`.

## Bên trong một file .pyc

![Cấu trúc file .pyc: header 16 byte và code object marshal](/assets/img/technique-reverse/assets/phan-07/pyc-structure.svg)

File `.pyc` có hai phần: một header ngắn, rồi một code object đã được marshal (serialize).

Header 16 byte (từ Python 3.7 trở đi):

```
+0  magic number (4 byte)   cho biết phiên bản bytecode
+4  bit field   (4 byte)    quyết định 8 byte sau là timestamp hay hash
+8  timestamp/hash (4 byte) thời điểm biên dịch, hoặc hash nguồn
+12 source size (4 byte)    kích thước file .py gốc
```

Đây là 16 byte đầu của một `.pyc` thật do Python 3.11 sinh ra (lấy từ lab bên dưới):

```
a7 0d 0d 0a  00 00 00 00  dc b4 c4 6a  05 01 00 00
\_________/  \_________/  \_________/  \_________/
  magic        bit field    timestamp    source size
```

Bốn byte đầu `a7 0d 0d 0a` là **magic number**. Đây là thứ quan trọng nhất với bạn.

## Magic number: chọn đúng decompiler hay thất bại

Mỗi phiên bản Python có một magic number riêng, vì bytecode thay đổi giữa các bản (thêm/bớt/đổi opcode). Hai byte `0d 0a` cuối cố định, hai byte đầu phân biệt phiên bản. Vài giá trị để bạn hình dung:

| Python | Magic (2 byte đầu, little-endian trong file) |
|---|---|
| 3.8 | `55 0d` |
| 3.9 | `61 0d` |
| 3.10 | `6f 0d` |
| 3.11 | `a7 0d` |
| 3.12 | `cb 0d` |

Vì sao quan trọng: decompiler như pycdc hay uncompyle6 phải biết đúng phiên bản mới dịch đúng bytecode. Dịch một `.pyc` 3.11 bằng công cụ chỉ hiểu 3.8 là ra rác hoặc lỗi. Khi cầm một `.pyc` lạ, việc đầu tiên là đọc magic để biết nó của Python nào. Bài [7.2](/posts/tr-7-2-pycdc-pycdas/) dùng chính con số này.

## Code object: nơi chứa gần hết thông tin

Phần sau header là một code object đã marshal. Giải ra, nó chứa:

- `co_code`: dãy byte bytecode thật.
- `co_consts`: các hằng số dùng trong hàm (số, chuỗi, cả code object của hàm con).
- `co_names`: tên biến global và tên thuộc tính.
- `co_varnames`: tên biến cục bộ và tham số.
- `co_filename`, `co_name`, `co_firstlineno`: tên file, tên hàm, số dòng.

Nhìn danh sách này là hiểu vì sao Python dễ reverse: tên biến cục bộ còn nguyên, chuỗi còn nguyên, cả số dòng gốc. Không có bước nào xé nát thông tin như compiler C làm.

## Đọc thử bytecode bằng dis

Module `dis` của Python in bytecode cho dễ đọc. Với hàm này:

```python
def check(name):
    total = 0
    for c in name:
        total += ord(c)
    return total == 0x29A
```

`dis.dis(check)` cho ra (output thật từ Python 3.11.9):

```
  2     LOAD_CONST    1 (0)
        STORE_FAST    1 (total)      # total = 0

  3     LOAD_FAST     0 (name)
        GET_ITER
    >>  FOR_ITER      20 (to 52)     # vòng for c in name
        STORE_FAST    2 (c)

  4     LOAD_FAST     1 (total)
        LOAD_GLOBAL   1 (NULL + ord)
        LOAD_FAST     2 (c)
        PRECALL       1
        CALL          1              # ord(c)
        BINARY_OP     13 (+=)        # total += ...
        STORE_FAST    1 (total)
        JUMP_BACKWARD 21 (to 10)     # quay lại đầu vòng lặp

  5 >>  LOAD_FAST     1 (total)
        LOAD_CONST    2 (666)        # 0x29A = 666
        COMPARE_OP    2 (==)
        RETURN_VALUE
```

Đọc nó gần như đọc lại source. Cột trái là số dòng Python gốc. `LOAD_CONST`, `STORE_FAST`, `LOAD_FAST` đẩy và lưu giá trị, `FOR_ITER` là vòng lặp, `COMPARE_OP 2 (==)` là phép so sánh, và để ý `LOAD_CONST 2 (666)`: hằng số `0x29A` lộ thẳng ra. Một crackme Python kiểu này bị lộ bí mật ngay trong `co_consts`.

Chú ý opcode đổi theo phiên bản: `PRECALL` và `BINARY_OP` ở trên là của 3.11. Bản 3.8 gọi hàm bằng `CALL_FUNCTION` và cộng bằng `INPLACE_ADD`. Đây chính là lý do magic number quan trọng.

## Reverse Python gồm những gì

Thực tế bạn gặp ba tình huống, tăng dần độ khó:

1. Có sẵn `.pyc`: decompile thẳng bằng pycdc hoặc uncompyle6 (Bài 7.2, 7.3).
2. Chương trình đóng thành `.exe` bằng PyInstaller/py2exe: phải giải nén lấy `.pyc` ra trước (Bài 7.4).
3. Bị Nuitka/Cython/PyArmor biến thành native hoặc mã hoá: khó hẳn, phải reverse như C (Bài 7.5).

Bài này là nền: biết `.pyc` chứa gì và đọc được magic. Phần còn lại của Phần 7 dựng trên đó.

## Lab tự làm

Xem `labs/7.1/`: bạn sẽ tự viết một hàm, dùng `dis` xem bytecode, biên dịch ra `.pyc` và đọc header bằng tay. Dùng chính `python3` trên máy.

## Checklist ghi nhớ
- Python biên dịch source sang bytecode rồi chạy trên CPython VM (stack-based).
- `.pyc` = header 16 byte (magic, bit field, timestamp/hash, size) + code object đã marshal.
- Magic number (4 byte đầu) cho biết phiên bản Python. Đọc nó trước khi chọn decompiler.
- code object giữ tên biến, tên hàm, hằng số, số dòng, nên Python rất dễ reverse.
- Opcode đổi giữa các phiên bản, dịch sai phiên bản là ra rác.
