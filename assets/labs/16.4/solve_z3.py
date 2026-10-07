# Solves crackme 16.4 with Z3. The constants A, C, xor, and sum are all read from the binary.
from z3 import *

A = [3,5,7,3,5,7,3,5,7,3,5]
C = [65,94,235,107,181,39,12,158,235,59,122]
N = 12

f = [BitVec(f'f{i}', 8) for i in range(N)]
s = Solver()
for c in f:
    s.add(c >= 0x20, c <= 0x7e)              # printable
for i in range(N-1):
    s.add((A[i]*f[i] + f[i+1]) & 0xff == C[i])  # chain
s.add(f[0] ^ f[11] == 0x7b)                  # cross xor 1
s.add(f[2] ^ f[5] == 0x33)                   # cross xor 2
s.add(Sum([ZeroExt(24, c) for c in f]) == 988)  # sum

assert s.check() == sat
m = s.model()
flag = bytes(m[c].as_long() for c in f)
print("FLAG:", flag.decode())
