#!/usr/bin/env bash
# Build lab 6.1 (ret2libc). Da kiem tren Ubuntu 24.04, glibc 2.39, gcc 13.3.
# -fcf-protection=none: tranh endbr64 lam ban gadget.
set -e
cd "$(dirname "$0")"

FLAGS="-fno-stack-protector -no-pie -fcf-protection=none -O0 -g"

gcc $FLAGS -o ret2libc src.c
echo "[*] built: ret2libc"
