#!/usr/bin/env bash
# Lab 1.3 - solve: dung MBR va GPT image bang python, roi parse bang mmls + xxd.
set -u
cd "$(dirname "$0")"

echo "=== MBR: tao va parse ==="
python3 -I mkmbr.py mbr.dd
echo "-- 64 byte partition table + chu ky (offset 0x1b0..0x1ff) --"
xxd -s 0x1b0 -l 80 mbr.dd
echo "-- mmls parse --"
mmls mbr.dd 2>&1

echo
echo "=== GPT: tao va parse ==="
python3 -I mkgpt.py gpt.dd
echo "-- LBA1 GPT header (chu ky EFI PART) --"
xxd -s 512 -l 32 gpt.dd
echo "-- mmls parse --"
mmls gpt.dd 2>&1
echo "-- backup header EFI PART o sector cuoi --"
xxd -s $((512*43007)) -l 16 gpt.dd
