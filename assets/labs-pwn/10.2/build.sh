#!/usr/bin/env bash
# Build lab 10.2 (guestbook: leak libc + ret2libc).
# Da kiem tren Ubuntu 24.04.4, glibc 2.39-0ubuntu8.9, gcc 13.3.0.
# -fno-stack-protector: tat canary. -no-pie: dia chi binary co dinh.
# -fcf-protection=none: khong endbr64 lam ban gadget. -O0 -g: de doc/debug.
set -e
cd "$(dirname "$0")"

FLAGS="-fno-stack-protector -no-pie -fcf-protection=none -O0 -g"

gcc $FLAGS -o guestbook src.c
echo "[*] built: guestbook"

# flag gia de minh hoa (exploit lay shell roi tu doc file nay)
echo 'FLAG{wr1teup_leak_libc_ret2libc_ok}' > flag.txt
echo "[*] flag.txt created"

command -v checksec >/dev/null 2>&1 && checksec --file=guestbook || true
