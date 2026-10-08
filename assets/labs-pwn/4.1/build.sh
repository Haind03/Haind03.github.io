#!/usr/bin/env bash
# Build lab 4.1 (loader shellcode). Da kiem tren Ubuntu 24.04, glibc 2.39, gcc 13.3.
# Loader xin RWX thang tu mmap nen khong can -z execstack o day.
set -e
cd "$(dirname "$0")"

gcc -O0 -g -o loader src.c
echo "[*] built: loader"
