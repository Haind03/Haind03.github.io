---
title: "Bài 7.2: pycdc và pycdas, hai con dao mổ file .pyc"
date: 2026-10-06 08:54:00 +0700
categories: ["Technique Reverse", "Phần 7 · Python (pycdc)"]
tags: [reverse-engineering, python]
render_with_liquid: false
---
Bài trước bạn đã biết một file `.pyc` là gì và cách đọc magic number của nó. Giờ tới lúc mở nó ra. Bộ công cụ chủ lực là Decompyle++ (tên repo là `pycdc`), gồm hai chương trình: `pycdc` cố dựng lại source Python, và `pycdas` xả ra bytecode dạng người đọc được. Cả hai đã nằm sẵn trong repo này tại `pycdc-master/pycdc-master`, kèm vài file `.pyc` mẫu để nghịch.

Điểm khiến bộ này đáng giá: nó viết bằng C++, **không phụ thuộc runtime Python**. Các decompiler khác như uncompyle6 chạy bằng chính Python và thường chỉ decompile được `.pyc` cùng dòng phiên bản với interpreter đang chạy. pycdc thì đọc trực tiếp cấu trúc file, nên trên máy chỉ có Python 3.11 bạn vẫn thử được `.pyc` của 2.7 hay 3.6. Đổi lại, nó phải tự cài hiểu biết cho từng phiên bản bytecode, nên các phiên bản mới nhất (3.12, 3.13) hỗ trợ chưa đầy đủ. Phần dưới sẽ thấy rõ cả mặt mạnh lẫn mặt yếu đó, bằng kết quả chạy thật.

## Build trong năm phút

pycdc dùng CMake. Trên Linux/WSL:

```sh
cd pycdc-master/pycdc-master
cmake . -DCMAKE_BUILD_TYPE=Release
make -j4
```

Xong bạn có hai file thực thi `pycdc` và `pycdas` ngay trong thư mục. Repo này có kèm bản build sẵn, nhưng nếu nó báo lỗi thiếu `GLIBC`/`GLIBCXX` (bản build trên máy khác, glibc cũ hơn), cứ build lại như trên là hết. Trên Windows dùng Visual Studio hoặc MinGW, quy trình CMake tương tự.

## pycdc: cố dựng lại source

Cú pháp đơn giản nhất:

```sh
./pycdc duong_dan_file.pyc
```

Nó in thẳng source dựng lại ra stdout. Với một file bytecode 3.8 sạch sẽ trong bộ test của repo, kết quả gần như hoàn hảo:

```
$ ./pycdc tests/compiled/test_calls.3.8.pyc
# Source Generated with Decompyle++
# File: test_calls.3.8.pyc (Python 3.8)

import sys
import os
sys.stdout.write('Test\n')
sys.stdout.write(os.path.join('foo', 'bar'))
print('\n')
print(eval('4 * 13'))
print()
```

Đọc như source gốc. Đây là trường hợp lý tưởng: phiên bản được hỗ trợ tốt, code không obfuscate.

## Khi pycdc bó tay: mặt yếu với Python mới

Repo kèm file `out_sequencer.pyc`. Chạy pycdc:

```
$ ./pycdc out_sequencer.pyc
Unsupported opcode: LOAD_FROM_DICT_OR_GLOBALS
# Source Generated with Decompyle++
# File: out_sequencer.pyc (Python 3.13)

if not None + None:
    pass
# WARNING: Decompyle incomplete
```

Đây là bài học thực tế quan trọng nhất của cả bài. File này là Python 3.13 (magic `f3 0d 0d 0a`), và pycdc gặp opcode `LOAD_FROM_DICT_OR_GLOBALS` mà nó chưa hiểu, nên đầu hàng và in ra thứ vô nghĩa (`if not None + None`). Đừng tin output kiểu này. Khi thấy dòng `Unsupported opcode` hoặc `WARNING: Decompyle incomplete`, nghĩa là bạn không thể dựa vào source nó in ra. Lúc đó chuyển sang `pycdas` đọc bytecode thô.

## pycdas: xả bytecode khi decompile thất bại

`pycdas` không cố dựng source, nó chỉ liệt kê mọi thứ trong file: tên biến, hằng số, chuỗi, và bytecode. Khi pycdc thất bại, đây là phao cứu sinh vì nó hầu như luôn đọc được phần metadata.

```
$ ./pycdas out_sequencer.pyc
out_sequencer.pyc (Python 3.13)
[Code]
    File Name: <genetic_sequencer>
    Object Name: <module>
    ...
    [Names]
        'base64'
        'zlib'
        'marshal'
        'types'
        'encoded_catalyst_strand'
        'b85decode'
        'compressed_catalyst'
        'decompress'
        'marshalled_genetic_code'
        'loads'
        'catalyst_code_object'
        'FunctionType'
```

