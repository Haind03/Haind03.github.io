#!/usr/bin/env bash
# Build lab 9.4 capstone (note app, GOT overwrite). Ubuntu 24.04, glibc 2.39, gcc 13.3.
# -no-pie: dia chi backdoor() va cac o GOT co dinh. Partial RELRO (mac dinh) GIU .got.plt
# ghi duoc -> dieu kien can de ghi de atoi@got. Full RELRO se chan cach nay.
set -e
cd "$(dirname "$0")"

FLAGS="-no-pie -fno-stack-protector -O0 -g"

gcc $FLAGS -o noteapp src.c
echo "[*] built: noteapp"
[ -f flag.txt ] || echo 'PTIT{h3ap_n0t3_tc4ch3_p0is0n_2026}' > flag.txt
echo "[*] flag.txt san sang"
