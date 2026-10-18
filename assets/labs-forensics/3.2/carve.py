#!/usr/bin/env python3
# Simple header/footer file carver. Usage: carve.py image outdir
import sys, os
img, outdir = sys.argv[1], sys.argv[2]
data = open(img,'rb').read()
os.makedirs(outdir, exist_ok=True)
found = []
def grab(name, start, end):
    path = os.path.join(outdir, name)
    open(path,'wb').write(data[start:end])
    found.append((name, start, end-start))

# JPEG: FFD8 ... FFD9
i=0; n=0
while True:
    s=data.find(b'\xff\xd8\xff', i)
    if s<0: break
    e=data.find(b'\xff\xd9', s)
    if e<0: break
    n+=1; grab(f'{n:02d}.jpg', s, e+2); i=e+2
# PNG: 89504E470D0A1A0A ... IEND + 4-byte CRC
i=0; n=0
sig=bytes.fromhex('89504e470d0a1a0a')
while True:
    s=data.find(sig, i)
    if s<0: break
    e=data.find(b'IEND', s)
    if e<0: break
    n+=1; grab(f'{n:02d}.png', s, e+8); i=e+8
# ZIP: local file header PK\x03\x04 ... EOCD PK\x05\x06 (+18 bytes +comment)
i=0; n=0
while True:
    s=data.find(b'PK\x03\x04', i)
    if s<0: break
    eo=data.find(b'PK\x05\x06', s)
    if eo<0: break
    clen=int.from_bytes(data[eo+20:eo+22],'little')
    e=eo+22+clen
    n+=1; grab(f'{n:02d}.zip', s, e); i=e
# PDF: %PDF ... %%EOF
i=0; n=0
while True:
    s=data.find(b'%PDF', i)
    if s<0: break
    e=data.find(b'%%EOF', s)
    if e<0: break
    n+=1; grab(f'{n:02d}.pdf', s, e+5); i=e+5
for name,off,size in found:
    print(f'{name:10s} offset={off:<6d} size={size}')
