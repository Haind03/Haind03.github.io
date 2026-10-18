import sys, struct
img, target = sys.argv[1], sys.argv[2].upper()
with open(img,'r+b') as f:
    bs=f.read(36)
    bps=struct.unpack('<H',bs[11:13])[0]; resv=struct.unpack('<H',bs[14:16])[0]
    nfat=bs[16]; rootn=struct.unpack('<H',bs[17:19])[0]; spf16=struct.unpack('<H',bs[22:24])[0]
    root_start=resv+nfat*spf16; root_sectors=(rootn*32+bps-1)//bps
    f.seek(root_start*bps); root=bytearray(f.read(root_sectors*bps))
    nm,_,ex=target.partition('.')
    key=(nm.ljust(8)[:8]+ex.ljust(3)[:3]).encode()
    for i in range(0,len(root),32):
        if root[i:i+11]==key:
            clu=struct.unpack('<H',root[i+26:i+28])[0]
            f.seek(root_start*bps+i); f.write(b'\xe5')     # mark deleted
            for k in range(nfat):                          # free FAT chain (1 cluster)
                f.seek((resv+k*spf16)*bps+clu*2); f.write(struct.pack('<H',0))
            print("deleted %s (was cluster %d)"%(target,clu)); break
