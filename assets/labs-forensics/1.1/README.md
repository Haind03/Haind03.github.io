# Lab 1.1: Magic byte va extension noi doi

Lab chay that tren Linux (khong can root). Muc tieu: luyen phan xa khong tin duoi file, luon doc magic byte de biet kieu that.

## Cong cu
`file`, `xxd`, `dd`, `python3`, ImageMagick (`convert`), `zip`.

## Chay lab
```bash
bash make.sh     # tao bo file bi doi sai duoi
bash solve.sh    # nhan dien kieu that, va demo pha/va magic byte
```
`transcript.txt` la output THAT da chay san de doi chieu.

## Artifact da tao san (nhe, giu trong lab)
- `report.pdf`  : thuc ra la PNG
- `hoa-don.pdf` : thuc ra la JPEG
- `logo.jpg`    : thuc ra la PDF
- `backup.dat`  : thuc ra la ZIP
- `anh.png`     : thuc ra la text thuong
- `goc.png`     : PNG hop le, dung cho bai tap pha/va chu ky

## Nhiem vu
1. Doc 8 byte dau moi file bang `xxd -l 8`, doi chieu bang magic trong `detect.py`, noi moi file THUC SU la gi va bang chung byte nao. Kiem lai bang `file`.
2. Pha chu ky: copy `goc.png` thanh `benh-nhan.png`, dap 4 byte dau thanh 0, xac nhan `file` khong con nhan ra PNG. Tu viet lenh va 4 byte dung de va lai cho den khi `file` bao PNG tro lai.
3. Bai tap giay but (khong chay tool): doc 5 day byte dau trong `solution.md` muc "Nhiem vu giay but" va noi moi cai la dinh dang gi.

## Dap an
Xem `solution.md`. Output that: `transcript.txt`.
