# Lab 7.1 - Path Traversal / LFI

App Flask "DocViewer" doc tai lieu theo tham so `file`. Loi: noi ghep chuoi nguoi dung vao duong dan, khong chuan hoa, khong giới hạn thu muc goc. Co them endpoint `/safe` loc `../` mot lan de tap bypass.

## Dung

```bash
python3 app.py
# lang nghe 127.0.0.1:8061
```

Yeu cau: Python 3, Flask (`pip install flask`). Chi chay loopback, dung cho hoc tap.

## Endpoint

- `GET /view?file=<ten>`  doc `docs/<ten>` (lo hong traversal, khong loc gi).
- `GET /safe?file=<ten>`  giong tren nhung `replace('../','')` mot lan (bypass bang `....//`).

## Khai thac

```bash
bash exploit.sh
```

Script lam: doc file hop le, doc `/etc/passwd` bang `../`, doc source `app.py`, cho thay `/safe` chan request tho, roi bypass bang `....//`, va bang URL-encode `%2e%2e%2f`.

## Ket qua mong doi

Doc duoc `/etc/passwd` (dong `root:x:0:0:...`) va source `app.py`. Xem `transcript.txt` la log chay that.

## Vi sao dinh

`os.path.join(DOCS, filename)` giu nguyen `../` do nguoi dung gui, OS tu resolve len tren thu muc goc. Khong co buoc `os.path.realpath()` roi kiem tra ket qua co nam trong `DOCS` khong.

## Phong

- Khong ghep chuoi nguoi dung vao duong dan. Map input qua danh sach cho phep (allowlist id -> ten file thuc).
- Neu buoc phai nhan ten file: `realpath` roi kiem tra `startswith(DOCS + os.sep)`; loc theo basename (`os.path.basename`).
- Bo loc kieu `replace('../','')` (vo dung), dung chuan hoa duong dan that su.
