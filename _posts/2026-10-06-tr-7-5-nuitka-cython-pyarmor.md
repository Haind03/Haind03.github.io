---
title: "Bài 7.5: Khi Python không còn là .pyc dễ nuốt"
date: 2026-10-06 08:57:00 +0700
categories: ["Technique Reverse", "Phần 7 · Python (pycdc)"]
tags: [reverse-engineering, python]
render_with_liquid: false
---
Mấy bài trước cho bạn cảm giác Python là mồi ngon: kéo .pyc vào pycdc là gần như có lại source. Đúng, nhưng chỉ đúng khi tác giả để nguyên bytecode. Một khi họ dùng Nuitka, Cython hay PyArmor, bữa tiệc kết thúc. pycdc trả về rỗng, uncompyle6 báo lỗi, và bạn nhận ra mình không còn đang reverse Python nữa.

Đây là bước ngoặt giống hệt NativeAOT bên .NET (Bài 5.6): công cụ chuyên ngành vô dụng, phải lùi về reverse native bằng IDA/Ghidra, hoặc chuyển sang đánh runtime. Bài này dạy bạn nhận ra mình đang đối mặt với loại nào, vì chọn sai hướng là mất cả buổi.

## Ba kẻ phá đám, ba bản chất khác nhau

![Python đóng gói: PyInstaller dễ decompile, Nuitka/Cython/PyArmor khó](/assets/img/technique-reverse/assets/phan-07/python-packaging.svg)

Điều quan trọng nhất phải nắm: ba thứ này khác nhau về bản chất, nên cách xử lý cũng khác hẳn.

- **Nuitka** biên dịch Python sang C rồi biên dịch tiếp ra machine code native. Bytecode Python biến mất hoàn toàn.
- **Cython** cũng dịch Python (hoặc cú pháp Cython) sang C rồi ra một C extension (`.pyd` trên Windows, `.so` trên Linux). Native nốt.
- **PyArmor** thì khác: nó vẫn chạy bytecode Python, nhưng mã hoá và bọc lại, chỉ giải mã trong bộ nhớ lúc chạy. Bản chất vẫn là Python, chỉ bị khoá.

Nói cách khác: Nuitka và Cython đẩy bạn sang thế giới native. PyArmor giữ bạn trong thế giới Python nhưng dựng một bức tường.

## Nuitka: Python mặc áo C

Nuitka lấy chương trình Python của bạn, sinh ra code C gọi vào CPython API, rồi biên dịch thành exe (hoặc một thư mục chứa exe và DLL). Kết quả là một native binary thực thụ, không có co_code, không có PYZ archive, pycdc nhìn vào chịu chết.

Nhưng Nuitka không giấu được dấu vân tay của nó. Trong binary vẫn đầy lời gọi tới CPython runtime: những cái tên như `PyObject_`, `PyTuple_New`, `Py_INCREF`, `PyImport_`. Và quan trọng hơn, Nuitka nhúng một bảng module cùng rất nhiều chuỗi lộ tên hàm, tên biến, tên module Python gốc. Nghĩa là dù phải đọc assembly, bạn vẫn có nhiều mỏ neo hơn so với reverse một chương trình C thuần.

Chiến lược với Nuitka: coi như một binary C/C++. Mở bằng IDA/Ghidra, dựa vào các lời gọi CPython API để hiểu từng bước đang thao tác object Python gì. Ví dụ thấy `PyObject_RichCompare` ngay sau khi nạp input là đang so sánh, rất giống logic check password quen thuộc. Dùng lại mọi thứ đã học ở Phần 3 và 4.

## Cython: cùng một câu chuyện, gói nhỏ hơn

Cython thường không tạo ra cả một exe mà tạo một module đã biên dịch (`.pyd`/`.so`) được import từ một script Python mỏng. Phần code nhạy cảm nằm trong module native đó, phần còn lại có khi vẫn là .pyc đọc được.

Nhận ra Cython: trong module có các symbol kiểu `__pyx_`, `__Pyx_`, tên hàm wrapper như `__pyx_pf_...`. Cũng đầy CPython API như Nuitka. Chiến lược giống hệt: mở `.pyd`/`.so` bằng Ghidra/IDA, lần theo `__pyx_` và CPython API. Đừng phí thời gian tìm decompiler Python, không có đâu.

## PyArmor: vẫn là Python, nhưng bị khoá

