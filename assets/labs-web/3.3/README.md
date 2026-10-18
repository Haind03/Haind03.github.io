# Lab 3.3 - DOM-based XSS

Khac han reflected/stored: server o day VO CAN. No chi tra ve mot trang tinh, khong bao
gio nhin thay payload. Lo hong nam o JavaScript phia client: no lay du lieu tu `location.hash`
(source, nguon du lieu ke tan cong kiem soat) va nhet thang vao `innerHTML` (sink, diem
du lieu bien thanh code/markup). Vi phan sau dau `#` khong duoc gui len server, cac bo loc
phia server khong he thay payload.

## Thanh phan
- `app.py` : Flask tra ve trang tinh co lo hong, cong 8034. Trang luon y het nhau.
- `exploit.py` : phan tich luong source -> sink, va chung minh fragment khong gui len server.
- `dom-emulate.js` : "trinh duyet mini" bang Node, CHAY that doan JS cua trang de cho thay
  payload thuc thi (khong can GUI).
- `transcript.txt` : output that.

## Chay
```bash
python3 app.py                                      # terminal 1, cong 8034
python3 exploit.py                                  # terminal 2, phan tich luong
node dom-emulate.js "<img src=x onerror=alert(document.domain)>"   # terminal 2, chay that
```
Ctrl+C app khi xong.

## Payload
```
http://127.0.0.1:8034/#<img src=x onerror=alert(document.domain)>
http://127.0.0.1:8034/#<img src=x onerror="exfil(document.cookie)">
```
Luu y: payload dung `<img onerror=...>` chu khong dung `<script>`. Khi gan qua `innerHTML`,
trinh duyet KHONG chay the `<script>` moi chen, nhung VAN chay event handler nhu `onerror`,
`onload`. Day la ly do payload DOM XSS kinh dien dung the anh loi.

## Cach verify (khong can trinh duyet GUI)
1. **Phan tich luong (`exploit.py`)**: tai trang, xac nhan co source `location.hash` chay
   thang toi sink `innerHTML`, giua chung khong co ham lam sach (DOMPurify, textContent...).
2. **Fragment khong roi trinh duyet**: `exploit.py` cho thay khi yeu cau URL co `#...`, path
   that su gui len server chi la `/`, va trang tra ve y het trang goc. Bo loc server khong
   the chan loai XSS nay.
3. **Thuc thi that (`dom-emulate.js`)**: Node tai doan JS THAT ma server ship, dat
   `location.hash = payload`, chay script, va mo phong dung hanh vi then chot cua trinh
   duyet khi gan `innerHTML` (parse HTML, kich hoat `onerror`/`onload`). Ket qua trong
   `transcript.txt`: handler ke tan cong chay that, `alert()` in ra `127.0.0.1` va `exfil()`
   gui di `session=dom-victim-9b1c`.

## Phong thu
- Dung `textContent`/`innerText` thay vi `innerHTML` khi chi can hien van ban.
- Neu buoc phai dung innerHTML, lam sach bang DOMPurify.
- Tranh cac sink nguy hiem: `eval`, `document.write`, `setTimeout(string)`,
  `element.innerHTML/outerHTML`, `insertAdjacentHTML`, `jQuery .html()`.
- Coi moi source ke tan cong dieu khien duoc la do: `location.*`, `document.URL`,
  `document.referrer`, `postMessage`, `localStorage`.
