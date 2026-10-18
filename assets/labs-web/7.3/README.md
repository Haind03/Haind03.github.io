# Lab 7.3 - LFI leo thang RCE

Mini CMS PHP chon "trang" qua tham so `page`, roi `include($page)` thang. Loi LFI kinh dien. Lab nay cho thay 4 cach bien LFI thanh doc source va RCE.

## Dung

```bash
php -S 127.0.0.1:8063 -t www -d allow_url_include=1 -d allow_url_fopen=1
```

Vi sao co `allow_url_include=1`: hai ky thuat `php://input` va `data://` chi chay khi server bat setting nay (mot cau hinh long, gap o server cu/sai). Hai ky thuat con lai (`php://filter` doc source va log poisoning) KHONG can no, chay ca khi setting tat.

## Khai thac

```bash
bash exploit.sh
# drvfs bao "Invalid argument": cat exploit.sh | bash
```

Cac buoc trong `exploit.sh`:
1. LFI co dien: `?page=../../../etc/passwd` -> `include` in ra noi dung file.
2. `php://filter/convert.base64-encode/resource=index.php` -> lay SOURCE (base64) roi giai ma, lo code + mat khau DB.
3. `data://text/plain;base64,<PHP>` -> include chay ma -> `id`.
4. `php://input` + body la ma PHP -> `id`.
5. Log poisoning: nhet `<?php ... ?>` vao `User-Agent`, app ghi vao `logs/access.log`, roi `?page=../logs/access.log` include file log -> ma trong UA chay -> `id`.

## Ket qua mong doi

Buoc 3, 4, 5 deu tra ve `uid=... gid=...` (RCE that). Buoc 2 lo source. Xem `transcript.txt`.

## Phong

- Khong `include`/`require` tu input nguoi dung. Map qua allowlist (`'home' => 'pages/home.php'`).
- Tat `allow_url_include` va `allow_url_fopen` (mac dinh da tat `allow_url_include`).
- Khong cho web ghi vao duong log ma co the bi include; doi quyen file log.
- Neu buoc phai nhan ten: `basename()` + `realpath()` + kiem thu muc goc, chan cac wrapper (`php://`, `data://`, `phar://`).
