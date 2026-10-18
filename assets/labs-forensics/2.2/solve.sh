#!/usr/bin/env bash
# Lab 2.2 - acquisition + verify toan ven
# 1) dd ra image, 2) md5/sha256 nguon == image, 3) liet ke file da xoa + khoi phuc,
# 4) tamper 1 byte -> hash doi hoan toan.
set -euo pipefail
cd "$(dirname "$0")"

SRC=device.img
IMG=evidence.img
[ -f "$SRC" ] || { echo "Chua co $SRC. Chay ./make.sh truoc."; exit 1; }

echo "============================================================"
echo "[1] ACQUISITION: dd tu thiet bi nguon ra image"
echo "============================================================"
dd if="$SRC" of="$IMG" bs=512 conv=noerror,sync status=none
echo "dd xong: $SRC -> $IMG"

echo
echo "============================================================"
echo "[2] VERIFY: hash nguon phai KHOP hash image"
echo "============================================================"
SRC_MD5=$(md5sum "$SRC" | cut -d' ' -f1)
IMG_MD5=$(md5sum "$IMG" | cut -d' ' -f1)
SRC_SHA=$(sha256sum "$SRC" | cut -d' ' -f1)
IMG_SHA=$(sha256sum "$IMG" | cut -d' ' -f1)
printf 'source md5    : %s\n' "$SRC_MD5"
printf 'image  md5    : %s\n' "$IMG_MD5"
printf 'source sha256 : %s\n' "$SRC_SHA"
printf 'image  sha256 : %s\n' "$IMG_SHA"
if [ "$SRC_MD5" = "$IMG_MD5" ] && [ "$SRC_SHA" = "$IMG_SHA" ]; then
  echo "=> MATCH: image la ban sao bit-by-bit chinh xac cua nguon."
else
  echo "=> MISMATCH: acquisition loi!"; exit 1
fi

echo
echo "============================================================"
echo "[3] NOI DUNG: liet ke file (gom file an va file DA XOA)"
echo "============================================================"
echo "--- fls -r (dau * = file da xoa) ---"
fls -r "$IMG"
echo
echo "--- khoi phuc file da xoa deleted_invoice.txt bang icat ---"
DEL_INODE=$(fls -r "$IMG" | awk '/deleted_invoice.txt/ {gsub(/:/,"",$3); print $3}')
echo "inode cua file da xoa: $DEL_INODE"
echo "noi dung khoi phuc:"
icat "$IMG" "$DEL_INODE"

echo
echo "============================================================"
echo "[4] TAMPER TEST: sua 1 byte -> hash doi hoan toan"
echo "============================================================"
cp "$IMG" tampered.img
printf '\xff' | dd of=tampered.img bs=1 seek=600000 count=1 conv=notrunc status=none
TAMP_MD5=$(md5sum tampered.img | cut -d' ' -f1)
TAMP_SHA=$(sha256sum tampered.img | cut -d' ' -f1)
printf 'image goc   sha256 : %s\n' "$IMG_SHA"
printf 'sau sua 1B  sha256 : %s\n' "$TAMP_SHA"
printf 'image goc   md5    : %s\n' "$IMG_MD5"
printf 'sau sua 1B  md5    : %s\n' "$TAMP_MD5"
echo "=> Doi 1 byte lam ca MD5 lan SHA-256 doi hoan toan (avalanche effect)."
echo "   Day la vi sao verify hash phat hien moi thay doi, du nho nhat."
rm -f tampered.img
