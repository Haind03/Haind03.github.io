#!/usr/bin/env bash
# Build lab 9.3 (double free + tcache poisoning). Da kiem tren Ubuntu 24.04, glibc 2.39, gcc 13.3.
# -no-pie: &hook va &win co dia chi co dinh (khong can leak code).
set -e
cd "$(dirname "$0")"

FLAGS="-no-pie -fno-stack-protector -O0 -g"

gcc $FLAGS -o poison src.c
echo "[*] built: poison"
