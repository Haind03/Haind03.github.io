#!/usr/bin/env bash
# Lab 9.1 - tao image ext4 nho mo phong mot vu xam nhap web server Linux,
# voi timestamp duoc dat co dinh (UTC) de dung TSK dung super timeline bang mactime.
# Khong can root, khong mount. Cong cu: dd, mkfs.ext4, debugfs.
set -euo pipefail
cd "$(dirname "$0")"

IMG=case.ext4
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
rm -f "$IMG"

echo "[*] 1. Tao image ext4 1MB"
dd if=/dev/zero of="$IMG" bs=1M count=1 status=none
mkfs.ext4 -q -F -L WEBSRV -U aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee "$IMG" 2>/dev/null

echo "[*] 2. Nap file (noise truoc + chuoi tan cong) bang debugfs"
# noise pre-existing
printf 'root:x:0:0:root:/root:/bin/bash\n'                 > "$WORK/passwd"
printf '<?php echo "home"; ?>\n'                            > "$WORK/index.php"
printf 'export PATH=$PATH:/usr/local/bin\n'                 > "$WORK/bashrc"
printf 'Jan 15 00:05:01 web CRON[1]: session opened\n'      > "$WORK/auth.log"
# attack chain
printf '<?php system($_GET["c"]); ?>\n'                     > "$WORK/upload.php"
printf '\x7fELF harmless-lab-payload sysupd\n'              > "$WORK/sysupd"
printf '*/5 * * * * root /tmp/.cache/sysupd\n'              > "$WORK/apache-check"
printf 'ssh-rsa AAAAB3Nz...attacker-key... evil@attacker\n' > "$WORK/authorized_keys"
printf 'staged data for exfiltration (will be deleted)\n'   > "$WORK/exfil.tar.gz"

debugfs -w "$IMG" >/dev/null 2>&1 <<EOF
mkdir /var
mkdir /var/www
mkdir /var/www/html
mkdir /var/log
mkdir /etc
mkdir /etc/cron.d
mkdir /home
mkdir /home/user
mkdir /root
mkdir /root/.ssh
mkdir /tmp
mkdir /tmp/.cache
write $WORK/passwd /etc/passwd
write $WORK/index.php /var/www/html/index.php
write $WORK/bashrc /home/user/.bashrc
write $WORK/auth.log /var/log/auth.log
write $WORK/upload.php /var/www/html/upload.php
write $WORK/sysupd /tmp/.cache/sysupd
write $WORK/apache-check /etc/cron.d/apache-check
write $WORK/authorized_keys /root/.ssh/authorized_keys
write $WORK/exfil.tar.gz /tmp/exfil.tar.gz
EOF

echo "[*] 3. Dat timestamp co dinh (UTC) cho tung file"
setts () { # $1=path  $2=YYYYMMDDHHMMSS (UTC)
  debugfs -w "$IMG" >/dev/null 2>&1 <<EOF
set_inode_field $1 mtime  $2
set_inode_field $1 atime  $2
set_inode_field $1 ctime  $2
set_inode_field $1 crtime $2
EOF
}
# noise (truoc cua so tan cong)
setts /etc/passwd                 20251101080000
setts /var/www/html/index.php     20251102093000
setts /home/user/.bashrc          20251101080000
setts /var/log/auth.log           20260115000501
# chuoi tan cong 2026-01-15 10:15 -> 10:22 (UTC)
setts /var/www/html/upload.php    20260115101503
setts /tmp/.cache/sysupd          20260115101640
setts /etc/cron.d/apache-check    20260115101712
setts /root/.ssh/authorized_keys  20260115101830
setts /tmp/exfil.tar.gz           20260115102245

echo "[*] 4. Xoa file exfil (de no thanh artifact 'deleted' trong timeline)"
debugfs -w "$IMG" >/dev/null 2>&1 <<EOF
rm /tmp/exfil.tar.gz
EOF

echo "[*] Xong. Image: $IMG ($(stat -c%s "$IMG") bytes)"
echo "    Chay ./solve.sh de dung super timeline bang fls + mactime."
