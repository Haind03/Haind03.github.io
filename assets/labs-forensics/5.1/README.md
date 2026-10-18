# Lab 5.1: Linux artifact, lan theo mot host bi brute force SSH

Lab chay that di kem [Bai 5.1](../../phan-05-linux-macos/5.1-linux-artifact.md). Toan bo
artifact la gia lap, sinh ra tu kich ban co dinh trong `make_artifacts.py`, khong dung
du lieu rieng tu that. IP tan cong `203.0.113.44` dung dung nhu trong bai hoc.

## File trong lab
- `make_artifacts.py` tao cay thu muc `evidence/` gia lap host `web01`: `var/log/auth.log`
  (brute force SSH + mot login thanh cong), `home/deploy/.bash_history`, cron drop-in,
  systemd `.service`/`.timer` reverse shell, `/etc/passwd` co account UID 0 backdoor,
  binary SUID trong `/tmp/.cache`, staging trong `/dev/shm`.
- `solve.sh` phan tich cay do bang dung cac lenh trong bai (`grep`, `awk`, `sort/uniq`,
  `find -perm -4000`, `stat`) va in ra IP tan cong, moc compromise, persistence, backdoor,
  roi dung mot timeline.
- `transcript.txt` output that cua mot lan chay make + solve.

## Chay
```bash
python3 -I make_artifacts.py evidence
bash solve.sh evidence
```

Luu y he thong tap tin: bit SUID (`chmod 4755`) chi ton tai tren ext4/xfs that. Tren o
Windows mount qua WSL (`/mnt/c`, `/mnt/d`, drvfs) bit SUID bi bo khi tao file, nen buoc 8
se bao "khong con bit SUID". Chay lab o mot thu muc Linux that (vi du `~/lab51`) de thay
`find -perm -4000` bat duoc `/tmp/.cache/sh`. `transcript.txt` o day duoc sinh tren ext4
nen SUID hien dung.

## Nhiem vu (khop muc 3 cua bai hoc)
1. Tu `auth.log`, xac dinh IP brute force va moc login thanh cong dau tien.
2. Doc `.bash_history` cua deploy; kiem `root/.bash_history` co bi symlink toi `/dev/null` khong.
3. Liet ke moi persistence (cron drop-in, systemd service + timer) va ghi `ExecStart`.
4. Liet ke account UID 0 ngoai root va SUID binary bat thuong.
5. Dung timeline theo thu tu thoi gian, moi dong neu artifact nguon.

## Dap an rut gon
- IP tan cong: `203.0.113.44`, vao account `deploy` luc `Oct 5 14:23:11` (Accepted password + session opened).
- Account backdoor: `backup` UID 0 (gia danh account dich vu), tao luc 14:25:40.
- Persistence: `mysqld-backup.service`/`.timer` (reverse shell toi `203.0.113.44:4444`),
  cron `/etc/cron.d/apache-backup` (`curl ... | bash` moi 15 phut).
- Privesc: `/tmp/.cache/sh` co bit SUID, chu root.
- Anti-forensic: `root/.bash_history -> /dev/null`, deploy chay `history -c`.

## Mo rong (tu lam them)
- Bai hoc nhac `wtmp`/`btmp` doc bang `last`/`lastb`. Lab nay dung auth.log text cho de tai
  lap; de tap `lastb`, tu sinh mot btmp bang `python3` (struct utmp) hoac lay tu VM that.
- Neu may chi dung journald, thu `journalctl -D <thu muc journal>` tren mot image VM that.
