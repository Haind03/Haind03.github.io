# Lab 10.2 - Chuoi client-side: Stored XSS -> CSRF -> Account Takeover

App Flask tu chua, co lo hong CO Y, bind loopback `127.0.0.1:8077`. Chay local, KHONG deploy ra Internet.

## Chuoi lo hong
- **Mat xich 1 - Stored XSS**: `POST /comment` luu binh luan; `GET /feed` render KHONG escape -> script attacker nam nguyen trong HTML, chay trong trinh duyet nguoi xem.
- **Mat xich 2 - CSRF**: `POST /account/email` doi email tai khoan dang dang nhap, khong co CSRF token, cookie `SameSite=None` -> request gia mao van doi duoc email.
- **Ghep chuoi -> ATO**: nan nhan xem `/feed` -> script attacker chay trong session nan nhan -> doi email sang email attacker -> attacker `/account/forgot` nhan reset token -> `/account/reset` -> chiem tai khoan.

Hai mat xich chinh (Stored XSS va CSRF) deu chung minh duoc truc tiep tu server, khong can GUI trinh duyet.

## Chay
```bash
pip install flask requests        # neu chua co
python3 app.py                     # server len cong 8077
python3 exploit.py                 # terminal khac
```

## Ket qua
`exploit.py`:
1. Dang binh luan chua `<script>` roi `GET /feed` -> xac nhan script tra ve nguyen ven (stored XSS).
2. Gia lap request CSRF (chi cookie session, khong CSRF token) doi email admin sang `attacker@evil.local`.
3. `/account/forgot` -> reset token gui ve email attacker -> `/account/reset` -> flag.

- `FLAG{10.2_stored_xss_csrf_account_takeover}`

Xem `transcript.txt`.

## Vá
- Escape/encode output theo context; dung template auto-escape; them CSP.
- CSRF token (hoac double-submit cookie) cho moi request doi trang thai; cookie `SameSite=Lax/Strict`.
- Buoc xac nhan mat khau cu / xac minh email khi doi email; reset token gan thoi han va one-time.
