---
title: "Bài 14.6: Deobfuscation tự động, để máy gỡ hộ thay vì cày tay"
date: 2026-10-06 09:25:00 +0700
categories: ["Technique Reverse", "Phần 14 · Packer & Obfuscation"]
tags: [reverse-engineering, packer, obfuscation]
render_with_liquid: false
---
Bài [14.4](/posts/tr-14-4-obfuscation-ky-thuat/) cho bạn thấy obfuscation trông như thế nào: control flow flattening biến một hàm gọn thành cái dispatcher khổng lồ, MBA biến `x + y` thành một biểu thức bit dài ngoằng, opaque predicate rải nhánh chết khắp nơi. Gỡ từng cái bằng tay thì làm được, nhưng với một binary vài nghìn hàm obfuscated thì bạn sẽ bỏ cuộc trước khi xong hàm thứ ba. Bài này nói về cách để công cụ làm phần nặng nhọc.

Ý tưởng chung của mọi công cụ deobfuscation tự động chỉ gói trong một câu: **nâng code lên một dạng trung gian (IR) sạch hơn, rút gọn trên đó bằng các quy tắc đại số hoặc bằng solver, rồi hạ xuống lại.** Khác nhau chỉ là chúng làm ở tầng nào và mạnh tới đâu.

## Vì sao làm trên IR chứ không trên assembly

Assembly x86 rất rối để biến đổi tự động: cùng một phép toán có chục cách viết, cờ trạng thái (flags) thay đổi ngầm, lệnh dài ngắn khác nhau. Nếu cố viết quy tắc rút gọn thẳng trên assembly, bạn chết chìm trong trường hợp đặc biệt.

Nên công cụ nâng (lift) assembly lên một Intermediate Representation: một ngôn ngữ nhỏ, đều đặn, mỗi lệnh làm đúng một việc, không có tác dụng phụ ẩn. Trên IR, `x + y` luôn là `x + y`, và một biểu thức MBA tương đương `x + y` có thể rút gọn về đúng `x + y` bằng các luật đại số. Xong thì hạ (lower) ngược về dạng đọc được, hoặc đưa thẳng vào decompiler.

Hex-Rays gọi IR của nó là microcode. Ghidra gọi là P-Code. Binary Ninja có BNIL nhiều tầng. Mỗi tool deobfuscation bám vào một trong các IR đó.

## D-810, gỡ ngay trong Hex-Rays

Nếu bạn dùng IDA Pro với Hex-Rays, D-810 là thứ nên biết đầu tiên. Nó là plugin cắm vào tầng microcode: trong lúc decompiler dựng pseudocode, D-810 chen vào, nhận ra các mẫu obfuscation quen và viết lại microcode trước khi bạn nhìn thấy kết quả.

Nó mạnh nhất với ba thứ:
- **MBA**: nhận diện và rút các biểu thức Mixed Boolean-Arithmetic về phép toán gốc.
- **Opaque predicate**: phát hiện điều kiện luôn đúng hoặc luôn sai rồi cắt nhánh chết.
- **Control flow flattening**: dựng lại luồng gốc từ dispatcher, trả về if/else/loop bình thường.

Cái hay là bạn không phải chạy một bước riêng rồi import kết quả. Cài rule phù hợp, nhấn F5, pseudocode hiện ra đã sạch. Điểm yếu: nó theo rule, nên gặp một biến thể obfuscation mà rule chưa biết thì bó tay, bạn phải tự viết thêm rule (D-810 cho phép) hoặc đổi cách.

## HexRaysDeob và dòng plugin microcode

Trước D-810 có HexRaysDeob của Rolf Rolles, cũng làm ở tầng microcode và là một trong những minh chứng đầu tiên rằng microcode của Hex-Rays đủ mở để tự động gỡ obfuscation. Nó nhắm vào một số protector cụ thể (nổi tiếng với các mẫu của một họ malware thời đó). Giờ D-810 phổ biến hơn, nhưng đọc lại loạt bài của Rolles về microcode vẫn là cách tốt nhất để hiểu cơ chế bên dưới, chứ không chỉ bấm nút.

Điểm chung của cả hai: chúng chữa triệu chứng ở đúng nơi triệu chứng sinh ra, tức là trong lúc decompile, nên kết quả ăn thẳng vào pseudocode.

## Miasm, khi bạn cần một bộ đồ nghề đầy đủ

Miasm không phải plugin cho một decompiler, mà là cả một framework Python: nó lift nhiều kiến trúc lên IR riêng, emulate được, có engine symbolic execution, và có expression simplifier. Vì nó là thư viện, bạn tự lập trình quy trình gỡ.

