---
title: "Lesson 2.2: Caesar, Vigenere and Frequency Analysis"
image:
  path: /assets/img/covers/crypto-2-2-caesar-vigenere-frequency-analysis.webp
  alt: "Caesar, Vigenere and Frequency Analysis"
date: 2023-03-20 09:12:00 +0700
categories: ["Cryptography", "Crypto · Classical Ciphers"]
tags: [cryptography, classical-ciphers, vigenere, frequency-analysis]
render_with_liquid: false
---

This lesson takes apart the classical substitution ciphers: Caesar, ROT13, Vigenere and general substitution. It then uses letter frequency analysis and the index of coincidence to break them without knowing the key. After it you can break a Vigenere text from the ciphertext alone.

![Breaking Vigenere: find the key length with IoC, then solve each column as Caesar](/assets/img/crypto/crypto-2-2-caesar-vigenere-frequency-analysis.svg)
_Split the ciphertext into m columns, pick the m with high IoC, and solve every column as a Caesar shift._

Part: 2 (Encoding and classical ciphers) | Time: about 40 minutes | Difficulty: medium

**Prerequisites:** Lesson 2.1 (so you do not confuse encoding with a cipher). Modular arithmetic at the level of add, subtract and remainder is enough.

**Tools:** Python 3 (standard library), optionally CyberChef for quick checks.

## Goals

By the end of this lesson you understand that Caesar, ROT, Vigenere and substitution are one family and where they are weak. You can break Caesar by brute-forcing 25 shifts and scoring with letter frequency. You can measure the index of coincidence (IoC) to tell a simple shift cipher from a polyalphabetic one. You can find the Vigenere key length with IoC and then recover each key character with frequency analysis.

## 1. Theory

### One family: replace letters with letters

Caesar, ROT13, Vigenere and substitution are all substitution ciphers. Each plaintext letter is replaced by another letter according to a rule. They differ only in how simple or complex the rule is. The shared weakness is that none of them hides the letter frequencies well enough, so the statistics of the language still leak.

### Caesar: shift the whole alphabet by k

Caesar replaces each letter with the letter k positions later in the alphabet, wrapping around. With k = 3, A becomes D, B becomes E, ..., X becomes A. The formula, with A=0 to Z=25:

```
c = (p + k) mod 26        # encrypt
p = (c - k) mod 26        # decrypt
```

ROT13 is just Caesar with k = 13. It is special because 13 + 13 = 26, so ROT13 applied twice gives the original back. Encryption and decryption use the same operation. ROT13 is not for security. It is used to hide spoilers on forums.

Caesar has only 25 nonzero keys. You break it by trying all 25 shifts and looking for the one that gives readable text. The key space is far too small to call secure.

### General substitution: permute the whole alphabet

Instead of a plain shift, a substitution cipher maps each letter to any other letter, as long as the mapping is a permutation (a bijection) of the 26 letters. The key space is 26 factorial, about 4 times 10^26, so brute force is hopeless.

But substitution still breaks easily, because it is monoalphabetic and a plaintext letter always becomes exactly one ciphertext letter. Letter frequencies are preserved and only relabeled. In English, E is the most common letter, so the most common letter in the ciphertext is very likely E. Add analysis of letter pairs (bigrams such as TH, HE) and short words (a, the, of), and the mapping is recovered step by step. It is a puzzle-solving task, not a math problem.

### Vigenere: several Caesar shifts in turn

Vigenere is polyalphabetic. It uses a keyword, and each letter of the key defines its own Caesar shift. These shifts are applied in turn to the plaintext, and the key repeats. With the key `KEY` (K=10, E=4, Y=24):

```
letter 1 of the plaintext shifts by 10
letter 2 shifts by 4
letter 3 shifts by 24
letter 4 shifts by 10 again
...
```

The formula, with key length m:

```
c_i = (p_i + k_(i mod m)) mod 26
```

Because one plaintext letter can now become several different ciphertext letters (depending on which key character it lands on), the frequencies get flattened. For a few hundred years Vigenere was called "le chiffre indechiffrable" (the indecipherable cipher). Then people noticed one thing. If you know the key length m, you can split the ciphertext into m groups, each encrypted with the same Caesar shift, and Caesar is easy to break. So breaking Vigenere reduces to two steps: find m, then break m Caesar ciphers.

### Frequency analysis: the main tool

Each language has a letter frequency fingerprint. For English, approximately in percent:

