---
title: "Bài 7.4: Khi Python biến thành file .exe, cách mở ngược ra"
date: 2026-10-06 08:56:00 +0700
categories: ["Technique Reverse", "Phần 7 · Python (pycdc)"]
tags: [reverse-engineering, python]
render_with_liquid: false
---
Bạn tải về một chương trình, DIE báo nó là PE Windows bình thường, nhưng mở trong IDA thì toàn code của bootloader chẳng liên quan gì tới logic. Nhìn kỹ strings thấy `python311.dll`, `_MEIPASS`, `pyi-`. Đây không phải chương trình C, đây là một script Python được đóng gói thành exe. Và tin tốt: logic thật vẫn là bytecode Python nằm bên trong, chỉ cần moi ra rồi decompile như Bài 7.2.

Ba công cụ đóng gói hay gặp là PyInstaller (phổ biến nhất), py2exe, và cx_Freeze. Cách xử lý na ná nhau: nhận diện, trích (extract), rồi decompile.

## PyInstaller: cấu trúc và cách nhận ra

PyInstaller không biên dịch Python sang machine code. Nó nhét nguyên một bộ runtime vào trong exe: một bootloader viết bằng C (phần bạn thấy trong IDA), interpreter Python (`python3xx.dll` hoặc `libpython`), và một archive chứa toàn bộ `.pyc` của chương trình, nén lại trong khối gọi là PYZ. Lúc chạy, bootloader giải nén vào thư mục tạm (biến môi trường `_MEIPASS`) rồi gọi interpreter chạy script chính.

Dấu hiệu nhận ra, chỉ cần `strings`:

```
_MEIPASS
pyi-contents-directory
pyimod01_archive
PYZ-00.pyz
python3.11.so.1.0        (hoặc python311.dll trên Windows)
```

Thấy `_MEIPASS` và `pyi` là gần như chắc chắn PyInstaller. DIE cũng nhận ra và báo thẳng.

## Trích ra bằng pyinstxtractor

Công cụ kinh điển là `pyinstxtractor` (và bản mới hơn `pyinstxtractor-ng`, xử lý tốt hơn các phiên bản PyInstaller gần đây). Chạy thẳng lên file exe:

```
python3 pyinstxtractor.py secretapp
```

Đây là output thật khi trích một binary dựng bằng PyInstaller 6.20, Python 3.11:

```
[+] Processing dist/secretapp
[+] Pyinstaller version: 2.1+
[+] Python version: 3.11
[+] Length of package: 16432443 bytes
[+] Found 54 files in CArchive
[+] Beginning extraction...please standby
[+] Possible entry point: pyiboot01_bootstrap.pyc
[+] Possible entry point: pyi_rth_inspect.pyc
[+] Possible entry point: secretapp.pyc
[+] Found 99 files in PYZ archive
[+] Successfully extracted pyinstaller archive: dist/secretapp
```

Hai thông tin vàng ở đây:

- **Python version: 3.11.** Đây là phiên bản bạn cần để chọn đúng decompiler. Nhớ Bài 7.2, pycdc không phụ thuộc runtime nhưng vẫn cần biết phiên bản để decompile chuẩn.
- **Possible entry point: secretapp.pyc.** PyInstaller sinh ra cả rừng `.pyc`, phần lớn là code hỗ trợ của chính nó (`pyiboot`, `pyimod`, `pyi_rth`). Những file `pyi*` đó bỏ qua. File entry point mang tên script gốc (`secretapp.pyc`) mới là thứ bạn muốn đọc.

Sau khi trích, bạn có một thư mục `secretapp_extracted/` với toàn bộ `.pyc` và các thư viện đi kèm.

## Cái bẫy magic header

Đây là chỗ người mới hay vấp. Một file `.pyc` tử tế bắt đầu bằng 16 byte header (magic number + cờ + timestamp/hash + size), như Bài 7.1 đã nói. Vấn đề: nhiều phiên bản PyInstaller **cắt bỏ magic header** của file entry point khi đóng gói, nên file `.pyc` trích ra bị thiếu 8 hoặc 16 byte đầu. Decompiler mở lên sẽ báo lỗi hoặc đọc sai.

