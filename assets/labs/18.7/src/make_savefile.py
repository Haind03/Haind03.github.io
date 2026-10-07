#!/usr/bin/env python3
# Generates save game files in a self-made binary format (.sav).
# Used as a practice target for reversing a file format: you use make_savefile.py
# to create a few samples, compare the hex to guess the structure, then write a parser.
#
# Layout (little-endian):
#   offset 0  : magic      4 byte  "SAVE"  (0x53 0x41 0x56 0x45)
#   offset 4  : version    u16     = 2
#   offset 6  : flags      u16     bit0 = hardcore, bit1 = cheats_used
#   offset 8  : level      u32
#   offset 12 : gold       u32
#   offset 16 : name_len   u16
#   offset 18 : name       name_len byte (ASCII, NOT null-terminated)
#   next      : n_items    u16
#   each item : item_id u16 + qty u16   (repeated n_items times)
#   file end  : checksum   u32  = sum of all preceding bytes, mod 2^32
import struct, sys

def build(name: str, level: int, gold: int, flags: int, items):
    body = b"SAVE"
    body += struct.pack("<H", 2)          # version
    body += struct.pack("<H", flags)      # flags
    body += struct.pack("<I", level)      # level
    body += struct.pack("<I", gold)       # gold
    nb = name.encode()
    body += struct.pack("<H", len(nb)) + nb
    body += struct.pack("<H", len(items))
    for item_id, qty in items:
        body += struct.pack("<HH", item_id, qty)
    chk = sum(body) & 0xFFFFFFFF
    body += struct.pack("<I", chk)
    return body

SAMPLES = {
    "save_alice.sav": ("alice", 7,  1500, 0b01, [(101, 3), (205, 1)]),
    "save_bob.sav":   ("bob",   7,  1500, 0b01, [(101, 3), (205, 1)]),   # differs only in name -> reveals the name offset
    "save_rich.sav":  ("alice", 7, 999999, 0b11, [(101, 3), (205, 1)]),  # differs only in gold+flags -> reveals the gold offset
}

if __name__ == "__main__":
    for fn, args in SAMPLES.items():
        data = build(*args)
        with open(fn, "wb") as f:
            f.write(data)
        print(f"{fn}: {len(data)} byte")
