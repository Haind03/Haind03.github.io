---
title: "Bài 18.3: Symbolic execution, bắt máy tính tự giải crackme cho bạn"
date: 2026-10-06 09:49:00 +0700
categories: ["Technique Reverse", "Phần 18 · Nâng cao"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
Ở [bài 16.4](/posts/tr-16-4-viet-lai-python-z3/) bạn viết constraint bằng tay rồi thả cho Z3 giải. Nhưng viết constraint tay nghĩa là phải đọc hiểu từng phép so sánh trong binary, chép lại không sai một dấu. Với một hàm check dài vài chục nhánh, việc đó mệt và dễ lỗi. Symbolic execution làm hộ bạn khâu chép đó: nó tự chạy binary với input là biến ký hiệu, tự thu thập constraint dọc đường, rồi gọi solver. Bạn chỉ cần nói "tìm đường tới chỗ in Correct".

## Ý tưởng cốt lõi

Chạy bình thường thì input là giá trị cụ thể, ví dụ `s[0] = 0x41`. Symbolic execution thay nó bằng một biến ký hiệu (symbol), gọi là `c0`. Khi gặp lệnh `s[0] ^ 0x41`, máy không tính ra số mà ghi lại biểu thức `c0 ^ 0x41`. Khi gặp nhánh `if (... == 0)`, nó tách làm hai đường: một đường thêm constraint `c0 ^ 0x41 == 0`, đường kia thêm `c0 ^ 0x41 != 0`, rồi đi tiếp cả hai.

Cứ thế, mỗi đường thực thi tích luỹ một tập constraint. Tới đích (chỗ in "Correct"), ta có đủ ràng buộc mô tả "input nào dẫn tới đây", đưa cho SMT solver là ra input cụ thể. Bạn không đọc logic, không chép constraint, chỉ chỉ đích và chỉ chỗ cần tránh.

Thuật ngữ:
- **Symbolic execution**: chạy với biến ký hiệu, khám phá đường bằng cách tách nhánh.
- **Concolic** (concrete + symbolic): vừa chạy với giá trị thật vừa theo dõi ký hiệu, cân bằng giữa chính xác và tốc độ. Triton theo hướng này.
- **Path explosion**: số đường tăng theo cấp số mũ với số nhánh, đây là tử huyệt của phương pháp.

## angr, con dao chủ lực

**angr** là framework Python mở, phổ biến nhất cho symbolic execution trên binary. Khung làm việc luôn gồm bốn thứ:

1. **Project**: nạp binary.
2. **State**: trạng thái ban đầu (register, memory, input ký hiệu).
3. **Simulation manager** (`simgr`): bộ máy đẩy các state đi tới, phân loại found/active/deadended.
4. **explore(find=..., avoid=...)**: nói đích cần tới và chỗ cần tránh.

Ví dụ giải một crackme nhận serial qua `argv[1]`:

```python
import angr, claripy

proj = angr.Project("./crackme", auto_load_libs=False)

# 8 byte serial, mỗi byte một BitVec 8-bit
chars  = [claripy.BVS(f"c{i}", 8) for i in range(8)]
serial = claripy.Concat(*chars)

state = proj.factory.full_init_state(args=["./crackme", serial])
for c in chars:                       # ép ký tự in được cho gọn
    state.solver.add(c >= 0x20, c <= 0x7e)

simgr = proj.factory.simulation_manager(state)
simgr.explore(
    find =lambda s: b"Correct" in s.posix.dumps(1),   # tới chỗ in Correct
    avoid=lambda s: b"Nope"    in s.posix.dumps(1),    # tránh chỗ in Nope
)

found = simgr.found[0]
print(found.solver.eval(serial, cast_to=bytes))
```

`find` và `avoid` nhận stdout của tiến trình mô phỏng (`posix.dumps(1)` là file descriptor 1). Thay vì chỉ địa chỉ tay, ta để angr tự chạy tới khi stdout chứa "Correct". Chạy xong, `found.solver.eval` hỏi solver "serial nào thoả mọi constraint trên đường này" và trả về bytes.

Chạy trên crackme của lab này, angr in ra đúng serial trong vài giây mà ta không hề đọc hàm `check`.

## Triton và các lựa chọn khác

- **Triton** (Quarkslab): thiên về concolic và tích hợp DBI (nối [bài 17.7](/posts/tr-17-7-dbi-pin-dynamorio-tinyinst/)). Mạnh khi bạn muốn trace một đường thực thi thật rồi suy ký hiệu dọc theo nó, tránh path explosion.
- **Miasm**, **maat**, **manticore**: các framework khác, mỗi cái một thế mạnh.
- Dưới đáy tất cả vẫn là một SMT solver (thường là Z3).

## Khi nào dùng angr, khi nào quay về Z3 tay

angr thắng khi: logic check nhiều nhánh nhưng mỗi nhánh đơn giản, bạn lười đọc, và không gian input vừa phải. Nó tự lo khâu dịch binary sang constraint.

angr thua (và Z3 tay hoặc cách khác thắng) khi:
- **Path explosion**: vòng lặp lớn, nhiều nhánh lồng nhau làm số đường bùng nổ. Lúc này giới hạn vùng khám phá, hoặc chỉ symbolic hoá đúng hàm check (dùng `call_state` gọi thẳng hàm thay vì chạy từ main).
- **Crypto nặng hoặc hash một chiều**: băm MD5/SHA, AES nhiều vòng tạo constraint khổng lồ mà solver không kham. Với hash một chiều thì về lý thuyết không giải được bằng solver, phải brute hoặc tìm hướng khác (nối [bài 16.4](/posts/tr-16-4-viet-lai-python-z3/)).
- **Syscall/môi trường phức tạp**: angr phải mô phỏng được những gì chương trình gọi; thiếu hook thì lạc.

Quy tắc thực dụng: thử angr trước vì rẻ công, nếu nó treo hoặc bùng nổ thì thu hẹp phạm vi, không được nữa thì đọc tay và viết Z3.

## Lab tự làm

Thư mục [labs/18.3/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/18.3). `src/crackme.c` kiểm serial 8 ký tự qua một chuỗi ràng buộc trên các byte. Nhiệm vụ: build, rồi để `solve_angr.py` tự tìm serial, không đọc hàm `check`. So kết quả với cách đọc tay. Lời giải và serial đúng ở `solution.md` (serial này đã được angr thật tìm ra, xem writeup).

## Checklist ghi nhớ
- Symbolic execution thay input bằng biến ký hiệu, tách nhánh để khám phá, rồi dùng SMT solver tìm input tới đích.
- angr: Project, State (input ký hiệu bằng `claripy.BVS`), simulation manager, `explore(find=, avoid=)`.
- `find`/`avoid` có thể bắt theo stdout, không cần địa chỉ tay.
- Tử huyệt là path explosion và crypto/hash nặng; khi đó thu hẹp phạm vi hoặc quay về Z3 tay.
- Thử angr trước vì rẻ công, không được thì đọc tay.
