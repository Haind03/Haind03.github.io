# Lab 11.1: Cryptopals, ba challenge xương sống

Kèm Bài 11.1 (Cryptopals). Ba script giải ba dạng đại diện của set 1 tới 3, chạy độc lập.

## File

- `c03_single_xor.py`: set 1 bài 3. Phá single-byte XOR bằng chấm điểm tần suất tiếng Anh.
- `c08_detect_ecb.py`: set 1 bài 8. Phát hiện ciphertext mã bằng AES-ECB qua đếm block trùng.
- `c17_padding_oracle.py`: set 3 bài 17. Padding oracle attack trên CBC, giải trọn plaintext mà không biết khóa.

## Chạy

```bash
python3 c03_single_xor.py
python3 c08_detect_ecb.py
python3 c17_padding_oracle.py
```

## Kết quả mong đợi

```
# c03
khoa (byte) : 88 0x58
plaintext   : Cooking MC's like a pound of bacon

# c08
so block trung (ECB): 2 -> day la ECB
so block trung (CBC): 0 -> khong lo pattern

# c17
flag: flag{p4dding_0racle_l34ks_th3_wh0le_plaintext}
```

Xem `transcript.txt` để đối chiếu output thật.

## Yêu cầu

`c08` và `c17` cần PyCryptodome (`pip install pycryptodome`). `c03` chỉ cần thư viện chuẩn.

## Điểm mấu chốt

- Padding oracle giải từng block, dùng block ngay trước làm bàn đạp, đi từ byte cuối (padding 1) ngược lên.
- Có mẹo chống nhiễu ở byte padding bằng 1 (lật byte trước rồi hỏi lại oracle), bỏ là sai biên block.
