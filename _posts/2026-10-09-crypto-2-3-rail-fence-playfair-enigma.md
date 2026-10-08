---
title: "Lesson 2.3: Rail Fence, Playfair, and Enigma"
image:
  path: /assets/img/covers/crypto-2-3-rail-fence-playfair-enigma.webp
  alt: "Rail Fence, Playfair, and Enigma"
date: 2026-10-09 10:15:00 +0700
categories: ["Cryptography", "Crypto · Classical Ciphers"]
tags: [cryptography, classical-ciphers, rail-fence, playfair, enigma]
render_with_liquid: false
---

Three names show up in CTF challenges besides the simple substitution family: rail fence (a pure transposition cipher), Playfair (a cipher that works on pairs of letters), and Enigma (the German electromechanical cipher machine). After this lesson you can code rail fence and Playfair, you understand how Enigma works, and you have a procedure for recognizing them when they appear in a challenge.

![Three classical ciphers compared by what they change and how to break them](/assets/img/crypto/crypto-2-3-rail-fence-playfair-enigma.svg)
_Rail fence moves letters, Playfair substitutes pairs, Enigma changes its substitution after every key press._

Level: medium, about 40 minutes. Prerequisite: Lesson 2.2 (frequency analysis, IoC). Rail fence and Playfair stand on their own, but the IoC-based recognition needs the previous lesson. Tools: Python 3 with the standard library only. The Enigma part uses a self-contained pure Python simulation included below. For full historical accuracy, see the "Enigma" operation in CyberChef.

## Goals

You will be able to tell a transposition cipher (letters change position) from a substitution cipher (letters change identity), and to know what the IoC reveals. You will code rail fence encode/decode and brute-force the number of rails. You will understand the Playfair rules (digraphs, three cases) and decrypt it yourself. You will know the Enigma mechanism well enough to explain why it was strong and what its fatal weakness was. You will also have a checklist for recognizing a classical cipher in an unfamiliar challenge.

## Theory

### Two big branches of classical ciphers

Recall the important boundary:

- Substitution changes the identity of each letter and keeps its position. Caesar, Vigenere, and Playfair belong here.
- Transposition keeps the identity of each letter and only shuffles the positions. Rail fence belongs here.

This distinction is useful right away. Transposition changes no letter, so the letter frequencies and the IoC of the ciphertext are identical to the plaintext (an IoC of about 0.066 for English). If a ciphertext has a normal letter distribution (many E, T, A), a high IoC, and still reads as nonsense, it is almost certainly a transposition. In that case do not look for a substitution key. Look for a way to rearrange the letters.

### Rail fence

Rail fence writes the plaintext in a zigzag over a number of rows (rails), then reads each row from left to right to produce the ciphertext. For example `WEAREDISCOVERED` with 3 rails:

```
W . . . E . . . C . . . R . . .
. E . R . D . S . O . E . E . D
. . A . . . I . . . V . . . ...
```

Read row 1, then row 2, then row 3, and join them into the ciphertext. The only key is the number of rails. One variant adds an offset (starting partway through the zigzag).

Rail fence is very easy to break because the key space is tiny. The number of rails runs from 2 up to about the length of the text. Try them all and see which one reads correctly. The recognition signs are that the ciphertext is a reordering of the plaintext letters (the same letter set), the IoC is as high as for normal text, and the letters are out of order.

### Playfair

Playfair encrypts digraphs (pairs of letters) instead of single letters. It uses a 5x5 square holding 25 letters (I and J merged, or Q dropped, depending on the convention). The square is shuffled by a keyword: write the keyword first (skipping repeated letters), then fill in the remaining letters in alphabet order.

Encryption rules for each pair (a, b):

