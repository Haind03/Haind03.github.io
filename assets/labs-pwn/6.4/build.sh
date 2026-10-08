#!/usr/bin/env bash
# Build lab 6.4 (ROP Emporium tuong duong). Ubuntu 24.04, glibc 2.39, gcc 13.3.
# Tu dung binary vi khong tai duoc tu ropemporium.com tren server; cung lo hong,
# cung mitigation (no-PIE, NX, khong canary), gadget nhet san giong ban goc.
set -e
cd "$(dirname "$0")"

FLAGS="-fno-stack-protector -no-pie -fcf-protection=none -O0 -g"

gcc $FLAGS -o ret2win ret2win.c
gcc $FLAGS -o split   split.c
gcc $FLAGS -o callme  callme.c
gcc $FLAGS -o write4  write4.c

echo "FLAG{rop_emporium_local_equivalent_p6_2026}" > flag.txt
echo "[*] built: ret2win split callme write4 (+ flag.txt)"
