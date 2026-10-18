#!/usr/bin/env bash
# Lab 1.1 - solve: nhan dien kieu that bang magic byte, khong tin extension.
set -u
cd "$(dirname "$0")"

echo "=== B1: file noi gi (doc magic, bo qua duoi) ==="
file report.pdf hoa-don.pdf logo.jpg backup.dat anh.png

echo
echo "=== B2: 8 byte dau tung file (xxd) ==="
for f in report.pdf hoa-don.pdf logo.jpg backup.dat anh.png; do
  printf "%-14s " "$f"; xxd -l 8 "$f" | head -1
done

echo
echo "=== B3: solver python (doi chieu bang magic) ==="
python3 -I detect.py report.pdf hoa-don.pdf logo.jpg backup.dat anh.png

echo
echo "=== B4: pha roi va magic byte cua PNG ==="
cp -f goc.png benh-nhan.png
printf '\x00\x00\x00\x00' | dd of=benh-nhan.png bs=1 seek=0 count=4 conv=notrunc status=none
echo "-- sau khi dap 4 byte dau --"; file benh-nhan.png
printf '\x89\x50\x4e\x47' | dd of=benh-nhan.png bs=1 seek=0 count=4 conv=notrunc status=none
echo "-- sau khi va lai chu ky PNG --"; file benh-nhan.png