1. If the two letters are equal, insert a filler letter (usually X) between them and split again into pairs. If the plaintext has an odd length, append X at the end.
2. Same row: replace each letter with the letter to its right in the row (wrapping to the start of the row).
3. Same column: replace each letter with the letter below it in the column (wrapping to the top of the column).
4. Different row and column: the two letters form a rectangle. Replace each letter with the letter in its own row but in the column of the other letter (swap the corners).

Decryption reverses this: same row takes the letter on the left, same column takes the letter above, and the rectangle case still swaps corners (this operation is its own inverse).

You can recognize Playfair because the ciphertext always has an even number of characters, it contains only 25 letters (usually J or Q is missing), it never has two identical letters side by side (because of the filler rule), and it often has X in odd places (from the filler). Single-letter frequency analysis does not work. You need bigram frequency analysis.

### Enigma, simplified

Enigma is the German electromechanical cipher machine used in World War II. It is a polyalphabetic substitution cipher whose alphabet changes after every key press, which made it much stronger than Vigenere. The main parts:

- Plugboard (Steckerbrett): swaps some pairs of letters before and after the signal passes through the rotors. It contributes most of the key space.
- Rotors: each rotor is a fixed permutation of the 26 letters. The machine usually has 3 or 4 rotors in a row, chosen from a set of available rotors, and each rotor has its own starting setting (ring setting and start position).
- Reflector (Umkehrwalze): sits at the end and sends the signal back through the rotors a second time.

The signal path for one key press: current goes through the plugboard, forward through the three rotors, hits the reflector, goes back through the three rotors, passes the plugboard again, and lights the result lamp. The key point is that after every key press at least one rotor steps (like an odometer), so the substitution alphabet keeps changing. Typing the letter E three times in a row can give three different letters.

Two properties shape how Enigma was attacked:

1. Enigma is self-inverse (because of the reflector). With the same configuration, typing the plaintext gives the ciphertext, and typing the ciphertext gives the plaintext again. This is convenient for the operator, but it is also a structural constraint.
2. The reflector means no letter is ever encrypted to itself: E never becomes E. This is the gap that Bletchley Park (the group around Alan Turing) exploited. They guessed a likely piece of plaintext (a crib, for example weather reports often began with "WETTER") and aligned it along the ciphertext. Any position where a crib letter equals the ciphertext letter under it is impossible and is eliminated. The bombe machine automated the testing of rotor settings based on logical loops derived from the crib.

In CTFs today you rarely need to break Enigma from scratch. Usually the challenge gives the configuration (rotor types, order, ring settings, plugboard) and you only simulate it to decrypt. Or one small parameter is missing (for example only the start position of 3 rotors, which is 26^3 = 17576 possibilities) and you brute-force that part and score the result by letter frequency.

### Three questions to answer

1. What does correct use look like: rail fence keeps the letters and only shuffles positions; Playfair encrypts in pairs; Enigma changes its alphabet after every key press.
2. Where does it fail: a small key space (rail fence), bigram leakage (Playfair), the "no letter maps to itself" constraint plus reused daily keys (Enigma).
3. How is it exploited: brute-force the number of rails; bigram analysis or key search for Playfair; simulate and brute-force the missing configuration for Enigma.

## Demo

### Rail fence: encode, decode, brute-force

