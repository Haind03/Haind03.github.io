# Lab 9.1 - REST API security (BOLA / BFLA / lo field)

App Flask tu chua, co lo hong CO Y, chi bind loopback `127.0.0.1:8071`. Chay local de hoc, KHONG deploy ra Internet.

## Lo hong
- **BOLA** (Broken Object Level Authorization, IDOR cap object): `GET /api/users/<id>` chi kiem tra token hop le, khong kiem tra token co thuoc ve dung `<id>`.
- **Lo field** (excessive data exposure): tra ca `ssn`, `card`, `secret_note`.
- **BFLA** (Broken Function Level Authorization): `POST /api/admin/promote` chi can dang nhap, khong kiem tra `role == admin`.
- **Khong rate limit** o `/api/login`.

## Chay
```bash
pip install flask requests          # neu chua co
python3 app.py                       # server len cong 8071
python3 exploit.py                   # chay trong terminal khac
```

## Kich ban khai thac
Dang nhap bang chinh tai khoan `alice` (user thuong) de lay token hop le, roi:
1. Dung token do doc object cua `bob` (`/api/users/2`) -> lo ssn/card/secret_note (chua flag BOLA).
2. Doc don hang cua bob qua `/api/users/2/orders`.
3. Goi ham admin `/api/admin/promote` de tu nang quyen -> flag BFLA.

## Ket qua
- `FLAG{9.1_bola_read_other_users_object}` (BOLA, trong `secret_note` cua bob)
- `FLAG{9.1_bfla_function_level_bypass}` (BFLA)

Xem `transcript.txt` cho lan chay that.

## Vá
- Kiem tra chu so huu: `token.user_id == requested_id` (hoac role phu hop) o MOI endpoint theo object.
- Phan quyen theo chuc nang: endpoint `/admin/*` phai kiem tra role server-side.
- Chi tra field can thiet (DTO/serializer rieng), khong tra nguyen ban ghi.
- Them rate limit / lockout cho login.
