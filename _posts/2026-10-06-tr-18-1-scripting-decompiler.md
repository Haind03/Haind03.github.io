---
title: "Bài 18.1: Scripting decompiler, để máy làm việc nhàm chán"
date: 2026-10-06 09:47:00 +0700
categories: ["Technique Reverse", "Phần 18 · Nâng cao"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
Có những việc trong reverse lặp đi lặp lại đến phát chán: giải cùng một kiểu mã hoá chuỗi cho ba trăm chuỗi, đổi tên hàng loạt hàm theo một quy luật, đánh dấu mọi lời gọi tới một API. Làm tay thì vừa lâu vừa dễ sai. Đây là lúc bạn viết script để decompiler tự làm. Biết scripting là ranh giới giữa người dùng công cụ và người điều khiển công cụ.

Ba nền tảng lớn đều có API: IDA có IDAPython, Ghidra có scripting Java/Python, Binary Ninja có API Python. Ý tưởng giống nhau, chỉ khác cú pháp. Bài này tập trung IDAPython vì nó phổ biến nhất, rồi điểm qua hai cái kia.

## Khi nào thì đáng viết script

Đừng script mọi thứ. Quy tắc thực dụng: nếu một thao tác bạn sắp làm hơn chục lần giống nhau, hoặc một phép biến đổi áp cho nhiều vị trí, thì script. Vài trường hợp kinh điển:

- Giải chuỗi bị mã hoá (string decryption) hàng loạt rồi đặt comment ngay cạnh.
- Đổi tên hàm theo pattern (ví dụ mọi hàm gọi `print_error` với một mã lỗi cố định).
- Tìm tất cả vị trí gọi một API đáng ngờ và liệt kê tham số.
- Đánh dấu hằng số crypto, patch hàng loạt, trích bảng dữ liệu.

Nếu chỉ làm một hai lần thì làm tay nhanh hơn viết script.

## IDAPython: ba nhóm hàm cần nhớ

IDAPython gói thành vài module. Ba thứ dùng nhiều nhất:

- `idautils`: các iterator tiện lợi (`Functions()` duyệt mọi hàm, `XrefsTo(ea)` liệt kê xref).
- `idc`: các hàm kiểu script cũ (đọc/ghi byte, đặt comment, đổi tên), dễ dùng.
- `idaapi` / `ida_*`: API cấp thấp đầy đủ.

Vài thao tác nền tảng:

```python
import idautils, idc, ida_bytes, ida_name

# duyệt mọi hàm và in tên
for ea in idautils.Functions():
    print(hex(ea), idc.get_func_name(ea))

# đọc n byte tại địa chỉ
data = ida_bytes.get_bytes(ea, n)

# đặt comment lặp lại (repeatable) tại địa chỉ
idc.set_cmt(ea, "chuoi da giai: hello", 1)

# đổi tên một địa chỉ
ida_name.set_name(ea, "decrypt_string", ida_name.SN_CHECK)

# tìm mọi nơi gọi tới một hàm
for xref in idautils.XrefsTo(target_ea):
    print(hex(xref.frm))
```

Nhìn thì nhiều tên hàm, nhưng bạn chỉ cần thuộc vài cái: duyệt, đọc byte, đặt comment, đổi tên, lấy xref. Phần còn lại tra khi cần.

## Ví dụ thực chiến: giải chuỗi XOR hàng loạt

Giả sử bạn đã reverse ra một binary mã hoá mọi chuỗi bằng XOR một byte key `0x5A`, và các chuỗi mã hoá nằm trong một section dữ liệu. Làm tay ba trăm chuỗi thì nghỉ việc. Script thì ba chục giây:

```python
import idautils, idc, ida_bytes

KEY = 0x5A

def xor_decrypt(data, key):
    return bytes(b ^ key for b in data)

# giả sử mỗi chuỗi mã hoá được tham chiếu qua lời gọi decrypt_string(ptr, len)
# ta tìm mọi xref tới hàm decrypt_string rồi đọc tham số
decrypt_ea = idc.get_name_ea_simple("decrypt_string")

for xref in idautils.XrefsTo(decrypt_ea):
    call_ea = xref.frm
    # (tuỳ binary) lần ngược lên để lấy con trỏ và độ dài truyền vào
    # ở đây minh hoạ: giả sử đã biết ptr và length
    ptr = idc.get_operand_value(idc.prev_head(call_ea), 1)
    length = 16
    enc = ida_bytes.get_bytes(ptr, length)
    if enc:
        dec = xor_decrypt(enc, KEY).split(b"\x00")[0].decode("latin1")
        # đặt comment ngay tại chỗ gọi, để đọc pseudocode thấy liền
        idc.set_cmt(call_ea, f"str: {dec}", 1)
        print(hex(call_ea), dec)
```

Điểm hay không phải đoạn code cụ thể (mỗi binary một khác), mà là khuôn tư duy: **tìm mỏ neo (hàm decrypt, hằng số, pattern byte), duyệt mọi vị trí, áp phép biến đổi, ghi kết quả trở lại dưới dạng comment hoặc tên.** Sau khi chạy, mở lại pseudocode thì mọi lời gọi đã có chú thích chuỗi thật, đọc như đọc source.

## Tìm pattern byte

Nhiều khi bạn cần tìm một dãy byte (ví dụ prologue của một loại hàm, hoặc một hằng số crypto):

```python
import ida_search, ida_bytes

# tìm chuỗi byte "48 8B 05" bắt đầu từ đầu chương trình
ea = ida_bytes.find_bytes("48 8B 05", idc.get_inf_attr(idc.INF_MIN_EA))
while ea != idc.BADADDR:
    print(hex(ea))
    ea = ida_bytes.find_bytes("48 8B 05", ea + 1)
```

## Ghidra scripting

Ghidra cho viết script bằng Java hoặc Python (Jython). API trung tâm là `FlatProgramAPI` (các hàm `getFunctionManager`, `getInstructionAt`, `setComment`, `createLabel`). Ví dụ Python trong Ghidra:

```python
# Ghidra Python (Jython)
fm = currentProgram.getFunctionManager()
for func in fm.getFunctions(True):
    print(func.getName(), func.getEntryPoint())
```

Thứ khiến Ghidra mạnh cho tự động hoá là **headless analyzer**: chạy phân tích và script từ dòng lệnh, không mở GUI, hợp để xử lý hàng loạt binary:

```
analyzeHeadless /path/to/project MyProject -import target.exe -postScript MyScript.py
```

Dùng headless khi bạn có một trăm mẫu malware cần trích cùng một thứ (ví dụ config, IOC). Viết một script, chạy batch, xong.

## Binary Ninja API

Binary Ninja có API Python được khen là sạch nhất, và truy cập được các tầng IL (BNIL: LLIL, MLIL, HLIL). Ví dụ:

```python
# Binary Ninja
import binaryninja as bn
with bn.load("target.exe") as bv:
    for func in bv.functions:
        print(func.name, hex(func.start))
```

Làm việc trên IL thay vì raw assembly giúp viết các phân tích độc lập kiến trúc (cùng một script chạy cho x86 lẫn ARM), rất hợp cho deobfuscation tự động.

## Chọn cái nào

Không có câu trả lời duy nhất. Thực tế: nếu bạn sống trong IDA thì IDAPython; cần miễn phí và batch thì Ghidra headless; cần phân tích trên IL đẹp và độc lập kiến trúc thì Binary Ninja. Ba cái không loại trừ nhau, nhiều người dùng cả ba tuỳ việc.

## Lab tự làm

Xem [labs/18.1/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/18.1). Nhiệm vụ: viết một script giải chuỗi tự động cho một binary có chuỗi bị XOR, đặt comment kết quả vào từng vị trí. File `src/` có script IDAPython và Ghidra mẫu để bạn tham khảo và sửa cho binary của mình.

## Checklist ghi nhớ

- Script khi một thao tác lặp lại hơn chục lần hoặc áp cho nhiều vị trí, còn không thì làm tay.
- IDAPython: thuộc năm thao tác là đủ: duyệt hàm, đọc byte, đặt comment, đổi tên, lấy xref.
- Khuôn deobfuscation tự động: tìm mỏ neo, duyệt mọi vị trí, áp biến đổi, ghi kết quả trở lại.
- Ghidra headless để xử lý hàng loạt binary mà không mở GUI.
- Binary Ninja API làm việc trên BNIL nên script độc lập kiến trúc.

---
Phần trước: [17.7 DBI](/posts/tr-17-7-dbi-pin-dynamorio-tinyinst/) · [Về mục lục](/technique-reverse/) · Bài tiếp: 18.2 Emulation (Unicorn, Qiling, Speakeasy)
