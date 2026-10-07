---
title: "Bài 8.4: Lab, giải một crackme Go từ đầu đến cuối"
date: 2026-10-06 09:02:00 +0700
categories: ["Technique Reverse", "Phần 8 · Go"]
tags: [reverse-engineering, golang]
render_with_liquid: false
---
Ba bài trước cho bạn lý thuyết: binary Go to vì mang cả runtime, pclntab giữ tên hàm, string Go đi theo độ dài chứ không kết thúc bằng null. Bài này ghép tất cả lại trên một crackme thật mà tôi build bằng Go 1.22 ngay trong lúc viết, rồi dẫn bạn đi tìm password như thể chưa từng thấy source.

Mọi con số dưới đây là output thật, không phải tôi bịa cho đẹp.

## Bước 0: triage, biết mình cầm cái gì

Luôn bắt đầu bằng `file` và nhìn kích thước:

```
$ file crackme
crackme: ELF 64-bit LSB executable, x86-64, statically linked,
         Go BuildID=HFE5KTdi..., with debug_info, not stripped
$ ls -la crackme
1895284 bytes
```

Hai chi tiết tố cáo ngay đây là Go: **statically linked** (gần 1.9 MB cho một chương trình in ra một dòng) và chuỗi **Go BuildID** trong header. Nếu bạn còn nghi, `go version` đọc được build info nhúng sẵn:

```
$ go version crackme
crackme: go1.22.0
```

Trên Windows thì DIE sẽ báo thẳng "Compiler: Go". Xong triage: đây là binary Go, build bằng Go 1.22, chưa strip.

## Bước 1: lấy lại tên hàm

Vì chưa strip, pclntab còn nguyên và tên hàm lộ ra ngay cả trong `strings`:

```
$ strings crackme | grep "main\."
main.main
main.checkKey
```

`main.main` là điểm vào thật của tác giả (khác với `main` trong C, Go có runtime chạy trước rồi mới gọi `main.main`). `main.checkKey` nghe như hàm kiểm tra. Đã có mục tiêu.

Trong Ghidra/IDA, nếu tên không tự hiện (hoặc binary bị strip), chạy GoReSym để phục hồi rồi import vào, đúng như Bài 8.2. Ở đây chưa strip nên nhảy thẳng vào `main.checkKey`.

Một điểm đáng nhớ: tôi thử strip hẳn bằng `-ldflags "-s -w"`, file tụt từ 1.9 MB xuống 1.23 MB, **nhưng `main.checkKey` vẫn còn trong strings và `go version` vẫn đọc ra go1.22.0.** Đó là vì pclntab không phải symbol table thường, `-s -w` không đụng tới nó. Với reverser, đây là tin vui: binary Go stripped vẫn khai ra tên hàm.

## Bước 2: đọc logic của checkKey

Decompile `main.checkKey` (hoặc đọc pseudocode trong Ghidra sau khi có symbol). Bỏ qua phần boilerplate của Go, phần lõi quy về thế này:

```go
func checkKey(input string) bool {
    want := []byte{0x50, 0x79, 0x56, 0x68, 0x7a, 0x79, 0x82, 0x61, 0x7a, 0x2e, 0x2d}
    if len(input) != len(want) {      // so len trước, len(want) = 11
        return false
    }
    for i := 0; i < len(input); i++ {
        if (input[i]^0x17)+byte(i) != want[i] {
            return false
        }
    }
    return true
}
```

Khi đọc ở mức assembly, có vài dấu hiệu Go bạn sẽ gặp:

- **So sánh độ dài trước tiên.** String Go là một struct gồm con trỏ data và length. Hàm lấy length của input so với 11 (hằng số). Thấy một `cmp` với hằng số ngay đầu hàm kiểm tra là nó đang chặn sai độ dài, cho bạn biết password dài đúng 11 ký tự.
- **Vòng lặp qua từng byte.** Bên trong có `movzx` lấy một byte của input, `xor` với 0x17, `add` chỉ số vòng lặp, rồi `cmp` với một byte trong mảng hằng. Mảng `want` nằm trong `.rodata`.
- **Không có password dạng plaintext.** Tôi kiểm `strings crackme | grep GoCrackMe24` ra 0 kết quả. Password bị biến đổi nên không lộ, bạn bắt buộc phải đảo thuật toán.

## Bước 3: đảo ngược để lấy password

Quan hệ là `want[i] = (input[i] XOR 0x17) + i`. Đảo lại:

```
input[i] = (want[i] - i) XOR 0x17
```

Viết vài dòng Python cho chắc:

```python
want = [0x50,0x79,0x56,0x68,0x7a,0x79,0x82,0x61,0x7a,0x2e,0x2d]
pw = ''.join(chr(((w - i) & 0xff) ^ 0x17) for i, w in enumerate(want))
print(pw)   # GoCrackMe24
```

Ra `GoCrackMe24`. Thử lại trên binary thật:

```
$ ./crackme GoCrackMe24
Correct! Flag: GO{GoCrackMe24}
$ ./crackme GoCrackMe25
Wrong password.
```

Đúng. Bạn vừa reverse một crackme Go end to end: triage ra Go, dùng pclntab lấy tên hàm, đọc `checkKey`, đảo thuật toán, lấy password.

## Lab tự làm

File ở `labs/8.4/`:
- `src/crackme.go` cùng lệnh build (có cả bản thường, bản `-s -w`, và bản Windows).
- `README.md` giao nhiệm vụ.
- `solution.md` là writeup đầy đủ, kèm kết quả build và chạy thật.

Tự làm trước khi mở solution: build cả hai bản thường và stripped, xác nhận `main.checkKey` vẫn còn ở bản stripped, rồi đảo thuật toán ra password mà không chạy thử.

## Checklist ghi nhớ
- Binary Go: static-linked, to bất thường, có Go BuildID. `go version <file>` hoặc DIE xác nhận nhanh.
- Điểm vào của tác giả là `main.main`, không phải hàm `main` đầu tiên runtime gọi.
- pclntab giữ tên hàm, sống sót cả khi strip bằng `-s -w`. GoReSym để phục hồi khi IDA/Ghidra không tự nhận.
- Hàm kiểm tra Go hay so độ dài string trước, rồi lặp từng byte. Mảng hằng so sánh nằm trong .rodata.
- Password biến đổi thì không có trong strings, phải đọc thuật toán rồi đảo ngược.
