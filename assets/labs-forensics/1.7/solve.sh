#!/usr/bin/env bash
# Lab 1.7 - solve: verify hash, phat hien sua 1 byte, so hash 2 bien the, fuzzy hash.
set -u
cd "$(dirname "$0")"

echo "=== B1: hash goc da luu ==="
cat disk.img.sha256

echo
echo "=== B2: tao ban lam viec, verify OK, roi sua 1 byte va verify lai ==="
cp -f disk.img work.img
sha256sum work.img > work.sha256
echo "-- verify truoc khi sua --"; sha256sum -c work.sha256
printf '\x00' | dd of=work.img bs=1 seek=100 count=1 conv=notrunc status=none
echo "-- verify sau khi sua 1 byte tai offset 100 --"; sha256sum -c work.sha256 || true

echo
echo "=== B3: hai bien the van ban, hash mat ma khac hoan toan ==="
md5sum    v1.txt v2.txt
sha256sum v1.txt v2.txt

echo
echo "=== B4: fuzzy hash minh hoa (ssdeep khong co) ==="
python3 -I fuzzyhash.py v1.txt v2.txt disk.img
echo "(v1 vs v2 cao vi gan giong; v1/v2 vs disk.img ~0 vi khong lien quan)"
