---
title: "Bài 7.3: Khi pycdc bó tay, còn những ai khác"
date: 2026-10-06 08:55:00 +0700
categories: ["Technique Reverse", "Phần 7 · Python (pycdc)"]
tags: [reverse-engineering, python]
render_with_liquid: false
---
Bài trước bạn đã quen pycdc. Nhưng sẽ có ngày pycdc trả về một mớ lộn xộn, hoặc bỏ trống nguyên một hàm với dòng ghi chú kiểu "unsupported opcode". Không phải lỗi của bạn. Bytecode Python đổi gần như mỗi phiên bản, và không một decompiler nào theo kịp hết. Nghề này là biết trong tay có mấy con dao, con nào hợp với miếng nào.

Bài này điểm qua các decompiler còn lại, và quan trọng hơn: cách chọn đúng con dao dựa trên phiên bản Python, cùng phương án cuối cùng không bao giờ phản bội bạn là đọc thẳng bytecode.

## Vì sao không có decompiler nào thắng tuyệt đối

Gốc rễ nằm ở chỗ CPython thay đổi tập opcode liên tục. Python 3.10 thêm pattern matching, 3.11 làm lại toàn bộ cơ chế gọi hàm (`PRECALL`, `CALL`, `LOAD_METHOD` đổi hành vi), 3.12 tiếp tục dọn dẹp. Mỗi lần như vậy, decompiler phải được viết lại phần xử lý opcode mới.

Chia thành hai trường phái:

- **Phụ thuộc runtime** (uncompyle6, decompyle3): hiểu bytecode qua chính Python đang chạy, nên chỉ chạy tốt với các phiên bản tác giả đã hỗ trợ. Mạnh ở Python 2 và 3.x cũ.
- **Độc lập runtime** (pycdc): tự parse bytecode bằng C++, chạy được trên .pyc của phiên bản khác với Python trên máy bạn. Linh hoạt hơn nhưng phần hỗ trợ 3.9+ còn lỗ hổng.

Thực tế: thử vài tool trên cùng một file rồi lấy cái nào ra kết quả tốt nhất. Đừng trung thành với một tool.

## uncompyle6 và decompyle3

Đây là cặp decompiler kinh điển cho Python đời cũ.

- **uncompyle6**: phủ rộng nhất về lịch sử, từ Python 1.x, 2.x cho tới khoảng 3.8. Nếu bạn gặp một file `.pyc` của Python 2.7 (còn rất nhiều trong malware và phần mềm cũ), đây gần như là lựa chọn số một.
- **decompyle3**: cùng dòng tác giả, tập trung vá tốt hơn cho 3.7, 3.8 và một phần 3.9.

Cài bằng pip và chạy thẳng:

```
pip install uncompyle6
uncompyle6 target.pyc > target.py
```

Nhưng đây là lúc bạn phải tỉnh táo. Thử chạy uncompyle6 (bản mới nhất 3.9.3) trên một file `.pyc` biên dịch bằng Python 3.11, kết quả là:

```
# Unsupported bytecode in file secret.pyc
# Unsupported Python version, 3.11, for decompilation
# Can't uncompile secret.pyc
```

Nó thậm chí không thử. Đây chính là minh hoạ sống cho nguyên tắc ở trên: uncompyle6 không được viết để hiểu bytecode 3.11, nên nó từ chối thẳng. Gặp dòng này đừng hoảng, chỉ là bạn chọn sai dao cho miếng thịt. Với file 3.11 đó, pycdc hoặc PyLingual mới là chỗ nên tới.

Điểm cộng là uncompyle6 vẫn in ra phần header hữu ích trước khi bỏ cuộc: phiên bản bytecode, thời điểm biên dịch, tên file nguồn gốc, kích thước. Thông tin triage miễn phí.

## PyLingual, tay chơi mới cho Python đời mới

Khi file của bạn là Python 3.9, 3.10, 3.11, 3.12 và pycdc ra kết quả lỗi, **PyLingual** (pylingual.io) thường là cứu cánh. Nó là decompiler chạy trên web, dùng cách tiếp cận học máy (model học từ cặp bytecode và source) thay vì luật cứng, nên bắt kịp các phiên bản mới nhanh hơn.

Cách dùng: lên trang, tải file `.pyc` lên, nhận lại Python source. Vì chạy trên web nên lưu ý: đừng tải lên file nhạy cảm hay mẫu malware có dữ liệu riêng, vì bạn đang gửi nó cho một dịch vụ bên ngoài (xem lại [Bài 0.2](/posts/tr-0-2-phap-ly-dao-duc/) về gửi dữ liệu ra ngoài). Với crackme và CTF thì vô tư.

## xdis, con dao Thuỵ Sĩ để soi

Khi bạn chỉ cần biết file thuộc phiên bản Python nào, hoặc muốn đọc bytecode mà không cần đúng runtime, **xdis** (nền tảng của uncompyle6) rất tiện:

