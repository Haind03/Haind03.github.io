#!/usr/bin/env bash
# solve.sh - lab 6.4: moi credential tu RAM + giai payload -enc (fileless).
set -u
DUMPDIR="${DUMPDIR:-/tmp/mem6_4}"
DUMP="$DUMPDIR/victim.dump"

if [ ! -f "$DUMP" ]; then
  echo "[!] chua co dump. Chay capture.py truoc (DUMPDIR=$DUMPDIR)."
  exit 1
fi

echo "== 1. Moi credential bang strings + grep theo pattern =="
strings -a "$DUMP" | grep -aoE "password=[^ ]+"  | sort -u | head -1
strings -a "$DUMP" | grep -aoE "api_token=[^ ]+" | sort -u | head -1
echo

echo "== 2. Hash kieu NTLM (dinh dang user:rid:lm:nt) =="
strings -a "$DUMP" | grep -aoE "ntlm=[^ ]+" | sort -u | head -1
echo

echo "== 3. Chuoi -enc kieu PowerShell (base64 UTF-16LE) trong RAM =="
ENC=$(strings -a "$DUMP" | grep -aoE "PSENC=[A-Za-z0-9+/=]+" | head -1 | sed 's/^PSENC=//')
echo "PSENC (rut gon): ${ENC:0:48}..."
echo

echo "== 4. Giai -enc: base64 -d | iconv UTF-16LE -> lenh that =="
echo "$ENC" | base64 -d | iconv -f UTF-16LE -t UTF-8
echo
echo "(Giai dung phai qua iconv UTF-16LE; bo buoc do se ra chuoi co byte null xen ke.)"
