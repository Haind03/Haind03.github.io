---
title: "Lesson 16.2: XOR, RC4 and custom Base64, the three you'll meet most"
date: 2023-07-03 21:27:00 +0700
categories: ["Technique Reverse", "Part 16 · Crypto and Algorithms"]
tags: [reverse-engineering, crypto]
render_with_liquid: false
---
If I had to pick the three data-transformation techniques you'll run into most when taking apart crackmes and malware, it'd be these: XOR, RC4, and Base64 with a shuffled alphabet. They make up most of the "the string looks like garbage" cases you need to solve. The good news is all three can be recognized by eye and reversed with a few lines of Python. This lesson teaches you to spot them and write the decoder.

## XOR, the national operation of obfuscation

The reason XOR is everywhere is simple: it reverses itself. `A ^ key ^ key == A`. Encryption and decryption share one function, one line of code, no library needed. Malware authors are lazy, and XOR serves that laziness perfectly.

In assembly, an XOR loop looks very distinctive:

```asm
loop:
    mov  al, [rsi+rcx]      ; take one byte of ciphertext
    xor  al, dl             ; XOR with the key (here dl holds a 1-byte key)
    mov  [rdi+rcx], al      ; write out the decoded byte
    inc  rcx
    cmp  rcx, rbx           ; reached the length yet
    jl   loop
```

If you see a loop that walks through a buffer and does an `xor` of a byte with a constant or a value taken from a key array, it's almost certainly a string encryption/decryption routine. There are three variants. With a single-byte key, every byte is XORed with the same value, which is the easiest, and you can even brute-force all 256 possibilities. With a multi-byte (rolling) key, each byte is XORed with `key[i % len(key)]`, the key repeating in a cycle, which is very common. In a rolling/running XOR, the next byte depends on the previous one (for example XOR with the byte just decoded), which is less common.

### Finding the key when you don't know it: known-plaintext

The most powerful trick with XOR is the known-plaintext attack. If you can guess part of the plaintext (for example the flag always starts with `flag{`, or a config JSON always opens with `{"`), then XORing that part of the ciphertext with the known plaintext reveals the key:

```
key[i] = ciphertext[i] ^ plaintext[i]
```

Do the first few bytes and the key shows up. If the key is short and repeats, you see the period right away. The lab at the end of this lesson does exactly this.

## RC4, the one with no magic constant

RC4 is a stream cipher often seen in malware because it's compact and needs no library. The hard part is that it has no distinctive constants like AES or SHA, so findcrypt can't catch it. You have to recognize it through its structure, and the signs can't be mistaken.

First, a 256-byte array (S-box) gets initialized with 0, 1, 2, ..., 255, and seeing a loop `S[i] = i` run 256 times is the first alarm bell. Second comes the KSA loop (Key Scheduling), a 256-iteration loop that permutes S based on the key: `j = (j + S[i] + key[i % keylen]) & 0xFF; swap(S[i], S[j])`. Third is the PRGA loop (keystream generation): `i = (i+1) & 0xFF; j = (j + S[i]) & 0xFF; swap; k = S[(S[i]+S[j]) & 0xFF]` and then XOR k with the data.

If you see a sequentially initialized 256 array, then swaps with AND 0xFF (that is, mod 256) all over the place, that's RC4. Because RC4 is symmetric, you only need to find the key (usually near the KSA section, or a hardcoded string in the binary) to decrypt. Copy the algorithm into Python, pass in the key, run it.

## Custom Base64, the trap for people in a hurry

Standard Base64 uses the 64-character alphabet `A-Za-z0-9+/`. Many programs change the order of this alphabet so the encoded string looks like Base64 but decodes to garbage with a standard tool. Beginners see a Base64-shaped string (letters, digits, sometimes `=` at the end), throw it into CyberChef, get garbage, and give up.

The key is to find the 64-character alphabet table in the binary. It usually sits in `.rdata` as a string of 64 consecutive characters, for example `ZYXWVUTSRQPO...`. Once you have the custom table, decoding is just mapping back to the standard table and then decoding normally:

```python
trans = bytes.maketrans(CUSTOM_ALPHABET, STANDARD_ALPHABET)
plaintext = base64.b64decode(ciphertext.translate(trans))
```

You can suspect custom Base64 when the output string only has 64 distinct characters, the length is a multiple of 4 (with `=` padding), and standard base64 gives garbage but the length fits. At that point go hunting for the alphabet table.

## General rule: copy the algorithm, don't rerun the binary

For all three of the above, the fastest approach isn't to debug byte by byte in the binary but to read enough to understand the algorithm and then rewrite it in Python. Python has `base64` built in, arbitrary-size integers, and compact bitwise syntax. An encryption routine that takes a whole session to trace in a debugger is usually just ten lines of Python once you understand it.

## Lab

In `labs/16.2/` there's `src/make_data.py`, which generates three encrypted strings (multi-byte XOR, RC4, custom Base64), and `src/solve.py`, which solves all three. Task: look at the three ciphertexts, recognize each type, then write the Python decoder yourself before opening the solution. Everything was actually run with Python 3.11, and the results are in the solution.

## Key takeaways
A loop that XORs a buffer with a constant or key array is a string encryption routine, and known-plaintext gets you the key. RC4 has no magic constant: you recognize it by the 256 array initialized 0..255 and then the two permutation loops with mod 256, and finding the key is enough to decrypt because it's symmetric.

For custom Base64, find the 64-character alphabet table in the binary, map it back to the standard table, then decode. The fastest way overall is to understand the algorithm and rewrite it in Python rather than trace byte by byte.
