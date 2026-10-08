# Lab 5.1 - So sanh mitigation bang checksec

Thuoc Bai 5.1. Bien dich cung mot `vuln.c` voi nhieu to hop flag roi chay
`checksec` de thay tung mitigation bat/tat the nao.

## File

- `vuln.c` - chuong trinh toi thieu (co cho doc input).
- `build.sh` - bien dich 8 ban: vuln_all, vuln_nopie, vuln_exec, vuln_canary,
  vuln_pie, vuln_partial, vuln_norelro, vuln_nocet.
- `transcript.txt` - output checksec THAT cua ca 8 ban + bang tong hop.

## Build va chay

```bash
bash build.sh
pwn checksec vuln_all      # Full RELRO, Canary, NX, PIE, SHSTK+IBT
pwn checksec vuln_nopie    # Partial RELRO, No canary, NX, No PIE
# ... (xem transcript.txt cho ca 8 ban)
```

## Diem dang chu y tren Ubuntu 24.04 / gcc 13.3

- gcc MAC DINH bat `-fcf-protection` (CET), nen checksec hien them `SHSTK:
  Enabled` va `IBT: Enabled` o moi ban khong co `-fcf-protection=none`.
- gcc mac dinh cho `Full RELRO` (khong phai Partial nhu tai lieu cu). Muon
  Partial phai ep `-Wl,-z,relro,-z,lazy`.
- `-z execstack` lam checksec bao `NX unknown - GNU_STACK missing` + `Stack:
  Executable` + `RWX: Has RWX segments`.

## Moi truong

Ubuntu 24.04.4, glibc 2.39, gcc 13.3.0. Toan bo bang checksec trong
transcript.txt la output that.