PyArmor đi đường khác. Nó không biên dịch sang native. Nó mã hoá bytecode và thêm một lớp runtime (một module C đi kèm, hay thấy tên `pytransform` ở bản cũ hoặc `pyarmor_runtime` ở bản mới) để giải mã và nạp code trong bộ nhớ ngay trước khi chạy. Trên đĩa bạn chỉ thấy rác; code thật chỉ tồn tại trong RAM lúc thực thi.

Nhận ra PyArmor: script có dòng `from pytransform import pyarmor` hoặc `from pyarmor_runtime...`, kèm những blob dữ liệu mã hoá và một thư viện runtime gốc. pycdc dĩ nhiên bó tay.

Chiến lược với PyArmor xoay quanh một ý: **để chính nó giải mã rồi lấy từ bộ nhớ.** Vì cuối cùng CPython vẫn phải có code object để chạy, bạn có thể can thiệp ở tầng đó. Vài hướng:

- **Bản cũ (PyArmor 5/6):** cộng đồng từng có script unpack, hook vào `pytransform` để chặn code object sau khi giải mã. Tìm theo đúng phiên bản.
- **Bản mới (PyArmor 7/8+):** cứng hơn nhiều, có RFT mode và nhiều lớp. Hướng chung là hook hàm nạp code của CPython (ví dụ chặn `PyEval_EvalCodeEx`/`PyEval_EvalFrame` hoặc dùng một CPython đã vá để dump mọi code object được thực thi), rồi marshal các code object thu được ra .pyc để decompile.
- Việc này cần hiểu runtime và thường phải chạy mẫu, nên làm trong VM cô lập nếu nguồn gốc đáng ngờ (Bài 0.3).

## Nhận ra loại nào trong một phút

Trước khi đào, luôn triage để biết mình đang cầm gì. Quy trình nhanh:

1. Kéo vào **Detect It Easy** và chạy `strings`.
2. Tìm dấu hiệu:
   - Thấy `python3x.dll`/`libpython`, chuỗi `PyInstaller`, `MEI`, hoặc một archive PYZ: đây là **PyInstaller thường** (Bài 7.4), extract rồi decompile, dễ nhất.
   - Thấy nhiều `Py_`, `PyObject_`, kèm bảng chuỗi tên module Python nhưng không có PYZ: nghi **Nuitka**.
   - Thấy `__pyx_`, `__Pyx_` trong một `.pyd`/`.so`: **Cython**.
   - Thấy `pytransform`, `pyarmor_runtime`, blob mã hoá: **PyArmor**.
3. Chọn hướng theo bảng trong lab bên dưới.

Nhầm lẫn hay gặp: tưởng một binary Nuitka là PyInstaller rồi loay hoay tìm PYZ không có. Phân biệt nhanh: PyInstaller có archive gắn ở cuối file và bootloader để lại chuỗi rất đặc trưng; Nuitka thì không có archive, chỉ có native code và CPython API rải khắp.

## Vì sao đây là bước ngoặt

Toàn bộ Phần 7 tới giờ dạy bạn một kỹ năng hẹp: đọc và decompile Python bytecode. Nuitka và Cython xoá sạch kỹ năng đó và buộc bạn quay lại nền tảng native ở Phần 1 tới 4. Đó chính là lý do giáo trình xếp assembly và C/C++ lên trước: khi lớp vỏ ngôn ngữ bậc cao bị gỡ đi, bạn luôn rơi về native, và ai vững native thì không có đường cùng. PyArmor thì dạy một bài khác: khi code chỉ tồn tại trong bộ nhớ lúc chạy, câu trả lời nằm ở dynamic analysis chứ không phải static.

## Checklist ghi nhớ
- Nuitka và Cython biên dịch Python ra native, hết bytecode, phải dùng IDA/Ghidra như với C.
- Dấu vết để bám: CPython API (`Py_`, `PyObject_`) với Nuitka, `__pyx_`/`__Pyx_` với Cython.
- PyArmor vẫn là Python nhưng mã hoá bytecode, giải mã trong RAM lúc chạy. Hướng xử lý là dump code object từ bộ nhớ.
- Luôn triage bằng DIE và strings trước để biết đang gặp loại nào, đừng tìm nhầm PYZ trên một binary Nuitka.
- Khi lớp vỏ ngôn ngữ bị gỡ, bạn luôn rơi về native. Nền tảng Phần 1 tới 4 là cứu cánh.
