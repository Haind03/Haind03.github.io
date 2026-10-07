---
title: "Bài 15.2: Anti-debug đọc thẳng PEB, khi không có API để hook"
date: 2026-10-06 09:27:00 +0700
categories: ["Technique Reverse", "Phần 15 · Anti-Reverse chuyên sâu và cách vượt qua"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
Bài trước nói về anti-debug gọi API như IsDebuggerPresent. Điểm yếu của cách đó: đã là API thì bạn đặt breakpoint hoặc hook được, trả về giá trị giả là xong. Nên người viết protector khôn hơn sẽ bỏ qua API và đọc thẳng cấu trúc bộ nhớ mà API kia vốn chỉ đọc hộ. Không còn lời gọi nào để bạn chặn, chỉ là vài lệnh `mov` đọc bộ nhớ lẫn giữa code thường. Đây là nhóm anti-debug khó chịu hơn, và cũng là lý do bạn phải hiểu PEB từ [Bài 1.11](/posts/tr-1-11-windows-internals-2-peb-teb-handle-token/).

## PEB nằm ở đâu, và vì sao chương trình tự đọc được

PEB (Process Environment Block) là một struct Windows tạo cho mỗi tiến trình, chứa thông tin về tiến trình đó. IsDebuggerPresent thực chất chỉ là đọc một byte trong PEB rồi trả về. Nếu chương trình tự tìm tới PEB, nó có đúng thông tin đó mà không cần gọi ai.

PEB luôn truy cập được qua thanh ghi segment, không cần API:
- Trên x64: `gs:[0x60]` trỏ tới PEB.
- Trên x86: `fs:[0x30]` trỏ tới PEB.

Thấy một đoạn đọc `gs:[0x60]` (hoặc `fs:[0x30]`) là phải cảnh giác ngay: chương trình đang tự lấy PEB, và chín trên mười lần là để kiểm tra một cờ anti-debug.

## BeingDebugged, byte tố cáo

Trường đơn giản nhất là `PEB.BeingDebugged` ở offset `0x2`. Bằng 1 khi tiến trình đang bị debug, 0 khi không. Đây chính xác là thứ IsDebuggerPresent trả về.

Đoạn asm điển hình trên x64:

```asm
mov  rax, gs:[0x60]     ; rax = địa chỉ PEB
movzx eax, byte ptr [rax+2]  ; eax = PEB.BeingDebugged
test eax, eax
jnz  bi_phat_hien       ; khác 0 nghĩa là đang bị debug
```

Dịch ra C thì nó tương đương:

```c
if (((PEB*)__readgsqword(0x60))->BeingDebugged)
    thoat_hoac_pha();
```

Nhận diện: đọc `gs:[0x60]`, rồi đọc byte tại `[rax+2]`, rồi `test` và nhảy. Không có tên API nào xuất hiện, nên tìm theo tên hàm là trượt. Phải tìm theo pattern truy cập segment.

## NtGlobalFlag, dấu vết tinh vi hơn

`PEB.NtGlobalFlag` ở offset `0xBC` (x64) hoặc `0x68` (x86). Khi tiến trình được tạo dưới debugger, loader bật ba cờ trong trường này:

- `FLG_HEAP_ENABLE_TAIL_CHECK` (0x10)
- `FLG_HEAP_ENABLE_FREE_CHECK` (0x20)
- `FLG_HEAP_VALIDATE_PARAMETERS` (0x40)

Cộng lại là `0x70`. Nên kiểm tra thường thấy dạng:

```asm
mov  rax, gs:[0x60]
mov  eax, [rax+0xBC]    ; eax = NtGlobalFlag
and  eax, 0x70
cmp  eax, 0x70
jz   bi_phat_hien       ; cả ba cờ bật nghĩa là có debugger
```

Trường này tinh vi hơn BeingDebugged vì nhiều người mới không biết nó tồn tại, và nó bị đặt bởi loader chứ không phải code chương trình, nên patch BeingDebugged thôi không đủ.

## Heap flags, hệ quả kéo theo

NtGlobalFlag ở trên làm heap được tạo ở chế độ debug, để lại dấu trong chính heap header. Hai trường `Flags` và `ForceFlags` trong cấu trúc heap (lấy heap qua `PEB.ProcessHeap` ở offset `0x30` trên x64) mang giá trị khác khi có debugger:

- Bình thường: `Flags` = `HEAP_GROWABLE` (0x2), `ForceFlags` = 0.
- Dưới debugger: `Flags` có thêm các bit như `HEAP_TAIL_CHECKING_ENABLED`, `ForceFlags` khác 0.

Code kiểm tra sẽ lấy ProcessHeap rồi đọc `ForceFlags`, thấy khác 0 là biết. Offset của Flags/ForceFlags trong heap khác nhau theo phiên bản Windows, nên đây là kiểm tra kén phiên bản, ít gặp hơn nhưng vẫn có.

## Vì sao nhóm này khó hơn nhóm API

Với nhóm API (Bài 15.1), bạn đặt breakpoint tại `IsDebuggerPresent` và ép trả về 0. Nhóm này không có hàm để đặt breakpoint vào. Code chỉ là `mov` và `cmp` trộn giữa logic bình thường, trông chẳng khác gì đọc một biến thường. Bạn phải đọc hiểu mới nhận ra nó đang đọc offset nhạy cảm của PEB.

Mẹo nhận diện nhanh khi đọc tĩnh: tìm mọi chỗ chạm `gs:[0x60]` (x64) hoặc `fs:[0x30]` (x86), rồi xem offset nó đọc tiếp:
- `[...+2]` byte: BeingDebugged.
- `[...+0xBC]` dword: NtGlobalFlag.
- `[...+0x30]` rồi đọc tiếp heap: ProcessHeap flags.

## Cách vượt qua

Vì các cờ này nằm trong bộ nhớ tiến trình của chính bạn (chạy trong debugger), bạn sửa được trực tiếp:

- **Sửa bằng tay trong debugger.** Trước khi code check chạy, tới PEB và ghi `BeingDebugged = 0`, xoá ba bit của NtGlobalFlag. Trong x64dbg, lệnh `dump` theo PEB rồi sửa byte, hoặc dùng biểu thức.
- **ScyllaHide.** Plugin này làm chuyện đó tự động và toàn diện: nó dọn BeingDebugged, NtGlobalFlag, heap flags, và hàng loạt check khác ngay khi tiến trình khởi động. Với phần lớn anti-debug user-mode, bật ScyllaHide là xong, đỡ phải vá từng cái. Xem thêm ở [Bài 15.9](/posts/tr-15-9-bypass-scyllahide-titanhide/).
- **Patch code check.** Nếu chỉ vài chỗ, đổi lệnh `jnz`/`jz` phát hiện thành nhảy ngược lại, hoặc NOP đoạn kiểm tra. Cách này bền nếu bạn định chạy lại nhiều lần.

Thường ScyllaHide là lựa chọn đầu tiên vì nó phủ gần hết nhóm PEB một lần. Patch tay để dành cho khi bạn muốn hiểu rõ từng check hoặc khi check được giấu kỹ.

## Lab tự làm

Thư mục [labs/15.2/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/15.2). Có `peb_check.c` tự đọc BeingDebugged và NtGlobalFlag trực tiếp qua PEB. Nhiệm vụ: build, chạy thường (báo không bị debug), chạy dưới x64dbg (báo bị debug), rồi tìm trong disassembly đoạn đọc `gs:[0x60]` và vượt qua bằng cách sửa cờ hoặc ScyllaHide. Hướng dẫn trong README của lab.

## Checklist ghi nhớ
- PEB truy cập không cần API: `gs:[0x60]` (x64), `fs:[0x30]` (x86). Thấy là cảnh giác.
- BeingDebugged ở offset `0x2`, bằng 1 khi bị debug.
- NtGlobalFlag ở offset `0xBC` (x64), ba bit heap debug cộng lại `0x70`, loader đặt chứ không phải code.
- Heap Flags/ForceFlags khác 0 khi có debugger, kén phiên bản Windows.
- Nhóm này không có API để hook, phải đọc hiểu pattern truy cập segment.
- Vượt qua: sửa cờ trong bộ nhớ, ScyllaHide (nhanh nhất), hoặc patch nhánh check.
