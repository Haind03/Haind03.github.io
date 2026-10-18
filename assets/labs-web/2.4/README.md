# Lab 2.4 - NoSQL injection (MongoDB) va auth bypass

App Flask mo phong tang luu tru Mongo. Lo hong: nhet thang gia tri nguoi dung
vao `find_one({"username": <u>, "password": <p>})`. Neu `<u>`/`<p>` la DICT
toan tu (`$ne`, `$gt`, `$regex`...) thay vi chuoi, logic so khop bi lat nguoc.

Hai dang dau vao:

- `POST /login` JSON: `{"username":"admin","password":{"$ne":null}}` -> bypass.
- `GET /login` query-string: `?username=admin&password[$ne]=x` (app tu parse
  ngoac `[$op]` thanh dict, giong cach qs cua Express hay mang cua PHP lam).

Muc tieu: dang nhap thanh admin de lay FLAG, va trich mat khau admin bang `$regex`.

## Yeu cau

- Python 3, Flask, va `mongomock` (`pip install flask mongomock`), curl.
- Neu KHONG cai duoc mongomock: app tu dong chuyen sang ban mo phong toan tu
  `$ne/$gt/$regex/$in/$eq` bang Python thuan (xem nhanh o `app.py`, ham
  `_match_field`). Luc do field `backend` tra ve `python-mo-phong`. Logic auth
  bypass van dung het. Lab goc chay voi mongomock 4.3.0.

## Chay

```bash
PORT=8024 python3 app.py     # terminal 1
PORT=8024 bash exploit.sh    # terminal 2 (goi them exploit_regex.py)
```

## Ket qua

- Dang nhap thuong sai pass: `ok:false` (401).
- `{"$ne":null}`, `{"$gt":""}`, va `password[$ne]=x` deu dang nhap thanh admin,
  tra `WEB{nosql_operator_injection_auth_bypass}`.
- `$regex` trich mat khau admin tung ky tu: `Adm1nSecret2024`.

Xem `transcript.txt` la output that.

## Phong chong

- Ep kieu dau vao: username/password PHAI la chuoi; tu choi khi nhan dict/mang.
- Khong truyen truc tiep object nguoi dung vao query. Tach dieu kien ro rang.

## Canh bao

App co y de lo hong, chi chay local loopback, KHONG deploy ra Internet.
