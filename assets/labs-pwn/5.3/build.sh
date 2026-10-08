#!/usr/bin/env bash
# Build lab 5.3 (ASLR/PIE leak). Da kiem tren Ubuntu 24.04, glibc 2.39, gcc 13.3.
# -fpie -pie            : binary PIE (ET_DYN), base image random khi ASLR bat
# -fno-stack-protector  : bo canary, tap trung vao PIE leak
# -fcf-protection=none  : khong endbr/CET, gadget ret sach
# -O0 -g                : stack frame de doc
set -e
cd "$(dirname "$0")"

FLAGS="-fno-stack-protector -fpie -pie -fcf-protection=none -O0 -g"
gcc $FLAGS -o lab src.c

echo "[*] built: lab (PIE, No canary, NX). Nho bat ASLR that khi chay (randomize_va_space=2)."
