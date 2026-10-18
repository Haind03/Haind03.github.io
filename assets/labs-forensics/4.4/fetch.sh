#!/usr/bin/env bash
# Lab 4.4: tai artifact DU LIEU cong khai: mot Jump List (CustomDestinations) va mot hive
# UsrClass.dat. Khong tai file thuc thi.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "[*] Cai dependency:"
echo "    pip install LnkParse3 pylnk3 'regipy[cli]' tabulate libfwsi-python libfwps-python libolecf-python"
python3 -m pip install --quiet LnkParse3 pylnk3 "regipy[cli]" tabulate \
    libfwsi-python libfwps-python libolecf-python >/dev/null 2>&1 || true

cd "$HERE"
echo "[*] tai Jump List mau (LnkParse3 tests, github.com/Matmaus/LnkParse3)"
curl -sL -o jumplist.customDestinations-ms \
  "https://github.com/Matmaus/LnkParse3/raw/master/tests/raw/5afe4de1b92fc382.customDestinations-ms"
echo "[*] tai UsrClass.dat (regipy test data, github.com/mkorman90/regipy, MIT)"
curl -sL -o UsrClass.dat.xz \
  "https://github.com/mkorman90/regipy/raw/master/regipy_tests/data/UsrClass.dat.xz"
xz -dkf UsrClass.dat.xz
echo "[*] sinh mot .lnk benign bang pylnk3"
python3 -I "$HERE/make.py"
echo "[*] xong"
