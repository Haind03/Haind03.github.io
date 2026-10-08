#!/usr/bin/env bash
# Build lab 3.2. Da kiem tren Ubuntu 24.04, glibc 2.39, gcc 13.3.
set -e
cd "$(dirname "$0")"

FLAGS="-fno-stack-protector -no-pie -fcf-protection=none -O0 -g"

gcc $FLAGS -o ret2win ret2win.c   # demo: buf[64], win dung syscall
gcc $FLAGS -o jump    jump.c      # lab:  buf[120], offset khac

echo 'picoCTF{fake_flag_for_demo}' > flag.txt

echo "[*] built: ret2win jump ; flag.txt created"