```
E 12.7   T 9.1   A 8.2   O 7.5   I 7.0   N 6.7   S 6.3   H 6.1   R 6.0 ...
```

Z, Q, X and J are rare. The idea is that for a long enough ciphertext you count the frequency of each letter. If the distribution is still uneven like English (only relabeled), the cipher is monoalphabetic. If the distribution is flattened close to uniform, it is polyalphabetic (Vigenere) or not ordinary text.

To score a trial decryption, compute the deviation between its frequency distribution and the standard English distribution. The candidate with the best match is most likely the real plaintext. A convenient measure is chi-squared, which is the sum of (observed minus expected) squared divided by expected. The smaller the value, the better the match with English.

### Index of coincidence (IoC): measuring the unevenness

IoC is the probability that two characters drawn at random from the text are equal. With n_i the number of times letter i appears and N the total number of letters:

```
IoC = ( sum over i of n_i * (n_i - 1) ) / ( N * (N - 1) )
```

The intuition is that the more uneven the text (a few letters make up most of it), the more likely two drawn characters match, so IoC is higher. The more even the text (all letters equal), the lower the IoC.

Two reference values to memorize:

- Ordinary English: IoC about 0.066 to 0.067.
- A uniform random string over 26 letters: IoC about 1/26 = 0.0385.

First use: Caesar and substitution keep the IoC of the plaintext (they only relabel), so their IoC stays around 0.066. For Vigenere, the longer the key, the further IoC drops toward 0.0385. So by looking at IoC you can tell whether you face a monoalphabetic or polyalphabetic cipher.

The second use is finding the Vigenere key length. Assume a key length m and split the ciphertext into m columns (column j holds the characters at positions j, j+m, j+2m, ...). Each column is really a Caesar cipher, so it must have a high IoC (about 0.066). Compute the average column IoC for m = 1, 2, 3, ... The value of m where the average IoC jumps close to 0.066 is the key length (or a multiple of it).

### Three questions to answer

1. What does a correct result look like: substitution ciphers preserve the statistical structure of the language, so the plaintext matches the English frequency fingerprint.
2. Where does it fail: this whole family cannot hide the statistics. A small key (Caesar) or a repeating key (Vigenere) lets the statistics leak.
3. How to exploit it: brute force for Caesar, and frequency analysis and IoC for Vigenere and substitution, with no need to know the key beforehand.

## 2. Demo

### Breaking Caesar with brute force and scoring

```python
# caesar_break.py: break Caesar by trying all 26 shifts, scored with chi-squared
import string

# English letter frequencies (percent), index 0..25 maps to A..Z
ENG_FREQ = [8.2,1.5,2.8,4.3,12.7,2.2,2.0,6.1,7.0,0.15,0.77,4.0,2.4,
            6.7,7.5,1.9,0.095,6.0,6.3,9.1,2.8,0.98,2.4,0.15,2.0,0.074]

def shift(text, k):
    out = []
    for ch in text:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            out.append(chr((ord(ch) - base - k) % 26 + base))  # shift backwards to decrypt
        else:
            out.append(ch)
    return "".join(out)

def chi_squared(text):
    # count letters only, ignore spaces and other characters
    letters = [c.upper() for c in text if c.isalpha()]
    n = len(letters)
    if n == 0:
        return float('inf')
    score = 0.0
    for i, ch in enumerate(string.ascii_uppercase):
        observed = letters.count(ch)
        expected = ENG_FREQ[i] / 100 * n
        if expected > 0:
            score += (observed - expected) ** 2 / expected
    return score

ct = "Wklv lv d vhfuhw phvvdjh"   # Caesar k=3
candidates = [(chi_squared(shift(ct, k)), k, shift(ct, k)) for k in range(26)]
candidates.sort()                  # smallest chi-squared first
print("Guessed key k =", candidates[0][1])
print("Plaintext     :", candidates[0][2])
```

Output:

```
Guessed key k = 3
Plaintext     : This is a secret message
```

The nice part is that you do not need human eyes on 26 lines. Chi-squared picks the candidate closest to English by itself. The same procedure applies to any Caesar or ROT challenge.

### Measuring IoC to classify the cipher

