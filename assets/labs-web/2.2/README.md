# Lab 2.2 - Blind SQL injection (boolean-based + time-based)

App Flask + sqlite khong tra ve du lieu truy van, chi lo gian tiep:

- `GET /api/check?user=` : tra `FOUND` / `NOTFOUND`. Oracle boolean: chen dieu
  kien, quan sat FOUND/NOTFOUND de doan tung bit.
- `GET /api/log?user=` : chay dung cau truy van nhung LUON tra `ok` (khong lo
  boolean). Phai dung time-based. sqlite khong co `SLEEP()` nen ta ep tre bang
  `HEX(RANDOMBLOB(N))` (N lon -> tinh toan lau).

Muc tieu: trich mat khau cua `admin` (chinh la FLAG) tung ky tu.

## Yeu cau

- Python 3, Flask, curl.

## Chay

```bash
PORT=8022 python3 app.py       # terminal 1
PORT=8022 python3 exploit.py   # terminal 2
```

`exploit.py` tu dong: do dai mat khau -> binary search tung ky tu qua boolean,
roi minh hoa trich 4 ky tu dau bang time-based de chung minh oracle do tre hoat dong.

## Ket qua

- Boolean-based trich day du: `WEB{bl1nd_b00l3an_and_t1me}` (27 ky tu).
- Time-based: `CASE WHEN 1=1` tre ~1.4s, `1=2` tre ~0.2s -> phan biet true/false.
  4 ky tu dau trich ra `WEB{` khop voi boolean.

Xem `transcript.txt` la output that.

## Hieu chinh (neu may nhanh/cham)

Trong `exploit.py` doi hai hang so:

- `BLOB` : kich thuoc RANDOMBLOB. May cham thi giam, may nhanh thi tang de
  tre ro rang hon (lab goc ~1.1s voi 90.000.000).
- `THRESHOLD` : nguong giay de coi la TRUE (mac dinh 0.5s).

## Canh bao

App co y de lo hong, chi chay local loopback, KHONG deploy ra Internet.
