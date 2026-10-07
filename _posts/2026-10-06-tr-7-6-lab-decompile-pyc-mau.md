---
title: "Bài 7.6: Lab, decompile các file .pyc mẫu bằng pycdc"
date: 2026-10-06 08:58:00 +0700
categories: ["Technique Reverse", "Phần 7 · Python (pycdc)"]
tags: [reverse-engineering, python]
render_with_liquid: false
---
Lý thuyết của Phần 7 giờ đem ra dùng thật. Repo này có sẵn thư mục `pycdc-master` kèm ba file `.pyc` mẫu, và ba file đó không hẹn mà gặp lại đúng ba tình huống bạn sẽ đụng ngoài đời: một file hỏng, một file không có header, và một file viết bằng phiên bản Python mới hơn cái pycdc hỗ trợ. Mỗi file dạy một bài khác nhau, nên đừng bỏ file nào.

Toàn bộ output trong bài này là kết quả chạy thật trên máy, không phải minh hoạ bịa. Bạn chạy lại sẽ ra y hệt.

## Chuẩn bị: build pycdc

Binary dựng sẵn trong repo có thể không chạy trên máy bạn (lệch phiên bản GLIBC, đúng vấn đề gặp khi viết bài này). Build lại từ source cho chắc:

```bash
cd pycdc-master/pycdc-master
cmake . -DCMAKE_BUILD_TYPE=Release
make -j4
```

Xong bạn có hai binary: `pycdc` (decompile ra Python source) và `pycdas` (disassemble ra bytecode đọc được). Nhớ nguyên tắc từ [Bài 7.2](/posts/tr-7-2-pycdc-pycdas/): pycdc cho ra source đẹp khi thành công, pycdas luôn chạy được và là phao cứu sinh khi pycdc bó tay.

## File 1: ok.pyc, bài học về cái file rỗng

Chạy thử:

```
$ ./pycdc ok.pyc
Bad MAGIC!
Could not load file .../ok.pyc
```

Trước khi đổ lỗi cho tool, kiểm tra file. `ls -l` cho thấy `ok.pyc` nặng đúng 0 byte. Nó rỗng. Không có gì để decompile cả.

Nghe ngớ ngẩn nhưng đây là lỗi thật bạn sẽ gặp: file tải về dở, extract hỏng, hoặc ghi đè nhầm. "Bad MAGIC!" không phải lúc nào cũng nghĩa là sai phiên bản, đôi khi chỉ là file không có nổi 4 byte magic để đọc. Bài học rẻ tiền nhưng tiết kiệm cả giờ ngồi nghi oan cho pycdc.

## File 2: apple_collector_game.pyc, file không có header

```
$ ./pycdc apple_collector_game.pyc
Bad MAGIC!
```

Lại "Bad MAGIC!". Nhưng file này nặng 11KB, không rỗng. Xem byte đầu:

```
$ xxd apple_collector_game.pyc | head -1
00000000: e300 0000 0000 0000 0000 0000 0005 0000
```

Một file `.pyc` chuẩn phải bắt đầu bằng 4 byte magic (xem [Bài 7.1](/posts/tr-7-1-bytecode-python-pyc-magic/)). Đây bắt đầu bằng `e3`. Byte `0xe3` chính là mã marshal cho một code object (`TYPE_CODE` = `0x63` = `'c'`, cộng cờ ref `0x80`). Nói cách khác, đây không phải `.pyc` đầy đủ, mà là một **code object đã marshal trần trụi**, bị lột mất 16 byte header.

Chuyện này rất hay gặp khi bạn trích `.pyc` ra từ PyInstaller: nhiều phiên bản cắt header đi. pycdc có cờ cho đúng ca này: `-c` (nạp code object trần) kèm `-v` (chỉ định phiên bản Python, vì không còn magic để tự đoán).

Vấn đề: phiên bản nào? Khi không có magic, cách nhanh nhất là thử. Chạy pycdas với vài phiên bản cho tới khi nó nạp được:

