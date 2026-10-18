#!/usr/bin/env bash
# Lab 3.2 - solve: binwalk tim offset, carver python trich theo header/footer, verify file mo duoc.
set -u
cd "$(dirname "$0")"

echo "=== B1: binwalk quet chu ky ==="
# Moi truong binh thuong: binwalk carve.img
# May nay binwalk 2.x ket voi capstone moi, nen chay qua shim (xem binwalk_shim.py):
/usr/bin/python3 binwalk_shim.py carve.img 2>&1 | head -12

echo
echo "=== B2: carver python theo header/footer ==="
python3 -I carve.py carve.img out

echo
echo "=== B3: verify tung file carve ra co mo duoc khong ==="
for f in out/*; do printf "%-12s -> " "$f"; file -b "$f"; done
echo "-- unzip test --"; unzip -t out/01.zip 2>&1 | tail -2

echo
echo "=== B4: so khop byte voi ban goc (JPG/PNG carve dung tron) ==="
echo -n "JPG "; cmp -s j.jpg out/01.jpg && echo "khop tung byte (md5 $(md5sum out/01.jpg|awk '{print $1}'))" || echo "khac (van mo duoc)"
echo -n "PNG "; cmp -s p.png out/01.png && echo "khop tung byte (md5 $(md5sum out/01.png|awk '{print $1}'))" || echo "khac (van mo duoc)"

echo
echo "=== B5: tu tim header JPEG bang xxd + grep (doi chieu offset voi binwalk) ==="
xxd carve.img | grep -i 'ffd8 ff' | head -1
