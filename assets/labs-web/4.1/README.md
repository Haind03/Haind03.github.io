# Lab 4.1: Username enumeration + brute force

App login Flask tu chua, co y de lo hong authentication. Chay local, cong loopback `127.0.0.1:8041`.

## Lo hong co trong app
- Thong bao loi khac nhau: `Unknown user` (user khong ton tai) vs `Invalid password` (user ton tai, sai pass). Day la username enumeration qua noi dung.
- Timing side-channel: chi khi user ton tai server moi goi `check_password` (co `time.sleep` gia lap chi phi hash), nen response cham hon han. Enumeration qua thoi gian.
- Khong co rate limit, khong co account lockout: brute force thoai mai.
- Tai khoan dung mat khau yeu (`admin:Password123`, `john.doe:letmein`, `alice:sunshine`).

## Yeu cau
- Python 3, `pip install flask requests`.

## Chay
```bash
# Terminal 1: khoi dong app
python3 app.py

# Terminal 2: chay exploit
python3 exploit.py
```

## Nhiem vu
1. Tim cac username hop le (khong duoc cho truoc) bang message va timing.
2. Brute force mat khau cho cac user tim duoc.
3. Lay `flag` tra ve khi dang nhap thanh cong.

## Dap an
`exploit.py` lam ca 3 buoc. Ket qua that luu trong `transcript.txt`:
chiem duoc ca 3 tai khoan, flag `FLAG{4.1_brute_force_no_rate_limit}`.

## Thu nhanh bang curl
```bash
# user khong ton tai -> Unknown user
curl -s -X POST localhost:8041/login -d username=root -d password=x
# user ton tai, sai pass -> Invalid password (va cham hon)
curl -s -X POST localhost:8041/login -d username=admin -d password=x
# dang nhap dung
curl -s -X POST localhost:8041/login -d username=admin -d password=Password123
```

## Vi sao an toan khi chay
App chi bind `127.0.0.1`, khong ra Internet. Mat khau va flag la gia, dung de hoc.
