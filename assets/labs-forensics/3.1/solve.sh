#!/usr/bin/env bash
# Lab 3.1 - solve: mmls/fsstat, fls -rd, icat khoi phuc, bodyfile + mactime timeline.
set -u
cd "$(dirname "$0")"
IMG=case.ext4

echo "=== B1: mmls (image la mot phan vung don -> khong co bang phan vung) ==="
if mmls "$IMG" 2>/dev/null; then :; else
  echo "mmls: khong tim thay partition table (exit 1) -> image la FS don, dung offset 0, bo -o."
fi

echo
echo "=== B2: fsstat - loai FS va offset (dung offset 0) ==="
fsstat "$IMG" 2>/dev/null | sed -n '1,6p'

echo
echo "=== B3: fls -rd - liet ke file da xoa ==="
fls -rd "$IMG" 2>&1 | head
DINO=$(fls -rd "$IMG" 2>/dev/null | awk '/tobedeleted/{gsub(/:/,"",$3);print $3;exit}')
echo "inode file da xoa = $DINO"

echo
echo "=== B4: icat khoi phuc noi dung file da xoa ==="
icat "$IMG" "$DINO" 2>&1

echo
echo "=== B5: bodyfile + mactime timeline (hien thi UTC cho khop gio da gan) ==="
fls -r -m / "$IMG" 2>/dev/null > body.txt
mactime -z UTC -b body.txt 2>&1 | grep -viE '^[[:space:]]*$'
