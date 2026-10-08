#!/usr/bin/env bash
# Build lab 3.4. Da kiem tren Ubuntu 24.04, glibc 2.39, gcc 13.3.
set -e
cd "$(dirname "$0")"

FLAGS="-fno-stack-protector -no-pie -fcf-protection=none -O0 -g"

gcc $FLAGS -o chall1 chall1.c   # ret2win khong tham so
gcc $FLAGS -o chall2 chall2.c   # ret2win mot tham so (system)
gcc $FLAGS -o chall3 chall3.c   # ret2win hai tham so (system)

echo 'FLAG{ret2win_level_cleared}' > flag.txt

echo "[*] built: chall1 chall2 chall3 ; flag.txt created"