```
$ ./pycdas -c -v 3.10 apple_collector_game.pyc
CreateObject: Got unsupported type 0x0
terminate called ... std::bad_cast

$ ./pycdas -c -v 3.11 apple_collector_game.pyc
apple_collector_game.pyc (Python 3.11)
[Code]
    File Name: apple_collector_game.py
    ...
```

3.10 trở xuống nổ tung, 3.11 nạp sạch và còn lộ tên file gốc `apple_collector_game.py`. Vậy là Python 3.11. Giờ decompile:

```
$ ./pycdc -c -v 3.11 apple_collector_game.pyc
```

Kết quả ra gần như trọn vẹn:

```python
import os
import sys
from dotenv import load_dotenv
_BASE = os.path.dirname(os.path.abspath(__file__))

def R0(p):
    return os.path.join(sys._MEIPASS, p) if hasattr(sys, '_MEIPASS') else os.path.join(_BASE, p)

load_dotenv(R0('flag.env'))
...
class G:
    def __init__(self):
        self.s = pygame.display.set_mode(_W)
        pygame.display.set_caption('Apple Collector Game')
        ...
        self.fl = os.getenv('CTF_FLAG')
```

Đọc được là hiểu ngay: đây là một game pygame "Apple Collector", và nó là một challenge CTF. Hàm `R0` kiểm tra `sys._MEIPASS`, dấu hiệu chắc chắn chương trình từng được đóng gói bằng **PyInstaller** (xem [Bài 7.4](/posts/tr-7-4-unpack-pyinstaller-py2exe/)). Flag nằm trong biến môi trường `CTF_FLAG`, nạp từ file `flag.env` đi kèm. Vậy với challenge này, "giải" không phải đọc code mà là tìm ra file `flag.env` trong gói PyInstaller.

Để ý pycdc có in vài dòng `Unsupported opcode: BEFORE_WITH` và `JUMP_BACKWARD`, và một số hàm kết thúc bằng `# WARNING: Decompyle incomplete`. Đây là giới hạn thật của pycdc với Python 3.11: nó vấp khối `with` và một số dạng vòng lặp. Nhưng phần decompile được đã quá đủ để hiểu chương trình. Chỗ nào incomplete thì mở pycdas đọc bytecode của riêng hàm đó.

## File 3: out_sequencer.pyc, phiên bản mới hơn pycdc

File này có header đàng hoàng:

```
$ xxd out_sequencer.pyc | head -1
00000000: f30d 0d0a 0000 0000 240e d668 ...
```

Magic `f3 0d 0d 0a`, tức `0x0df3` = 3571, là Python 3.13. Thử decompile:

```
$ ./pycdc out_sequencer.pyc
Unsupported opcode: LOAD_FROM_DICT_OR_GLOBALS
# Source Generated with Decompyle++
# File: out_sequencer.pyc (Python 3.13)

if not None + None:
    pass
# WARNING: Decompyle incomplete
```

Thất bại gần như hoàn toàn. Python 3.13 quá mới so với pycdc, opcode `LOAD_FROM_DICT_OR_GLOBALS` chưa được hỗ trợ, và kết quả là rác. Đây đúng là tình huống [Bài 7.3](/posts/tr-7-3-decompiler-python-khac/) cảnh báo: không decompiler nào theo kịp mọi phiên bản.

Nhưng đừng bỏ cuộc. Chuyển sang pycdas để đọc bytecode, nó luôn chạy:

```
$ ./pycdas out_sequencer.pyc
out_sequencer.pyc (Python 3.13)
[Code]
    File Name: <genetic_sequencer>
    [Names]
        'base64'  'zlib'  'marshal'  'types'
        'encoded_catalyst_strand'  'print'  'b85decode'
        'compressed_catalyst'  'decompress'
        'marshalled_genetic_code'  'loads'
        'catalyst_code_object'  'FunctionType'  'globals'
    [Constants]
        b'c$|e+O>7&-6`m!Rzak~llE|2<...'   (một blob base85 rất dài)
        '--- Calibrating Genetic Sequencer ---'
        'Decoding catalyst DNA strand...'
