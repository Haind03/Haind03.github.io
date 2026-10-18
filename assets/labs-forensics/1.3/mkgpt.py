#!/usr/bin/env python3
# Dung mot GPT disk image hop le (protective MBR + primary/backup GPT header + entry array).
# CRC32 tinh dung de mmls/gdisk doc duoc. Khong can root.
import struct, zlib, uuid, os, sys
SEC = 512
NENT = 128
ESZ = 128
out = sys.argv[1] if len(sys.argv) > 1 else "gpt.dd"
total_sectors = 43008            # ~21 MiB
# --- partition entries ---
TYPE_EFI   = uuid.UUID("c12a7328-f81f-11d2-ba4b-00a0c93ec93b")  # EFI System
TYPE_LINUX = uuid.UUID("0fc63daf-8483-4772-8e79-3d69d8477de4")  # Linux filesystem
def ent(type_guid, first, last, name):
    b  = type_guid.bytes_le
    b += uuid.uuid4().bytes_le
    b += struct.pack('<QQ', first, last)
    b += struct.pack('<Q', 0)                       # attrs
    nm = name.encode('utf-16-le')[:72].ljust(72, b'\x00')
    b += nm
    assert len(b) == ESZ, len(b)
    return b
entries  = ent(TYPE_EFI,   2048, 10239, "EFI System")
entries += ent(TYPE_LINUX, 10240, 40959, "Linux root")
entries += b'\x00' * (ESZ * NENT - len(entries))
arr_crc = zlib.crc32(entries) & 0xffffffff
# --- primary GPT header (LBA 1) ---
first_usable = 34
last_usable  = total_sectors - 34
disk_guid = uuid.uuid4().bytes_le
def header(cur, bak, arr_lba):
    h  = b'EFI PART'
    h += struct.pack('<III', 0x00010000, 92, 0)     # rev, size, crc(placeholder)
    h += struct.pack('<I', 0)                        # reserved
    h += struct.pack('<QQQQ', cur, bak, first_usable, last_usable)
    h += disk_guid
    h += struct.pack('<QIII', arr_lba, NENT, ESZ, arr_crc)
    h = h.ljust(92, b'\x00')
    crc = zlib.crc32(h) & 0xffffffff
    h = h[:16] + struct.pack('<I', crc) + h[20:]
    return h.ljust(SEC, b'\x00')
backup_lba = total_sectors - 1
prim = header(1, backup_lba, 2)
bak  = header(backup_lba, 1, last_usable + 1)
# --- protective MBR (LBA 0) ---
mbr = bytearray(SEC)
pe  = struct.pack('<B', 0x00) + b'\x00\x02\x00' + struct.pack('<B', 0xEE) + b'\xff\xff\xff'
pe += struct.pack('<II', 1, min(total_sectors - 1, 0xffffffff))
mbr[446:446+16] = pe
mbr[510] = 0x55; mbr[511] = 0xaa
# --- write image ---
with open(out, 'wb') as f:
    f.truncate(total_sectors * SEC)
    f.seek(0);              f.write(mbr)
    f.seek(1 * SEC);        f.write(prim)
    f.seek(2 * SEC);        f.write(entries)
    f.seek(backup_lba*SEC); f.write(bak)
    f.seek((last_usable+1)*SEC); f.write(entries)
print("wrote", out, os.path.getsize(out), "bytes")
