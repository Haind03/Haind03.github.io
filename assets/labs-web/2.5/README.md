# Lab 2.5 - Command injection (in-band + blind + loc ky tu)

App Flask co chuc nang "ping" noi chuoi thang vao shell (`subprocess.run(cmd,
shell=True)`) -> command injection.

- `GET /ping?host=` : IN-BAND, output lenh hien thang trong phan hoi.
- `GET /ping2?host=` : loc `; & | $ \`` nhung QUEN ky tu xuong dong (`%0a`).
- `GET /ping3?host=` : BLIND, chi tra "da gui" -> suy ket qua bang time-based
  (`; sleep N`) hoac OOB (ghi output ra file/goi ve server minh).

Muc tieu: chay lenh tuy y, doc `flag.txt`.

## Yeu cau

- Python 3, Flask, curl, va `ping` (co san tren Linux/WSL). Co `id`, `sleep`, `cat`.

## Chay

```bash
PORT=8025 python3 app.py     # terminal 1
PORT=8025 bash exploit.sh    # terminal 2
```

## Ket qua

- In-band `; id` -> `uid=1000(...)`; `; cat flag.txt` -> `WEB{c0mm4nd_1nj3ct10n_rce_qua_ping}`.
- `/ping2` chan `; id` (400) nhung bypass bang xuong dong `%0a` -> van chay `id`/`cat`.
- `/ping3` blind: `; sleep 3` -> phan hoi ~3.0s (so voi ~0.007s); OOB ghi output
  ra `/tmp/oob_2_5.txt` roi doc lai -> lay duoc flag du khong co output in-band.

Xem `transcript.txt` la output that.

## Ky tu noi lenh hay dung

- `;`  chay lan luot.   `&&` chay neu lenh truoc OK.   `||` chay neu loi.
- `|`  dua output lam input.   `$(...)` / `` `...` `` thay the lenh con.
- Xuong dong (`%0a`) cung la dau tach lenh (hay bi filter bo quen).
- OOB that: dung DNS/HTTP goi ve server minh (vd interactsh) khi khong co output.

## Phong chong

- Khong goi shell voi chuoi ghep. Dung `subprocess.run([...], shell=False)` voi
  danh sach tham so. Validate allowlist (vd chi cho IP/hostname hop le).

## Canh bao

App co y de lo hong (shell=True), chi chay local loopback, KHONG deploy ra Internet.