```

Dù bytecode disassembly của 3.13 cũng hơi lệch (pycdc chưa map đúng hết opcode 3.13), phần `[Names]` và `[Constants]` vẫn đọc được, và chúng kể hết câu chuyện. Nhìn danh sách tên là dựng lại được logic: lấy `encoded_catalyst_strand` (blob base85), `base64.b85decode`, rồi `zlib.decompress`, rồi `marshal.loads` ra một code object, rồi `types.FunctionType` để biến nó thành hàm và chạy. Đây là một **loader tự giải mã**: nó giấu payload thật dưới ba lớp encode.

## Khi tool bó tay, làm bằng tay

pycdc không đọc được 3.13, nhưng chính Python đọc được marshal của nó (với một chút linh hoạt). Ta tự lột từng lớp đúng như loader làm. Viết script (chạy với `python3 -I` cho an toàn, xem lưu ý đầu khoá học về thư mục chứa file lạ):

```python
import sys, base64, zlib, marshal
data = open('out_sequencer.pyc','rb').read()
code = marshal.loads(data[16:])          # bỏ 16 byte header .pyc rồi unmarshal module
blob = [c for c in code.co_consts if isinstance(c, bytes)][0]
inner = marshal.loads(zlib.decompress(base64.b85decode(blob)))
print(inner.co_names)
```

Kết quả thật:

```
('os', 'sys', 'emoji', 'random', 'asyncio', 'cowsay', 'pyjokes',
 'art', 'arc4', 'ARC4', 'activate_catalyst', 'run')
```

Lớp trong là một code object khác, import `arc4.ARC4` (tức thuật toán RC4) và có hàm `activate_catalyst`. Đào sâu các hằng số của nó:

```
fn: activate_catalyst
  bytes: b'm\x1b@I\x1dAoe@\x07ZF[BL\rN\n\x0cS'   (ciphertext)
  bytes: b'r2b-\r\x9e\xf2\x1f...'                 (ciphertext)
  str: '--- Catalyst Serum Injected ---'
  str: "Verifying Lead Researcher's credentials via biometric scan..."
  str: 'AUTHENTICATION   SUCCESS'
  str: 'I am alive! The secret formula is:\n'
  str: 'AUTHENTICATION   FAILED'
```

Giờ thì rõ: đây là challenge "Project Chimera". Payload thật mã hoá một "secret formula" bằng RC4, khoá sinh từ `os.getlogin()` (tên user, đóng vai "biometric scan"). pycdc chưa bao giờ hé được dòng nào, nhưng bằng cách tự lột ba lớp base85, zlib, marshal, ta khôi phục được toàn bộ cấu trúc và cả thuật toán. Đây chính là tinh thần [Bài 0.4](/posts/tr-0-4-quy-trinh-reverse/): tool chỉ là đòn bẩy, hiểu cơ chế mới là thứ cứu bạn khi tool gãy.

## Ba file, ba bài học

- **ok.pyc**: kiểm tra file trước khi nghi tool. "Bad MAGIC!" trên file 0 byte nghĩa là file rỗng.
- **apple_collector_game.pyc**: code object trần (byte đầu `e3`, không có magic). Dùng `pycdc -c -v <ver>`, dò phiên bản bằng cách thử. Hoá ra là game PyInstaller giấu flag trong `flag.env`.
- **out_sequencer.pyc**: Python 3.13 quá mới, pycdc fail. pycdas vẫn đọc được names/consts, và tự lột lớp base85 + zlib + marshal thì khôi phục được payload RC4 bên trong.

## Checklist ghi nhớ
- Build pycdc từ source nếu binary dựng sẵn không chạy (lệch GLIBC/GLIBCXX).
- "Bad MAGIC!" có ba nguyên nhân hay gặp: file rỗng/hỏng, code object trần không header, hoặc phiên bản lạ.
- Byte đầu `e3` (hoặc `63`) nghĩa là code object trần, dùng `-c -v`, dò phiên bản bằng pycdas.
- pycdc fail thì pycdas gần như luôn còn đọc được names và consts, đủ để dựng lại logic.
- Loader Python hay giấu payload qua base64/base85 + zlib + marshal. Lột đúng thứ tự đó là ra.
- Khi mọi tool gãy, dùng chính `marshal` của Python để lột từng lớp bằng tay.
