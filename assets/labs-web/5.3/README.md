# Lab 5.3 - CSRF (Cross-Site Request Forgery)

Chuc nang doi email khong co CSRF token. Nan nhan dang dang nhap chi can mo
mot trang do ke tan cong dung la bi doi email sang dia chi cua ke tan cong.

## Thanh phan

| File | Vai tro |
|---|---|
| `app.py` | App Flask, bind `127.0.0.1:8052`. Co endpoint CO LOI va endpoint BAN VA |
| `attacker.html` | Trang attacker: form an tu dong submit sang `/change-email` |
| `exploit.py` | Mo phong trinh duyet nan nhan: mang cookie phien, submit form attacker |
| `transcript.txt` | Output that cua lan chay |

## Cach chay

```bash
python3 app.py        # terminal 1
python3 exploit.py    # terminal 2
```

Tai khoan: `victim:pw`.

## Vi sao chay duoc

CSRF loi dung viec trinh duyet TU DONG dinh kem cookie phien vao moi request
toi mot site, ke ca khi request do do trang khac khoi tao. Endpoint
`/change-email` doi trang thai chi dua vao cookie phien, khong co token bi
mat nao gan voi phien, cung khong kiem Origin/Referer. Vi the mot form o trang
la cung "lam thay" nan nhan.

Trong lab, cookie phien dat `SameSite=None` de minh hoa cau hinh de bi khai
thac. `exploit.py` mo phong hanh vi trinh duyet: no doc form trong
`attacker.html` roi gui bang chinh session (cookie) cua nan nhan, dung nhu khi
nan nhan mo trang do trong trinh duyet dang dang nhap.

Endpoint `/change-email-safe` yeu cau `csrf_token` khop token trong phien.
Trang attacker o origin khac KHONG doc duoc token nay (same-origin policy) nen
khong gia mao duoc, request bi tra 403.

## Cach va

- CSRF token theo tung phien/tung form, kiem o phia server cho moi request
  doi trang thai.
- Dat cookie phien `SameSite=Lax` (hoac `Strict`). Lax da chan phan lon CSRF
  dang form POST cross-site.
- Kiem `Origin`/`Referer` cho cac hanh dong nhay cam.
- Yeu cau xac nhan lai (mat khau/OTP) cho thao tac quan trong.
