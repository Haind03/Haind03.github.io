#!/usr/bin/env bash
# Build lab 4.2 (shellcode tren stack, NX tat). Da kiem tren Ubuntu 24.04,
# glibc 2.39, gcc 13.3.
set -e
cd "$(dirname "$0")"

# NX TAT (-z execstack) la diem then chot: stack thuc thi duoc.
FLAGS="-z execstack -fno-stack-protector -no-pie -fcf-protection=none -O0 -g"

gcc $FLAGS -o vuln src.c
echo "[*] built: vuln"
echo "[*] kiem tra GNU_STACK phai la RWE:"
readelf -lW vuln | grep -A1 GNU_STACK
