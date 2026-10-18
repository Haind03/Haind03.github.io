#!/usr/bin/env bash
# Lab 7.1 - dung tshark dieu tra phien HTTP, trich file va verify hash.
set -euo pipefail
cd "$(dirname "$0")"
PCAP=lab71.pcap
[ -f "$PCAP" ] || { echo "Chua co $PCAP. Chay: python3 -I make.py"; exit 1; }

echo "============================================================"
echo "[1] capinfos: so goi + cua so thoi gian"
echo "============================================================"
capinfos -c -u -a -e "$PCAP"

echo
echo "============================================================"
echo "[2] Conversations (Statistics > Conversations): phien nang nhat"
echo "============================================================"
tshark -r "$PCAP" -q -z conv,tcp

echo
echo "============================================================"
echo "[3] http.request + Follow HTTP Stream (xac nhan magic byte)"
echo "============================================================"
echo "--- cac HTTP request ---"
tshark -r "$PCAP" -Y http.request -T fields -e frame.number -e http.request.method -e http.host -e http.request.uri
echo "--- follow tcp stream 0 (header request + response) ---"
tshark -r "$PCAP" -q -z follow,tcp,ascii,0 | sed -n '1,22p'

echo
echo "============================================================"
echo "[4] Export Objects HTTP -> trich file ra dia"
echo "============================================================"
rm -rf extracted && mkdir -p extracted
tshark -r "$PCAP" --export-objects http,extracted -q
ls -l extracted
echo "--- loai file that (khong tin ten header) ---"
file extracted/*

echo
echo "============================================================"
echo "[5] VERIFY: hash file trich duoc == hash file goc"
echo "============================================================"
EXP=$(sha256sum expected_update.exe | cut -d' ' -f1)
GOT=$(sha256sum extracted/update.exe | cut -d' ' -f1)
printf 'file goc        sha256 : %s\n' "$EXP"
printf 'file trich (http) sha : %s\n' "$GOT"
[ "$EXP" = "$GOT" ] && echo "=> MATCH: file lay tu pcap nguyen ven, dung bang file da truyen." \
                     || { echo "=> MISMATCH"; exit 1; }
