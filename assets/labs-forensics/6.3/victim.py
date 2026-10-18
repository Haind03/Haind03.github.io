#!/usr/bin/env python3
# victim.py - lab 6.3: tien trinh co mot vung nho RWX bat thuong (vo hai).
#
# Mo phong dau hieu cua code injection: cap mot vung anonymous RWX (vua ghi vua chay)
# va dat vao do "shellcode gia". KHONG BAO GIO thuc thi no - chi la bytes vo hai de
# ta quet lai (giong malfind tim vung RWX + header MZ). Khong co hanh vi doc hai nao.
import ctypes
import ctypes.util
import os
import time

# Byte gia: header MZ (4d 5a) + vai NOP (0x90) + chuoi marker + padding.
# Day KHONG phai shellcode that; khong co lenh nao chay no.
FAKE = (
    b"\x4d\x5a"                         # "MZ" - header PE gia
    b"\x90\x90\x90\x90\x90\x90"         # NOP sled gia
    b"FAKE_SHELLCODE_NOT_EXECUTED_LAB63\x00"
    b"\xcc" * 16                        # int3 gia cho co ve "code"
)

libc = ctypes.CDLL(ctypes.util.find_library("c") or "libc.so.6", use_errno=True)
libc.mmap.restype = ctypes.c_void_p
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int,
                      ctypes.c_int, ctypes.c_int, ctypes.c_long]

PROT_READ, PROT_WRITE, PROT_EXEC = 1, 2, 4
MAP_PRIVATE, MAP_ANONYMOUS = 0x02, 0x20
SIZE = 4096

addr = libc.mmap(None, SIZE, PROT_READ | PROT_WRITE | PROT_EXEC,
                 MAP_PRIVATE | MAP_ANONYMOUS, -1, 0)
if addr in (None, ctypes.c_void_p(-1).value, -1):
    raise OSError(ctypes.get_errno(), "mmap RWX that bai")

# Ghi fake "shellcode" vao vung RWX (chi ghi du lieu, khong goi toi no).
ctypes.memmove(addr, FAKE, len(FAKE))

print(os.getpid(), flush=True)
print(f"RWX region at {addr:#x} size {SIZE}", flush=True)
print("READY", flush=True)

deadline = time.time() + 120
while time.time() < deadline:
    time.sleep(0.2)
# Giu tham chieu, khong bao gio nhay vao addr.
_ = addr
