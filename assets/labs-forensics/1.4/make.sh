#!/usr/bin/env bash
# Lab 1.4 - FAT16: tao image bang mkfs.vfat, chep 2 file bang python injector
# (vi moi truong khong co mtools/mount), roi xoa 1 file de luyen khoi phuc.
set -eu
cd "$(dirname "$0")"
IMG=lab14.fat
rm -f "$IMG" note.txt luong.txt rec_luong.txt

dd if=/dev/zero of="$IMG" bs=1M count=16 status=none
mkfs.vfat -F 16 -n LABFAT "$IMG" >/dev/null 2>&1

printf 'wifi password: Hunter2!  tai khoan: admin\n'            > note.txt
printf 'bang luong thang 9: giam doc 50tr, ke toan 18tr\n'      > luong.txt

python3 -I fatput.py "$IMG" NOTE.TXT  note.txt
python3 -I fatput.py "$IMG" LUONG.TXT luong.txt

echo "[make] da tao $IMG voi NOTE.TXT va LUONG.TXT"
ls -l "$IMG"
