---
title: "Bài 6.1: JVM bytecode và dàn decompiler Java"
date: 2026-10-06 08:44:00 +0700
categories: ["Technique Reverse", "Phần 6 · Java / Kotlin / Android (JADX)"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
Nếu bạn vừa đi qua phần C/C++ và thấy nản vì tên biến bay sạch, Java sẽ là một liều thuốc an ủi. File `.class` của Java giữ lại gần như đầy đủ thông tin: tên class, tên method, tên field, kiểu dữ liệu. Thả một file `.jar` vào JADX là bạn có lại code Java đọc được gần như bản gốc. Lý do nằm ở chỗ Java, giống .NET, không biên dịch thẳng ra machine code mà dừng ở một tầng trung gian gọi là bytecode. Bài này giải thích tầng đó và điểm qua dàn công cụ để lật nó về Java.

## Vì sao .class dễ đọc đến vậy

Khi bạn `javac Hello.java`, trình biên dịch không tạo ra lệnh cho CPU. Nó tạo ra JVM bytecode, một tập lệnh cho máy ảo Java (Java Virtual Machine). Lúc chạy, JVM mới dịch bytecode đó sang machine code (qua JIT) hoặc thông dịch từng lệnh.

Điểm mấu chốt với người reverse: để JVM chạy được, file `.class` buộc phải mang theo rất nhiều metadata. Tên method phải còn để gọi, kiểu tham số phải còn để kiểm tra, tên field phải còn để truy cập. Những thứ mà compiler C vứt đi thì compiler Java bắt buộc phải giữ. Đó là lý do decompiler Java cho ra kết quả đẹp hơn hẳn decompiler native.

## Bên trong một file .class

Một `.class` gồm vài phần, hai phần bạn cần quan tâm nhất:

- **Constant pool**: một bảng tra chứa mọi hằng số, tên, và tham chiếu mà class dùng tới. Chuỗi, tên method, tên class, tất cả gom vào đây rồi bytecode chỉ trỏ tới bằng số thứ tự (`#7`, `#13`...). Đây là mỏ vàng khi reverse: cứ đọc constant pool là thấy hết chuỗi và tên hàm ngoại được gọi.
- **Các method**, mỗi method có một khối **Code** chứa bytecode.

JVM là một máy ảo **stack-based**, khác với x86 là **register-based**. Nghĩa là thay vì đổ dữ liệu vào thanh ghi rồi tính, bytecode đẩy toán hạng lên một stack rồi lệnh lấy từ stack ra xử lý. Ví dụ phép cộng không nói "cộng thanh ghi này với thanh ghi kia", mà là "lấy hai giá trị trên cùng của stack, cộng, đẩy kết quả lại".

## Đọc thử bytecode thật

![JVM bytecode stack-based so với DEX bytecode register-based](/assets/img/technique-reverse/assets/phan-06/dex-vs-jvm.svg)

Lấy một method cộng hai số:

```java
static int add(int a, int b) {
    return a + b;
}
```

Dùng `javap -c` (công cụ có sẵn trong JDK) để xem bytecode:

```
static int add(int, int);
  Code:
     0: iload_0      // đẩy tham số 0 (a) lên stack
     1: iload_1      // đẩy tham số 1 (b) lên stack
     2: iadd         // lấy hai số trên stack, cộng, đẩy kết quả
     3: ireturn      // trả về số nguyên trên đỉnh stack
```

Bốn lệnh, đọc thẳng được ý. `i` ở đầu là integer, `load` là nạp lên stack, `add` là cộng, `return` là trả về. Không cần thuộc lòng, nhìn tiền tố là đoán ra.

Giờ một method có nhánh, kiểu bạn gặp trong crackme:

```java
static boolean checkPass(String s) {
    return s.length() == 8 && s.equals("JavaRev!");
}
```

Bytecode:

```
0: aload_0                       // đẩy tham số s (kiểu tham chiếu) lên stack
1: invokevirtual String.length  // gọi s.length(), kết quả lên stack
4: bipush 8                      // đẩy hằng 8
6: if_icmpne 22                  // nếu hai số khác nhau, nhảy tới 22 (trả false)
9: aload_0                       // đẩy s
10: ldc "JavaRev!"              // đẩy hằng chuỗi (tra trong constant pool #13)
12: invokevirtual String.equals // gọi s.equals("JavaRev!")
15: ifeq 22                      // nếu kết quả là 0 (false), nhảy tới 22
18: iconst_1                     // đẩy 1 (true)
19: goto 23
22: iconst_0                     // đẩy 0 (false)
23: ireturn
```

Để ý `ldc "JavaRev!"`: chuỗi so sánh lộ ra ngay trong bytecode. Một crackme Java ngây thơ dâng password cho bạn thế này. `invokevirtual String.equals` cho biết nó so sánh chuỗi, và cặp `if_icmpne`/`ifeq` chính là hai điều kiện `&&`. Giống hệt việc tìm cặp `cmp`/`jne` trong assembly ở Bài 1.3, chỉ là dễ đọc hơn nhiều.

Những tên như `String.length`, `String.equals`, chuỗi `JavaRev!`, tất cả đến từ constant pool. Bytecode chỉ ghi số `#7`, `#13`, `javap` tra hộ bạn và chú thích bên cạnh.

## Dàn decompiler Java, chọn cái nào

Đọc bytecode thô chỉ cần khi decompiler dịch sai. Phần lớn thời gian bạn đọc thẳng Java đã dựng lại. Mỗi tool mạnh một kiểu:

| Tool | Điểm mạnh | Khi nào dùng |
|---|---|---|
| **JADX** | Nuốt luôn cả APK/DEX lẫn JAR, UI gọn, có deobfuscation cơ bản và sinh snippet Frida | Mặc định cho Android, cũng tốt cho JAR. Có sẵn trong repo |
| **CFR** | Xử lý cú pháp Java mới rất tốt (lambda, switch hiện đại), dòng lệnh | Khi JADX dịch ra khó đọc, đối chiếu |
| **Procyon** | Ổn định, lâu đời | Phương án đối chiếu thứ ba |
| **Vineflower** | Kế thừa Fernflower/Quiltflower, chất lượng cao, hay dùng trong modding | Code phức tạp, cần bản dịch sạch |
| **Recaf** | Không chỉ xem mà còn **sửa** bytecode rồi đóng gói lại | Khi cần patch class/jar |
| **Bytecode Viewer** | Gộp nhiều decompiler trong một GUI, so sánh cạnh nhau | Khi muốn nhiều góc nhìn cùng lúc |

Mẹo thực chiến: không có decompiler nào đúng 100%. Khi một tool cho ra code lạ (biến `var3` vô nghĩa, cấu trúc điều khiển rối), mở cùng file bằng một tool khác. Rất thường một trong số chúng dịch ra sạch. Dân Java RE hay để sẵn hai ba decompiler.

## Android thì khác một chút

Android không chạy `.class` trực tiếp. Nó biên dịch chúng thành DEX (Dalvik Executable), một định dạng khác, và máy ảo Android (ART/Dalvik) là **register-based** chứ không stack-based như JVM chuẩn. Nhưng tin tốt: bạn gần như không phải đọc Dalvik bytecode bằng tay, vì JADX gộp mọi `.dex` trong APK rồi dựng thẳng về Java. Cấu trúc APK và DEX để dành cho Bài 6.2.

## Lab tự làm

Xem hướng dẫn tại [labs/6.1](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/6.1). Tóm tắt: biên dịch một file Java nhỏ, dùng `javap -c` để xem bytecode, rồi decompile lại bằng JADX hoặc CFR và đối chiếu với source gốc. Cảm nhận xem decompiler khôi phục tốt tới đâu.

## Checklist ghi nhớ
- Java biên dịch ra JVM bytecode (không phải machine code), nên `.class` giữ nguyên tên method/field/kiểu.
- JVM là máy ảo stack-based: đẩy toán hạng lên stack rồi lệnh lấy ra xử lý.
- Constant pool chứa mọi chuỗi và tên tham chiếu, đọc nó là thấy hết manh mối.
- `javap -c` xem bytecode, tiền tố lệnh (`i` cho int, `a` cho tham chiếu) cho biết kiểu.
- Decompiler chính: JADX (mặc định, có trong repo), CFR, Vineflower, Procyon; Recaf để sửa. Dịch lạ thì đổi tool.
- Android dùng DEX (register-based), nhưng JADX lo hết, để Bài 6.2.