```python
# railfence.py: encode, decode and brute-force rail fence
def rail_encode(text, rails):
    if rails < 2:
        return text
    rows = [[] for _ in range(rails)]
    r, step = 0, 1                       # r: current row, step: direction (down +1, up -1)
    for ch in text:
        rows[r].append(ch)
        if r == 0:
            step = 1
        elif r == rails - 1:
            step = -1
        r += step
    return "".join("".join(row) for row in rows)

def rail_decode(cipher, rails):
    if rails < 2:
        return cipher
    # Step 1: work out which row each position belongs to (walk the zigzag again)
    pattern = []
    r, step = 0, 1
    for _ in range(len(cipher)):
        pattern.append(r)
        if r == 0:
            step = 1
        elif r == rails - 1:
            step = -1
        r += step
    # Step 2: count how many letters each row needs, cut the cipher into rows
    counts = [pattern.count(i) for i in range(rails)]
    rows, idx = [], 0
    for c in counts:
        rows.append(list(cipher[idx:idx + c]))
        idx += c
    # Step 3: read in zigzag order, taking letters from each row in turn
    pos = [0] * rails
    out = []
    for r in pattern:
        out.append(rows[r][pos[r]])
        pos[r] += 1
    return "".join(out)

msg = "WEAREDISCOVEREDFLEEATONCE"
ct = rail_encode(msg, 3)
print("Encode 3 rail:", ct)
print("Decode again :", rail_decode(ct, 3))

# Brute-force when the number of rails is unknown: try 2 up to len/2, print everything for a human to pick
print("--- brute-force the number of rails ---")
for rails in range(2, 8):
    print(rails, ":", rail_decode(ct, rails))
```

Output:

```
Encode 3 rail: WECRLTEERDSOEEFEAOCAIVDEN
Decode again : WEAREDISCOVEREDFLEEATONCE
--- brute-force the number of rails ---
2 : WEEFCERALOTCEAEIRVDDSEONE
3 : WEAREDISCOVEREDFLEEATONCE   <- readable, correct
4 : WTEVFEEEEDARCDOECSROANIEL
5 : WLSADOOTEEECEAEECRFINVEDR
6 : WRRECEAFDLETSEINVAOECEEOD
7 : WREOEAEIAERLETDEOVNDCFSEC
```

With rail fence you only need to print a few rail values and let a human eye (or an English scoring function such as the chi-squared score from Lesson 2.2) pick the readable one. The key space is small enough to always search fully.

### Playfair: build the square and decrypt

```python
# playfair.py: build the 5x5 square from a keyword and decrypt
def build_square(key):
    key = key.upper().replace("J", "I")
    seen, square = [], []
    for ch in key + "ABCDEFGHIKLMNOPQRSTUVWXYZ":   # alphabet without J (I=J)
        if ch.isalpha() and ch not in seen:
            seen.append(ch)
            square.append(ch)
    # return a dict: letter -> (row, column) for fast lookup
    pos = {square[i]: (i // 5, i % 5) for i in range(25)}
    return square, pos

def playfair_decrypt(cipher, key):
    square, pos = build_square(key)
    cipher = cipher.upper().replace("J", "I")
    cipher = "".join(c for c in cipher if c.isalpha())
    out = []
    for i in range(0, len(cipher), 2):
        a, b = cipher[i], cipher[i + 1]
        ra, ca = pos[a]
        rb, cb = pos[b]
        if ra == rb:                       # same row: take the letter on the LEFT
            out.append(square[ra * 5 + (ca - 1) % 5])
            out.append(square[rb * 5 + (cb - 1) % 5])
        elif ca == cb:                     # same column: take the letter ABOVE
            out.append(square[((ra - 1) % 5) * 5 + ca])
            out.append(square[((rb - 1) % 5) * 5 + cb])
        else:                              # rectangle: swap the corners
            out.append(square[ra * 5 + cb])
            out.append(square[rb * 5 + ca])
    return "".join(out)

# The ciphertext below is encrypted with the key "MONARCHY" (a classic Playfair example)
ct = "BFCKPDFIMPBKRQCFZDIUILLZOL"
print("Playfair decrypted:", playfair_decrypt(ct, "MONARCHY"))
```

Output:

```
Playfair decrypted: HIDETHEGOLDINTHETREXESTUMP
```

The original plaintext is `HIDE THE GOLD IN THE TREE STUMP`. Notice the X between `TRE` and `ES`. It is the Playfair filler, added automatically when a pair has two equal letters (the two E in TREES). After decrypting you remove it when reading. Remember that Playfair decryption reverses the first two rules (right becomes left, below becomes above), while the rectangle rule stays the same because it is its own inverse. When the key is unknown, Playfair is attacked with hill climbing: start from a random square, swap a few cells, score with English bigram frequencies, keep the changes that improve the score, and repeat many times.

