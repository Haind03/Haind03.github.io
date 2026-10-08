#!/usr/bin/env bash
# Build lab 7.2 (format string ghi %n). Da kiem tren Ubuntu 24.04, glibc 2.39, gcc 13.3.
# -D_FORTIFY_SOURCE=0 -U_FORTIFY_SOURCE : tat FORTIFY, neu khong glibc doi printf
#   thanh __printf_chk va chan %n hoan toan.
# -no-pie            : dia chi win va GOT co dinh -> ghi GOT khong can leak (du ASLR bat).
# -fno-stack-protector: khong canary cho don gian.
# -Wl,-z,relro,-z,lazy: Partial RELRO -> .got.plt GHI DUOC (dieu kien de ghi de GOT).
#   Mac dinh gcc 13 la Full RELRO (-z now) se khoa GOT, khi do phai doi muc tieu.
set -e
cd "$(dirname "$0")"

FLAGS="-U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=0 -fno-stack-protector -no-pie -fcf-protection=none -Wl,-z,relro,-z,lazy -O0 -g"

gcc $FLAGS -o writen src.c
echo "[*] built: writen"
