#!/usr/bin/env bash
# Lab 1.5 - solve: doc MFT record bang istat, parse record tho bang xxd + mftparse.py,
# va convert FILETIME bang python.
set -u
cd "$(dirname "$0")"
IMG=lab15.ntfs

echo "=== B1: fsstat NTFS ==="
fsstat "$IMG" 2>/dev/null | sed -n '1,14p'

echo
echo "=== B2: istat record 0 (\$MFT) ==="
istat "$IMG" 0 2>&1 | head -14

echo
echo "=== B3: istat record 5 (root directory) - co \$STANDARD_INFORMATION va \$FILE_NAME ==="
istat "$IMG" 5 2>&1 | sed -n '1,30p'

echo
echo "=== B4: 4 byte dau record tho = chu ky FILE ==="
xxd -l 16 mft_rec0.bin

echo
echo "=== B5: parse header record tho bang mftparse.py ==="
python3 -I mftparse.py mft_rec0.bin

echo
echo "=== B6: convert FILETIME sang gio nguoi doc (vi du bai) ==="
python3 -I -c "import datetime; v=0x01DA6F1C4B2E9A30; print(datetime.datetime(1601,1,1)+datetime.timedelta(microseconds=v//10))"
