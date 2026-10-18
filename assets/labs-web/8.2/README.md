# Lab 8.2 - Insecure Deserialization (Python pickle)

App Flask luu "prefs" nguoi dung duoi dang pickle base64 trong cookie `prefs`, roi `pickle.loads()` khi doc lai. Loi: pickle.loads tren du lieu khong tin duoc = thuc thi ma tuy y.

## CANH BAO

`pickle` cuc ky nguy hiem. Chi can `pickle.loads()` mot chuoi do ke tan cong dieu khien la RCE ngay, khong can "gadget" phuc tap nhu Java/PHP. Tuyet doi khong unpickle du lieu tu ben ngoai.

## Dung

```bash
python3 app.py
# 127.0.0.1:8065
```

Yeu cau: Python 3, Flask, requests.

## Khai thac

```bash
python3 exploit.py
```

Payload dung `__reduce__` tra ve `(os.system, (cmd,))`. Khi `pickle.loads` chay, no goi `os.system(cmd)`. Vi output lenh khong quay ve HTTP response (server chi in gia tri unpickle = exit code 0), exploit ghi `id`/`uname` ra file `/tmp/lab82_proof.txt` roi doc lai de chung minh lenh da chay.

## Ket qua mong doi

File `/tmp/lab82_proof.txt` chua `uid=... gid=...` va `Linux ...` that. Xem `transcript.txt`.

## Vi sao dinh

Format pickle la mot chuong trinh stack-machine, co opcode `REDUCE` goi callable voi args. `__reduce__` cho doi tuong khai bao callable + args duoc goi luc unpickle. Khong co buoc "chi doc du lieu"; pickle von dĩ chay code.

## Phong

- Khong dung pickle cho du lieu di qua ranh gioi tin cay (cookie, request, hang doi, cache). Dung JSON cho du lieu thuan.
- Ky du lieu (HMAC) neu buoc phai serialize nhi phan, va van tranh pickle.
- PHP: tranh `unserialize()` input nguoi dung (POP chain qua magic method `__wakeup`/`__destruct`); dung `json_decode`. Java: tranh `ObjectInputStream.readObject` input ngoai (ysoserial gadget).
