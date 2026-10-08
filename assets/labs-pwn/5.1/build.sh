#!/usr/bin/env bash
# Build lab 5.1: cung mot vuln.c, nhieu to hop mitigation de so sanh checksec.
# Da kiem tren Ubuntu 24.04, glibc 2.39, gcc 13.3.
set -e
cd "$(dirname "$0")"

# 1) Mac dinh cua gcc 13.3 tren Ubuntu 24.04: du bo mitigation
#    (Full RELRO, Canary, NX, PIE, va CET: SHSTK + IBT vi gcc bat -fcf-protection mac dinh)
gcc                                            -o vuln_all      vuln.c

# 2) No PIE + No canary (binary de luyen overflow co dien)
gcc -fno-stack-protector -no-pie               -o vuln_nopie    vuln.c

# 3) Tat NX (stack execute duoc) - de so sanh voi (2)
gcc -fno-stack-protector -no-pie -z execstack  -o vuln_exec     vuln.c

# 4) Canary manh nhat, van No PIE
gcc -fstack-protector-all -no-pie              -o vuln_canary   vuln.c

# 5) NX + PIE, khong canary (de thay rieng tac dong cua PIE)
gcc -fno-stack-protector -fpie -pie            -o vuln_pie      vuln.c

# 6) Partial RELRO (ep linker, vi mac dinh gcc cho Full RELRO)
gcc -fno-stack-protector -no-pie -Wl,-z,relro,-z,lazy -o vuln_partial vuln.c

# 7) No RELRO
gcc -fno-stack-protector -no-pie -Wl,-z,norelro       -o vuln_norelro vuln.c

# 8) Tat CET tren ban mac dinh (de thay SHSTK/IBT bien mat)
gcc -fcf-protection=none                       -o vuln_nocet    vuln.c

echo "[*] built: vuln_all vuln_nopie vuln_exec vuln_canary vuln_pie vuln_partial vuln_norelro vuln_nocet"