```python
# ioc.py: measure the index of coincidence
def ioc(text):
    letters = [c.upper() for c in text if c.isalpha()]
    n = len(letters)
    if n <= 1:
        return 0.0
    total = 0
    for ch in set(letters):
        c = letters.count(ch)
        total += c * (c - 1)
    return total / (n * (n - 1))

english = ("Cryptography is the practice and study of techniques for secure communication "
           "in the presence of adversaries. Frequency analysis works because every natural "
           "language keeps a stubborn fingerprint no matter how you shuffle the alphabet, and "
           "that fingerprint is exactly what the index of coincidence measures for us here.")
print("English IoC (longer text gets closer to 0.066):", round(ioc(english), 4))

# an almost random string
import random
rnd = "".join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(2000))
print("Random string IoC (around 0.038)              :", round(ioc(rnd), 4))
```

Output (the exact numbers vary because the English passage is short and the other string is random):

```
English IoC (longer text gets closer to 0.066): 0.0618
Random string IoC (around 0.038)              : 0.0385
```

An English passage of a few hundred letters already gives an IoC around 0.06, and a longer one converges to 0.066, while the random string stays at 0.038. The gap between the two values is the boundary for classification. High means monoalphabetic, low means polyalphabetic or not text.

### Breaking Vigenere from the ciphertext

```python
# vigenere_break.py: find the key length with IoC, then recover each key character with chi-squared
import string

ENG_FREQ = [8.2,1.5,2.8,4.3,12.7,2.2,2.0,6.1,7.0,0.15,0.77,4.0,2.4,
            6.7,7.5,1.9,0.095,6.0,6.3,9.1,2.8,0.98,2.4,0.15,2.0,0.074]

def only_letters(text):
    return [c.upper() for c in text if c.isalpha()]

def ioc_list(letters):
    n = len(letters)
    if n <= 1:
        return 0.0
    total = sum(letters.count(ch) * (letters.count(ch) - 1) for ch in set(letters))
    return total / (n * (n - 1))

def guess_keylen(letters, max_len=20, threshold=0.06):
    # for each m, split into m columns and compute the average column IoC
    table = []
    for m in range(1, max_len + 1):
        cols = [letters[j::m] for j in range(m)]
        avg = sum(ioc_list(c) for c in cols) / m
        table.append((m, avg))
    # Pick the SMALLEST m whose average IoC passes the threshold (clearly above the random level 0.038).
    # This gets the true period and avoids picking a multiple of it (which also has a high IoC).
    for m, avg in table:
        if avg >= threshold:
            return m, table
    # if no m passes the threshold, take the m with the highest IoC
    return max(table, key=lambda x: x[1])[0], table

def best_shift(column):
    # column is a list of uppercase letters, find the Caesar shift that best matches English
    best_k, best_score = 0, float('inf')
    n = len(column)
    for k in range(26):
        dec = [chr((ord(ch) - 65 - k) % 26 + 65) for ch in column]
        score = 0.0
        for i, letter in enumerate(string.ascii_uppercase):
            observed = dec.count(letter)
            expected = ENG_FREQ[i] / 100 * n
            if expected > 0:
                score += (observed - expected) ** 2 / expected
        if score < best_score:
            best_score, best_k = score, k
    return best_k

def decrypt(text, key):
    out, ki = [], 0
    for ch in text:
        if ch.isalpha():
            base = 65 if ch.isupper() else 97
            k = ord(key[ki % len(key)]) - 65
            out.append(chr((ord(ch) - base - k) % 26 + base))
            ki += 1
        else:
            out.append(ch)
    return "".join(out)

ciphertext = (
    "Nvkdgzkdocsc ug gsi bfnnxuqr lrp ggfhk cs eiovatugsf qsd grnyds pzqyiatgmhvzr "
    "ub gsi bfrdizqr zj mripveoetie. O fffehveyfwby gudupv dscweosf peov ypxfse hmfv "
    "nysfvrc pqhgpv, mbq mioohdi fvr xebdvyk zsipv ovnykqg ve pqoxd xts scicirygk cs "
    "elq znykgotp yzrrcrqogs. Xts Itkqbrci owcsid hetie hb smps gsme pl fwubt l "
    "vqdrlxubt vik, phe szqr elq yrj pqbtel ug xysib gsi owcsidhrix edytxe waes "
    "ewzapq Qnpwmf fsmrhf lkmwa."
)
letters = only_letters(ciphertext)

# Step 1: find the key length
keylen, table = guess_keylen(letters)
print("IoC by key length :", [(m, round(a, 4)) for m, a in table[:8]])
print("Chosen key length :", keylen)

# Step 2: recover each key character from its column
cols = [letters[j::keylen] for j in range(keylen)]
key = "".join(chr(best_shift(c) + 65) for c in cols)
print("Recovered key     :", key)
print("Plaintext         :", decrypt(ciphertext, key)[:80], "...")
```

