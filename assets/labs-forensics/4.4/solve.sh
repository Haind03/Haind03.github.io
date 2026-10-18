#!/usr/bin/env bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 -I "$HERE/solve.py" "$HERE/bang_luong.xlsx.lnk" \
    "$HERE/jumplist.customDestinations-ms" "$HERE/UsrClass.dat"
