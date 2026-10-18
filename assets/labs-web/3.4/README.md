# Lab 3.4 - Vuot filter va CSP

Hai chu de ghep trong mot app (cong 8035):

- **A. Filter blacklist ngay tho**: `/search` xoa literal `<script>` va `</script>`
  (phan biet HOA thuong, chi mot luot). Day la kieu loc sai kinh dien.
- **B. CSP (Content-Security-Policy)**: `/csp-inline` dung CSP co `unsafe-inline` (vo dung),
  `/csp-strict` dung `script-src 'self'` (chan inline) nhung van bi vuot nho endpoint
  JSONP `/jsonp` tren cung origin.

## Thanh phan
- `app.py` : app co lo hong, cong 8035.
- `exploit.py` : kiem tra tu dong moi buoc vuot filter va phan tich/vuot CSP.
- `transcript.txt` : output that.

## Chay
```bash
python3 app.py            # terminal 1, cong 8035
python3 exploit.py        # terminal 2
```

## A. Vi sao bon payload nay vuot duoc filter
| Payload | Vi sao qua |
|---|---|
| `<scr<script>ipt>alert(1)</scr</script>ipt>` | Filter xoa `<script>` MOT LUOT. Phan con lai `<scr`+`ipt>` ghep lai thanh `<script>` that. |
| `<SCRIPT>alert(1)</SCRIPT>` | Filter phan biet hoa thuong, chi khop chu thuong. |
| `<img src=x onerror=alert(1)>` | Filter chi nham the `<script>`, bo qua event handler. |
| `jaVasCript:/*...*/onerror=alert(1)//` | Polyglot: chay o nhieu context (href, attribute, JS). |

Bai hoc: blacklist luon thieu. Dung allowlist, hoac escape theo context, hoac thu vien
loc da kiem dinh (DOMPurify).

## B. CSP: khi co va khi khong bao ve
- `/csp-inline` -> `script-src 'self' 'unsafe-inline'`. Co `unsafe-inline` nghia la inline
  script va event handler (onerror...) VAN chay. CSP nay khong chan duoc XSS.
- `/csp-strict` -> `script-src 'self'`. Inline bi chan that. Nhung `'self'` cho phep nap
  script tu chinh origin, va `/jsonp?callback=...` phan chieu callback nguyen van voi
  content-type JavaScript. Ke tan cong nap:
  ```html
  <script src="/jsonp?callback=alert(document.domain)//"></script>
  ```
  Script nay den tu `'self'` nen HOP LE voi CSP, nhung noi dung do ke tan cong dieu khien.
  CSP strict bi vuot.

Cac kieu vuot CSP hay gap khac: `unsafe-inline` khong di kem nonce/hash; `unsafe-eval`;
nonce bi lo hoac tai su dung (nonce reuse); domain allow-list qua rong (vi du CDN co ho
JSONP); `base-uri` khong khoa; thieu `object-src 'none'`.

## Cach verify (khong can trinh duyet)
`exploit.py` grep response: payload ngay tho bi filter XOA, con cac payload vuot thi con
nguyen van trong HTML tra ve (tuc se chay trong trinh duyet). Voi CSP, script doc header
that tra ve, phan tich vi sao bi vuot, va xac nhan `/jsonp` phan chieu callback nguyen van
voi content-type `application/javascript`. Ket qua that o `transcript.txt`: tat ca buoc
vuot THANH CONG.
