#!/usr/bin/env bash
# Build lab 7.1 (format string leak). Da kiem tren Ubuntu 24.04, glibc 2.39, gcc 13.3.
# -D_FORTIFY_SOURCE=0 -U_FORTIFY_SOURCE: tat FORTIFY, neu khong glibc doi printf
#   thanh __printf_chk va chan %n, mat tinh huong format string that.
# GIU canary (-fstack-protector-all) va GIU PIE (mac dinh) vi bai nay can
#   LEAK canary va PIE base, nen chung phai ton tai.
set -e
cd "$(dirname "$0")"

FLAGS="-U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=0 -fstack-protector-all -O0 -g"

gcc $FLAGS -o leak src.c
echo "[*] built: leak"
