#!/usr/bin/env python3
# Lab 1.5 - parse header cua mot MFT record (1024 byte) va liet ke attribute type.
# Chay: python3 -I mftparse.py mft_rec.bin
import struct, sys

data = open(sys.argv[1], "rb").read()
sig = data[0:4]
print("Signature (0x00)            :", sig, "->", "FILE record hop le" if sig == b"FILE" else "KHONG phai FILE")
usa_off   = struct.unpack("<H", data[0x04:0x06])[0]
usa_cnt   = struct.unpack("<H", data[0x06:0x08])[0]
lsn       = struct.unpack("<Q", data[0x08:0x10])[0]
seq       = struct.unpack("<H", data[0x10:0x12])[0]
links     = struct.unpack("<H", data[0x12:0x14])[0]
attr_off  = struct.unpack("<H", data[0x14:0x16])[0]
flags     = struct.unpack("<H", data[0x16:0x18])[0]
used      = struct.unpack("<I", data[0x18:0x1c])[0]
alloc     = struct.unpack("<I", data[0x1c:0x20])[0]
print("Update Sequence offset (0x04):", usa_off, " count:", usa_cnt)
print("$LogFile Seq Number    (0x08):", lsn)
print("Sequence number        (0x10):", seq, " Hard links (0x12):", links)
print("Offset to 1st attribute(0x14):", attr_off, "(0x%02x)" % attr_off)
fl = []
if flags & 0x01: fl.append("IN_USE")
else:            fl.append("DELETED")
if flags & 0x02: fl.append("DIRECTORY")
else:            fl.append("FILE")
print("Flags                  (0x16): 0x%04x ->" % flags, ", ".join(fl))
print("Used size / Allocated  (0x18): %d / %d byte" % (used, alloc))

ATTR = {0x10: "$STANDARD_INFORMATION", 0x30: "$FILE_NAME", 0x40: "$OBJECT_ID",
        0x50: "$SECURITY_DESCRIPTOR", 0x60: "$VOLUME_NAME", 0x70: "$VOLUME_INFORMATION",
        0x80: "$DATA", 0x90: "$INDEX_ROOT", 0xA0: "$INDEX_ALLOCATION", 0xB0: "$BITMAP"}
print("Attributes:")
off = attr_off
while off + 4 <= len(data):
    atype = struct.unpack("<I", data[off:off+4])[0]
    if atype == 0xffffffff:
        print("  0xffffffff  END marker"); break
    alen = struct.unpack("<I", data[off+4:off+8])[0]
    if alen == 0: break
    resident = data[off+8] == 0
    print("  type 0x%02x  %-22s  len=%-4d  %s" % (atype, ATTR.get(atype, "?"), alen,
          "resident" if resident else "non-resident"))
    off += alen
