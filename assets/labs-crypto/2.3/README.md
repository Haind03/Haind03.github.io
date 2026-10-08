# Lab 2.3: Transposition (rail fence) va Enigma

Script giải cho phần Lab của Bài 2.3.

## Chạy

```bash
python3 solve.py     # pha rail fence (transposition)
python3 enigma.py    # Enigma gian luoc + brute 26^3 vi tri xuat phat
```

Chỉ dùng thư viện chuẩn (`string`). `transcript.txt` là output thật của cả hai script.

## File

- `solve.py`: đo IoC (cao nhu text thuong, báo hiệu transposition), brute số rail từ 2 tới 7, chấm điểm chi-squared, khôi phục bản rõ.
- `enigma.py`: Enigma 3 rotor thuần Python (rotor + reflector + plugboard), round-trip, kiểm tính chất "không chữ nào map về chính nó", rồi brute 26^3 tìm lại vị trí xuất phát.
- `transcript.txt`: output thật.

## Ý chính

- Rail fence chỉ xáo vị trí, IoC và tần suất không đổi, nên brute số rail là ra. Bản rõ: `WEAREDISCOVEREDFLEEATONCE`.
- Enigma tự nghịch đảo (nhờ reflector) và không chữ nào tự mã thành chính nó, đó là kẽ hở Bletchley Park khai thác. Thiếu vị trí xuất phát thì 26^3 = 17576 khả năng, brute trong tích tắc.
