---
title: "Bài 13.4: Lua và LuaJIT bytecode, mổ script trong game"
date: 2026-10-06 09:18:00 +0700
categories: ["Technique Reverse", "Phần 13 · Game: Unity, Unreal, Lua"]
tags: [reverse-engineering, game-hacking]
render_with_liquid: false
---
Rất nhiều game không viết logic gameplay bằng C++ mà bằng Lua, vì Lua nhẹ, nhúng dễ, và sửa được mà không phải build lại cả engine. Roblox, Garry's Mod, World of Warcraft (addon), và một rừng game mobile đều chạy script Lua. Với người reverse, đây là tin tốt: Lua giữ gần hết thông tin, decompile ra lại gần như source. Tin xấu: có tới hai dòng Lua khác nhau (Lua chuẩn và LuaJIT), bytecode đổi theo phiên bản, và game hay mã hoá script để làm khó bạn. Bài này gỡ từng khúc đó.

## Lua chạy bằng bytecode, giống Python

Khi bạn viết một file `.lua`, trình thông dịch không chạy thẳng text. Nó biên dịch sang bytecode trước rồi mới chạy trên máy ảo Lua (register-based, khác CPython stack-based). Phần lớn thời gian game nhúng luôn text `.lua` nên bạn đọc được ngay, nhưng khi tác giả muốn giấu, họ phân phối dạng bytecode đã biên dịch (bằng `luac`, Lua compiler). Lúc đó bạn cần decompiler.

Điểm mấu chốt phải nhớ ngay: **có hai hệ bytecode hoàn toàn khác nhau.**

- **Lua chuẩn** (lua.org): bytecode do `luac` sinh. Decompile bằng `unluac` (Java, tốt nhất hiện nay) hoặc `luadec`.
- **LuaJIT**: một implementation riêng, nhanh hơn, bytecode KHÔNG tương thích với Lua chuẩn. Phải dùng decompiler riêng: `luajit-decompiler`, `ljd`, hoặc bản `luajit-decompiler-v2`.

Chọn nhầm nhánh là decompiler báo lỗi ngay từ byte đầu. Nên bước số một luôn là nhận diện.

## Nhận diện: đọc magic và phiên bản

Mở file bytecode bằng hex editor, nhìn vài byte đầu.

**Lua chuẩn** mở đầu bằng magic `1B 4C 75 61`, tức `\x1bLua`. Byte thứ 5 là số phiên bản dạng hex: `51` = Lua 5.1, `52` = 5.2, `53` = 5.3, `54` = 5.4. Đây là thứ quyết định bạn dùng decompiler nào, vì bytecode mỗi phiên bản khác nhau.

```
1B 4C 75 61 54 00 19 93 0D 0A 1A 0A ...
\x1b L  u  a  |  phiên bản 0x54 = Lua 5.4
```

**LuaJIT** mở đầu bằng magic `1B 4C 4A`, tức `\x1bLJ`, rồi một byte phiên bản bytecode (`01`, `02`...). Thấy `LJ` là biết ngay phải rẽ sang nhánh ljd, đừng phí thời gian với unluac.

Nếu không thấy magic nào mà file lại trông như rác có entropy cao, nhiều khả năng script đã bị mã hoá (xem phần cuối).

## Decompile Lua chuẩn với unluac

Quy trình gọn khi đã biết là Lua chuẩn:

```
# biên dịch (nếu bạn tự tạo mẫu để học)
luac -o script.luac script.lua

# decompile ngược
java -jar unluac.jar script.luac > script_decompiled.lua
```

unluac trả lại code rất gần bản gốc: giữ tên biến cục bộ (nếu bytecode chưa strip debug info), tên hàm, hằng số chuỗi, cấu trúc if/for/while. Nếu bytecode bị strip (`luac -s`), tên biến cục bộ mất, bạn nhận được `A0_1`, `L1_2`... nhưng logic vẫn đầy đủ, vẫn đọc hiểu được.

