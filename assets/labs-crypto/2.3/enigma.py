#!/usr/bin/env python3
# enigma.py: Enigma gian luoc thuan Python (Bai 2.3, "Bai ba").
# Mo phong 3 rotor + reflector + plugboard, round-trip duoc, va brute 26^3
# tim lai vi tri xuat phat khi de giau mat set_display.
import string

A = string.ascii_uppercase

ROTORS = {
    "I":   ("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q"),
    "II":  ("AJDKSIRUXBLHWTMCQGZNPYFVOE", "E"),
    "III": ("BDFHJLCPRTXVZNYEIWGAKMUSQO", "V"),
}
REFLECTORS = {"B": "YRUHQSLDPXNGOKMIEBFZCWVJAT"}

ENG_FREQ = [8.2, 1.5, 2.8, 4.3, 12.7, 2.2, 2.0, 6.1, 7.0, 0.15, 0.77, 4.0, 2.4,
            6.7, 7.5, 1.9, 0.095, 6.0, 6.3, 9.1, 2.8, 0.98, 2.4, 0.15, 2.0, 0.074]


class Rotor:
    def __init__(self, name, ring, pos):
        wiring, notch = ROTORS[name]
        self.fwd = [ord(c) - 65 for c in wiring]
        self.bwd = [0] * 26
        for i, v in enumerate(self.fwd):
            self.bwd[v] = i
        self.notch = ord(notch) - 65
        self.ring = ring - 1
        self.pos = ord(pos) - 65

    def at_notch(self):
        return self.pos == self.notch

    def turn(self):
        self.pos = (self.pos + 1) % 26

    def encode(self, c, table):
        off = (self.pos - self.ring) % 26
        return (table[(c + off) % 26] - off) % 26


class Enigma:
    def __init__(self, rotors, reflector, rings, positions, plugboard=""):
        self.rotors = [Rotor(n, r, p) for n, r, p in zip(rotors, rings, positions)]
        self.reflector = [ord(c) - 65 for c in REFLECTORS[reflector]]
        self.plug = {c: c for c in A}
        for pair in plugboard.split():
            a, b = pair
            self.plug[a], self.plug[b] = b, a

    def _step(self):
        right, middle, left = self.rotors[2], self.rotors[1], self.rotors[0]
        if middle.at_notch():
            middle.turn()
            left.turn()
        elif right.at_notch():
            middle.turn()
        right.turn()

    def encode_char(self, ch):
        if ch not in A:
            return ch
        self._step()
        c = ord(self.plug[ch]) - 65
        for rotor in reversed(self.rotors):
            c = rotor.encode(c, rotor.fwd)
        c = self.reflector[c]
        for rotor in self.rotors:
            c = rotor.encode(c, rotor.bwd)
        return self.plug[A[c]]

    def process(self, text):
        return "".join(self.encode_char(ch) for ch in text.upper())


ROTOR_ORDER = ["I", "II", "III"]
REFLECTOR = "B"
RINGS = [1, 1, 1]
PLUG = "AV BS CG DL FU HZ IN KM OW RX"


def machine(positions):
    return Enigma(ROTOR_ORDER, REFLECTOR, RINGS, positions, PLUG)


def chi(text):
    L = [c for c in text if c in A]
    n = len(L)
    s = 0.0
    for i, ch in enumerate(A):
        o = L.count(ch)
        e = ENG_FREQ[i] / 100 * n
        if e > 0:
            s += (o - e) ** 2 / e
    return s


def main():
    plaintext = "THEENIGMAMACHINEWASBROKENATBLETCHLEYPARKBYEXPLOITINGCRIBS"
    start = "WXC"
    ct = machine(start).process(plaintext)
    print("plaintext :", plaintext)
    print("ciphertext:", ct)
    print("giai lai  :", machine(start).process(ct))
    print("khong chu nao map ve chinh no:",
          all(p != c for p, c in zip(plaintext, ct)))

    # Brute 26^3 tim lai vi tri xuat phat, cham diem bang chi-squared tieng Anh
    best = None
    for a in A:
        for b in A:
            for c in A:
                dec = machine(a + b + c).process(ct)
                sc = chi(dec)
                if best is None or sc < best[0]:
                    best = (sc, a + b + c, dec)
    print("--- brute 26^3 ---")
    print("vi tri tim lai:", best[1])
    print("ban ro        :", best[2])


if __name__ == "__main__":
    main()
