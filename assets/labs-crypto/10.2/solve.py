#!/usr/bin/env python3
# solve.py: dung Z3 khoi phuc seed cua custom xorshift32 PRNG tu known-plaintext,
# roi giai ma toan bo ciphertext de lay flag.
from z3 import BitVec, BitVecVal, LShR, Solver, sat

MASK = 0xFFFFFFFF

# --- Ban cai dat "that" cua PRNG, dung de tai tao keystream sau khi co seed ---
def xorshift32(x):
    x ^= (x << 13) & MASK
    x ^= (x >> 17)
    x ^= (x << 5) & MASK
    return x & MASK

def decrypt(ct, seed):
    state = seed
    out = bytearray()
    for b in ct:
        state = xorshift32(state)
        ks = (state >> 24) & 0xFF
        out.append(b ^ ks)
    return bytes(out)

# --- Phien ban symbolic cua mot buoc xorshift, viet bang bieu thuc Z3 ---
def xorshift32_sym(x):
    x = x ^ (x << 13)
    x = x ^ LShR(x, 17)   # LShR: dich phai KHONG dau, dung cho so hoc bit
    x = x ^ (x << 5)
    return x

def recover_seed(ct, known_prefix):
    s = Solver()
    seed = BitVec("seed", 32)
    state = seed
    # Moi byte plaintext da biet cho ta mot byte keystream da biet:
    # ks_i = pt_i XOR ct_i. Rang buoc tung byte high cua state qua tung buoc.
    for i, pt_byte in enumerate(known_prefix):
        state = xorshift32_sym(state)
        ks = pt_byte ^ ct[i]
        s.add(LShR(state, 24) == BitVecVal(ks, 32))
    assert s.check() == sat, "khong tim ra seed, kiem lai mo hinh"
    model = s.model()
    return model[seed].as_long()

if __name__ == "__main__":
    ct = bytes.fromhex(open("ct.hex").read().strip())
    known = b"flag{"          # chi can biet 5 byte dau cua flag
    seed = recover_seed(ct, known)
    print("seed tim duoc :", hex(seed))
    flag = decrypt(ct, seed)
    print("flag          :", flag.decode())
