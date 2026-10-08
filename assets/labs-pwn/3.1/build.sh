#!/usr/bin/env bash
# Build lab 3.1. Da kiem tren Ubuntu 24.04, glibc 2.39, gcc 13.3.
# Flag gcc: tat stack canary, tat PIE (dia chi co dinh), tat CET/endbr
# (de gadget sach), -O0 cho stack frame de doc, -g de debug.
set -e
cd "$(dirname "$0")"

FLAGS="-fno-stack-protector -no-pie -fcf-protection=none -O0 -g"

# login: gets ghi de bien authed trong struct -> shell. gets con link duoc
# tren glibc 2.39 (chi canh bao implicit declaration + "gets is dangerous").
gcc $FLAGS -o login login.c

# admin: gets ghi gia tri cu the 0x80000001 vao role -> in flag
gcc $FLAGS -o admin admin.c

# flag gia de test local (chi cho admin)
echo 'FLAG{ban_da_ghi_de_bien_cuc_bo}' > flag.txt

echo "[*] built: login admin ; flag.txt created"