Cách sửa: chép header từ một `.pyc` lành lặn (ví dụ một module chuẩn như `struct.pyc` trong cùng thư mục trích) dán vào đầu file thiếu. Với binary ở trên, header của `struct.pyc` và `secretapp.pyc` đều bắt đầu bằng cùng magic:

```
secretapp.pyc : a7 0d 0d 0a 00 00 00 00 ...
struct.pyc    : a7 0d 0d 0a 00 00 00 00 ...
```

`a70d0d0a` chính là magic number của Python 3.11. Tin vui là PyInstaller và pyinstxtractor-ng đời mới giữ nguyên header, nên nhiều khi bạn không phải vá gì cả. Nhưng khi gặp binary cũ, nhớ chiêu vá header này, nếu không sẽ tưởng file hỏng.

## Decompile: logic lộ ra hết

Có `.pyc` với header đầy đủ rồi thì chạy pycdc như Bài 7.2. Để thấy logic thật sự còn nguyên, đây là kết quả đọc `co_consts` của `secretapp.pyc` trích ra ở trên (chưa cần decompiler hoàn chỉnh, chỉ marshal-load rồi duyệt hằng số):

```
 [hàm] check
  const: 'PyInst@ller_2024'
 [hàm] main
  const: 'License key: '
  const: 'Licensed!'
  const: 'Wrong key.'
```

License key `PyInst@ller_2024` nằm trần trụi trong hằng số của hàm `check`. Không mã hoá, không gì cả. Đây là lý do đóng gói Python thành exe gần như không bảo vệ được secret: nó chỉ giấu, không khoá. Muốn khoá thật phải dùng những thứ như PyArmor hoặc Nuitka (Bài 7.5).

## py2exe và cx_Freeze

Hai công cụ cũ hơn, nguyên lý giống nhau.

- **py2exe**: nhét `.pyc` vào resource hoặc một file `library.zip` cạnh exe. Dùng `unpy2exe`, hoặc nhiều khi chỉ cần giải nén `library.zip` bằng tool zip thường rồi decompile.
- **cx_Freeze**: thường để `.pyc` trong `library.zip` hoặc thư mục `lib/`. Giải nén zip rồi decompile.

Cả hai đều không chống reverse: tìm `.pyc`, vá header nếu cần, decompile.

## Quy trình gọn

1. Triage: `strings`/DIE thấy `_MEIPASS`, `pyi`, `python3xx` là PyInstaller. Thấy `library.zip` cạnh exe là py2exe/cx_Freeze.
2. Trích: `pyinstxtractor(-ng)` cho PyInstaller, giải nén zip cho hai cái kia. Ghi lại **phiên bản Python** mà tool báo.
3. Tìm đúng file: bỏ qua `pyi*`, lấy file entry point mang tên script gốc.
4. Vá magic header nếu `.pyc` thiếu (chép từ một module chuẩn cùng thư mục).
5. Decompile bằng pycdc (Bài 7.2), hoặc decompiler hợp phiên bản (Bài 7.3).

## Lab tự làm

Thư mục [labs/7.4/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/7.4) có hướng dẫn dựng một PyInstaller exe từ một script nhỏ rồi tự trích ngược lại, kèm cách xử lý magic header. Toàn bộ quy trình trong bài này đã được chạy thật trên PyInstaller 6.20 / Python 3.11, output trong [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/7.4/solution.md) là thật.

## Checklist ghi nhớ
- PyInstaller gói interpreter + `.pyc` nén vào exe, logic vẫn là bytecode Python.
- Nhận ra bằng `_MEIPASS`, `pyi`, `python3xx` trong strings.
- `pyinstxtractor(-ng)` trích ra, đọc dòng Python version và Possible entry point.
- Bỏ qua các `.pyc` tên `pyi*`, lấy file mang tên script gốc.
- `.pyc` trích ra có thể thiếu magic header, chép từ một `.pyc` lành lặn vào đầu để vá.
- py2exe/cx_Freeze thường để `.pyc` trong `library.zip`, giải nén rồi decompile.
- Đóng gói không phải mã hoá: secret trong code lộ ra hết.
