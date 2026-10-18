#!/usr/bin/env bash
# Lab 10.2: buoc NHAN DIEN FDE chay that (signature). Buoc giai ma/crack la BAI TAP (xem README).
HERE="$(cd "$(dirname "$0")" && pwd)"
echo "### [1] tao sample signature (stub, KHONG phai container ma hoa that):"
python3 -I "$HERE/make_sig_samples.py"
echo
echo "### [2] nhan dien FDE bang signature:"
python3 -I "$HERE/identify_fde.py" "$HERE/luks_header.sig" "$HERE/bitlocker.sig" "$HERE/filevault.sig"
echo
echo "### cryptsetup co trong moi truong nay khong?"
if command -v cryptsetup >/dev/null 2>&1; then
  echo "co: $(command -v cryptsetup) -> co the lam phan LUKS that (xem README buoc B)."
else
  echo "KHONG co cryptsetup -> phan tao/mo/crack LUKS la BAI TAP (xem README)."
fi
