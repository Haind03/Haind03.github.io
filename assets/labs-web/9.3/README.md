# Lab 9.3 - CORS cau hinh sai

Victim app Flask tu chua, co lo hong CO Y, bind loopback `127.0.0.1:8073`. Chay local, KHONG deploy ra Internet.

## Lo hong
- Server **reflect** nguyen header `Origin` vao `Access-Control-Allow-Origin`, dong thoi bat `Access-Control-Allow-Credentials: true`.
- Chap nhan ca `Origin: null`.
- `/api/account` la du lieu nhay cam, xac thuc bang cookie session (`SameSite=None`).

Hau qua: mot trang web bat ky (vi du `https://evil.example`) co the dung `fetch(..., {credentials:'include'})` doc du lieu cua nan nhan dang dang nhap, vi trinh duyet thay CORS header cho phep.

## Chay
```bash
pip install flask requests        # neu chua co
python3 app.py                     # victim len cong 8073
python3 exploit.py                 # terminal khac
```

`exploit.py` chung minh truc tiep (khong can GUI trinh duyet) rang server reflect Origin + credentials. File `attacker.html` la trang ac that de chay thu bang trinh duyet (huong dan trong chinh file).

## Kich ban khai thac
1. Nan nhan dang nhap -> co cookie session.
2. Gia lap request tu trang ac: gui `Origin: https://evil.example` kem cookie nan nhan -> xem server tra `Access-Control-Allow-Origin: https://evil.example` + `Access-Control-Allow-Credentials: true` + body nhay cam.
3. Thu `Origin: null` -> cung duoc chap nhan.

## Ket qua
- `FLAG{9.3_cors_reflect_origin_with_credentials}` (trong `api_token` cua account).

Xem `transcript.txt`.

## Vá
- Khong reflect Origin. Dung allowlist origin tin cay; so khop CHINH XAC (khong regex lo nhu `evil-corp.com` khop `corp.com`).
- Neu `Access-Control-Allow-Origin: *` thi TUYET DOI khong kem credentials.
- Khong chap nhan `Origin: null`.
