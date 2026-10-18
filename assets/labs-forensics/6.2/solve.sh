#!/usr/bin/env bash
# solve.sh - lab 6.2: moi IOC mang tu RAM + doc bang ket noi + liet ke module nap.
set -u
DUMPDIR="${DUMPDIR:-/tmp/mem6_2}"
DUMP="$DUMPDIR/victim.dump"
MAPS="$DUMPDIR/victim.maps"
CONNS="$DUMPDIR/connections.txt"

if [ ! -f "$DUMP" ]; then
  echo "[!] chua co dump. Chay capture.py truoc (DUMPDIR=$DUMPDIR)."
  exit 1
fi

echo "== 1. Cau hinh C2 nhung trong RAM (grep dump) =="
strings -a "$DUMP" | grep -a "C2CONFIG|" | head -1
echo

echo "== 2. Trich IP:cong kieu C2 trong dump (IOC) =="
strings -a "$DUMP" \
  | grep -aoE "(c2_host=|fallback=|beacon_url=http://)[0-9.]+(:[0-9]+)?" \
  | sort -u
echo

echo "== 3. Bang ket noi song luc chup (netscan analog, tu ss -tnp) =="
cat "$CONNS"
echo

echo "== 4. Module nap vao tien trinh (dlllist analog, cac .so tu maps) =="
grep -oE "/[^ ]+\.so(\.[0-9]+)*" "$MAPS" | sort -u | head -12
echo "... (tong so .so: $(grep -oE "/[^ ]+\.so(\.[0-9]+)*" "$MAPS" | sort -u | wc -l))"
