#!/usr/bin/env bash
# Build lab 9.2 (UAF + type confusion). Da kiem tren Ubuntu 24.04, glibc 2.39, gcc 13.3.
# -no-pie: dia chi win() co dinh, khong can leak. -fno-stack-protector: khong lien quan
# heap, chi de output checksec gon. Partial RELRO (mac dinh) la du cho bai nay.
set -e
cd "$(dirname "$0")"

FLAGS="-no-pie -fno-stack-protector -O0 -g"

gcc $FLAGS -o uaf src.c
echo "[*] built: uaf"
