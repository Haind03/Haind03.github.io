#!/usr/bin/env python3
# Tao cac MAU CHU KY (signature stub) de chay thu identify_fde.py.
# CANH BAO: day KHONG phai container ma hoa that, chi la vai byte header de minh hoa
# buoc NHAN DIEN. Khong crack/giai ma duoc. Container that can cryptsetup/BitLocker (xem README).
import os
HERE = os.path.dirname(os.path.abspath(__file__))

def stub(name, data, total=4096):
    buf = bytearray(total)
    buf[0:len(data)] = data
    with open(os.path.join(HERE, name), "wb") as f:
        f.write(buf)
    print("wrote", name, "(%d bytes, signature stub only)" % total)

# LUKS1/LUKS2: magic "LUKS\xba\xbe" tai offset 0, sau do la version (2 byte big-endian)
stub("luks_header.sig", b"LUKS\xba\xbe\x00\x02")                 # LUKS2
# BitLocker: chuoi "-FVE-FS-" trong vung metadata (o day dat gan dau de minh hoa)
stub("bitlocker.sig", b"\xeb\x58\x90-FVE-FS-")                    # -FVE-FS-
# FileVault 2 (CoreStorage): magic "CS" o volume header (minh hoa)
stub("filevault.sig", b"\x00\x00\x00\x00CS\x00\x00")