Output:

```
IoC by key length : [(1, 0.0422), (2, 0.0435), (3, 0.0422), (4, 0.0446), (5, 0.0714), (6, 0.0449), (7, 0.0408), (8, 0.0451)]
Chosen key length : 5
Recovered key     : LEMON
Plaintext         : Cryptography is the practice and study of techniques for secure communication in ...
```

The IoC table shows it clearly. Every length sits around 0.043 (close to the random level 0.038), and only m = 5 jumps to 0.0714 (the English level). That is the key length. Step 2 splits the ciphertext into 5 columns, finds the best Caesar shift for each, assembles the key `LEMON`, and decrypts. At no point is the key needed beforehand. With a long enough ciphertext (a few hundred characters or more) this method works almost every time.

In practice, the longer the ciphertext, the more accurate IoC and chi-squared are. A very short text gives noisy statistics. In that case try the first few key length candidates in the table and do not trust the top one alone.

## 3. Lab

- Task: the ciphertext below is Vigenere with an English-word key. Find the key and the plaintext. The plaintext contains a flag of the form `FLAG{...}`.

  ```
  HCYV{o1u3p3ic_r1iv3t_1j_l0i_l4tg}
  ```

  (Hint: the part inside the braces is leetspeak, the key is an English word in uppercase, and only letters are shifted while digits and punctuation stay unchanged.)

- Hints, in steps:
  - Hint 1: the challenge has many non-letter characters (digits, braces, underscores). When computing IoC and splitting columns, count only letters. When decrypting, keep the other characters unchanged and do not advance the key index on them.
  - Hint 2: the ciphertext is very short, so IoC is noisy and you should not rely on IoC alone. The flag starts with `FLAG`, and the four letters `HCYV` at the start decrypt to `FLAG`, which gives the first four key characters.
  - Hint 3: the first four key characters suggest a word familiar in the crypto world, and the key length is 6. Fill in the last two characters so the plaintext becomes readable and you are done.
- Done when: you read out the flag and know the key.

As an extension, generate about 500 words of English text, encrypt it with a Vigenere key of 6 characters, then run the script from section 2 to check that it recovers the key. Shorten the ciphertext step by step (300, 150, 80 words) and note at what length the method starts to guess wrong.

## 4. Key takeaways

- Caesar, ROT, Vigenere and substitution are all substitution ciphers, and their weakness is leaking language statistics.
- Caesar has only 25 keys. Brute force and then score with chi-squared.
- English IoC is about 0.066 and random is about 0.038. High means monoalphabetic, low means polyalphabetic.
- Break Vigenere in two steps. Find the key length with column IoC, then break each column as Caesar.
- This whole family can be broken without the key, as long as the ciphertext is long enough.

## 5. Common pitfalls

- Computing statistics over spaces and punctuation. Count only letters and drop everything else during analysis.
- Advancing the key index on non-letter characters while decrypting. For Vigenere on text with digits and punctuation, the key index may advance only on a letter, otherwise the key goes out of phase and you get garbage.
- Getting the shift sign wrong. Encryption adds k and decryption subtracts k. The wrong sign gives a "nearly right" plaintext off by a few letters, which can look like a wrong key length guess.
- Fully trusting the top key length on a short ciphertext. Multiples of the true key length also give a high IoC, so 4 and 8 can both stand out if the real key length is 4.
- Using English frequencies for plaintext that is not English. If the plaintext is Vietnamese without accents, Base64 or code, the frequency fingerprint is very different and chi-squared goes wrong.
- Forgetting case. Normalize everything to one case when counting, but keep the original case when printing the plaintext so it stays readable.

## 6. Further reading

- The Code Book (Simon Singh): the chapter on Vigenere and the Kasiski/Babbage method, explained in plain language.
- Tables of English letter, bigram and trigram frequencies, to refine your scoring.
- CryptoHack, the Classical / General section, and the "Vigenere" challenges on beginner wargames.
- The Kasiski method (finding the key length from the distances between repeated fragments), an alternative to IoC. It is worth knowing both.
- Continue with Lesson 2.3 on rail fence, Playfair and Enigma, to see classical ciphers that are not simple substitution.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 2.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/2.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/2.2/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>