Nhìn danh sách `[Names]` là đoán ra ngay kịch bản, dù chưa đọc một dòng logic nào: file này `b85decode` một chuỗi, `zlib.decompress`, rồi `marshal.loads` để dựng lại một code object và biến nó thành hàm bằng `types.FunctionType`. Đây là mẫu loader tự giải mã kinh điển: lớp ngoài chỉ là vỏ, code thật bị nén và marshal giấu trong một blob base85 (bạn cũng thấy blob đó nằm trong phần `[Constants]` của pycdas). Muốn đi tiếp, bạn trích blob ra, tự `b85decode` + `zlib.decompress` + `marshal.loads` trong một phiên Python để lấy code object bên trong, rồi lại mang vào pycdc. Kỹ thuật bóc lớp này gặp lại ở bài về unpack ([7.4](/posts/tr-7-4-unpack-pyinstaller-py2exe/)).

Lưu ý: với file 3.13 này, ngay cả phần `[Disassembly]` của pycdas cũng hiện opcode sai lệch (nó gán nhầm tên opcode vì chưa map đúng bảng 3.13). Nhưng phần `[Names]` và `[Constants]` vẫn đủ để hiểu ý đồ. Bài học: tool có thể sai ở tầng này mà đúng ở tầng kia, đừng vứt bỏ toàn bộ output chỉ vì một phần hỏng.

## Hai cái bẫy về header, qua file mẫu thật

Repo còn hai file minh hoạ hai lỗi hay gặp:

`ok.pyc` nặng 0 byte. Chạy gì cũng ra:

```
$ ./pycdc ok.pyc
Bad MAGIC!
Could not load file ok.pyc
```

File rỗng hoặc cụt thì không có magic để đọc. Trước khi đổ lỗi cho tool, kiểm tra kích thước file.

`apple_collector_game.pyc` thì thú vị hơn, cũng báo `Bad MAGIC!` nhưng file không hề rỗng (gần 12 KB). Xem bốn byte đầu:

```
$ xxd -l 4 apple_collector_game.pyc
00000000: e300 0000
```

Một `.pyc` hợp lệ phải mở đầu bằng magic number (ví dụ `f3 0d 0d 0a` cho 3.13). Byte `e3` ở đây chính là opcode marshal cho một code object. Nói cách khác, file này không phải `.pyc` đầy đủ mà là một **code object đã marshal thô**, bị tước mất phần header 16 byte. pycdc cần header để biết phiên bản nên nó từ chối. Cách xử lý: tự đắp lại header (ghép magic number đúng phiên bản + phần đệm vào trước), hoặc đọc thẳng bằng module `marshal` của Python. Đây là thủ thuật giấu đơn giản mà hiệu quả, và giờ bạn nhận ra nó chỉ qua bốn byte đầu.

## Nhịp làm việc gợi ý

1. `pycdas file.pyc` trước để biết phiên bản và nhìn tổng thể Names/Constants, kể cả khi định dùng pycdc.
2. `pycdc file.pyc` để lấy source. Nếu sạch, xong.
3. Thấy `Unsupported opcode` hoặc `WARNING: Decompyle incomplete`: quay lại đọc bytecode bằng pycdas, hoặc thử một decompiler khác ([7.3](/posts/tr-7-3-decompiler-python-khac/)).
4. Thấy `Bad MAGIC!`: kiểm tra file rỗng, hay là marshal thô mất header, hay đã bị mã hoá.

## Lab tự làm

Thư mục [labs/7.2/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/7.2) có hướng dẫn build pycdc và chạy trên đúng các file mẫu trong repo (`ok.pyc`, `out_sequencer.pyc`, `apple_collector_game.pyc`) để bạn tự tay thấy cả ba kết cục: decompile sạch, decompile thất bại vì phiên bản mới, và lỗi header. `solution.md` kèm output thật.

## Checklist ghi nhớ
- pycdc dựng source, pycdas xả bytecode. Cả hai không cần runtime Python đúng phiên bản.
- Build bằng cmake + make trong vài phút nếu bản dựng sẵn lỗi thư viện.
- `Unsupported opcode` hoặc `WARNING: Decompyle incomplete` nghĩa là đừng tin source pycdc in ra, chuyển sang pycdas.
- pycdc yếu với Python 3.12/3.13, đây là hạn chế thật, không phải bạn làm sai.
- `Bad MAGIC!` có ba nguyên nhân hay gặp: file rỗng/cụt, marshal thô mất header, hoặc file đã mã hoá.
- Luôn đọc `[Names]` và `[Constants]` của pycdas: nhiều khi chúng tiết lộ cả kịch bản (loader base64/zlib/marshal) trước khi bạn đọc logic.
