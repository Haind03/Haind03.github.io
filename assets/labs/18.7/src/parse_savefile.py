#!/usr/bin/env python3
# Reference parser for the .sav format from make_savefile.py.
# This is the result you should rebuild yourself after reversing the structure from the hex samples.
import struct, sys

def parse(data: bytes) -> dict:
    assert data[:4] == b"SAVE", "wrong magic"
    off = 4
    version, flags, level, gold = struct.unpack_from("<HHII", data, off)
    off += 12
    (name_len,) = struct.unpack_from("<H", data, off); off += 2
    name = data[off:off + name_len].decode(); off += name_len
    (n_items,) = struct.unpack_from("<H", data, off); off += 2
    items = []
    for _ in range(n_items):
        item_id, qty = struct.unpack_from("<HH", data, off); off += 4
        items.append((item_id, qty))
    (checksum,) = struct.unpack_from("<I", data, off); off += 4
    calc = sum(data[:-4]) & 0xFFFFFFFF
    return {
        "version": version, "flags": flags, "level": level, "gold": gold,
        "name": name, "items": items,
        "checksum": checksum, "checksum_ok": checksum == calc,
    }

if __name__ == "__main__":
    for fn in sys.argv[1:]:
        with open(fn, "rb") as f:
            print(fn, "->", parse(f.read()))
