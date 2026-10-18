# Lab 5.4 - Mass assignment / parameter tampering

Endpoint cap nhat profile nhan nguyen body JSON va gan het vao object user.
Nguoi dung chi duoc phep doi email/bio, nhung gui kem `isAdmin=true` la tu
nang quyen len admin.

## Thanh phan

| File | Vai tro |
|---|---|
| `app.py` | App Flask co lo hong, bind `127.0.0.1:8053` |
| `exploit.py` | Nang quyen qua mass assignment, lay flag |
| `transcript.txt` | Output that cua lan chay |

## Cach chay

```bash
python3 app.py        # terminal 1
python3 exploit.py    # terminal 2
```

Tai khoan: `eve:pw` (user thuong).

## Lo hong o dau

Trong `profile()` khi POST:

```python
for k, v in data.items():
    user[k] = v       # gan het, khong loc theo whitelist ALLOWED
```

Client gui `{"isAdmin": true, "balance": 1000000, "role": "admin"}` thi cac
truong dac quyen bi ghi de luon. Endpoint `/admin` lai suy quyen tu
`user["isAdmin"]`, nay da bi sua thanh true.

Mass assignment hay gap khi code bind thang request body vao model/ORM
(`Model(**request.json)`, `user.update(body)`, `Object.assign(user, body)`).

## Nhiem vu

1. Dang nhap `eve:pw`, xem profile (isAdmin=false).
2. POST `/api/profile` voi JSON co them `isAdmin:true`.
3. Truy cap `/admin` -> lay flag.

## Cach va

- Whitelist truong duoc phep ghi (chi email, bio), bo het truong la.
- Dung DTO/schema rieng cho input, khong bind thang vao model du lieu.
- Danh dau cac truong nhay cam (isAdmin, role, balance) la read-only o tang
  nhap lieu; chi sua qua luong co kiem quyen rieng.
