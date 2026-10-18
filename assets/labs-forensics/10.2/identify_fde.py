#!/usr/bin/env python3
# Nhan dien phan vung ma hoa toan o (FDE) bang signature. CHAY THAT tren bat ky file image nao.
# Doc buoc 2.1 cua bai 10.2: nhan dien truoc, tim khoa truoc, crack sau cung.
import sys

SIGS = [
    (b"LUKS\xba\xbe",  "LUKS (Linux Unified Key Setup) - dm-crypt"),
    (b"-FVE-FS-",      "BitLocker (Windows Full Volume Encryption)"),
    (b"-FVE-FS-NTFS",  "BitLocker (phien ban cu, bootable)"),
]

def scan(path, window=1<<20):
    with open(path, "rb") as f:
        head = f.read(window)
    hits = []
    for magic, desc in SIGS:
        off = head.find(magic)
        if off >= 0:
            hits.append((off, magic, desc))
    print("[*] %s" % path)
    if not hits:
        print("    khong thay signature FDE quen thuoc trong %d byte dau." % len(head))
        print("    => co the chua ma hoa, hoac FDE khac (VeraCrypt khong co magic ro rang).")
    for off, magic, desc in hits:
        print("    offset 0x%x: magic %r => %s" % (off, magic, desc))
        if magic.startswith(b"LUKS"):
            ver = int.from_bytes(head[off+6:off+8], "big")
            print("        LUKS version field = %d (buoc tiep: cryptsetup luksDump)" % ver)
        if magic == b"-FVE-FS-":
            print("        buoc tiep: dislocker -V / repair-bde -rp de lay RecoveryKeyID")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: identify_fde.py <image1> [image2 ...]"); sys.exit(1)
    for p in sys.argv[1:]:
        scan(p)
