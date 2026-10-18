# Lab 8.1: Browser forensics, dung lai hoat dong duyet web

Lab chay that di kem [Bai 8.1](../../phan-08-browser-email-mobile/8.1-browser-forensics.md).
Artifact la SQLite gia lap dung cau truc that cua Chrome va Firefox, khong dung du lieu
rieng tu that.

Diem mau chot cua bai la timestamp:
- Chrome/Edge `History` dung WebKit epoch: microgiay tu `1601-01-01`.
  Doi ra UTC: `last_visit_time/1000000 - 11644473600`.
- Firefox `places.sqlite`/`formhistory.sqlite` dung PRTime: microgiay tu `1970-01-01`.
  Doi ra UTC: `last_visit_date/1000000` (KHONG tru gi).
Lan cong thuc giua hai trinh duyet la loi kinh dien, lech 369 nam.

## File trong lab
- `make_artifacts.py` tao `profile/History` (bang `urls`, `visits`, `downloads` voi WebKit
  timestamp), `profile/places.sqlite` va `profile/formhistory.sqlite` (PRTime).
- `solve.sh` truy van bang `sqlite3`, doi timestamp, trich tu khoa tim kiem (giai URL-encoding
  bang `python3`), liet ke download, roi dung timeline.
- `transcript.txt` output that.

## Chay
```bash
python3 -I make_artifacts.py profile
bash solve.sh profile
```

## Nhiem vu (khop muc 3 cua bai hoc)
1. Mo `History`, liet ke trang ghe nhieu nhat, doi `last_visit_time` ra UTC.
2. Trich truy van search tu URL va giai URL-encoding ra tu khoa.
3. Liet ke download kem `target_path` va trang khoi phat.
4. Lam tuong tu voi Firefox `places.sqlite` va `formhistory.sqlite`, chu y cong thuc khac.
5. (Mo rong) chay `hindsight` tren mot profile Chrome that va doi chieu timeline.

## Dap an rut gon
- Chuoi duyet: go Google (TYPED) -> search "usb wiping tool" (FORM_SUBMIT) -> click
  `eraser-tools.example/download` (LINK) -> tai `eraser-setup.exe` (7.3 MB) -> ghe webmail.
- formhistory Firefox lo tu khoa "how to wipe usb without trace" nguoi dung go nhung khong
  chac da bam Enter (lich su khong ghi, formhistory van ghi).
- Tu khoa tim kiem the hien y dinh ro nhat; download cho biet cong cu da lay.

## Cai bay da cai san trong lab
- Cot `transition` phan biet TYPED (go tay, co y) voi LINK (click/redirect).
- Neu doi timestamp Chrome theo Unix se nhay ra the ky 24; day la dau quen tru 11644473600.
- `formhistory` giu ca du lieu go vao form ma lich su khong co.
