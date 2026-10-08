#!/usr/bin/env bash
# Build lab 6.3 (ret2syscall). STATIC. Ubuntu 24.04, glibc 2.39, gcc 13.3.
set -e
cd "$(dirname "$0")"

FLAGS="-static -fno-stack-protector -no-pie -fcf-protection=none -O0 -g"

gcc $FLAGS -o syscall src.c
echo "[*] built: syscall (static)"
