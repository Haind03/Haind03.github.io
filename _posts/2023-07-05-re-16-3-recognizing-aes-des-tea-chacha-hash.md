---
title: "Lesson 16.3: Recognizing AES, DES, TEA, ChaCha and hash functions by structure"
image:
  path: /assets/img/covers/re-16-3-recognizing-aes-des-tea-chacha-hash.webp
  alt: "Lesson 16.3: Recognizing AES, DES, TEA, ChaCha and hash functions by structure"
date: 2023-07-05 22:39:00 +0700
categories: ["Technique Reverse", "Part 16 · Crypto and Algorithms"]
tags: [reverse-engineering, crypto]
render_with_liquid: false
---
In the last lesson you learned to find crypto constants with findcrypt. But the tool doesn't always work, and a lot of the time you only have a piece of pseudocode in front of you and have to guess. The good news: every common crypto algorithm has its own "gait", and once you know a few of them you can tell at a glance which one you're facing. And once you know the name, you don't need to reimplement it, just call a standard library to decrypt.

This lesson goes through the algorithms you'll see most, with the fastest tell for each one.

## TEA and XTEA: easiest to spot thanks to one number

Start with the easiest one. TEA (Tiny Encryption Algorithm) and its variant XTEA are compact and often get stuffed into malware and crackmes because the code is short and needs no lookup tables. The sign is almost instant: the **delta constant 0x9E3779B9**.

This number is the fractional part of the golden ratio times 2^32, and it shows up in every round of TEA. If you see `0x9E3779B9` in code, it's 90% TEA/XTEA. The loop usually runs 32 times, each round adding delta into a sum variable and then mixing the two halves of the block with shift left 4, shift right 5, add, and XOR.

In assembly, a TEA round looks like this:

```asm
; v0, v1 are the two 32-bit halves of the block; sum is in a register
add  esi, 0x9E3779B9      ; sum += delta   <- THE GIVEAWAY
mov  eax, edx             ; eax = v1
shl  eax, 4               ; v1 << 4
add  eax, [key+0]         ; + key[0]
mov  ecx, edx
add  ecx, esi             ; v1 + sum
xor  eax, ecx             ; ^ ...
mov  ecx, edx
shr  ecx, 5               ; v1 >> 5
add  ecx, [key+4]         ; + key[1]
xor  eax, ecx
add  ebx, eax             ; v0 += ...
```

The pattern "shl 4, shr 5, add key, XOR, add into the other half" repeating symmetrically for v0 and v1, together with delta, is a signature you can't confuse with anything else. Decrypting TEA is very easy because it's symmetric: run the 32 rounds backwards, subtracting delta instead of adding.

## AES: look at the S-box

AES (Rijndael) is the most widely used symmetric encryption algorithm in the world, so you'll meet it constantly. The strongest sign is a 256-byte S-box starting with `63 7C 77 7B F2 6B 6F C5 30 01 67 2B...`. This is the byte substitution table, and seeing exactly this sequence means it's definitely AES. The Rcon (round constant) for the key schedule is another tell: `01 02 04 08 10 20 40 80 1B 36...`.

The number of rounds is 10, 12 or 14 for 128, 192, 256-bit keys. MixColumns uses multiplication in a Galois field, so you often see multiplication by 2 and 3 with a conditional XOR of `0x1B`.

Many optimized implementations merge SubBytes, ShiftRows, MixColumns into T-tables (4 tables of 1KB), in which case you see four large tables and lots of table lookups plus XOR. Whether it's a plain S-box or T-tables, findcrypt catches both, but remembering the `63 7C 77 7B` start of the S-box is enough to recognize it by eye.

## DES: lots of permutations and 8 S-boxes

DES is old but still turns up in legacy systems. The signs are lots of permutation tables (initial permutation, final permutation, expansion, P-box) and 8 separate S-boxes, each turning 6 bits into 4 bits. DES code is full of bit shifts and small table lookups, with 16 Feistel rounds. If you see many fixed permutation tables along with 8 small S tables, think DES/3DES.

## ChaCha and Salsa20: look for the constant string

These are modern stream ciphers, increasingly common (TLS, WireGuard, lots of newer malware). The nicest tell is an ASCII string sitting right in the binary: "expand 32-byte k" (ChaCha20/Salsa20 with a 256-bit key) or "expand 16-byte k".

If you see this string in strings, it's almost certainly ChaCha/Salsa. The internal structure is the quarter-round: four additions, XORs, and bit rotations with characteristic rotation constants (ChaCha uses 16, 12, 8, 7). No S-box, just add-rotate-XOR all the way (called ARX).

## Hash functions: MD5, SHA, CRC

Hashes don't encrypt, they hash, but the recognition is similar, through constants. MD5 has four init values `0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476` and a 64-element K table (the sin table), over 64 rounds. SHA-1 has init `0x67452301...0xC3D2E1F0` and four round constants `0x5A827999, 0x6ED9EBA1, 0x8F1BBCDC, 0xCA62C1D6`. SHA-256 has a K table of 64 constants starting `0x428A2F98, 0x71374491...` and an init of eight values from the square roots of primes.

CRC32 uses a 256-entry table generated from the polynomial `0xEDB88320` (reversed form), with an XOR and shift right 8 loop. CRC is often mistaken for crypto but it's just a checksum, not secure. What the real hashes share is padding (append a 1 bit, then 0 bits, then the length at the end) and a compression loop that processes each 64-byte block.

## Quick lookup table by eye

