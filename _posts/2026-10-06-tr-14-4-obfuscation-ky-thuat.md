---
title: "Bài 14.4: Obfuscation ở mức code, khi luồng chương trình bị bẻ cong"
date: 2026-10-06 09:23:00 +0700
categories: ["Technique Reverse", "Phần 14 · Packer & Obfuscation"]
tags: [reverse-engineering, packer, obfuscation]
render_with_liquid: false
---
Packer giấu code đến khi chạy (bài 14.1, 14.2). Obfuscation làm chuyện khác: code vẫn nằm đó, bạn vẫn disassemble được, nhưng nó được viết lại cố ý cho khó đọc. Hàm mười dòng phình thành năm trăm dòng, một phép cộng biến thành một mớ phép bit, luồng if/else gọn gàng biến thành một vòng lặp vô hạn với cái switch khổng lồ. Logic không đổi, chỉ hình dạng đổi.

Bài này điểm qua các kỹ thuật hay gặp nhất, cách nhận ra từng cái, và quan trọng hơn là chiến lược chung để không bị chúng dọa. Phần lớn trong số này đến từ OLLVM (Obfuscator-LLVM), một bộ pass LLVM mã nguồn mở mà rất nhiều protector thương mại và malware dùng lại.

## Control flow flattening, kẻ phá đám số một

Đây là kỹ thuật bạn gặp nhiều nhất và cũng gây ức chế nhất. Ý tưởng: lấy luồng tự nhiên của hàm (khối A chạy xong tới B, B rẽ sang C hoặc D) rồi đập phẳng hết. Mọi khối cơ bản trở thành một `case` trong một `switch` lớn, và một biến trạng thái (state variable) quyết định case nào chạy tiếp. Toàn bộ nằm trong một vòng `while(1)`.

Nhìn trên graph view của IDA, hàm bình thường có hình cây chảy xuống. Hàm bị flatten trông như một con nhện: một dispatcher ở giữa, mọi khối đều quay về dispatcher rồi tỏa ra lại. Cấu trúc if/for/while gốc biến mất hoàn toàn, vì thứ tự chạy giờ do biến state điều khiển chứ không do vị trí lệnh.

Hãy xem cụ thể. Hàm gốc kiểm tra serial:

```c
int check(const char *s) {
    int len = strlen(s);
    if (len != 8) return 0;
    if (s[0] != 'R') return 0;
    int sum = 0;
    for (int i = 0; i < len; i++) sum += s[i];
    if (sum % 7 != 0) return 0;
    return 1;
}
```

Sau khi flatten (đây là file `flattened.c` trong lab, viết tay cho dễ thấy hình dạng):

```c
int check(const char *s) {
    int state = 0, len = 0, sum = 0, i = 0, ret = 0;
    while (1) {
        switch (state) {
            case 0:  len = strlen(s); state = 1; break;
            case 1:  if (len != 8) { ret = 0; state = 99; } else state = 2; break;
            case 2:  if (s[0] != 'R') { ret = 0; state = 99; } else { sum = 0; i = 0; state = 3; } break;
            case 3:  if (i < len) state = 4; else state = 5; break;   // dieu kien loop
            case 4:  sum += s[i]; i++; state = 3; break;              // than loop
            case 5:  if (sum % 7 != 0) { ret = 0; state = 99; } else { ret = 1; state = 99; } break;
            case 99: return ret;
        }
    }
}
```

Hai bản này chạy ra kết quả y hệt nhau (lab đã kiểm bằng cách build cả hai và so trên nhiều input). Nhưng bản dưới mất hết hình dáng gốc. Muốn hiểu nó, bạn phải làm thủ công cái việc mà biến state đang làm: lần theo state nhảy đi đâu. case 0 đặt state=1, case 1 đặt state=2 nếu qua, case 2 nhảy vào vòng lặp case 3 và 4, xong tới case 5. Dựng lại được chuỗi state là dựng lại được luồng gốc.

Chiến lược đối phó:
- Nhận ra ngay qua graph "con nhện" và một biến được gán hằng số liên tục rồi so sánh ở đầu vòng lặp. Đó là state variable.
- Với hàm nhỏ, lần state bằng tay như trên là đủ.
- Với hàm lớn, dùng công cụ tự động ở bài 14.6 (D-810, Miasm, emulation) để dựng lại CFG gốc.
- Hoặc bỏ qua static, chạy động: đặt breakpoint và xem thực tế các case chạy theo thứ tự nào với input của bạn.

## Opaque predicate, những nhánh không bao giờ chạy

Opaque predicate là một điều kiện mà kẻ obfuscate biết chắc kết quả (luôn đúng hoặc luôn sai), nhưng compiler và decompiler thì không. Ví dụ kinh điển: `if ((x*x + x) % 2 == 0)`. Tích của hai số liên tiếp luôn chẵn, nên điều kiện này luôn đúng, nhánh else là code chết (dead code) chỉ để làm nhiễu.