### Enigma: a hand-written simulation

Enigma is hard to code with full accuracy because of the double-stepping of the rotors (the middle rotor sometimes steps twice in a row). A self-contained simplified version is still enough to show the mechanism and the weakness. Below is a three-rotor Enigma in pure Python, with no external library, that runs with `python3 -I`:

```python
# enigma_demo.py: simplified Enigma, pure Python, self-contained (no external library)
# Simulates 3 rotors + reflector + plugboard. Enough to see the mechanism and the weakness.
import string

A = string.ascii_uppercase

# Historical wiring of rotors I, II, III and reflector B, plus the notch positions
ROTORS = {
    "I":   ("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q"),
    "II":  ("AJDKSIRUXBLHWTMCQGZNPYFVOE", "E"),
    "III": ("BDFHJLCPRTXVZNYEIWGAKMUSQO", "V"),
}
REFLECTORS = {"B": "YRUHQSLDPXNGOKMIEBFZCWVJAT"}

class Rotor:
    def __init__(self, name, ring, pos):
        wiring, notch = ROTORS[name]
        self.fwd = [ord(c) - 65 for c in wiring]
        self.bwd = [0] * 26
        for i, v in enumerate(self.fwd):
            self.bwd[v] = i
        self.notch = ord(notch) - 65
        self.ring = ring - 1            # ring setting 1..26 -> 0..25
        self.pos = ord(pos) - 65        # current position 0..25

    def at_notch(self):
        return self.pos == self.notch

    def turn(self):
        self.pos = (self.pos + 1) % 26

    def encode(self, c, table):
        off = (self.pos - self.ring) % 26
        return (table[(c + off) % 26] - off) % 26

class Enigma:
    def __init__(self, rotors, reflector, rings, positions, plugboard=""):
        # rotors: list of names from LEFT to RIGHT, the last one is the fast rotor
        self.rotors = [Rotor(n, r, p) for n, r, p in zip(rotors, rings, positions)]
        self.reflector = [ord(c) - 65 for c in REFLECTORS[reflector]]
        self.plug = {c: c for c in A}
        for pair in plugboard.split():
            a, b = pair
            self.plug[a], self.plug[b] = b, a

    def _step(self):
        right, middle, left = self.rotors[2], self.rotors[1], self.rotors[0]
        if middle.at_notch():           # double-stepping of the middle rotor
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
        for rotor in reversed(self.rotors):     # right -> left (forward direction)
            c = rotor.encode(c, rotor.fwd)
        c = self.reflector[c]                    # hit the reflector
        for rotor in self.rotors:               # left -> right (return direction)
            c = rotor.encode(c, rotor.bwd)
        return self.plug[A[c]]

    def process(self, text):
        return "".join(self.encode_char(ch) for ch in text.upper())

def make():
    return Enigma(["I", "II", "III"], "B", [1, 1, 1], "WXC",
                  "AV BS CG DL FU HZ IN KM OW RX")

plaintext = "HELLOWORLD"
ct = make().process(plaintext)
print("Enigma out:", ct)
# Enigma is self-inverse: reset to the same configuration and feed in the ciphertext to get the plaintext
print("Decrypted :", make().process(ct))
# Historical weakness: no letter is encrypted to itself (thanks to the reflector)
print("No letter maps to itself:",
      all(p != c for p, c in zip(plaintext, ct)))
```

Output:

```
Enigma out: TJMSWAMMDZ
Decrypted : HELLOWORLD
No letter maps to itself: True
```

The last line shows the historical weakness. Thanks to the reflector, no letter is encrypted to itself (E never becomes E), and the machine is self-inverse, so typing the ciphertext with the same configuration gives the plaintext again. For full historical accuracy (all rotor types, ring settings, correct double-stepping), use the "Enigma" operation in CyberChef or the `py-enigma` library. To understand the principle, the code above is enough.

