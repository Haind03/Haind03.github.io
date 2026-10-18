#!/usr/bin/env bash
# Lab 3.3 - solve: fls -rd / istat / icat khoi phuc tren ext4 va FAT, so MD5, va demo ghi de.
set -u
cd "$(dirname "$0")"

echo "################ EXT4 ################"
echo "=== fls -rd ==="; fls -rd ext.img 2>&1 | grep -i baocao
EINO=$(fls -rd ext.img 2>/dev/null | awk '/baocao/{gsub(/:/,"",$3);print $3;exit}')
echo "inode da xoa = $EINO"
echo "=== istat ==="; istat ext.img "$EINO" 2>&1 | sed -n '1,3p;/Inode Times/,/Direct/p'
echo "=== icat khoi phuc + so MD5 ==="
echo -n "md5 goc:   "; md5sum baocao.txt | awk '{print $1}'
echo -n "md5 cuu:   "; icat ext.img "$EINO" 2>/dev/null | md5sum | awk '{print $1}'

echo
echo "################ FAT ################"
echo "=== fls -rd (ten dau bi thay 0xE5) ==="; fls -rd fat.img 2>&1 | grep -i OTE
FINO=$(fls -rd fat.img 2>/dev/null | awk '/OTE/{gsub(/:/,"",$3);print $3;exit}')
echo "inode da xoa = $FINO"
echo "=== istat ==="; istat fat.img "$FINO" 2>&1 | sed -n '1,8p'
echo "=== icat khoi phuc + so MD5 ==="
echo -n "md5 goc:   "; md5sum note.txt | awk '{print $1}'
echo -n "md5 cuu:   "; icat fat.img "$FINO" 2>/dev/null | md5sum | awk '{print $1}'

echo
echo "################ GHI DE = MAT DU LIEU ################"
echo "Ghi mot file moi de len dung cluster cua NOTE.TXT da xoa, roi thu cuu lai:"
printf 'DU LIEU MOI DE LEN CLUSTER CU 0000000000\n' > big.bin
python3 -I fatput.py fat.img OTHER.TXT big.bin
echo "-- icat lai inode da xoa $FINO sau khi cluster bi ghi de --"
icat fat.img "$FINO" 2>/dev/null | head -1
echo "-> noi dung cu da bi thay, khong con cuu dung nua. Bai hoc: ngung dung o ngay khi can khoi phuc."
