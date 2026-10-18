#!/usr/bin/env python3
# Minimal FAT12/16 single-cluster file injector (no mount, no mtools).
# Writes into the first free root-dir slot and first free data cluster.
# Usage: fatput.py image.fat NAME.EXT datafile
import sys, struct
img, name83, dataf = sys.argv[1], sys.argv[2], sys.argv[3]
data = open(dataf,'rb').read()
with open(img,'r+b') as f:
    bs = f.read(36)
    bps   = struct.unpack('<H', bs[11:13])[0]
    spc   = bs[13]
    resv  = struct.unpack('<H', bs[14:16])[0]
    nfat  = bs[16]
    rootn = struct.unpack('<H', bs[17:19])[0]
    spf16 = struct.unpack('<H', bs[22:24])[0]
    cluster_bytes = bps*spc
    if len(data) > cluster_bytes:
        sys.exit("file too big for single-cluster demo (max %d)" % cluster_bytes)
    root_sectors = (rootn*32 + bps - 1)//bps
    fat_start  = resv
    root_start = resv + nfat*spf16
    data_start = root_start + root_sectors
    # find first free data cluster (FAT entry == 0), starting at cluster 2
    f.seek(fat_start*bps)
    fat0 = bytearray(f.read(spf16*bps))
    clu = None
    for c in range(2, (spf16*bps)//2):
        if struct.unpack('<H', fat0[c*2:c*2+2])[0] == 0:
            clu = c; break
    if clu is None: sys.exit("no free cluster")
    clu_sector = data_start + (clu-2)*spc
    f.seek(clu_sector*bps); f.write(data)
    for i in range(nfat):
        f.seek((fat_start+i*spf16)*bps + clu*2); f.write(struct.pack('<H', 0xFFFF))
    # find first free root slot (first byte 0x00 or 0xE5)
    f.seek(root_start*bps)
    root = f.read(root_sectors*bps)
    slot = None
    for i in range(0, len(root), 32):
        b0 = root[i]
        if b0 in (0x00, 0xE5): slot = i; break
    if slot is None: sys.exit("root dir full")
    nm, _, ex = name83.partition('.')
    ent  = (nm.upper().ljust(8)[:8] + ex.upper().ljust(3)[:3]).encode('ascii')
    ent += bytes([0x20]) + bytes(10)
    ent += struct.pack('<H', 0x4A21) + struct.pack('<H', 0x5948)  # write time/date
    ent += struct.pack('<H', clu) + struct.pack('<I', len(data))
    f.seek(root_start*bps + slot); f.write(ent)
print("injected %s (%d bytes) cluster=%d sector=%d slot=%d" % (name83, len(data), clu, clu_sector, slot//32))