Hậu quả: graph đầy nhánh rẽ giả, bạn tốn công đọc code không bao giờ chạy. Nhận ra bằng cách để ý các điều kiện số học kỳ quặc trên một biến mà giá trị thực ra cố định. Công cụ symbolic execution (angr, Triton ở Phần 18) hoặc SMT solver chứng minh được predicate là hằng, rồi cắt nhánh chết.

## Mixed Boolean-Arithmetic, phép cộng mặc áo giáp

MBA biến một phép toán đơn giản thành biểu thức tương đương nhưng rối mắt, trộn phép số học với phép bit. Ví dụ `x + y` có thể thành `(x ^ y) + 2*(x & y)`, hay tệ hơn là cả một chuỗi `|`, `&`, `^`, `~`, shift dài cả chục dòng. Về mặt toán học chúng bằng nhau, nhưng nhìn vào bạn không đoán nổi nó đang cộng.

Nhận ra MBA khi thấy một khối toàn phép bit không có mục đích rõ ràng, trên cùng vài biến. Đối phó: dùng công cụ simplify biểu thức (Miasm, Triton có simplifier, hoặc các MBA solver chuyên dụng), hoặc emulate đoạn đó với vài giá trị để suy ra nó thực sự tính gì.

## String encryption

Chuỗi là manh mối quý nhất của reverser (bài 0.4), nên obfuscator mã hoá hết. Thay vì "Invalid license" nằm trong `.rdata`, bạn thấy một mảng byte vô nghĩa và một hàm giải mã được gọi ngay trước khi dùng chuỗi. Giải mã thường rất nhẹ: XOR với khoá, hoặc cộng/trừ hằng số.

Đối phó hiệu quả nhất là động: đặt breakpoint sau lời gọi hàm giải mã rồi đọc chuỗi đã rõ trong bộ nhớ. Hoặc nếu thuật toán đơn giản, viết lại bằng Python để giải hàng loạt (chính là Phần 16). FLOSS của Mandiant tự động hoá phần lớn việc này.

## Junk code, dead code, instruction substitution

Ba kỹ thuật nhỏ hay đi kèm:
- **Junk / dead code**: chèn lệnh vô nghĩa (nop biến tấu, tính toán rồi vứt kết quả) để làm loãng. Bỏ qua được một khi nhận ra chúng không ảnh hưởng output.
- **Instruction substitution**: thay một lệnh bằng chuỗi lệnh tương đương (vd `a = b - c` thành `a = b + (-c)` qua nhiều bước). Decompiler tốt thường gộp lại giúp bạn.
- **Junk bytes chống disassembly**: chuyện của bài 15.6, hơi khác vì nó đánh vào bộ disassembler chứ không vào người đọc.

## Chiến lược chung khi gặp obfuscation

Đừng cố đọc tuyến tính một hàm đã obfuscate, bạn sẽ chết chìm. Thay vào đó:

1. **Nhận diện** đang gặp kỹ thuật gì (flatten có hình con nhện, MBA có khối bit, string encryption có hàm giải mã trước mỗi chuỗi).
2. **Ưu tiên động hơn tĩnh.** Obfuscation làm khó việc đọc tĩnh, nhưng lúc chạy chương trình vẫn phải làm đúng việc. Breakpoint đặt đúng chỗ cho bạn thấy giá trị thật, chuỗi đã giải mã, nhánh thật sự chạy.
3. **Tập trung vào input và output của đoạn code**, đừng sa vào từng lệnh. Một khối MBA dài chỉ cần biết "nó cộng hai số này" là đủ.
4. **Tự động hoá khi quy mô lớn**: emulation và symbolic execution (Phần 18), hoặc công cụ deobfuscation chuyên dụng (bài 14.6).

Điểm mấu chốt: obfuscation làm tốn thời gian chứ không làm bất khả thi. Logic vẫn phải chạy đúng, nên luôn có một con đường động để nhìn thấy sự thật.

## Lab tự làm

Trong `labs/14.4/` có `original.c` và `flattened.c`, cùng một hàm `check` nhưng một bản gốc, một bản đã control flow flattening thủ công. Build cả hai, xác nhận chúng cho kết quả giống nhau, rồi tập dựng lại luồng gốc chỉ từ bản flattened bằng cách lần biến state. Chi tiết trong `labs/14.4/README.md`, lời giải và serial hợp lệ trong `labs/14.4/solution.md`.

## Checklist ghi nhớ
- Control flow flattening: while(1) + switch(state), graph hình con nhện. Dựng lại luồng bằng cách lần biến state.
- Opaque predicate: điều kiện luôn đúng/sai tạo nhánh chết, cắt bằng symbolic execution.
- MBA: phép toán đơn giản mặc áo phép bit, gỡ bằng simplifier hoặc emulate.
- String encryption: đặt breakpoint sau hàm giải mã để đọc chuỗi thật.
- OLLVM là nguồn phổ biến của flatten, substitution, bogus control flow.
- Nguyên tắc vàng: ưu tiên động hơn tĩnh, tập trung input/output, tự động hoá khi lớn (bài 14.6).
