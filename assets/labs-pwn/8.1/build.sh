#!/usr/bin/env bash
# Build lab 8.1 (GOT overwrite bang format string).
# Ubuntu 24.04, glibc 2.39, gcc 13.3.
# Partial RELRO de GOT ghi duoc: -z relro -z lazy (KHONG -z now/full).
set -e
cd "$(dirname "$0")"

FLAGS="-fno-stack-protector -no-pie -fcf-protection=none -z relro -z lazy -O0 -g"

gcc $FLAGS -o fmtgot src.c
echo "[*] built: fmtgot"
echo "flag{got_overwrite_via_format_string}" > flag.txt
