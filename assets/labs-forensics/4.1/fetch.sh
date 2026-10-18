#!/usr/bin/env bash
# Lab 4.1: tai hive mau CONG KHAI (regipy test data, MIT) de parse offline.
# Chi tai artifact DU LIEU (registry hive), KHONG tai file thuc thi.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
BASE="https://github.com/mkorman90/regipy/raw/master/regipy_tests/data"

echo "[*] Cai dependency python (neu thieu):"
echo "    pip install 'regipy[cli]' tabulate libfwsi-python libfwps-python libolecf-python"
python3 -m pip install --quiet "regipy[cli]" tabulate >/dev/null 2>&1 || true

cd "$HERE"
for f in SYSTEM.xz SOFTWARE.xz NTUSER.DAT.xz; do
  echo "[*] tai $f"
  curl -sL -o "$f" "$BASE/$f"
  xz -dkf "$f"
done
echo "[*] xong. Hive: SYSTEM SOFTWARE NTUSER.DAT (nguon: github.com/mkorman90/regipy, MIT)"
