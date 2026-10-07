---
title: "Bài 3.6: Viết keygen, khi moi serial không còn đủ"
date: 2026-10-06 08:30:00 +0700
categories: ["Technique Reverse", "Phần 3 · C: ngôn ngữ gốc của mọi thứ"]
tags: [reverse-engineering, c]
render_with_liquid: false
---
Ở bài 3.5 bạn tìm ra password của một crackme bằng cách moi nó từ bộ nhớ. Cách đó hiệu quả với loại check đơn giản: chương trình giữ serial đúng ở đâu đó rồi đem so, bạn chỉ việc đọc trộm lúc nó so. Nhưng có một loại khác cứng đầu hơn, và chính nó phân biệt người mới với người thực sự hiểu code: keygenme.

Keygenme không giữ sẵn serial nào cả. Nó **tính** serial đúng từ username ngay lúc chạy, rồi so với cái bạn nhập. Mỗi username một serial khác nhau. Moi một serial ra chỉ giải quyết được đúng một username, mà nhiều khi username còn do bạn tự nhập. Muốn thắng kiểu này, bạn phải hiểu thuật toán đủ sâu để tự sinh serial cho username bất kỳ. Thứ bạn viết ra gọi là keygen.

## Hai loại crackme, hai lối đánh

Trước khi đụng tay, phải phân loại mục tiêu. Nhìn nhầm loại là tốn công vô ích.

**Loại 1: so sánh serial cố định.** Trong code có một chuỗi hằng, hoặc một serial được dựng ra không phụ thuộc username, rồi `strcmp` với cái bạn nhập. Dấu hiệu: hàm validate không hề đọc username, hoặc đọc nhưng không dùng nó để tính serial. Lối đánh: moi serial từ bộ nhớ (bài 3.5) hoặc patch jump cho qua. Nhanh, gọn.

**Loại 2: kiểm tra theo thuật toán (keygenme).** Hàm validate lấy username, chạy qua một loạt phép tính, ra serial kỳ vọng, rồi so. Lối đánh moi serial vẫn chạy nhưng chỉ cho một username. Patch jump thì phần mềm "mở khoá" trên máy bạn nhưng bạn không có chìa tổng quát. Muốn keygen, bạn buộc phải đọc hiểu phép tính đó rồi viết lại nó.

Câu hỏi quyết định khi mở hàm validate: **nó có dùng username để tính ra cái đem so không?** Có thì là loại 2, chuẩn bị viết keygen.

## Quy trình viết keygen

Bốn bước, lần nào cũng vậy:

1. **Định vị hàm validate.** Đi từ chuỗi "Correct"/"Wrong" bằng xref, như mọi khi.
2. **Tách phần tính serial.** Đọc xem username được biến đổi thế nào: cộng dồn, nhân trọng số, băm, định dạng ra chuỗi ra sao.
3. **Viết lại thuật toán bằng ngôn ngữ của bạn.** Python là lựa chọn tự nhiên vì nhanh và không phải build.
4. **Kiểm chéo.** Chạy keygen cho một username, nạp serial vào keygenme, phải thấy "Correct". Nếu sai, bạn đọc nhầm một bước nào đó, quay lại bước 2.

## Mổ keygenme của lab

Lab [labs/3.6](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/3.6) có một keygenme nhận `username` và `serial`. Mở trong Ghidra, đi tới `validate`, bạn thấy lõi của nó là vòng lặp này (đã dịch về C cho dễ nhìn):

```c
static const uint16_t SEED[4] = { 0x1337, 0xBEEF, 0xCAFE, 0x5A5A };

for (int k = 0; k < 4; k++) {
    uint32_t acc = SEED[k];
    for (size_t i = 0; i < n; i++) {
        uint8_t c = user[i];
        acc += (c + 1) * (i + 1 + k);
    }
    blk[k] = acc & 0xFFFF;
}
```

Rồi bốn block 16-bit đó được in ra dạng hex: `"%04X%04X%04X%04X"`, chính là serial đúng.

Có hai manh mối mà bạn nên bắt được ngay trong disassembly:

- **Bốn hằng số seed đẹp** `0x1337, 0xBEEF, 0xCAFE, 0x5A5A`. Hằng số literal kiểu này nhảy vào mắt, và chúng gần như luôn là tham số của thuật toán. Thấy chúng là biết mình đang ở đúng chỗ.
- **Vòng lặp lồng đi qua từng ký tự username** với một phép nhân theo chỉ số. Đó là dấu hiệu rõ ràng của loại 2: serial phụ thuộc cả nội dung lẫn vị trí ký tự.

Thuật toán này cố tình đối xứng, nghĩa là tính xuôi được thì tính lại cũng được, không có hàm một chiều chặn đường. Keygen chỉ việc lặp lại đúng công thức.

## Keygen chưa tới mười dòng

```python
SEED = [0x1337, 0xBEEF, 0xCAFE, 0x5A5A]

def make_serial(user):
    blocks = []
    for k in range(4):
        acc = SEED[k]
        for i, ch in enumerate(user):
            acc += (ord(ch) + 1) * (i + 1 + k)
        blocks.append(acc & 0xFFFF)
    return "-".join(f"{b:04X}" for b in blocks)

print(make_serial("alice"))   # 193F-C6FA-D50C-666B
```

Chạy thử với username `alice` ra `193F-C6FA-D50C-666B`, nạp vào keygenme và nó báo "Correct". Thử `bob`, `RE_Learner`, hay bất cứ chuỗi nào khác, đều ra serial hợp lệ. Đó là khác biệt giữa "qua được một lần" và "hiểu thật": bạn vừa tái tạo được logic cấp phép của chương trình.

Writeup đầy đủ, gồm cả kết quả kiểm chéo đã chạy thật, nằm ở [labs/3.6/solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/3.6/solution.md).

## Khi nào keygen bất lực

Keygen sống được nhờ thuật toán đối xứng. Nếu validate dùng một hàm băm một chiều thật (SHA-256 chẳng hạn): tính từ username ra hash thì dễ, nhưng tìm serial sao cho hash khớp thì chỉ còn nước brute-force, bất khả thi. Mạnh hơn nữa, phần mềm thương mại thường ký serial bằng chữ ký số RSA: trong binary chỉ có public key để kiểm tra, còn private key để tạo serial thì nằm ở máy chủ nhà sản xuất. Bạn đọc hết thuật toán cũng không sinh được serial, vì thiếu khoá bí mật. Lúc đó người ta quay về patch (vô hiệu hoá bước kiểm chữ ký), và đó lại là một cuộc chơi khác, thuộc Phần 15 về anti-tamper.

Hiểu được ranh giới này quan trọng hơn bản thân cái keygen: nó cho bạn biết khi nào nên đọc thuật toán, khi nào nên chuyển sang patch.

## Checklist ghi nhớ
- Phân loại trước: validate có dùng username để tính cái đem so không? Có thì là keygenme.
- Moi serial và patch jump chỉ giải loại so sánh cố định, không cho chìa tổng quát.
- Viết keygen: định vị validate, tách phần tính serial, viết lại, kiểm chéo bằng cách nạp serial sinh ra.
- Hằng số seed đẹp và vòng lặp qua từng ký tự username là dấu hiệu của thuật toán phụ thuộc username.
- Thuật toán đối xứng thì keygen được. Hàm băm một chiều hay chữ ký RSA thì không, phải chuyển sang patch.
