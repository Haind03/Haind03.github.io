# Lab 9.1 - Super timeline bang TSK mactime (thay plaso)

Lab chay that, 100% local, khong can root, khong mount.

## Vi sao dung TSK mactime thay plaso
Moi truong nay KHONG cai duoc `plaso` (`log2timeline.py`, `psort.py`, Timesketch).
Bai mo ta plaso o muc 2. O lab chay that nay ta dung The Sleuth Kit (`fls -r -m` +
`mactime`) tren mot image ext4: cung y tuong cot loi cua super timeline - gop timestamp
thanh mot timeline sap theo thoi gian, roi LOC cua so quanh moc su kien. Khac biet: plaso
gop them nhieu nguon (registry, event log, LNK, browser...), con mactime chi lam tu
file system MACB. Ki thuat loc theo cua so thoi gian la nhu nhau.

## Kich ban (ground truth) - xam nhap web server Linux, UTC 2026-01-15
| Gio (UTC)  | Artifact                          | Y nghia                     |
|------------|-----------------------------------|-----------------------------|
| 10:15:03   | /var/www/html/upload.php          | webshell (initial access)   |
| 10:16:40   | /tmp/.cache/sysupd                | payload ELF (thu muc an)    |
| 10:17:12   | /etc/cron.d/apache-check          | persistence qua cron        |
| 10:18:30   | /root/.ssh/authorized_keys        | them SSH key attacker       |
| 10:22:45   | /tmp/exfil.tar.gz (deleted)       | staging truoc exfil         |

Noise truoc do: /etc/passwd, /var/www/html/index.php, /home/user/.bashrc (2025-11),
/var/log/auth.log (2026-01-15 00:05) - nam ngoai cua so, de minh hoa viec loc.

## Chay
```
./make.sh     # tao case.ext4 voi timestamp co dinh (UTC)
./solve.sh    # fsstat + fls -r -m + mactime + loc cua so 10:15..10:25
```

## File trong lab
- `make.sh`, `case.ext4` (1 MB, < 2 MB), `solve.sh`, `transcript.txt`.

## Diem cot loi
- `fls -r -m /` tao bodyfile; `mactime` sap thanh timeline.
- LUON hien thi UTC (`mactime -z UTC -y`) de khop moc su kien, tranh lan mui gio.
- Loc cua so thoi gian (`2026-01-15T10:15:00..2026-01-15T10:25:00`) cat bo noise, chi con chuoi tan cong.
- File da xoa (`exfil.tar.gz`) van hien trong timeline voi nhan `(deleted)`: timeline bat ca dau vet file bi xoa.
- Timeline nay la dau vao cho Lab 9.2 (map artifact -> ATT&CK technique).

## Nhiem vu tu lam them
1. Doi cua so sang `..10:18:00` va xem ban bo lo buoc nao, hieu vi sao chon cua so dung quan trong.
2. Dung `istat case.ext4 <inode>` xem rieng crtime/mtime/atime/ctime cua `sysupd`.
3. Them mot file "noise" ngay trong cua so (vi du log hop le) va luyen phan biet tin hieu voi nhieu.