Mẫu dùng điển hình: lift một hàm obfuscated lên IR của Miasm, cho symbolic execution chạy qua, thu được biểu thức tượng trưng của output theo input, rồi để simplifier rút gọn. Flattening tan ra vì symbolic execution đi theo luồng thật bất kể dispatcher; MBA tan ra vì simplifier biết các luật. Bạn trả giá bằng việc phải viết code, nhưng đổi lại kiểm soát hoàn toàn và không phụ thuộc rule có sẵn.

Cùng nhóm tư duy này còn có vài hướng khác đáng biết tên: **gtirb** (IR dạng rewriting của GrammaTech) cho việc viết lại binary, và **Souper** (superoptimizer dùng solver) cho việc tìm biểu thức tương đương ngắn hơn. Bạn ít khi cần tới chúng lúc mới học, nhưng biết chúng tồn tại giúp bạn không nghĩ D-810 là lựa chọn duy nhất.

## Symbolic execution, vũ khí chung cho MBA và flattening

Đây là tiếp cận tổng quát nhất, và cũng là cầu nối sang [Phần 18](https://github.com/Haind03/Technique-Reverse/tree/main/phan-18-nang-cao). Công cụ như Triton hay angr coi input là biến tượng trưng (symbolic), chạy qua code, và thay vì tính ra một con số thì tính ra một công thức. Hai ứng dụng trực tiếp cho deobfuscation:

- **Rút gọn MBA**: cho Triton build biểu thức tượng trưng của một đoạn MBA, rồi dùng simplifier hoặc Z3 chứng minh nó tương đương với biểu thức ngắn. Thực tế một biểu thức MBA ba chục phép bit thường rút về `a ^ b` hoặc `a + b`.
- **Gỡ flattening**: symbolic/concolic execution đi theo luồng thực thi thật, nối các block gốc theo đúng thứ tự chạy, bỏ qua dispatcher. Từ trace đó dựng lại CFG sạch.

Triton gọn và nhúng được vào tool khác; angr nặng hơn nhưng có sẵn CFG recovery và nhiều tiện ích. Chi tiết về symbolic execution để dành [Bài 18.3](https://github.com/Haind03/Technique-Reverse/tree/main/phan-18-nang-cao).

## Tự động hay làm tay: chọn theo quy mô

Đừng mặc định cứ obfuscation là phải dựng cả pipeline symbolic. Cân theo công sức bỏ ra so với thu lại:

| Tình huống | Nên làm |
|---|---|
| Một hàm, một chỗ MBA nhỏ | Rút tay, nhanh hơn dựng tool |
| Nhiều hàm cùng một kiểu obfuscation | D-810 với rule phù hợp, hoặc viết một rule rồi áp hàng loạt |
| Flattening nặng, nhiều hàm | D-810 hoặc script Miasm/symbolic |
| Obfuscation lạ, chưa có rule | Miasm hoặc Triton, tự viết logic gỡ |
| Chỉ cần biết một hàm trả ra gì với input cho trước | Emulate (Unicorn/Qiling), khỏi gỡ |

Một mẹo hay bị quên: nhiều khi bạn không cần gỡ obfuscation gì cả. Nếu câu hỏi chỉ là "hàm check này trả true với serial nào", cứ emulate hoặc để symbolic execution giải ngược, mặc kệ luồng bên trong rối thế nào. Gỡ obfuscation để đọc là một mục tiêu; tìm đáp án là mục tiêu khác, và mục tiêu thứ hai thường rẻ hơn nhiều.

## Lab tự làm

Xem [labs/14.6/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/14.6). Bạn sẽ lấy một hàm có MBA hoặc opaque predicate, dùng D-810 hoặc Miasm để rút gọn và so sánh pseudocode trước với sau. Nếu chưa cài được tool, phần lab có một biểu thức MBA mẫu để bạn rút gọn bằng tay, đủ để thấy tận mắt một biểu thức khủng bố quy về một phép XOR.

## Checklist ghi nhớ
- Mọi deobfuscation tự động đều theo một công thức: lift lên IR, simplify, lower xuống.
- D-810 gỡ ngay trong Hex-Rays microcode, mạnh với MBA, opaque predicate, flattening; theo rule.
- HexRaysDeob là tiền bối, đọc loạt bài của Rolf Rolles để hiểu microcode.
- Miasm là framework Python đầy đủ (IR, emulate, symbolic, simplify), bạn tự lập trình quy trình.
- Symbolic execution (Triton, angr) là vũ khí tổng quát cho cả MBA lẫn flattening, chi tiết ở Phần 18.
- Cân nhắc quy mô: một chỗ nhỏ thì làm tay, hàng loạt mới dựng tool. Và đôi khi chỉ cần emulate để lấy đáp án, không cần gỡ gì.
