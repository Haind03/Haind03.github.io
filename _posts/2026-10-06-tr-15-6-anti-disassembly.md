---
title: "Bài 15.6: Anti-disassembly, khi chính disassembler bị lừa"
date: 2026-10-06 09:31:00 +0700
categories: ["Technique Reverse", "Phần 15 · Anti-Reverse chuyên sâu và cách vượt qua"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
Mấy bài anti-debug trước lo chuyện vượt mặt debugger lúc chạy. Bài này là một trò khác hẳn, nhắm vào bước tĩnh: làm sao cho IDA, Ghidra hay objdump giải ra một đống lệnh sai bét ngay khi bạn vừa mở file, trong khi CPU vẫn chạy code đúng. Reverser nhìn vào pseudocode tưởng là logic thật, hóa ra toàn rác. Hiểu mấy mẹo này thì bạn thôi tin mù vào output của disassembler.

Gốc rễ của mọi chiêu nằm ở một sự thật: x86 là kiến trúc lệnh dài ngắn khác nhau (variable-length), một byte có thể là đầu một lệnh, mà cũng có thể là giữa một lệnh khác. Chỉ cần đánh lừa disassembler về chỗ một lệnh bắt đầu là cả đoạn sau giải sai theo.

## Hai cách disassemble, hai điểm yếu

Trước khi phá, phải biết disassembler làm việc thế nào. Có hai chiến lược:

- **Linear sweep**: giải tuần tự từ đầu tới cuối, lệnh này xong tới byte ngay sau là lệnh kế. objdump mặc định kiểu này. Điểm yếu: gặp data chen vào giữa code là nó cứ giải data thành lệnh, sai từ đó trở đi.
- **Recursive descent (recursive traversal)**: đi theo luồng điều khiển, gặp `jmp`/`jcc`/`call` thì nhảy theo đích. IDA và Ghidra kiểu này, nên thông minh hơn. Điểm yếu: nếu nó đoán sai đích nhảy, hoặc bị lừa tin rằng một nhánh có thể tới trong khi thực tế không, thì cũng giải nhầm.

Anti-disassembly chính là khai thác đúng hai điểm yếu đó.

## Junk byte sau một jump vô điều kiện

Chiêu kinh điển nhất. Sau một `jmp` (hoặc `jcc` mà điều kiện luôn đúng) là một byte rác. CPU nhảy đi mất, không bao giờ chạm byte rác đó. Nhưng disassembler linear sweep thì giải tiếp byte rác như một lệnh, và vì byte rác thường là opcode mở đầu một lệnh nhiều byte, nó nuốt luôn mấy byte thật phía sau, lệch hết.

Ví dụ hay gặp:

```
EB 01        jmp short +1      ; nhảy tới byte ngay sau 0xE8
E8           db 0xE8           ; byte rác: opcode của CALL, nuốt 4 byte sau
...lệnh thật bắt đầu từ đây
```

`EB 01` nghĩa là nhảy tới vị trí hiện tại cộng 1, tức bỏ qua đúng một byte `E8`. CPU không bao giờ thực thi `E8`. Nhưng disassembler thấy `E8` tưởng là `call rel32`, ngốn thêm 4 byte địa chỉ, và lệnh thật bị xé làm đôi. Trong IDA đoạn này hiện ra lủng củng, có khi tô đỏ.

## Overlapping instruction, một dãy byte hai nghĩa

Đây là chiêu đẹp nhất về mặt kỹ thuật. Cùng một dãy byte đọc từ hai điểm bắt đầu khác nhau ra hai chuỗi lệnh hoàn toàn khác. Kẻ viết sắp xếp để disassembler bắt đầu ở chỗ A (ra lệnh vô hại), còn CPU thật sự nhảy vào chỗ B ở giữa một lệnh (ra lệnh khác).

Ví dụ cổ điển với byte `EB FF C0 48`:

```
Đọc từ đầu:
  EB FF        jmp short -1     ; nhìn như nhảy lùi
Nhưng CPU nhảy vào byte thứ 2:
  FF C0        inc eax
  48 ...       (lệnh tiếp theo)
```

Disassembler khóa vào cách đọc thứ nhất và bỏ lỡ `inc eax` mà CPU thật sự chạy. Byte `FF` vừa là đuôi của `jmp short -1` (EB FF) vừa là đầu của `inc eax` (FF C0). Một byte, hai vai.

## push + ret thay cho jmp

Một cách giấu đích nhảy khỏi recursive descent. Thay vì `jmp target` (đích lộ rõ cho disassembler đi theo), người ta làm:

```
push target_address
ret
```

`ret` lấy giá trị trên đỉnh stack làm địa chỉ trở về và nhảy tới đó. Về hiệu quả giống hệt `jmp target`, nhưng disassembler thấy `ret` thì tưởng hàm kết thúc và dừng đi theo luồng, không biết thực ra nó nhảy tới `target`. Biến thể khác: `call` + chỉnh địa chỉ trở về trên stack.

## Opaque predicate tạo nhánh chết

Một điều kiện mà kết quả thực tế luôn cố định (ví dụ `x*x >= 0` luôn đúng), nhưng compiler/disassembler không chứng minh được nên phải giả định cả hai nhánh đều có thể tới. Kẻ viết nhét code rác hoặc code gây lệch giải mã vào nhánh không bao giờ chạy. Bạn tốn công đọc một nhánh chết. Đã nói kỹ ở [Bài 14.4](/posts/tr-14-4-obfuscation-ky-thuat/), ở đây chỉ nhắc nó cũng là một dạng anti-disassembly khi nhánh chết chứa byte làm lệch.

## Self-modifying code (SMC)

Code sửa chính nó lúc chạy. Trên đĩa (và trong view tĩnh của IDA) đoạn đó là một dãy byte vô nghĩa hoặc đã mã hóa; chỉ tới runtime stub mới ghi đè bằng lệnh thật rồi mới thực thi. Nhìn tĩnh thấy rác, vì code thật chưa tồn tại lúc bạn đọc. Dấu hiệu: một vòng lặp ghi vào vùng `.text` (vốn chỉ nên đọc và chạy), hoặc section vừa ghi vừa thực thi (W+X). Gặp SMC thì static gần như bó tay, phải chạy động tới sau khi nó tự sửa xong rồi mới dump ra đọc. Đây cũng là cơ chế lõi của packer ([Bài 14.1](/posts/tr-14-1-packer-entropy-nhan-dien/)).

## Cách xử lý

Tin tốt: anti-disassembly làm khó bước tĩnh, nhưng CPU vẫn phải chạy đúng, nên bước động luôn cho bạn sự thật. Bộ công cụ xử lý:

- **Chạy động là trọng tài cuối cùng.** Mở trong x64dbg, single-step qua đoạn khả nghi, bạn thấy đúng luồng CPU đi và đúng lệnh nó thực thi, bất kể IDA vẽ gì.
- **Trong IDA, undefine rồi define lại.** Nhấn `U` (undefine) trên đoạn bị giải sai, rồi đặt con trỏ đúng chỗ lệnh thật bắt đầu (lấy từ bước động) và nhấn `C` (make code). IDA sẽ giải lại từ điểm đúng.
- **Patch junk byte thành `nop`.** Với junk byte sau `jmp`, ghi đè nó bằng `0x90` để disassembler giải lại cho sạch. Vì byte đó CPU không chạy nên patch vô hại.
- **Để ý vùng tô đỏ và lệnh vô lý.** IDA đánh dấu chỗ nó không chắc. Một `jmp short -1`, một `call` vào giữa hư không, một dãy `db` xen giữa code đang chạy, đều là cờ báo có anti-disassembly.
- **Nhận ra `push addr; ret`** và tự đi theo đích addr thay vì tin rằng hàm đã kết thúc.

Nguyên tắc chung: khi pseudocode trông loạn một cách bất thường ngay giữa một hàm bình thường, đừng tự trách mình đọc kém, hãy nghi là disassembler bị lừa và kiểm lại bằng cách chạy động.

## Lab tự làm

Xem [labs/15.6/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/15.6). Bạn được cho một dãy byte có junk byte và một chỗ overlapping, nhiệm vụ là xác định luồng CPU thật, chỉ ra lệnh bị disassembler bỏ lỡ, và sửa lại trong IDA (undefine, make code đúng chỗ). Lời giải ở [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/15.6/solution.md).

## Checklist ghi nhớ
- x86 là variable-length, một byte có thể vừa là giữa lệnh này vừa là đầu lệnh khác. Đó là gốc của mọi chiêu.
- Junk byte sau `jmp`: byte rác CPU không chạy nhưng làm disassembler lệch. Patch thành `nop`.
- Overlapping instruction: cùng dãy byte, đọc từ hai offset ra hai nghĩa. CPU nhảy vào giữa lệnh.
- `push addr; ret` giấu đích nhảy khỏi recursive descent.
- SMC: code thật chỉ xuất hiện lúc chạy, static thấy rác. Phải dump động.
- Bước động luôn là trọng tài: single-step để thấy luồng thật, rồi undefine/make code lại trong IDA.