| If you see this | Think |
|---|---|
| `0x9E3779B9` | TEA / XTEA |
| S-box starting `63 7C 77 7B` | AES |
| String "expand 32-byte k" | ChaCha / Salsa20 |
| 8 small S-boxes + many permutations | DES / 3DES |
| Init `67452301 EFCDAB89` + 64 rounds | MD5 |
| 64-element K table `428A2F98...` | SHA-256 |
| 256-entry table, poly `0xEDB88320` | CRC32 (checksum, not crypto) |

## Once you know the name, don't reimplement it

A beginner mistake: recognize AES and then sit down translating every round by hand into Python. No need. Once you know the algorithm, the key, and the mode (ECB/CBC/CTR), you call a standard library and you're done in a few lines:

```python
from Crypto.Cipher import AES
cipher = AES.new(key, AES.MODE_CBC, iv)
plaintext = cipher.decrypt(ciphertext)
```

Your job is just to reverse to get exactly three things: which algorithm, where the key is, which mode (and the IV if there is one). Let the library handle the computation. For TEA, since it's tiny and not in the standard library, rewriting it by hand is only about ten lines (see the lab).

## Lab

The goal is to recognize a crypto algorithm by its structure (without needing findcrypt) and then reverse it in Python. The crackme is `tea_lock.c`. Build it like this.

```bash
gcc -O0 -o tea_lock tea_lock.c          # Linux
# or with MinGW: x86_64-w64-mingw32-gcc -O0 -o tea_lock.exe tea_lock.c
```

Try it without knowing the password yet.

```bash
./tea_lock test1234      # -> Nope.
```

Open `tea_lock` in IDA or Ghidra and find the encryption function. Look at the loop and notice which constant stands out, and work out what algorithm it points to. Confirm there are exactly 32 rounds, and that there is a `shl 4` and a `shr 5`, which is the signature of a specific algorithm. Extract where the key (4 dwords) lives and what the expected ciphertext value is. Then write, or read, a Python script that reverses the algorithm to recover the password. The algorithm is symmetric, so decrypting means running the 32 rounds backward, subtracting the delta instead of adding it. Run `./tea_lock <password>` to confirm you get `Correct! CTF{...}`. Finally check whether the password shows up in `strings tea_lock`, and think about why it does not.

Two questions to think about. If this had been AES instead of TEA, what other sign would have told you? And why should you avoid hand-translating an algorithm into Python when it is AES or DES, while doing it by hand for TEA is reasonable? The solution and the verification script are in the collapsed section below and in `solve_tea.py`.

<div class="lab-box">
<div class="lab-head"><b>LAB 16.3</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/16.3/src/solve_tea.py" download><i class="fa-solid fa-file-code"></i>src/solve_tea.py</a>
<a class="lab-file" href="/assets/labs/16.3/src/tea_lock.c" download><i class="fa-solid fa-file-code"></i>src/tea_lock.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The values below come from a build with gcc on Linux.

Opening `tea_lock` in a decompiler, the encryption function has a loop running 32 times with a constant that jumps out immediately.

```c
sum += 0x9E3779B9;   // delta
v0 += ((v1 << 4) + k[0]) ^ (v1 + sum) ^ ((v1 >> 5) + k[1]);
v1 += ((v0 << 4) + k[2]) ^ (v0 + sum) ^ ((v0 >> 5) + k[3]);
```

The constant `0x9E3779B9` plus 32 rounds plus the symmetric `<<4` and `>>5` pattern across the two halves of the block is the signature of TEA. No findcrypt needed, just remembering the delta.

From the binary, the key is `KEY = {0x11223344, 0x55667788, 0x9ABCDEF0, 0x0F1E2D3C}`, the expected ciphertext (checked as `blk[0]==EXPECTED[0] && blk[1]==EXPECTED[1]`) is `(0xBBAAD475, 0x2E138704)`, and the password is 8 characters long (one TEA block is 2 dwords, 8 bytes).

TEA is symmetric, so decrypting means running the 32 rounds backward: start with `sum = delta*32`, and on each round subtract the mixing term and then subtract the delta. See `solve_tea.py` for the full script.

```
$ python3 solve_tea.py
Password: TEA_Rev!
```

Confirming it:

```
$ ./tea_lock TEA_Rev!
Correct! CTF{TEA_Rev!}

$ ./tea_lock wrongpwd
Nope.

$ strings tea_lock | grep TEA_Rev
(no output)
```

The password `TEA_Rev!` does not show up in `strings` because the binary only stores the already-encrypted ciphertext, not the plaintext. You have to reverse the algorithm to get it back, which is why a crackme using crypto is harder than one that just compares a plain string.

If this had been AES, you would have recognized it instead through the opening S-box bytes `63 7C 77 7B` or four 1KB T-tables, a round count of 10, 12 or 14, and no delta constant. findcrypt would catch the S-box right away.

As for why you should not hand-translate AES or DES into Python, they are complex, easy to get wrong, and `pycryptodome` already has correct, ready-made implementations. All you need is to reverse out the algorithm, the key and the mode, then call the library. TEA, by contrast, is tiny (a dozen lines) and is not part of any standard library, so writing it by hand is faster than going looking for a library that has it.

</details>

## Key takeaways
TEA/XTEA is recognized by the delta `0x9E3779B9`, 32 rounds, and shl 4 / shr 5, and it's easy to decrypt because it's symmetric. AES shows an S-box starting `63 7C 77 7B` (or 4 T-tables) and 10/12/14 rounds. ChaCha/Salsa has the string "expand 32-byte k" and is all add-rotate-XOR. DES has 8 small S-boxes, many permutation tables, and 16 Feistel rounds.

Hashes are recognized by init values and K tables, and CRC32 is a checksum with poly `0xEDB88320`. Once you've identified the algorithm, use a standard library to decrypt: you only need to find the right algorithm, key, and mode.
