# Lab 4.5: Password reset yeu + bypass MFA

App Flask tu chua minh hoa lo hong quy trinh reset mat khau va MFA. Chay local, `127.0.0.1:8046`.

## Lo hong co trong app
- Reset token doan duoc: `token = md5(email + pepper co dinh)[:12]`, suy ra offline chi can biet email victim (khong random).
- Host header poisoning: link reset xay tu `Host` header do client gui -> attacker ep link tro ve domain cua minh, token ro ri khi victim bam.
- MFA missing check: `/mfa/account` chi kiem da qua buoc password, KHONG kiem da nhap OTP -> bo qua MFA.
- OTP 4 chu so, khong rate limit -> brute 0000..9999.

## Endpoint
- `POST /forgot` form `email` -> tra `reset_link` (mo phong email).
- `POST /reset` form `token`, `new_password`.
- `POST /mfa/login` form `username`, `password` -> `mfa_token`, stage `mfa_required`.
- `POST /mfa/verify` form `mfa_token`, `otp`.
- `GET /mfa/account?mfa_token=...`.

Tai khoan: `ceo@corp.local` (reset takeover), `bob@corp.local:bobpass` (MFA).

## Chay
```bash
python3 app.py        # terminal 1
python3 exploit.py    # terminal 2
```

## Nhiem vu
1. Doan reset token cua `ceo@corp.local`, doi mat khau, chiem tai khoan.
2. Lam link reset tro ve domain attacker (host header poisoning).
3. Bo qua MFA bang missing-check (vao `/mfa/account` ma khong nhap OTP).
4. Brute OTP khi khong co rate limit.

## Dap an
`exploit.py` lam ca bon, ket qua that trong `transcript.txt`:
chiem ceo qua reset, bypass MFA cua bob. Flag `FLAG{4.5_reset_token_predictable}` va `FLAG{4.5_mfa_bypassed}`.

## Thu nhanh bang curl
```bash
# host header poisoning: link tro ve attacker.evil
curl -s -X POST localhost:8046/forgot -H 'Host: attacker.evil' -d email=ceo@corp.local
# MFA bypass: lay mfa_token roi vao thang account khong can OTP
MT=$(curl -s -X POST localhost:8046/mfa/login -d username=bob@corp.local -d password=bobpass | python3 -c 'import sys,json;print(json.load(sys.stdin)["mfa_token"])')
curl -s "localhost:8046/mfa/account?mfa_token=$MT"
```
