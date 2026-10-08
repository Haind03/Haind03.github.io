#!/usr/bin/env python3
# c03_single_xor.py: Cryptopals set 1 challenge 3 - single-byte XOR cipher
ENG = {'a':.082,'b':.015,'c':.028,'d':.043,'e':.127,'f':.022,'g':.020,'h':.061,
       'i':.070,'j':.0015,'k':.0077,'l':.040,'m':.024,'n':.067,'o':.075,'p':.019,
       'q':.0010,'r':.060,'s':.063,'t':.091,'u':.028,'v':.0098,'w':.024,'x':.0015,
       'y':.020,'z':.00074,' ':.18}

def score(b):
    return sum(ENG.get(chr(c).lower(), -0.05) for c in b)

ct = bytes.fromhex("1b37373331363f78151b7f2b783431333d78397828372d363c78373e783a393b3736")
best = max(((k, bytes(c ^ k for c in ct)) for k in range(256)), key=lambda kv: score(kv[1]))
print("khoa (byte) :", best[0], hex(best[0]))
print("plaintext   :", best[1].decode())
