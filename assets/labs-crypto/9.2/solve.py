#!/usr/bin/env python3
# solve.py: khoi phuc trang thai MT19937 tu 624 output roi du doan, va pha LCG.
# Tu chua, chi dung stdlib (random, math).
#
# Phan A: MT19937
#   Python random dung MT19937. Moi output 32-bit la trang thai noi bo da di qua
#   ham "temper" (kha nghich). Dao temper (untemper) cho 624 output lien tiep la
#   dung lai toan bo trang thai -> clone PRNG -> du doan moi so ke tiep.
#
# Phan B: LCG  X_{n+1} = (a*X_n + c) mod m
#   Chi can mot day output lien tiep, khoi phuc m, roi a, roi c, khong biet gi
#   truoc ve tham so.
#
# Chay:  python3 solve.py
import random
from math import gcd
from functools import reduce


# =========================== PHAN A: MT19937 ===============================
def _undo_rshift(y, shift):
    # dao phep: y = y ^ (y >> shift)
    r = y
    for _ in range(32 // shift + 1):
        r = y ^ (r >> shift)
    return r & 0xFFFFFFFF


def _undo_lshift(y, shift, mask):
    # dao phep: y = y ^ ((y << shift) & mask)
    r = y
    for _ in range(32 // shift + 1):
        r = y ^ ((r << shift) & mask)
    return r & 0xFFFFFFFF


def untemper(y):
    # dao 4 buoc temper cua MT19937, theo dung thu tu nguoc
    y = _undo_rshift(y, 18)
    y = _undo_lshift(y, 15, 0xEFC60000)
    y = _undo_lshift(y, 7, 0x9D2C5680)
    y = _undo_rshift(y, 11)
    return y


def clone_mt(outputs624):
    # dung lai trang thai tu dung 624 output 32-bit lien tiep
    state = tuple(untemper(o) for o in outputs624)
    clone = random.Random()
    # state Python = (version=3, (624 word trang thai) + (index=624), None)
    clone.setstate((3, state + (624,), None))
    return clone


def demo_mt():
    print("=== PHAN A: MT19937 ===")
    victim = random.Random()               # seed he thong, ke tan cong khong biet
    outputs = [victim.getrandbits(32) for _ in range(624)]
    print("[*] da quan sat 624 output 32-bit tu PRNG nan nhan")

    clone = clone_mt(outputs)
    predicted = [clone.getrandbits(32) for _ in range(6)]
    actual = [victim.getrandbits(32) for _ in range(6)]
    print("[*] du doan 6 so ke tiep:", predicted)
    print("[*] PRNG that sinh ra   :", actual)
    print("[*] khop?", predicted == actual)
    assert predicted == actual
    print("[+] clone MT19937 thanh cong, du doan dung so tuong lai")


# ============================= PHAN B: LCG =================================
def lcg_stream(seed, a, c, m, n):
    x = seed
    out = []
    for _ in range(n):
        x = (a * x + c) % m
        out.append(x)
    return out


def recover_lcg(seq):
    # buoc 1: tim m qua gcd cua cac "boi so cua m"
    #   t_i = s_{i+1} - s_i  thi  t_{i+1}*t_{i-1} - t_i^2  chia het cho m
    diffs = [seq[i + 1] - seq[i] for i in range(len(seq) - 1)]
    multiples = [diffs[i + 2] * diffs[i] - diffs[i + 1] ** 2
                 for i in range(len(diffs) - 2)]
    m = reduce(gcd, [abs(x) for x in multiples])
    # buoc 2: a = (s2 - s1) * inv(s1 - s0) mod m
    a = ((seq[2] - seq[1]) * pow(seq[1] - seq[0], -1, m)) % m
    # buoc 3: c = (s1 - a*s0) mod m
    c = (seq[1] - a * seq[0]) % m
    return a, c, m


def demo_lcg():
    print()
    print("=== PHAN B: LCG ===")
    # tham so bi an (kieu glibc rand), ke tan cong khong biet
    A, C, M, SEED = 1103515245, 12345, 2 ** 31, 987654321
    seq = lcg_stream(SEED, A, C, M, 12)
    print("[*] chi co day output:", seq)

    a, c, m = recover_lcg(seq)
    print("[*] khoi phuc m =", m, "| that =", M, "| dung?", m == M)
    print("[*] khoi phuc a =", a, "| that =", A, "| dung?", a == A)
    print("[*] khoi phuc c =", c, "| that =", C, "| dung?", c == C)

    # du doan so ke tiep
    nxt = (a * seq[-1] + c) % m
    truth = lcg_stream(SEED, A, C, M, 13)[-1]
    print("[*] du doan so ke tiep =", nxt, "| that =", truth, "| khop?", nxt == truth)
    assert (a, c, m) == (A, C, M) and nxt == truth
    print("[+] pha LCG thanh cong, khoi phuc het tham so va du doan dung")


if __name__ == "__main__":
    demo_mt()
    demo_lcg()
