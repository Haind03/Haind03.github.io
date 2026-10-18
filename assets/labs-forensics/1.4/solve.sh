#!/usr/bin/env bash
# Lab 1.4 - solve: doc cau truc FAT bang fsstat/fls/istat, xoa 1 file va khoi phuc bang icat.
set -u
cd "$(dirname "$0")"
IMG=lab14.fat

echo "=== B1: fsstat - layout FAT16 (reserved/FAT/root/data) ==="
fsstat "$IMG" 2>/dev/null | sed -n '1,22p'

echo
echo "=== B2: boot sector (BPB) bang xxd ==="
xxd -l 64 "$IMG"

echo
echo "=== B3: fls - liet ke file (volume label + 2 file) ==="
fls "$IMG" 2>&1 | head

echo
echo "=== B4: istat NOTE.TXT (first cluster, sector, size) ==="
NINO=$(fls "$IMG" 2>/dev/null | awk '/NOTE.TXT/{gsub(/:/,"",$2);print $2;exit}')
istat "$IMG" "$NINO" 2>&1 | head -15

echo
echo "=== B5: xoa LUONG.TXT (0xE5 + free FAT chain) roi khoi phuc ==="
echo -n "MD5 goc: "; md5sum luong.txt | awk '{print $1}'
python3 -I fatdel.py "$IMG" LUONG.TXT
echo "-- fls -rd (file da xoa, ten dau bi thay) --"
fls -rd "$IMG" 2>&1 | head
DINO=$(fls -rd "$IMG" 2>/dev/null | awk '/UONG/{gsub(/:/,"",$3);print $3;exit}')
echo "deleted inode = $DINO"
echo "-- icat khoi phuc --"
icat "$IMG" "$DINO" 2>/dev/null | tee rec_luong.txt
echo -n "MD5 sau khoi phuc: "; md5sum rec_luong.txt | awk '{print $1}'
echo -n "khop tung byte? "; cmp -s luong.txt rec_luong.txt && echo "YES (identical)" || echo "KHAC"
