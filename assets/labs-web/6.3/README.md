# Lab 6.3 - Open redirect

App cho phep chuyen huong toi URL do nguoi dung dua ma khong (hoac kiem sai)
tinh hop le. Ke tan cong dung link nam tren domain dang tin de day nan nhan
ra site gia, hoac lam ro ri token qua tham so redirect.

## Thanh phan

| File | Vai tro |
|---|---|
| `app.py` | App Flask, bind `127.0.0.1:8059`, 3 endpoint redirect co loi |
| `exploit.py` | Doc header Location de thay nan nhan bi day di dau |
| `transcript.txt` | Output that cua lan chay |

## Cach chay

```bash
python3 app.py        # terminal 1
python3 exploit.py    # terminal 2
```

## Ba loi

1. `/go?url=` khong kiem gi: chuyen huong di bat ky dau. Link
   `http://127.0.0.1:8059/go?url=https://evil.example` trong rat dang tin
   (domain that) nhung day nan nhan ra site gia -> phishing.

2. `/login?next=` kiem ngay tho `next.startswith("/")`. Chuoi `//evil.example`
   cung bat dau bang `/` nhung trinh duyet hieu la URL protocol-relative, tuc
   `https://evil.example`. Day la cach vuot pho bien nhat. (Bien the `/\evil`
   tuy trinh duyet; o day Werkzeug encode dau `\` thanh `%5C`.)

3. `/sso?next=` dinh token vao URL tra ve roi redirect. Neu `next` tro ra
   ngoai, token (o day la flag) se nam trong request toi domain attacker
   (qua query string, hoac qua header Referer khi trang dich tai tai nguyen).

## Vi sao nguy hiem

- Phishing dang tin hon vi link khoi dau o domain that.
- Chain voi SSRF: open redirect lam "ban dap" de vuot filter SSRF (xem lab 6.2,
  endpoint `/bounce`).
- Ro ri token: redirect_uri mo trong OAuth/SSO lam lo code/token (lien quan
  bai 4.4).

## Cach va

- Khong redirect toi URL do client kiem soat. Neu buoc phai, dung whitelist
  duong dan/host noi bo, hoac map qua ID (`?next=profile` -> tra cuu bang).
- Chi cho URL tuong doi va tu chan `//`, `/\`, `https:`...; tot nhat la ep
  redirect ve cung origin.
- Khong nhet token/secret vao URL redirect.
