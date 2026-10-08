#!/usr/bin/env bash
# Build lab 10.3 (do an cuoi: fmtstr leak canary+libc -> ret2libc).
# Da kiem tren Ubuntu 24.04.4, glibc 2.39-0ubuntu8.9, gcc 13.3.0.
# CHU Y: KHONG dung -fno-stack-protector o day. Ta MUON canary bat de phai leak.
# -fstack-protector-all ep moi ham deu co canary. -no-pie dia chi co dinh.
# -fcf-protection=none gadget sach. -O0 -g de doc/debug.
set -e
cd "$(dirname "$0")"

FLAGS="-fstack-protector-all -no-pie -fcf-protection=none -O0 -g"

gcc $FLAGS -o diary src.c
echo "[*] built: diary"

echo 'FLAG{do_an_cuoi_fmtstr_canary_ret2libc}' > flag.txt
echo "[*] flag.txt created"

command -v checksec >/dev/null 2>&1 && checksec --file=diary || true
