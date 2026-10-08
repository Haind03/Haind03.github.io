#!/usr/bin/env bash
# Build lab 6.2 (leak libc qua GOT). Ubuntu 24.04, glibc 2.39, gcc 13.3.
set -e
cd "$(dirname "$0")"

FLAGS="-fno-stack-protector -no-pie -fcf-protection=none -O0 -g"

gcc $FLAGS -o leaklibc src.c
echo "[*] built: leaklibc"
