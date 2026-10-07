---
title: "Bài 5.4: Sửa assembly .NET và lưu lại, nơi dnSpy toả sáng"
date: 2026-10-06 08:40:00 +0700
categories: ["Technique Reverse", "Phần 5 · C# / .NET (dnSpy, ILSpy)"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
Với native, patch một chương trình nghĩa là lọ mọ đổi từng byte opcode, canh sao cho không lệch địa chỉ, rồi rebuild. Với .NET thì khác hẳn một trời một vực: dnSpy cho bạn sửa thẳng code C#, nhấn biên dịch lại, lưu file, xong. Nghe như gian lận, nhưng đó là hệ quả tự nhiên của việc assembly .NET mang theo đầy đủ metadata (xem [Bài 5.1](/posts/tr-5-1-net-ben-trong-clr-il-metadata/)). Bài này là lúc hái quả.

Ta sẽ patch theo hai tầng: tầng C# (dễ nhất, nhưng không phải lúc nào cũng được) và tầng IL (luôn làm được, và là kỹ năng thật của dân RE .NET).

## Vì sao patch .NET sạch hơn patch native

Khi bạn sửa một hàm native, bạn phải nhét code mới vào đúng số byte cũ (hoặc tìm code cave), vì dịch mọi thứ phía sau sẽ làm hỏng mọi địa chỉ tuyệt đối và offset. Đó là lý do người ta hay phải `nop` thay vì viết lại.

IL không bị ràng buộc đó. Method trong .NET được định vị qua metadata token chứ không qua địa chỉ cố định, và dnSpy ghi lại cả module khi lưu, nên nó tự tính lại mọi offset, mọi bảng. Bạn thêm bớt lệnh IL thoải mái, dnSpy lo phần kế toán. Thực tế bạn sửa được cả chữ ký method, thêm field, đổi luồng, mà file vẫn chạy.

## Tầng 1: Edit Method, sửa thẳng C#

Đây là con đường nhanh nhất khi decompiler cho ra C# đủ sạch để biên dịch lại.

Quy trình trong dnSpy:
1. Mở assembly, tìm tới method cần sửa (dùng search hoặc Analyze như [Bài 5.2](/posts/tr-5-2-ilspy-dnspy-decompile/)).
2. Chuột phải vào method, chọn **Edit Method (C#)**. dnSpy mở một ô soạn C# ngay tại method đó.
3. Sửa logic. Ví dụ hàm kiểm tra trả về `false` khi sai, bạn đổi để nó luôn `return true`.
4. Nhấn **Compile**. dnSpy dùng Roslyn biên dịch lại method vào trong assembly.
5. **File > Save Module** để ghi ra đĩa.

Cái hay là bạn làm việc ở mức C# quen thuộc. Cái dở là nếu decompiler dịch sai (hay gặp với code bị obfuscate, dùng feature mới, hoặc có chỗ dnSpy không dựng lại chuẩn), đoạn C# đó sẽ không compile và bạn kẹt. Lúc đó phải xuống tầng IL.

## Tầng 2: Edit IL Instructions, chắc chắn nhất

IL là bytecode thật của method. Sửa ở đây không phụ thuộc decompiler dịch đúng hay sai, nên nó luôn dùng được. Dân RE .NET nghiêm túc đều quen tay với vài lệnh IL, không cần thuộc hết.

Chuột phải method, chọn **Edit IL Instructions**. dnSpy hiện danh sách lệnh IL, cho sửa từng dòng.

Vài lệnh IL cần biết, đủ để patch đa số crackme:

| IL | Ý nghĩa |
|---|---|
| `ldc.i4.0` / `ldc.i4.1` | Đẩy hằng số 0 / 1 (tức false / true) lên stack |
| `ldc.i4 <n>` | Đẩy số nguyên n |
| `ret` | Trả về (giá trị trả về là thứ trên đỉnh stack) |
| `brtrue` / `brtrue.s` | Nhảy nếu giá trị trên stack khác 0 (true) |
| `brfalse` / `brfalse.s` | Nhảy nếu bằng 0 (false) |
| `beq` / `bne.un` | Nhảy nếu bằng / khác |
| `call` / `callvirt` | Gọi method |
| `nop` | Không làm gì (dùng để xoá lệnh) |
| `ceq` | So sánh bằng, đẩy kết quả 0/1 lên stack |

Những thủ thuật patch kinh điển:

- **Đảo một nhánh**: đổi `brtrue` thành `brfalse` (và ngược lại) để nhánh "sai" và "đúng" hoán chỗ. Một lệnh, lật cả logic.
- **Ép giá trị trả về**: nếu hàm kiểm tra trả về bool, chèn `ldc.i4.1` rồi `ret` ngay đầu method. Hàm luôn trả `true`, không thèm chạy logic.
- **Vô hiệu một lời gọi**: thay `call` phiền phức (ví dụ gọi hàm anti-tamper) bằng số lượng `nop` tương đương, nhớ cân bằng stack (nếu call có trả giá trị và nó được dùng sau đó, bạn phải đẩy một giá trị giả thay thế).
- **Đổi hằng số so sánh**: nếu nó `cmp` độ dài với 8, đổi hằng số `ldc.i4.8` thành giá trị bạn muốn.

Mẹo thực dụng: thường bạn không cần hiểu cả method. Tìm đúng chỗ nó quyết định đúng/sai (hay là một `brtrue`/`brfalse` hoặc một `ret` của hàm bool), rồi can thiệp đúng chỗ đó. Ít chạm nhất, ít rủi ro nhất.

## Cạm bẫy: strong name signature

Nhiều assembly được ký bằng strong name. Sau khi bạn sửa và lưu, chữ ký không còn khớp nội dung, và nếu có nơi kiểm tra (strong name verification, hoặc assembly được nạp qua GAC/host có check), file sẽ bị từ chối chạy.

Cách xử lý:
- Nếu assembly tự nạp assembly khác và kiểm chữ ký, bạn có thể phải patch luôn đoạn kiểm tra đó.
- Với assembly thường chạy trực tiếp, strong name verification đã bị tắt mặc định từ .NET Framework 3.5 SP1 trở đi cho full-trust, nên nhiều khi chạy vẫn được.
- dnSpy khi Save Module có tùy chọn liên quan writer; nếu gặp lỗi về token/signature, thử bỏ chọn giữ chữ ký, hoặc xoá strong name rồi ký lại bằng key của bạn.
- Công cụ dòng lệnh như `sn.exe -Vr` (skip verification) có thể dùng trong môi trường test của chính bạn.

Đây là chỗ hay làm người mới bối rối: patch đúng rồi mà chạy vẫn báo lỗi, thủ phạm thường là chữ ký chứ không phải logic.

## Tự động hoá: dnlib và Mono.Cecil

Khi cần patch hàng loạt, hoặc viết tool unpack/deobfuscate, bạn không ngồi bấm dnSpy từng method. Hai thư viện đọc ghi assembly .NET bằng code:

- **dnlib**: nền tảng mà chính dnSpy dùng bên dưới. Mạnh, xử lý được cả assembly hỏng/bị obfuscate. Hầu hết tool .NET RE hiện đại (gồm de4dot) dựa trên nó.
- **Mono.Cecil**: cũ hơn, API gọn, đủ cho phần lớn tác vụ đọc/sửa IL.

Ví dụ ý tưởng với dnlib: nạp module, duyệt tới method kiểm tra, chèn `ldc.i4.1; ret` vào đầu body, ghi ra file mới. Khoảng chục dòng C#. Chi tiết API để dành bài về tự động hoá, ở đây chỉ cần biết con đường này tồn tại khi dnSpy thủ công không đủ.

## Lab tự làm

Bài tập nằm ở [labs/5.4/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/5.4): patch một .NET crackme để nó luôn báo thành công, làm bằng cả hai cách (Edit Method C# và Edit IL), rồi lưu module và chạy lại. Lời giải đầy đủ kèm IL cụ thể ở [labs/5.4/solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/5.4/solution.md), tự làm trước khi mở.

## Checklist ghi nhớ
- Patch .NET sạch hơn native vì method định vị qua metadata token, dnSpy tự tính lại offset khi Save Module.
- Edit Method (C#) nhanh nhất, nhưng kẹt khi decompiler dịch sai.
- Edit IL luôn dùng được. Nhớ vài lệnh: `ldc.i4.0/1`, `ret`, `brtrue/brfalse`, `nop`.
- Thủ thuật phổ biến: đảo `brtrue`/`brfalse`, chèn `ldc.i4.1; ret` ép hàm bool trả true, nop một call.
- Patch xong chạy vẫn lỗi thì nghi strong name signature trước khi nghi logic.
- Cần patch hàng loạt thì dùng dnlib hoặc Mono.Cecil.
