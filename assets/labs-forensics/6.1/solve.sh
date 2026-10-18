#!/usr/bin/env bash
# solve.sh - dieu tra dump bo nho tien trinh: tim lai secret bang strings + grep
# Minh hoa buoc "doc danh sach va soi noi dung" cua process memory forensics.
set -u
DUMPDIR="${DUMPDIR:-/tmp/mem6_1}"
DUMP="$DUMPDIR/holder.dump"

if [ ! -f "$DUMP" ]; then
  echo "[!] chua co dump: $DUMP . Chay capture.py truoc (hoac dat DUMPDIR)."
  exit 1
fi

echo "== kich thuoc dump =="
ls -l "$DUMP"
echo

echo "== sha256 dump (ghi lai de dam bao toan ven) =="
sha256sum "$DUMP"
echo

echo "== grep secret truc tiep trong dump =="
# strings -a quet toan bo; loc marker dac trung roi secret.
strings -a "$DUMP" | grep -a "FORENSICS_MARKER_" | head -3
echo

echo "== trich rieng chuoi secret =="
strings -a "$DUMP" | grep -ao "SECRET{[^}]*}" | sort -u
echo

echo "== dem so lan marker xuat hien (holder giu 64 ban) =="
strings -a "$DUMP" | grep -ac "FORENSICS_MARKER_"
