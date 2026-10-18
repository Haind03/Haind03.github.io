#!/usr/bin/env python3
# Lab 3.4 - LSB steganography that tren PNG (dung Pillow).
# embed : python3 -I lsb.py embed cover.png out.png "thong diep"
# extract: python3 -I lsb.py extract out.png
import sys, warnings
warnings.filterwarnings("ignore")
from PIL import Image

MARK = "\x00"  # ky tu ket thuc thong diep

def bits(msg):
    for ch in msg:
        v = ord(ch)
        for i in range(8):
            yield (v >> (7 - i)) & 1

def embed(cover, out, msg):
    im = Image.open(cover).convert("RGB")
    px = list(im.getdata())
    data = msg + MARK
    b = list(bits(data))
    if len(b) > len(px):
        sys.exit("thong diep qua dai so voi anh")
    newpx = []
    for i, (r, g, bl) in enumerate(px):
        if i < len(b):
            r = (r & 0xFE) | b[i]   # ghi bit vao LSB kenh do
        newpx.append((r, g, bl))
    im.putdata(newpx)
    im.save(out)
    print("da giau %d byte vao %s" % (len(data), out))

def extract(stego):
    im = Image.open(stego).convert("RGB")
    px = list(im.getdata())
    out = []
    cur = 0
    nbit = 0
    for (r, g, bl) in px:
        cur = (cur << 1) | (r & 1)
        nbit += 1
        if nbit == 8:
            if cur == 0:
                break
            out.append(chr(cur))
            cur = 0
            nbit = 0
    print("thong diep giau:", "".join(out))

if __name__ == "__main__":
    if sys.argv[1] == "embed":
        embed(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        extract(sys.argv[2])
