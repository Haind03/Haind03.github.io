#!/usr/bin/env bash
# Lab 10.1: tao image (neu chua co) roi phat hien timestomp + log clearing.
HERE="$(cd "$(dirname "$0")" && pwd)"
[ -f "$HERE/case_disk.img" ] || python3 -I "$HERE/make.py"
python3 -I "$HERE/solve.py" "$HERE/case_disk.img"
