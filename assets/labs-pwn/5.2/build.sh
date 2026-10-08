#!/usr/bin/env bash
# Build lab 5.2 (stack canary). Da kiem tren Ubuntu 24.04, glibc 2.39, gcc 13.3.
# -fstack-protector-all : bat canary o muc manh nhat (moi ham co buffer deu co canary)
# -no-pie               : dia chi win() co dinh, khong phai leak base (mot mitigation mot luc)
# -fcf-protection=none  : khong endbr/CET, giu gadget ret sach de can stack 16 byte
# -O0 -g                : stack frame de doc, de debug
set -e
cd "$(dirname "$0")"

FLAGS="-fstack-protector-all -no-pie -fcf-protection=none -O0 -g"
gcc $FLAGS -o lab src.c

echo "[*] built: lab (canary ON, No PIE, NX)"
