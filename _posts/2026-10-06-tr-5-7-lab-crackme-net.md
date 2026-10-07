---
title: "Bài 5.7: Lab tổng hợp, giải crackme .NET từ dễ tới obfuscated"
date: 2026-10-06 08:43:00 +0700
categories: ["Technique Reverse", "Phần 5 · C# / .NET (dnSpy, ILSpy)"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
Năm bài vừa rồi là lý thuyết và thao tác lẻ. Bài này ghép tất cả lại thành một buổi reverse .NET hoàn chỉnh, qua ba crackme khó dần. Nếu bạn làm được cả ba, mảng .NET coi như xong phần cơ bản.

Mã nguồn và nhiệm vụ chi tiết nằm ở [labs/5.7/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/5.7). Ở đây tôi dẫn tư duy, bạn xuống lab tự tay làm trước khi mở solution.

Cả ba đều dùng ILSpy và dnSpy có sẵn trong repo (thư mục cha). Cần cài .NET SDK để build chúng về dạng `.dll`, sau đó mổ chính sản phẩm của mình.

## Cấp 1: khi reverse chỉ là đọc

Crackme đầu tiên so sánh password nhập vào với một chuỗi cố định. Mở `.dll` trong dnSpy, tìm method `Check`, và vì .NET decompile gần như ra source gốc (lý do đã nói ở [Bài 5.1](/posts/tr-5-1-net-ben-trong-clr-il-metadata/)), bạn đọc thẳng:

```csharp
static bool Check(string input)
{
    return input == "dotnet_easy_123";
}
```

Hết. Password lộ nguyên trong lệnh IL `ldstr`. Không debug, không patch, không gì cả. Điểm của cấp này là cho bạn thấy sự thật phũ phàng: rất nhiều phần mềm .NET ngoài kia bảo vệ logic yếu tới mức này, và đó là lý do người ta phải obfuscate.

Mẹo nhanh hơn cả mở từng method: trong dnSpy nhấn search, gõ một phần chuỗi thông báo như "Correct", rồi Analyze để nhảy tới nơi dùng nó.

## Cấp 2: hiểu thuật toán, viết keygen

Crackme thứ hai không so chuỗi thẳng. Nó nhận username và serial, rồi tính một giá trị từ username và so với serial:

```csharp
static string Expected(string user)
{
    uint acc = 0x1505;
    foreach (char c in user)
        acc = (acc * 33u) + (byte)c;
    return acc.ToString("X8");
}
```

Đây là hash djb2 quen thuộc, tính trên `uint` (tràn 32-bit là cố ý). Giờ có hai lựa chọn. Patch cho nó luôn chấp nhận thì được, nhưng kém sang. Cách đúng là viết keygen: vì serial chỉ phụ thuộc username và toàn phép tính xuôi, ta chép y nguyên thuật toán sang Python rồi sinh serial cho username bất kỳ.

```python
def serial_for(user):
    acc = 0x1505
    for ch in user.encode():
        acc = ((acc * 33) + ch) & 0xFFFFFFFF
    return "%08X" % acc
# alice -> 0F174DC3
```

Chú ý cái bẫy mà người mới hay vướng: hash này một chiều, không đảo được username từ serial. Nhưng bạn **không cần** đảo, vì username do bạn chọn. Chỉ cần tính xuôi đúng như crackme. Đây là tư duy keygen đã gặp ở [Bài 3.6](/posts/tr-3-6-lab-viet-keygen/), lặp lại ở đây để nó thành phản xạ: phân biệt "đảo ngược thuật toán" với "tính lại thuật toán".

## Cấp 3: string ẩn và obfuscation

Crackme thứ ba giấu password. Mở ra bạn không thấy chuỗi nào, chỉ thấy một mảng byte và vòng lặp:

```csharp
static readonly byte[] Enc = { 127,83,82,90,73,79,89,99,113,89,99,8,14 };
...
if ((byte)(input[i] ^ 0x3C) != Enc[i]) return false;
```

Logic rõ ràng: nó XOR từng ký tự nhập với 0x3C rồi so với mảng. Vậy password = mảng XOR ngược lại 0x3C. Vài dòng Python ra ngay `Confuse_Me_42`. String encryption kiểu này (XOR hằng số) chỉ làm chậm bạn vài phút, không chặn được.

Phần thú vị là khi crackme được chạy qua một obfuscator thật như ConfuserEx. Mở lại trong dnSpy bạn sẽ thấy tên class và method biến thành ký tự Unicode vô nghĩa, chuỗi bị chuyển thành lời gọi hàm giải mã lúc chạy, và control flow bị làm rối. Lúc này:

- Chạy `de4dot -f level3.dll` để nó nhận diện protector, phục hồi tên, giải chuỗi tĩnh, làm phẳng control flow. Phần lớn ConfuserEx bản cũ bị de4dot xử gọn.
- Nếu string bị mã hoá runtime mà de4dot không giải được, quay lại [Bài 5.3](/posts/tr-5-3-debug-net-khong-source-dnspy/): đặt breakpoint trong dnSpy tại hàm giải mã, chạy tới đó, đọc chuỗi đã giải trong cửa sổ Locals. Vì .NET luôn chạy trên CLR, luôn có đường debug để tóm giá trị thật, bất kể obfuscate thế nào.

Đó là điểm mạnh lẫn điểm yếu của managed code: khó giấu hơn native nhiều, vì runtime buộc phải hiểu được bytecode thì mới chạy được, mà cái gì runtime hiểu được thì bạn cũng hiểu được.

## Checklist ghi nhớ
- Crackme .NET cấp dễ chỉ là đọc decompiled C#, password nằm trong `ldstr`.
- Thuật toán kiểm tra thì viết keygen, chép logic tính xuôi, đừng cố đảo hàm một chiều.
- String encryption kiểu XOR/Base64 custom giải ngược trong vài phút.
- Obfuscation thật: thử de4dot trước, không được thì trace runtime trong dnSpy.
- Managed code khó giấu vì CLR phải hiểu được bytecode, nên bạn luôn có đường vào.
