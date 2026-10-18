#!/usr/bin/env python3
# Lab 1.3 - dung mot raw image co MBR partition table hop le bang struct.
# Hai primary: FAT32 (type 0x0b, active) va Linux (type 0x83). mmls se parse ra dung offset.
# Chay: python3 -I mkmbr.py [out.dd]
import struct, os, sys

SEC = 512
out = sys.argv[1] if len(sys.argv) > 1 else "mbr.dd"

def entry(boot, ptype, lba, count):
    # 1 boot flag + 3 CHS start (placeholder) + 1 type + 3 CHS end + 4 LBA + 4 count
    return struct.pack('<B', boot) + b'\xfe\xff\xff' + struct.pack('<B', ptype) \
         + b'\xfe\xff\xff' + struct.pack('<II', lba, count)

mbr = bytearray(SEC)
mbr[446:446+16] = entry(0x80, 0x0b, 2048,  20480)   # FAT32, active,   LBA 2048,  10 MiB
mbr[462:462+16] = entry(0x00, 0x83, 22528, 20480)   # Linux, khong active, LBA 22528, 10 MiB
mbr[510] = 0x55
mbr[511] = 0xaa

with open(out, 'wb') as f:
    f.truncate((22528 + 20480) * SEC)   # sparse, du cho hai phan vung
    f.seek(0)
    f.write(mbr)
print("wrote %s (%d bytes, sparse)" % (out, os.path.getsize(out)))
