#!/usr/bin/env bash
# Build lab 3.3. Da kiem tren Ubuntu 24.04, glibc 2.39, gcc 13.3.
# -fcf-protection=none quan trong: tranh endbr64 chen vao dau ham, giu
# gadget pop rdi ; ret sach de ROPgadget tim thay.
set -e
cd "$(dirname "$0")"

FLAGS="-fno-stack-protector -no-pie -fcf-protection=none -O0 -g"

gcc $FLAGS -o callme   callme.c     # demo: win(magic) goi system
gcc $FLAGS -o keycheck keycheck.c   # lab:  win(code) goi system

echo "[*] built: callme keycheck"
