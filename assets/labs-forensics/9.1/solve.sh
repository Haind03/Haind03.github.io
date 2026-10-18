#!/usr/bin/env bash
# Lab 9.1 - super timeline bang TSK (fls + mactime) tren image ext4.
# Luu y: plaso (log2timeline.py) KHONG cai duoc o day. Bai mo ta plaso o muc 2;
# o lab chay that nay ta dung TSK mactime - cung y tuong: gop timestamp thanh timeline
# sap theo thoi gian, roi loc cua so quanh moc su kien. Moi gio deu hien thi UTC.
set -euo pipefail
cd "$(dirname "$0")"
IMG=case.ext4
[ -f "$IMG" ] || { echo "Chua co $IMG. Chay ./make.sh truoc."; exit 1; }

echo "============================================================"
echo "[1] fsstat: xac nhan filesystem ext4"
echo "============================================================"
fsstat "$IMG" | sed -n '1,8p'

echo
echo "============================================================"
echo "[2] fls -r -m /: tao bodyfile (nguon cho mactime)"
echo "============================================================"
fls -r -m / "$IMG" > bodyfile.txt
echo "bodyfile.txt: $(wc -l < bodyfile.txt) dong"
head -5 bodyfile.txt

echo
echo "============================================================"
echo "[3] mactime: super timeline day du (UTC)"
echo "============================================================"
mactime -z UTC -d -y -b bodyfile.txt 2>/dev/null | sed -n '1,30p'

echo
echo "============================================================"
echo "[4] LOC CUA SO SU KIEN: 2026-01-15 10:15 -> 10:25 UTC"
echo "============================================================"
echo "Chi con dung chuoi tan cong, sap theo thu tu thoi gian:"
mactime -z UTC -d -y -b bodyfile.txt 2026-01-15T10:15:00..2026-01-15T10:25:00 2>/dev/null

echo
echo "============================================================"
echo "[5] NHAN XET"
echo "============================================================"
echo " Thu tu doc duoc tu timeline (initial access -> persistence -> staging):"
echo "  10:15:03  /var/www/html/upload.php      webshell (initial access / T1190)"
echo "  10:16:40  /tmp/.cache/sysupd            payload ELF trong thu muc an (execution)"
echo "  10:17:12  /etc/cron.d/apache-check      persistence qua cron (T1053.003)"
echo "  10:18:30  /root/.ssh/authorized_keys    them SSH key attacker (persistence)"
echo "  10:22:45  /tmp/exfil.tar.gz (deleted)   staging truoc exfil (T1560)"
echo " File exfil.tar.gz da bi xoa nhung van hien trong timeline voi nhan (deleted)."
echo " Noise truoc do (passwd, index.php, .bashrc, auth.log) nam ngoai cua so -> da bi loc bo."
rm -f bodyfile.txt