`luadec` là lựa chọn thay thế, cũ hơn, hỗ trợ tốt Lua 5.1 nhưng đuối với các phiên bản mới. Gặp Lua 5.1 mà unluac trục trặc thì thử luadec.

## Decompile LuaJIT với ljd

LuaJIT cứng đầu hơn. `ljd` (và bản viết lại `luajit-decompiler-v2`) là công cụ chính:

```
python3 ljd/main.py -f script_ljbc.luac
```

Chất lượng output thường kém hơn unluac với Lua chuẩn: một số cấu trúc điều khiển phức tạp có thể ra không sạch, phải đọc kèm bytecode dạng disassembly để hiểu. Nhưng với script gameplay thông thường thì đủ dùng.

## Cấu trúc cần biết khi đọc

Vài thứ đặc trưng Lua sẽ gặp trong code decompiled:

- **table** là kiểu dữ liệu trung tâm của Lua, vừa làm array vừa làm dictionary vừa làm object (qua metatable). Thấy `t[1]`, `t.field`, `t:method()` đều là table.
- **string** trong Lua được intern và lưu trong constant pool của mỗi function prototype, nên tên hàm API, key, thông báo lộ ra khá nhiều. Đi từ chuỗi tới chỗ dùng là chiến thuật quen thuộc, giống mọi phần trước.
- **`t:method(a)`** chỉ là đường tắt cú pháp của `t.method(t, a)`, tức self là tham số đầu ẩn, tương tự `this`.

## Tìm script Lua trong game

Trước khi decompile, phải lấy được bytecode ra đã. Vài nơi hay nằm:

- Thư mục game: file `.lua`, `.luac`, `.lc`, hoặc trong archive riêng (`.pak`, `.rbxl`, asset bundle). Dùng `strings` và tìm magic `\x1bLua` / `\x1bLJ` để định vị khối bytecode ngay cả khi nó nhúng trong file lớn.
- Nhúng trong binary native: grep magic trong chính exe/so.
- Giải nén archive của game bằng tool tương ứng rồi quét.

## Khi script bị mã hoá

Nhiều game không để bytecode trần mà mã hoá (XOR, custom cipher) rồi giải trong bộ nhớ ngay trước khi nạp vào máy ảo Lua. Lúc đó decompile file trên đĩa vô ích. Hướng tiếp cận:

- **Dump từ runtime.** Để game tự giải mã rồi lấy bytecode đã giải ra khỏi bộ nhớ. Hook hàm nạp script (ví dụ `luaL_loadbuffer`, `lua_load`, `luaL_loadbufferx`) bằng Frida, in ra buffer tại thời điểm nó đã là bytecode sạch. Đây đúng tinh thần unpack động ở Phần 14.
- **Khoá nằm trong binary.** Nếu cipher đơn giản, tìm hàm giải mã trong native code, lấy khoá, giải offline.

Nguyên tắc chung giống mọi loại packer: tìm chỗ dữ liệu đã ở dạng sạch nhất rồi chộp tại đó, thay vì vật lộn với lớp mã hoá.

## Lab tự làm

Xem [labs/13.4/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/13.4). Nhiệm vụ: biên dịch một script Lua bằng `luac`, nhận diện magic và phiên bản trong hex, rồi decompile lại bằng `unluac` và so với bản gốc. Lời giải ở [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/13.4/solution.md).

## Checklist ghi nhớ
- Lua nhúng thường là text đọc thẳng được; chỉ khi dạng bytecode mới cần decompiler.
- Hai hệ khác nhau: Lua chuẩn (magic `\x1bLua`, dùng unluac/luadec) và LuaJIT (magic `\x1bLJ`, dùng ljd). Nhận diện trước.
- Byte phiên bản sau magic (`51`/`52`/`53`/`54`) quyết định decompiler.
- Bytecode strip chỉ mất tên biến cục bộ, logic vẫn còn.
- Script mã hoá thì dump từ runtime: hook `luaL_loadbuffer`/`lua_load` bằng Frida lấy bytecode sạch.
- table là trung tâm của Lua; `t:method()` có self là tham số ẩn đầu tiên.
