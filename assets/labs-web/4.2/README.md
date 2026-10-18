# Lab 4.2: Session yeu (predict, fixation, cookie, logout)

App Flask tu chua minh hoa bon loi quan ly session. Chay local, `127.0.0.1:8042`.

## Lo hong co trong app
- Session id cap tuan tu (`00001000`, `00001001`, ...): doan duoc token cua nguoi khac.
- Session fixation: server chap nhan `?sid=` / cookie do client mang san va giu nguyen sau khi login (khong regenerate token).
- Set-Cookie thieu `HttpOnly`, `Secure`, `SameSite`.
- `/logout` chi xoa cookie o client, khong huy session server-side: token cu van dung.

## Endpoint
- `POST /login` form `username`, `password` (them `?sid=...` de ep session id). Tra token, set cookie.
- `GET /me` doc cookie `SESSIONID`, cho biet dang la ai (admin thi kem flag).
- `POST /logout`.

Tai khoan: `mallory:mallory`, `admin:S3cretAdminPw`.

## Chay
```bash
python3 app.py        # terminal 1
python3 exploit.py    # terminal 2
```

## Nhiem vu
1. Doan session cua admin tu token cua chinh minh (tuan tu).
2. Ep victim dung session id co dinh roi chiem (fixation).
3. Chung minh cookie thieu co bao mat.
4. Chung minh token cu van dung sau logout.

## Dap an
`exploit.py` chay ca bon man, ket qua that trong `transcript.txt`:
chiem session admin bang predict va bang fixation, flag `FLAG{4.2_weak_session_hijack}`.

## Thu nhanh bang curl
```bash
# login mallory, xem token va Set-Cookie
curl -si -X POST localhost:8042/login -d username=mallory -d password=mallory
# ep session id co dinh
curl -s -X POST "localhost:8042/login?sid=deadbeef" -d username=admin -d password=S3cretAdminPw
# attacker dung lai sid co dinh
curl -s localhost:8042/me -b SESSIONID=deadbeef
```
