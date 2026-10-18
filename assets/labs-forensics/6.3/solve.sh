#!/usr/bin/env bash
# solve.sh - lab 6.3: phat hien vung RWX bat thuong va soi "shellcode" ben trong.
set -u
DUMPDIR="${DUMPDIR:-/tmp/mem6_3}"
MAPS="$DUMPDIR/victim.maps"

if [ ! -f "$MAPS" ]; then
  echo "[!] chua co maps. Chay capture.py truoc (DUMPDIR=$DUMPDIR)."
  exit 1
fi

echo "== 1. Quet maps tim vung RWX private + khong backing file (malfind analog) =="
# Cot 2 = quyen. 'rwxp' va dong khong co duong dan file o cuoi = anonymous.
awk '$2 ~ /^rwxp/ && NF < 6 {print}' "$MAPS"
echo

echo "== 2. Soi dau vung RWX da carve (header + noi dung) =="
for bin in "$DUMPDIR"/rwx_*.bin; do
  [ -e "$bin" ] || { echo "(khong co file rwx_*.bin)"; break; }
  echo "-- $bin --"
  echo "   16 byte dau (xxd):"
  xxd "$bin" | head -2
  echo "   magic 2 byte dau:"
  head -c2 "$bin" | xxd
  echo "   chuoi trong vung:"
  strings -a "$bin" | grep -a "FAKE_SHELLCODE" | head -1
done
echo

echo "== 3. Ket luan tu dong =="
first2=$(head -c2 "$(ls "$DUMPDIR"/rwx_*.bin 2>/dev/null | head -1)" 2>/dev/null | xxd -p)
if [ "$first2" = "4d5a" ]; then
  echo "Vung RWX bat dau bang 4d 5a (MZ) -> giong PE map tay / injected code. CO DAU."
else
  echo "Khong thay MZ dau vung (first2=$first2)."
fi
