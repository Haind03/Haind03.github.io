#!/usr/bin/env python3
# Emulates a string-decryption XOR routine with Unicorn, without running the whole program.
# x86-64 shellcode (System V): rdi = buffer pointer, rsi = length, key = 0x5A
#   loop: xor byte [rdi], 0x5A ; inc rdi ; dec rsi ; jnz loop ; ret
from unicorn import *
from unicorn.x86_const import *

# Machine code for the decryption loop (preassembled):
#   80 37 5A          xor byte ptr [rdi], 0x5A
#   48 ff c7          inc rdi
#   48 ff ce          dec rsi
#   75 f5             jnz -11 (back to the top of the loop)
#   c3                ret
CODE = bytes.fromhex("8037 5A 48ffc7 48ffce 75f5 c3".replace(" ", ""))

BASE = 0x1000000      # address where the code is loaded
DATA = 0x2000000      # address of the data buffer
STACK = 0x3000000

# Encrypted data: the original string XORed with 0x5A
plain = b"emulation_wins!"
enc = bytes(c ^ 0x5A for c in plain)

mu = Uc(UC_ARCH_X86, UC_MODE_64)
mu.mem_map(BASE, 0x1000)
mu.mem_map(DATA, 0x1000)
mu.mem_map(STACK, 0x1000)

mu.mem_write(BASE, CODE)
mu.mem_write(DATA, enc)

mu.reg_write(UC_X86_REG_RDI, DATA)        # buffer pointer
mu.reg_write(UC_X86_REG_RSI, len(enc))    # length
mu.reg_write(UC_X86_REG_RSP, STACK + 0x800)
# place a return address on the stack so the ret instruction stops here
mu.mem_write(STACK + 0x800, (BASE + len(CODE)).to_bytes(8, "little"))

print("Input (encrypted):", enc.hex())
mu.emu_start(BASE, BASE + len(CODE))      # run to the end of the code
out = mu.mem_read(DATA, len(enc))
print("Output (decrypted):", bytes(out).decode())
