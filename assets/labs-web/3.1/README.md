# Lab 3.1 - Reflected XSS theo context

App Flask tu chua, co y khong escape input, phan chieu (reflect) cung mot tham so `q`
vao ba context khac nhau de ban thay ro: payload khong co loai "dung moi noi", phai
chon theo noi input roi ra.

## Thanh phan
- `app.py` : app co lo hong, cong 8031 (loopback).
- `exploit.py` : client python dung `requests`, gui payload hop tung context va kiem tra
  payload co phan chieu nguyen van vao context nguy hiem hay khong.
- `transcript.txt` : output that cua lan chay (curl tho + exploit.py).

## Chay
```bash
python3 app.py            # terminal 1, lang nghe 127.0.0.1:8031
python3 exploit.py        # terminal 2
```
Tat app bang Ctrl+C khi xong.

## Cach verify (khong can trinh duyet)
XSS thuc thi trong trinh duyet, nhung dieu kien can va du de no chay la: payload di vao
context nguy hiem ma KHONG bi escape. Ta chung minh dieu do bang cach doc response va
tim chuoi "breakout" (chuoi pha context) xuat hien nguyen van:

| Endpoint | Context | Payload | Dau hieu PASS trong response |
|---|---|---|---|
| `/html` | than HTML | `<script>alert(document.domain)</script>` | the `<script>` nguyen van, khong thanh `&lt;script&gt;` |
| `/attr` | value cua input | `"><img src=x onerror=alert(1)>` | `value=""><img ...>` (nhay kep va `>` dong duoc the) |
| `/js` | JS string literal | `';alert(String.fromCharCode(88,83,83));//` | `var keyword = '';alert(...);//';` (nhay don dong duoc) |
| `/safe` | than HTML (doi chung) | `<script>alert(1)</script>` | bi bien thanh `&lt;script&gt;`, KHONG nguy hiem |

Neu chuoi breakout con nguyen van, trinh duyet se parse no thanh markup hoac cau lenh JS
va thuc thi. Day la ket qua that trong `transcript.txt`: ca ba context PASS, `/safe` chan duoc.

## Phong thu
Escape theo dung context dau ra: HTML body va attribute dung HTML entity encoding
(`<` thanh `&lt;`, `"` thanh `&quot;`), JS string dung JS/JSON encoding. Khong bao gio
nhet thang du lieu nguoi dung vao HTML. Trong lab, `/safe` dung `markupsafe.escape`.
