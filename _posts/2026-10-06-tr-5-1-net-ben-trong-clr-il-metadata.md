---
title: "Bài 5.1: .NET bên trong, vì sao decompile gần như ra source gốc"
date: 2026-10-06 08:37:00 +0700
categories: ["Technique Reverse", "Phần 5 · C# / .NET (dnSpy, ILSpy)"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
Sau mấy phần vật lộn với assembly native, phần này là một kỳ nghỉ. Mở một file .NET bằng dnSpy hay ILSpy, bạn thường nhận lại code C# đọc được gần y như bản tác giả viết: đúng tên class, đúng tên method, đúng tên biến, cả comment thì không nhưng cấu trúc thì nguyên vẹn. Câu hỏi hay là: vì sao native thì nát bét còn .NET lại ngon đến thế? Trả lời được câu đó là bạn hiểu cả cách tiếp cận cho toàn bộ phần này.

## Chương trình .NET không chứa machine code

Đây là mấu chốt. Khi bạn build một project C#, compiler (Roslyn) không sinh ra lệnh x86. Nó sinh ra **IL** (Common Intermediate Language, còn gọi là MSIL hay CIL), một dạng bytecode trung gian, độc lập CPU. Machine code thật chỉ được tạo ra **lúc chạy**, bởi JIT compiler của CLR, ngay trước khi một method được gọi lần đầu.

Luồng đầy đủ:

```
Source C#  --Roslyn-->  IL + metadata  (nằm trong file .exe/.dll)
                              |
                         CLR nạp, JIT
                              v
                        machine code x86/x64  (chỉ tồn tại trong RAM lúc chạy)
```

Vì thứ nằm trên đĩa là IL chứ không phải machine code, và IL ở mức cao hơn hẳn assembly, việc dịch ngược IL về C# dễ hơn nhiều so với dịch machine code về C++.

## CLR, IL, metadata: ba mảnh ghép

![Kiến trúc .NET: source sang IL cộng metadata, JIT ra native, dnSpy decompile ngược](/assets/img/technique-reverse/assets/phan-05/dotnet-arch.svg)

**CLR** (Common Language Runtime) là máy ảo chạy chương trình .NET, vai trò giống JVM với Java. Nó nạp assembly, JIT, quản lý bộ nhớ (garbage collector), kiểm tra an toàn kiểu. Code chạy trên CLR gọi là **managed code**.

**Assembly** là đơn vị triển khai: file `.exe` hoặc `.dll`. Điều thú vị là nó vẫn là một file PE hợp lệ (xem lại [Bài 1.7](/posts/tr-1-7-dinh-dang-pe/)), nhưng phần code không phải section `.text` chứa x86, mà là một CLI header trỏ tới stream IL và metadata. Đó là lý do DIE mở một file .NET vẫn báo PE, nhưng nói thêm là ".NET".

**IL** là bytecode stack-based: thay vì thao tác trên thanh ghi như x86, nó đẩy toán hạng lên một evaluation stack rồi lấy ra. Ví dụ `a + b` thành "đẩy a, đẩy b, cộng". Chính vì dạng trừu tượng và nhiều thông tin này mà decompiler dựng lại được biểu thức gốc.

**Metadata** mới là ngôi sao. Đi kèm IL là một bộ bảng mô tả đầy đủ mọi type, method, field, tham số, kèm **tên thật**. CLR cần metadata để làm reflection, binding, kiểm tra kiểu, nên tên không thể bị xoá như symbol trong native. Decompiler đọc thẳng metadata ra là có ngay tên class và method. Đây là khác biệt lớn nhất so với native, nơi tên biến bay sạch sau khi compile.

## Nhìn IL cho dễ hình dung

Một method C# nhỏ:

```csharp
public static int Add(int a, int b)
{
    return a + b;
}
```

IL tương ứng (dạng ildasm/ILSpy hiển thị):

```
.method public hidebysig static int32 Add(int32 a, int32 b) cil managed
{
    ldarg.0      // đẩy tham số 0 (a) lên stack
    ldarg.1      // đẩy tham số 1 (b) lên stack
    add          // lấy hai cái trên cùng, cộng, đẩy kết quả
    ret          // trả về giá trị trên cùng stack
}
```

Để ý: tên method `Add`, kiểu `int32`, tên tham số `a` và `b` đều còn nguyên. So với native, nơi hàm này thành `sub_401000` nhận hai số trong `rcx`/`rdx`, thì đây gần như là source. Decompiler chỉ việc ráp lại thành `return a + b;`.

## Vì sao managed dễ hơn native

Gom lại thành bảng cho rõ:

| | Native (C/C++) | Managed (.NET) |
|---|---|---|
| Thứ nằm trên đĩa | machine code x86/x64 | IL bytecode |
| Tên hàm/biến | mất (trừ khi có symbol) | còn nguyên trong metadata |
| Mức trừu tượng | thấp, sát CPU | cao, gần ngôn ngữ |
| Kết quả decompile | pseudocode gần đúng | C# gần như bản gốc |
| Cản trở chính | tối ưu của compiler | obfuscation (xem Bài 5.5) |

Điểm cuối rất quan trọng: thứ duy nhất đứng giữa bạn và source .NET thường không phải bản thân format, mà là **obfuscator** cố tình đổi tên và bóp méo. Phần lớn phần này vì thế xoay quanh việc gỡ obfuscation, chứ không phải vật lộn với IL.

## Công cụ

- **ILSpy** và **dnSpy** đều có sẵn trong repo này (thư mục cha `ILSpy_binaries_9.0.0...` và `dnSpy-net-win64`). ILSpy chuyên decompile và xem IL, dnSpy mạnh ở chỗ còn **debug và sửa** được assembly. Bài [5.2](https://github.com/Haind03/Technique-Reverse/blob/main/phan-05-csharp-dotnet/5.2-ilspy-dnspy.md) và [5.3](https://github.com/Haind03/Technique-Reverse/blob/main/phan-05-csharp-dotnet/5.3-debug-net-dnspy.md) đi sâu.
- **ildasm** (đi kèm Windows SDK) xuất IL dạng text, **ilasm** ráp ngược lại.
- **ilspycmd** là bản dòng lệnh của ILSpy, tiện tự động hoá.
- **dotPeek** của JetBrains là một decompiler miễn phí khác.

Tất cả đọc cùng một thứ: IL và metadata trong assembly. Khác nhau ở giao diện và khả năng sửa.

## Lab tự làm

Xem [labs/5.1/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/5.1). Bạn sẽ dùng DIE nhận ra một file là .NET, rồi mở bằng ILSpy hoặc dnSpy để thấy tận mắt IL và metadata. Nếu máy không có dotnet SDK, dùng luôn chính `ILSpy.dll` hoặc các DLL .NET trong repo làm mẫu quan sát.

## Checklist ghi nhớ
- File .NET trên đĩa chứa IL bytecode cộng metadata, không phải machine code. Machine code chỉ sinh ra lúc chạy bởi JIT.
- Assembly .NET vẫn là PE, nhưng code nằm sau CLI header chứ không phải section .text thường.
- Metadata giữ nguyên tên type/method/field, nên decompile ra gần như source gốc.
- IL là bytecode stack-based, mức cao hơn assembly nhiều, dễ dịch ngược.
- Cản trở thật khi RE .NET thường là obfuscation, không phải bản thân format.
