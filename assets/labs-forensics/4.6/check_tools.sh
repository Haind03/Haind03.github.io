#!/usr/bin/env bash
# Lab 4.6 helper: kiem tra moi truong co du cong cu lam VSS khong, va in buoc tiep theo.
# VSS can Windows (vssadmin) hoac libvshadow tren image co shadow -> lab nay chu yeu la BAI TAP.
echo "=== Lab 4.6: kiem tra cong cu Volume Shadow Copy ==="
for t in vshadowinfo vshadowmount mmls fls; do
  if command -v "$t" >/dev/null 2>&1; then
    echo "  [co]     $t -> $(command -v $t)"
  else
    echo "  [thieu]  $t"
  fi
done
echo
echo "libvshadow (vshadowinfo/vshadowmount) cai bang: apt install libvshadow-utils"
echo "hoac build tu github.com/libyal/libvshadow."
echo
if [ -n "$1" ] && command -v vshadowinfo >/dev/null 2>&1; then
  echo "=== vshadowinfo tren $1 ==="
  vshadowinfo "$1"
else
  echo "Dua image co VSS lam tham so de chay thu: bash check_tools.sh disk.raw"
  echo "Khong co image/tool -> xem README.md de lam BAI TAP tren VM Windows."
fi
