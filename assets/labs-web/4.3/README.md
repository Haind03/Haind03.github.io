# Lab 4.3: Tan cong JWT

App Flask phat JWT (HS256) khi login va kiem token o `/admin`. Verifier tu viet, co y de lo hong. Chay local, `127.0.0.1:8043`.

## Lo hong co trong app
- Chap nhan `alg=none`: bo qua chu ky hoan toan.
- Secret HS256 yeu (`"secret"`): crack bang wordlist nho.
- `kid` header duoc dung lam duong dan file de doc key (kid injection). Tro `kid=/dev/null` -> key rong, tu ky duoc.

## Endpoint
- `POST /login` form `username`, `password` -> tra JWT. User thuong co `role=user`.
- `GET /admin` header `Authorization: Bearer <jwt>`. Chi tra flag khi `role=admin`.

Tai khoan: `wiener:peter` (user thuong). Khong co ai dua cho ban token admin, phai forge.

## Chay
```bash
python3 app.py        # terminal 1
python3 exploit.py    # terminal 2
```

## Nhiem vu
Forge mot token `role=admin` duoc `/admin` chap nhan, bang bat ky cach nao:
1. `alg=none`.
2. Crack secret HS256 roi ky lai.
3. kid injection (`kid=/dev/null`).

## Dap an
`exploit.py` lam ca ba cach, ket qua that trong `transcript.txt`:
ca ba forge thanh cong, flag `FLAG{4.3_jwt_forged_admin}`.

## Thu nhanh bang curl (alg=none)
```bash
# header {"alg":"none","typ":"JWT"} . payload {"user":"admin","role":"admin"} . (chu ky rong)
H=$(printf '{"alg":"none","typ":"JWT"}' | basenc --base64url | tr -d '=')
P=$(printf '{"user":"admin","role":"admin"}' | basenc --base64url | tr -d '=')
curl -s localhost:8043/admin -H "Authorization: Bearer $H.$P."
```

## Lien quan (xem bai hoc)
HS/RS confusion (ky RS256 bang public key qua HMAC), `jwk`/`x5u` header injection. Verifier nay khong bat, nhung bai hoc co giai thich.
