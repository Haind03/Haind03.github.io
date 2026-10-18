# Lab 5.1 - IDOR (Insecure Direct Object Reference)

App shop mini co endpoint xem/sua don hang theo id tuan tu. Server chi kiem
tra "da dang nhap chua" chu khong kiem tra "don nay co phai cua ban khong".
Doi mot con so la doc va sua duoc don cua nguoi khac.

## Thanh phan

| File | Vai tro |
|---|---|
| `app.py` | App Flask co lo hong, bind `127.0.0.1:8050` |
| `exploit.py` | Khai thac IDOR doc va ghi, moc flag |
| `transcript.txt` | Output that cua lan chay |

## Cach chay

```bash
# Terminal 1: dung app (chi loopback, co y de loi)
python3 app.py

# Terminal 2: chay khai thac
python3 exploit.py
```

Dung app bang Ctrl+C khi xong.

## Lo hong o dau

Trong `get_order()` va `set_address()`, code lay `current_user()` roi lam
viec ngay voi `ORDERS[oid]` ma KHONG so sanh `order["owner"]` voi user hien
tai. Day la IDOR: id (1001, 1002...) la tham chieu truc tiep toi doi tuong,
lo ra ngoai va khong kem kiem tra quyen.

## Nhiem vu

1. Dang nhap bang tai khoan hop le `mallory:pw`.
2. Xem don cua chinh minh (1003) de thay dinh dang response.
3. Doi id sang 1001..1005, doc du lieu nhay cam (so the, dia chi) cua nguoi
   khac. Flag nam trong `note` cua don 1001.
4. Thu IDOR ghi: POST `/api/order/1004/address` doi dia chi don cua alice.

## Cach va

- Kiem tra quyen so huu o moi endpoint: `if order["owner"] != user: 403`.
- Uu tien kiem tra o tang truy van (chi SELECT don cua user hien tai).
- Dung id doan duoc khong phai la bien phap bao mat (security by obscurity):
  UUIDv4 ngau nhien giam rui ro enum nhung KHONG thay the duoc kiem quyen.
