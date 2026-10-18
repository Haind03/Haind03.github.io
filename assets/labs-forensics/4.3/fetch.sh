#!/usr/bin/env bash
# Lab 4.3: tai hive mau CONG KHAI (regipy test data, MIT): amcache.hve, SYSTEM, NTUSER.DAT.
# Deu la artifact DU LIEU (registry hive), khong phai file thuc thi.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
BASE="https://github.com/mkorman90/regipy/raw/master/regipy_tests/data"

echo "[*] Cai dependency: pip install 'regipy[cli]' tabulate"
python3 -m pip install --quiet "regipy[cli]" tabulate >/dev/null 2>&1 || true

cd "$HERE"
for f in amcache.hve.xz SYSTEM.xz NTUSER.DAT.xz; do
  echo "[*] tai $f"
  curl -sL -o "$f" "$BASE/$f"
  xz -dkf "$f"
done
echo "[*] xong (nguon: github.com/mkorman90/regipy, MIT)"
