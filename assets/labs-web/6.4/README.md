# Lab 6.4 - HTTP request smuggling (CL.TE)

Request smuggling khong phai lo hong cua mot app don le, no sinh ra khi hai
tang HTTP tren cung mot ket noi TCP (front-end proxy + back-end server) BAT
DONG y ve bien gioi request. Day la demo tu chua tai hien co che CL.TE.

## Thanh phan

| File | Vai tro |
|---|---|
| `demo.py` | Demo tu chua: Phan A (tat dinh) + Phan B (song, 2 socket server) |
| `transcript.txt` | Output that cua lan chay |

## Cach chay

```bash
python3 demo.py
```

Script tu dung back-end `127.0.0.1:8051` (framing theo Transfer-Encoding) va
front-end `127.0.0.1:8050` (framing theo Content-Length), roi gui request cua
ke tan cong va cua nan nhan. Tat ca trong mot tien trinh, thoat la dong het.

## Demo gom hai phan

- Phan A (tat dinh, luon dung): lay CUNG mot byte stream CL.TE roi parse theo
  hai kieu. Front (CL) thay 1 request; back (TE) thay 2 request, request thu
  hai la `GET /admin` bi smuggle. Day la hat nhan cua ky thuat.

- Phan B (song): front va back dung chung MOT ket noi keep-alive. Ke tan cong
  gui request CL.TE: front doc theo Content-Length nen forward het sang back;
  back doc theo chunked, dung o chunk `0`, phan `GET /admin` con lai nam trong
  buffer. Khi nan nhan gui request binh thuong, no bi GHEP vao sau phan smuggle
  -> back-end xu ly `GET /admin` ma khong ai gui truc tiep, con request that cua
  nan nhan bi nuot vao mot header.

## CL.TE va TE.CL

- CL.TE: front-end dung Content-Length, back-end dung Transfer-Encoding.
- TE.CL: nguoc lai, front dung TE, back dung CL.
- Nguyen nhan goc: hai ben xu ly khac nhau khi request co CA HAI header
  `Content-Length` va `Transfer-Encoding`, hoac khi `Transfer-Encoding` bi lam
  mo (`Transfer-Encoding: chunked` co khoang trang la, viet hoa la, nhan doi
  header...). Theo chuan, TE phai uu tien hon CL, nhung nhieu he thong lam sai.

## Phat hien (thuc te)

- Timing: gui request TE.CL "mo" khien back-end cho byte khong bao gio toi
  -> response tre bat thuong. Day la ky thuat phat hien an toan cua PortSwigger.
- Cong cu: Burp Suite extension "HTTP Request Smuggler", hoac tool `smuggler.py`.

## Luu y moi truong

Demo nay mo phong hai tang trong mot tien trinh de hoc co che, KHONG thay the
moi truong proxy phan tang that. De tai hien day du (va thu impact nhu chiem
request nguoi khac, bypass kiem soat front-end, cache poisoning), can dung:
front-end that (nginx/haproxy/CDN) + back-end app, voi phien ban/cau hinh co
bat dong CL vs TE. Lab PortSwigger Web Security Academy ve request smuggling la
cho luyen tot nhat.

## Cach va

- Dung HTTP/2 end-to-end (framing do do dai ro rang, khong co mo ho CL/TE).
- Front-end va back-end phai thong nhat cach parse; tu choi request co ca CL
  lan TE, hoac co TE khong hop le.
- Chuan hoa request o front-end truoc khi chuyen tiep; tat tai su dung ket noi
  (connection reuse) toi back-end neu khong kiem soat duoc.
