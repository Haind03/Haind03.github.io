# Dap an Lab 1.1

## Nhiem vu 1: kieu that cua tung file

| Ten file | Duoi noi doi | Magic byte dau | Kieu that |
|---|---|---|---|
| `report.pdf`  | .pdf | `89 50 4E 47 0D 0A 1A 0A` | PNG image |
| `hoa-don.pdf` | .pdf | `FF D8 FF E0` | JPEG image |
| `logo.jpg`    | .jpg | `25 50 44 46 2D` (`%PDF-`) | PDF document |
| `backup.dat`  | .dat | `50 4B 03 04` (`PK..`) | ZIP container |
| `anh.png`     | .png | `64 61 79 20` (`day `) | text thuong, khong co magic anh |

Bang chung la byte dau, khong phai duoi. ZIP `PK\x03\x04` can nhin sau moi biet la docx/xlsx/apk hay zip thuong (xem muc luc ben trong).

## Nhiem vu 2: pha va va chu ky PNG

PNG signature 8 byte: `89 50 4E 47 0D 0A 1A 0A`. Dap 4 byte dau ve 0 lam `file` tra ve `data`. Va lai 4 byte `89 50 4E 47` la du de `file` nhan ra PNG tro lai (xem `transcript.txt` muc B4). Day la ly do khong bao gio tin extension: chi can doi vai byte dau la "hong" file truoc mat nguoi dung, nhung du lieu van con.

## Nhiem vu giay but: doc day byte dau

```
a)  25 50 44 46 2D 31 2E 37     -> PDF 1.7            (%PDF-1.7)
b)  50 4B 03 04 14 00 06 00     -> ho ZIP             (nhin sau moi ro docx/apk)
c)  FF D8 FF E0 00 10 4A 46     -> JPEG/JFIF
d)  7F 45 4C 46 02 01 01 00     -> ELF 64-bit         (\x7fELF, byte 5 = 02 => 64-bit)
e)  4D 5A 90 00 03 00 00 00     -> PE/DOS (Windows)   (MZ)
```

## Ghi nho
- Luon doc toi thieu 8 byte dau, doi chieu bang magic.
- Voi dinh dang co footer (JPEG ket thuc `FF D9`, PNG co `IEND`), xem them cuoi file bang `xxd file | tail`.
- `file` dua tren thu vien magic; `xxd` cho ban nhin truc tiep byte de tu ket luan.
