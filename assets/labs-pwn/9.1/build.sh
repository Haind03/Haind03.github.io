#!/usr/bin/env bash
# Build demo 9.1 (quan sat heap layout). Da kiem tren Ubuntu 24.04, glibc 2.39, gcc 13.3.
set -e
cd "$(dirname "$0")"

FLAGS="-no-pie -fno-stack-protector -O0 -g"

gcc $FLAGS -o heapview src.c
echo "[*] built: heapview"
echo "[*] chay: setarch -R ./heapview   (ASLR off cho so on dinh)"
echo "[*] hoac: gdb -q -nx -x look.gdb ./heapview"
