# Lab 10.1 - Chuoi recon -> IDOR -> SSTI -> RCE

App Flask tu chua, nhieu buoc, co lo hong CO Y, bind loopback `127.0.0.1:8076`. Chay local, KHONG deploy ra Internet.

## Chuoi lo hong
- **B0 recon**: trang chu nhung mot file `/static/app.js`; file JS lo endpoint "noi bo" `/api/v2/users/<id>/keys` (khong co link cong khai).
- **B1 IDOR**: `/api/v2/users/<id>/keys` khong xac thuc, khong kiem quyen -> doc key cua admin (`id=1`), lo `admin_api_key`.
- **B2 SSTI**: `/admin/template/preview` chi "bao ve" bang `admin_api_key` (vua leak), va `render_template_string` tren input nguoi dung -> Server-Side Template Injection (Jinja2).
- **B3 RCE**: payload SSTI chay lenh he thong -> doc `flag.txt` tren dia.

## Chay
```bash
pip install flask requests        # neu chua co
python3 app.py                     # server len cong 8076 (chay tu thu muc lab)
python3 exploit.py                 # terminal khac
```

## Ket qua
`exploit.py` ghep ca 4 buoc, ket thuc bang RCE doc duoc:
- `FLAG{10.1_recon_idor_ssti_rce_chain}` (trong `flag.txt`, lay qua SSTI payload `{{ lipsum.__globals__.os.popen('cat flag.txt').read() }}`).

Xem `transcript.txt` (co output lenh `id` that + flag).

## Vá
- Khong de file dev/JS lo endpoint noi bo; coi endpoint "noi bo" nhu endpoint cong khai (van phai xac thuc).
- Moi endpoint tham chieu object phai kiem quyen (chong IDOR). Khong coi secret trong URL/JS la "bao mat".
- Khong `render_template_string` tren input nguoi dung. Dung template tinh + bien context, hoac sandbox; tach du lieu khoi template.
