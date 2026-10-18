# Lab 6.1 - SSRF co ban

App co chuc nang "xem truoc URL": ban dua URL, server di lay ho. Vi khong
kiem IP/host noi bo, ta ep server goi toi dich vu chi nghe tren loopback va
toi endpoint metadata cloud.

## Thanh phan

| File | Vai tro |
|---|---|
| `app.py` | App chinh co lo hong fetch, bind `127.0.0.1:8054` |
| `internal_services.py` | Admin noi bo `127.0.0.1:8055` + metadata gia lap `127.0.0.1:8056` |
| `exploit.py` | SSRF doc dich vu noi bo va credentials metadata |
| `transcript.txt` | Output that cua lan chay |

## Cach chay

```bash
python3 internal_services.py   # terminal 1: dich vu noi bo 8055 + 8056
python3 app.py                 # terminal 2: app chinh 8054
python3 exploit.py             # terminal 3: khai thac
```

## Lo hong o dau

`/fetch?url=...` goi `requests.get(url)` voi URL tuy y client dua, khong kiem:
- scheme (http/https/file/gopher...),
- host/IP co phai noi bo khong (127.0.0.1, ::1, 10.x, 172.16-31.x, 192.168.x,
  169.254.x metadata link-local).

Vi server chay trong mang noi bo, no voi toi nhung dich vu ma Internet khong
goi duoc.

## Luu y ve metadata cloud

Trong moi truong cloud that, endpoint metadata la
`http://169.254.169.254/latest/meta-data/...` (AWS), tra ve credentials tam
cua instance. IP link-local 169.254.169.254 khong route ra Internet nen chi
server noi bo goi duoc, dung la dieu SSRF loi dung. O lab ta gia lap bang
`127.0.0.1:8056` de khong phu thuoc moi truong cloud, nhung duong dan va y
nghia giu nguyen. IMDSv2 (yeu cau token PUT) la mot bien phap giam thieu.

## Cach va

- Whitelist domain/IP dich den; tu choi mac dinh (deny by default).
- Chan dai IP noi bo va link-local; resolve DNS roi kiem IP truoc khi goi.
- Chi cho phep scheme can thiet (http/https), cam file/gopher/ftp...
- Tach dich vu nhay cam ra mang rieng, bat xac thuc (vd IMDSv2) cho metadata.