When the challenge is missing the start positions, wrap the decryption in three nested loops of 26 x 26 x 26. Build an `Enigma` for each `positions` combination, decrypt, score with English chi-squared, and keep the combination with the best plaintext. 17576 possibilities run in an instant (see the Lab section below).

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 2.3</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/2.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/2.3/enigma.py" download><i class="fa-solid fa-file-code"></i>enigma.py</a>
<a class="lab-file" href="/assets/labs-crypto/2.3/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>

- Task: the ciphertext is `WECRLTEERDSOEEFEAOCAIVDEN`. It is a transposition cipher. Recover the plaintext.
- Hint 1: compute the IoC. If it is as high as for normal text, this is a transposition, not a substitution. Do not look for a Caesar key.
- Hint 2: try rail fence first because it is the most common. Use `rail_decode` from the demo and loop the number of rails from 2 to 7.
- Hint 3: the plaintext is an English sentence in capitals with no spaces.
- Done when: you can read the original English sentence.
- The reference material includes `solve.py` (solves rail fence, scores by bigram) and `enigma.py` (pure Python Enigma for exercise three, with a brute force over 26^3 start positions), plus `transcript.txt` with the real output.

For exercise two, do Playfair by yourself. Pick a key (for example `CRYPTO`), encrypt a short sentence by inverting the `playfair_decrypt` function (write a `playfair_encrypt`), and give the ciphertext to a friend to solve. When the key is unknown, try implementing a hill climbing loop scored by bigram frequency.

For exercise three, brute-force the Enigma start positions. Take the ciphertext from the Enigma demo (rotors I II III, reflector B, the plugboard above) but pretend you forgot the start positions. Write a 26^3 loop that finds the start positions that give readable plaintext.

## Key takeaways

- Transposition keeps the letters and only shuffles the positions, so the IoC and frequencies stay the same as the plaintext.
- The rail fence key is only the number of rails, so it can always be brute-forced.
- Playfair works on pairs, the ciphertext has an even length and lacks one letter (J or Q), and you attack it with bigram analysis, not single letters.
- Enigma changes its alphabet on every key press, is self-inverse, and never maps a letter to itself. That is the historical gap.
- In CTFs you usually only simulate Enigma or brute-force the missing configuration, not break it from zero.

## Common pitfalls

- Seeing a ciphertext of only letters that reads as nonsense and assuming it is a strong cipher. Compute the IoC first. If it is high, it is only a transposition, so rearrange the positions.
- Decoding rail fence wrongly by miscounting letters per row. Build the exact zigzag pattern first and then cut, do not divide evenly.
- Forgetting to merge I with J in Playfair (or forgetting to drop Q, depending on the convention). The square has 25 cells, so exactly one letter is always missing. Match the convention of the challenge.
- Forgetting the filler rule when two letters in a pair are equal, which shifts all the following pairs.
- Writing your own Enigma and forgetting double-stepping. With this detail wrong, only the first few dozen letters are correct and then the output drifts. Prefer a tested library.
- Brute-forcing Enigma and forgetting that the reflector rules out "a letter encrypted to itself". Use this constraint to cut the search space instead of searching blindly.

## Further reading

- The Code Book (Simon Singh): the chapter on Enigma and Bletchley Park, including cribs and the bombe, is easy to follow.
- Visual Enigma simulators (online rotor simulators) to see the signal path.
- The CyberChef documentation for the "Enigma" and "Rail Fence" operations.
- The `py-enigma` library on PyPI: read the README to see how rotors and plugboard are declared.
- The classical challenges on CryptoHack and dcode.fr (which has ready solvers for rail fence and Playfair) to compare your results.
- Continue with Lesson 3.1 to move to XOR, where the key starts to play a real role and the attacks become more programmatic.
