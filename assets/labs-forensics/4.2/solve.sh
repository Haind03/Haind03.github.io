#!/usr/bin/env bash
# Lab 4.2: parse .evtx da tai bang fetch.sh.
HERE="$(cd "$(dirname "$0")" && pwd)"
echo "### evtx_dump (python-evtx) 3 record dau de xem raw XML:"
evtx_dump "$HERE/security_4624_4688.evtx" 2>/dev/null | sed -n '1,40p'
echo
echo "### solver:"
python3 -I "$HERE/solve.py" "$HERE/security_4624_4688.evtx"
