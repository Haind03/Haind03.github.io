# Lab 5.2 - Broken Access Control / privilege escalation

Mot app co ba kieu loi kiem quyen kinh dien, moi kieu mot flag.

## Thanh phan

| File | Vai tro |
|---|---|
| `app.py` | App Flask co lo hong, bind `127.0.0.1:8051` |
| `exploit.py` | Khai thac ca ba duong leo quyen |
| `transcript.txt` | Output that cua lan chay |

## Cach chay

```bash
python3 app.py        # terminal 1
python3 exploit.py    # terminal 2
```

Tai khoan: `carol:pw` (user thuong), `admin:S3cr3t-admin` (admin).

## Ba lo hong

1. Forced browsing (duyet mo): `GET /backup/users.json` khong co bat ky
   kiem tra nao. "Khong co link" khong phai la kiem soat truy cap. Dung
   wordlist (ffuf, dirsearch) la tim ra.

2. Tin role tu client: `/admin/panel` chi so sanh `cookie role == "admin"`.
   Role nam o cookie do client gui, nguoi dung tu sua `role=admin` la vao.
   Quyen phai suy ra tu phien o server, khong bao gio tu gia tri client gui.

3. Verb/flow tampering: `/admin/promote` kiem quyen o buoc GET (hien thi form)
   nhung buoc POST (hanh dong that) lai quen kiem tra. Gui thang POST la tu
   phong minh len admin. Kiem quyen phai dat o buoc thuc thi hanh dong, va
   ap cho moi method.

## Cach va

- Kiem quyen o server, dua tren phien dang nhap, cho MOI endpoint va MOI
  method. Mac dinh la tu choi (deny by default).
- Khong bao gio tin role/quyen gui tu client (cookie, hidden field, header).
- Tap trung logic phan quyen vao mot cho (middleware/decorator) de khong sot.
- Khong dua vao "khong ai biet duong dan" (security by obscurity).
