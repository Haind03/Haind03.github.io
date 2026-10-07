---
title: "Bài 15.3: Anti-debug nhóm 3, timing và trap"
date: 2026-10-06 09:28:00 +0700
categories: ["Technique Reverse", "Phần 15 · Anti-Reverse chuyên sâu và cách vượt qua"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
Hai nhóm trước (API và PEB) dựa vào việc hỏi hệ điều hành "tôi có đang bị debug không". Nhóm này tinh ranh hơn: nó không hỏi ai cả, mà tự suy ra từ hai thứ debugger không giấu được. Một là thời gian: debugger làm chương trình chạy chậm đi hàng nghìn lần khi bạn step. Hai là exception: debugger phải chen vào giữa chương trình và cơ chế xử lý ngoại lệ, và sự chen đó để lại dấu.

Hiểu nhóm này quan trọng vì nó không có một lời gọi API gọn gàng để bạn đặt breakpoint, nên ScyllaHide cũng không phải lúc nào cũng lo hết.

## Timing: debugger làm thời gian giãn ra

Ý tưởng đơn giản đến mức đẹp. Một đoạn code bình thường chạy hết trong vài trăm chu kỳ CPU. Nếu bạn đang single-step qua nó trong debugger, mỗi lệnh tốn hàng triệu chu kỳ (vì debugger dừng lại, cập nhật UI, chờ bạn bấm). Chương trình chỉ cần đo thời gian hai mốc rồi so: chênh lệch mà lớn bất thường thì chắc chắn có người đang theo dõi.

### RDTSC, đồng hồ bấm giây của CPU

Lệnh `rdtsc` (Read Time-Stamp Counter) trả về số chu kỳ CPU đã trôi qua kể từ khi khởi động, kết quả nằm ở cặp `edx:eax` (edx là 32 bit cao, eax là 32 bit thấp). Pattern kinh điển:

```asm
rdtsc                 ; đọc mốc thời gian 1
mov   rsi, rax        ; cất lại (eax = phần thấp)
; ... đoạn code cần đo, thường ngắn ...
rdtsc                 ; đọc mốc thời gian 2
sub   rax, rsi        ; rax = chênh lệch chu kỳ
cmp   rax, 10000h     ; so với một ngưỡng
ja    debugger_found  ; chênh quá lớn, đang bị step
```

Dịch ra ý: "đo xem đoạn giữa chạy mất bao nhiêu chu kỳ, nếu vượt ngưỡng thì báo động". Thấy hai lệnh `rdtsc` cách nhau một đoạn ngắn rồi `sub` và `cmp` là gần như chắc chắn đây là timing check.

### Các biến thể qua API

Không phải chỗ nào cũng dùng `rdtsc`. Cùng ý tưởng nhưng đo bằng API:

- `QueryPerformanceCounter` cho bộ đếm độ phân giải cao.
- `GetTickCount` / `GetTickCount64` đếm mili giây từ lúc boot.
- `timeGetTime`, hoặc hàm `time()` của C cho mốc thô hơn.

Pattern vẫn là: gọi lấy mốc, chạy một đoạn, gọi lấy mốc lần hai, trừ, so ngưỡng. Với các API này thì bạn lại có chỗ để đặt breakpoint.

### Cách vượt timing check

Điểm yếu của timing check là nó chỉ là một phép `cmp` rồi nhảy. Vài cách xử lý:

- **Patch nhánh nhảy.** Tìm `ja debugger_found` (hay `jg`, `jb` tùy cài đặt) rồi đảo điều kiện hoặc nop nó đi. Đây là cách sạch nhất: không cần quan tâm giá trị thời gian, chỉ cần luồng không rẽ vào nhánh báo động.
- **Làm giả giá trị trả về.** Sau lệnh `rdtsc` hoặc lời gọi `GetTickCount` thứ hai, sửa `rax` cho chênh lệch nhỏ lại.
- **ScyllaHide** có tùy chọn xử lý một số timing check (ví dụ bình thường hoá `rdtsc`, hook GetTickCount), nhưng không phủ hết mọi biến thể tự chế, nên patch tay vẫn là vũ khí chắc chắn.

Một mẹo thực dụng: đừng step qua đoạn giữa hai mốc. Đặt breakpoint sau lần đo thứ hai rồi cho chạy thẳng (F9) tới đó, như vậy đoạn giữa chạy ở tốc độ thật và chênh lệch không bị thổi phồng.

## Trap: ném exception rồi xem ai bắt

Nhóm thứ hai lợi dụng cách Windows (và debugger) xử lý ngoại lệ. Bình thường, nếu chương trình gây ra một exception, hệ điều hành giao nó cho handler của chương trình (SEH/VEH, xem Bài 1.12). Nhưng khi có debugger, debugger được quyền nhìn exception trước. Nếu debugger "nuốt" mất exception thay vì trả lại cho chương trình, chương trình biết có người can thiệp.

### INT 3, con dao hai lưỡi

Byte `0xCC` là lệnh `int 3`, chính là breakpoint phần mềm mà mọi debugger dùng. Chiêu anti-debug: chương trình **tự** đặt một `int 3` kèm một exception handler riêng.

```asm
    ; cài SEH/VEH trỏ tới handler của mình trước đó
    int 3                 ; cố tình gây breakpoint
    ; nếu chạy TỚI đây nghĩa là handler KHÔNG được gọi
    ; -> debugger đã nuốt mất int 3 -> bị debug
    jmp debugger_found
handler:
    ; không có debugger: handler của chính mình bắt được
    ; -> chạy tiếp bình thường
```

Logic đảo ngược so với trực giác: nếu **handler của chương trình chạy**, nghĩa là không bị debug (chương trình tự bắt được breakpoint của mình). Nếu luồng chạy **thẳng qua** `int 3` mà handler không được gọi, nghĩa là debugger đã chặn breakpoint lại, tức là đang bị debug.

### INT 2D và ICEBP (0xF1)

Hai anh em ít người biết nhưng rất hay bị dùng vì gây rối cho debugger:

- `int 2d`: một kiểu kernel breakpoint. Khi chạy dưới debugger, nó làm lệch con trỏ lệnh một byte theo cách khó lường, và cách debugger xử lý khác với khi chạy tự do.
- `icebp` (opcode `0xF1`, còn gọi int 1): sinh single-step exception. Nhiều debugger xử lý sai, lộ sự hiện diện.

Thấy các opcode lạ `0xCD 0x2D`, `0xF1` nằm giữa luồng code bình thường là nên nghi ngờ đây là trap anti-debug chứ không phải code thật.

### Hardware breakpoint detection qua DR0-DR7

Hardware breakpoint của bạn nằm trong các debug register DR0 tới DR3 (địa chỉ) và DR7 (bật/tắt). Chương trình có thể tự đọc chúng để phát hiện: gọi `GetThreadContext` với cờ `CONTEXT_DEBUG_REGISTERS`, rồi kiểm xem DR0-DR3 có khác 0 không hoặc DR7 có bit nào bật không. Nếu có, ai đó đã đặt hardware breakpoint.

```asm
    ; CONTEXT.Dr0 .. Dr3 khác 0  hoặc  Dr7 != 0
    ; -> có hardware breakpoint -> đang bị phân tích
```

### Single-step detection qua trap flag

Trap flag (TF) trong thanh ghi cờ, khi bật, làm CPU sinh exception sau mỗi lệnh (đây chính là cơ chế single-step). Một số chiêu tự bật TF rồi kiểm xem exception có tới đúng như mong đợi không, hoặc đẩy giá trị flag lên stack (`pushfd`) rồi soi bit TF.

### Cách vượt nhóm trap

- **Với INT 3 / INT 2D / ICEBP**: trong x64dbg, cấu hình để truyền (pass) exception về cho chương trình thay vì tự nuốt. Vào Options > Exceptions, thêm các mã exception liên quan vào danh sách bỏ qua (ignore), để handler của chương trình nhận được như khi chạy tự do. Hoặc patch thẳng lệnh trap thành `nop`.
- **Với hardware breakpoint detection**: đừng dùng hardware breakpoint, dùng software breakpoint thay thế. Hoặc ScyllaHide/TitanHide che DR khỏi `GetThreadContext`.
- **Với trap flag**: thường cũng quy về patch nhánh so sánh kết quả.

Nguyên tắc chung cho cả nhóm 3: đừng cố chống lại từng phép đo, hãy tìm điểm cuối cùng nơi mọi check quy về một lệnh nhảy quyết định "có bị debug hay không", rồi vô hiệu hoá lệnh nhảy đó. Nhiều lớp đo lường phức tạp thường cùng đổ về một hoặc hai nhánh.

## Lab tự làm

Mã nguồn ở `labs/15.3/`. Nhiệm vụ: build `timing_check.c`, chạy tự do thấy nó báo "no debugger", chạy dưới x64dbg và single-step qua đoạn đo để thấy nó chuyển sang "debugger detected", rồi vượt bằng hai cách (chạy thẳng không step, và patch nhánh nhảy). Hướng dẫn trong `labs/15.3/README.md`, lời giải ở `labs/15.3/solution.md`.

## Checklist ghi nhớ
- Nhóm 3 không hỏi OS, mà tự suy ra từ thời gian và exception, nên khó hook hơn nhóm API.
- Hai `rdtsc` cách nhau một đoạn ngắn rồi `sub` + `cmp` + nhảy = timing check. Cách tương đương qua GetTickCount/QueryPerformanceCounter.
- Vượt timing: đừng step qua đoạn đo (chạy thẳng tới sau mốc 2), hoặc patch nhánh nhảy, hoặc làm giả giá trị.
- Trap: tự đặt int 3 / int 2d / icebp rồi xem debugger có nuốt exception không. Logic thường đảo ngược: handler chạy nghĩa là không bị debug.
- Vượt trap: cấu hình debugger pass exception về cho chương trình, hoặc nop lệnh trap.
- Hardware breakpoint bị dò qua DR0-DR7: chuyển sang software breakpoint, hoặc dùng ScyllaHide/TitanHide che debug register.
- Mẹo tổng: tìm lệnh nhảy quyết định cuối cùng và vô hiệu hoá nó thay vì đấu với từng phép đo.
