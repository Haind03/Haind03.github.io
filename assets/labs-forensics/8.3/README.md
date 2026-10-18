# Lab 8.3: Mobile forensics, Android SMS/WhatsApp va iOS backup

Lab chay that di kem [Bai 8.3](../../phan-08-browser-email-mobile/8.3-mobile-forensics.md).
Artifact la SQLite gia lap dung cau truc that. Tin nhan mo phong, khong dung du lieu rieng
tu that. Lab khong tao file `.ab` (phai co thiet bi); no vao thang buoc doc SQLite sau khi
backup da duoc bung, la phan ky nang chinh.

## File trong lab
- `make_artifacts.py` tao:
  - `backup/android/mmssms.db` (bang `sms`: `address`, `body`, `date` epoch mili giay,
    `type` 1=nhan 2=gui) va mot file `mmssms.db-wal` THAT chua tin moi nhat chua checkpoint.
  - `backup/android/msgstore.db` (WhatsApp, bang `messages`, `timestamp` mili giay).
  - `backup/ios/<UDID>/Manifest.db` (anh xa `domain`+`relativePath` -> `fileID` bam) va
    file sms.db bam ten `ios/<UDID>/3d/3d0d...28` (bang `message`, `date` CoreData nano-giay).
- `solve.py` mo moi db o che do READ-ONLY (giu nguyen bang chung va -wal), doi dung don vi
  thoi gian, trich tin nhan, minh hoa cai bay WAL, va di tuyen anh xa iOS.
- `transcript.txt` output that.

## Chay
```bash
python3 -I make_artifacts.py backup
python3 -I solve.py backup
```

## Nhiem vu (khop muc 3 cua bai hoc)
1. (Tren thiet bi that) hash file `.ab`, giai bang `abe.jar`, bung tar. Lab nay bat dau sau
   buoc do, thang vao SQLite.
2. Doc `mmssms.db` bang `sms`, doi `date` ra UTC dung (mili giay), liet ke theo thoi gian va huong.
3. Kiem co file `-wal` khong; dem so tin khi BO va khi GIU `-wal`, giai thich chenh lech.
4. Voi iOS: tra Manifest.db tim fileID cua `sms.db`, mo file bam, doc tin, doi CoreData ra UTC.
5. Ghi mot dong ket luan ve muc acquisition va pham vi (cai gi khong co trong logical backup).

## Dap an rut gon
- Don vi thoi gian: Android/WhatsApp = epoch mili giay (`/1000`); iOS CoreData = nano-giay tu
  2001 (`/1e9 + 978307200`). Moi nen mot cong thuc.
- Cai bay WAL: bo `mmssms.db-wal` mat dung tin moi nhat ("Nho mang USB qua giup minh").
  Luon thu ca ba file db, `-wal`, `-shm`; mo read-only de khong tu checkpoint lam mat wal.
- iOS: ten file bi bam, phai qua Manifest.db moi biet `Library/SMS/sms.db` nam o file bam nao.

## Cai bay da cai san trong lab
- Tin moi nhat chi nam trong `-wal`; mot read-write vo y se checkpoint va "nuot" wal.
- Doi sai don vi thoi gian la moc nhay ra nam 2050+ hoac the ky xa.
- WhatsApp that thuong ma hoa (crypt14/15) can key; lab dung ban msgstore.db chua ma hoa de tap doc.