```
pip install xdis
pydisasm target.pyc
```

`pydisasm` disassemble được bytecode của nhiều phiên bản hơn hẳn module `dis` của Python đang chạy, nên nó là cách tốt để đọc bytecode của một file 3.8 khi máy bạn chạy 3.11.

## Phương án không bao giờ phản bội: dis và marshal

Khi mọi decompiler đầu hàng, bạn vẫn còn một đường: đọc thẳng bytecode. Bytecode luôn đọc được, chỉ là tốn công hơn. Và nếu máy bạn có đúng phiên bản Python đã tạo file, module chuẩn `dis` làm việc này hoàn hảo.

Mở một `.pyc` bằng `marshal` rồi `dis` (bỏ qua header trước):

```python
import marshal, dis
with open('target.pyc', 'rb') as f:
    f.read(16)                 # bỏ header 16 byte (Python 3.7+)
    code = marshal.load(f)     # lấy code object của module
dis.dis(code)                  # in bytecode
```

Với một hàm kiểm tra như thế này:

```python
def check(pw):
    key = "r3v3rs3"
    if len(pw) != 10:
        return False
    total = 0
    for c in pw:
        total += ord(c)
    return total == 1000 and pw.startswith(key[:3])
```

`dis` (trên Python 3.11) cho ra bytecode thật, trích phần cốt lõi:

```
  2   LOAD_CONST    1 ('r3v3rs3')
      STORE_FAST    1 (key)
  3   LOAD_GLOBAL   1 (NULL + len)
      LOAD_FAST     0 (pw)
      CALL          1
      LOAD_CONST    2 (10)
      COMPARE_OP    3 (!=)
      POP_JUMP_FORWARD_IF_FALSE  (to 48)
  4   LOAD_CONST    3 (False)
      RETURN_VALUE
  5   LOAD_CONST    4 (0)
      STORE_FAST    2 (total)
  6   LOAD_FAST     0 (pw)
      GET_ITER
      FOR_ITER      (to 98)
  ...
  8   LOAD_FAST     2 (total)
      LOAD_CONST    5 (1000)
      COMPARE_OP    2 (==)
```

Đọc nó không khó như bạn tưởng. `co_consts` lộ ngay hai hằng số quan trọng: chuỗi `'r3v3rs3'` và số `1000`. `COMPARE_OP 3 (!=)` so độ dài với `10`, `FOR_ITER` là vòng lặp cộng dồn, `COMPARE_OP 2 (==)` so tổng với `1000`. Chỉ cần nhìn `co_consts` và vài lệnh `COMPARE_OP`, bạn đã suy ra luật kiểm tra mà chẳng cần decompiler nào. Đây là lý do bytecode Python được coi là món khai vị dễ nhất trong nghề.

Một mẹo nữa: in `code.co_consts` và `code.co_names` trước khi dis. Hằng số và tên hàm/biến thường tiết lộ câu trả lời nhanh hơn cả việc đọc hết bytecode.

## Bảng chọn decompiler theo phiên bản

Trước tiên xác định phiên bản từ magic number ([Bài 7.1](/posts/tr-7-1-bytecode-python-pyc-magic/)), rồi tra bảng:

| Phiên bản .pyc | Thử trước | Nếu lỗi |
|---|---|---|
| Python 2.x | uncompyle6 | đọc bytecode (xdis) |
| Python 3.0 tới 3.8 | uncompyle6 / decompyle3 | pycdc |
| Python 3.9 | decompyle3 / pycdc | PyLingual |
| Python 3.10 tới 3.12 | pycdc / PyLingual | dis/marshal thủ công |
| Rất mới (3.13+) | PyLingual | pydisasm / dis |

Bảng này sẽ cũ đi, vì tool mới ra liên tục. Nguyên tắc thì không đổi: biết phiên bản, thử vài tool, đọc bytecode khi bí.

## Lab tự làm

Xem [labs/7.3/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/7.3). Bạn sẽ lấy một file `.pyc`, thử lần lượt nhiều decompiler, chứng kiến tận mắt cái nào từ chối phiên bản nào, rồi tự đọc bytecode bằng `dis`/`marshal` để lấy câu trả lời khi tool bó tay.

## Checklist ghi nhớ
- Không có decompiler nào thắng mọi phiên bản, vì bytecode Python đổi liên tục.
- uncompyle6 mạnh ở Python 2.x tới 3.8, decompyle3 vá thêm 3.7 tới 3.9. Cả hai từ chối thẳng bytecode quá mới (đã thấy nó bỏ file 3.11).
- pycdc độc lập runtime, PyLingual (web, ML) hợp cho Python đời mới.
- Phương án cuối luôn dùng được: `marshal` đọc code object rồi `dis` in bytecode. `co_consts` và `co_names` thường lộ đáp án.
- Xác định phiên bản từ magic trước, rồi mới chọn tool.
