#!/usr/bin/env bash
# Build lab 8.2 (ret2plt + ret2dlresolve).
# Ubuntu 24.04, glibc 2.39, gcc 13.3.
# No-PIE + Partial RELRO (lazy binding) de ret2dlresolve dung duoc:
#   -z relro -z lazy (KHONG -z now/full).
set -e
cd "$(dirname "$0")"

FLAGS="-fno-stack-protector -no-pie -fcf-protection=none -z relro -z lazy -O0 -g"

gcc $FLAGS -o ret2plt   ret2plt.c
echo "[*] built: ret2plt"
gcc $FLAGS -o dlresolve dlresolve.c
echo "[*] built: dlresolve"
