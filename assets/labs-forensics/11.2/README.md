# Lab 11.2: Dieu tra mot he thong nhiem malware (tu chua)

Lab chay that di kem [Bai 11.2](../../phan-11-thuc-chien/11.2-dieu-tra-image-malware.md).
Day la mot "he thong" Linux gia lap da bi nhiem, tu chua va gon, de di het bay buoc dieu
tra ma khong can bo cong cu Windows (KAPE/EVTX). Kich ban mo phong, khong dung du lieu that;
moi IOC la gia tri vi du.

## File trong lab
- `make_artifacts.py` dung cay `case-host/`: log (`nginx/access.log`, `auth.log`, `syslog`),
  webshell `var/www/html/uploads/shell.php`, implant `var/tmp/.sysd/kworkerd` (ELF gia co
  nhung chuoi IOC, mtime bi timestomp ve 2009), staging exfil `data.tar.gz`, persistence
  qua `cron.d` va systemd `.service`.
- `solve.py` dieu tra theo BAY BUOC va trich bo IOC, roi xuat `iocs.json` (dung lam dau vao
  cho lab 11.3).
- `transcript.txt` output that (gom ca `file` nhan dien implant va `iocs.json`).

## Chay
```bash
python3 -I make_artifacts.py case-host
python3 -I solve.py case-host
```
`solve.py` chi doc artifact (du lieu khong tin cay) va truyen duong dan lam tham so, khong
chay file trong cay.

## Bay buoc (khop bai 11.2)
1. Chuan bi & xac minh: hash implant va webshell.
2. Triage: diem nong trong nginx log (POST upload, `cmd=`) va file an/staging trong `/var/tmp/.sysd`.
3. Root cause: webshell upload roi khai thac -> initial access (tuong duong T1505.003).
4. Persistence: cron drop-in + systemd service tro toi implant.
5. Lateral & pham vi: he tu chua 1 host; ca that se quet fleet bang IOC/YARA.
6. C2 & exfil: `strings` tren implant ra C2 IP/URL/UA/mutex; staging `data.tar.gz`.
7. IOC & anti-forensic: phat hien timestomp (mtime 2009), dau xoay log; dong bo IOC.

## Dap an rut gon
- Initial access: upload `shell.php` qua `POST /upload.php`, khai thac tu `198.51.100.23`.
- C2: `185.234.72.19` (URL `https://185.234.72.19:8443/gate.php`), UA `AcctLoader/1.2`, mutex `AcctLdr_7f3a`.
- Persistence: `etc/cron.d/nginx-cache` (`curl|bash` moi 10 phut), `network-helper.service` (chay implant).
- Exfil: `var/tmp/.sysd/data.tar.gz` staged.
- Anti-forensic: implant timestomp mtime ve 2009; rsyslog restart luc 10:15 (nghi xoa log).

## Luu y
- Moi ket luan neu gan duoc vao mot dong log/artifact cu the moi la ket luan, con lai la gia thuyet.
- `iocs.json` sinh ra o day chuyen thang sang lab 11.3 de dung khung bao cao.
