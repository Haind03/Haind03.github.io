# Lab 2.1 - SQL injection co ban (UNION-based + error-based)

App Flask + sqlite co 2 cho dinh SQLi do noi chuoi truc tiep vao cau truy van:

- `POST /login` : `... WHERE username='<u>' AND password='<p>'` -> auth bypass.
- `GET /search?q=` : `SELECT id,title,body FROM articles WHERE title LIKE '%<q>%'`
  (3 cot) -> UNION-based de dump cac bang khac.

App o che do "debug": khi truy van loi no tra nguyen van thong bao loi cua
sqlite, nho vay ta lam error-based detection (xac dinh so cot qua ORDER BY).

Muc tieu: lay FLAG trong bang `secret_flag`.

## Yeu cau

- Python 3, Flask (`pip install flask`), curl. Khong can gi them (sqlite di kem Python).

## Chay

```bash
PORT=8021 python3 app.py      # terminal 1, lang nghe 127.0.0.1:8021
PORT=8021 bash exploit.sh     # terminal 2
```

DB duoc tao lai sach moi lan khoi dong (`lab21.db`).

## Ket qua mong doi

- Auth bypass: dang nhap thanh cong voi `username=admin'-- -` ma khong can mat khau.
- ORDER BY 4 bao loi "out of range - should be between 1 and 3" -> 3 cot.
- UNION dump bang `users` ra username/password, va bang `secret_flag` ra FLAG.

FLAG: `WEB{un10n_select_dump_toan_bo_db}` (xem `transcript.txt` la output that).

## File

- `app.py` : app co lo hong.
- `exploit.sh` : chuoi khai thac bang curl.
- `transcript.txt` : output that cua lan chay.

## Canh bao

App co y de lo hong, chi chay local loopback, KHONG deploy ra Internet.
