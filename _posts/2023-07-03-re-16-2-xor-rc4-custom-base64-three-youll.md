---
title: "Lesson 16.2: XOR, RC4 and custom Base64, the three you'll meet most"
image:
  path: /assets/img/covers/re-16-2-xor-rc4-custom-base64-three-youll.webp
  alt: "Lesson 16.2: XOR, RC4 and custom Base64, the three you'll meet most"
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

Here are three ciphertexts, each produced with a different technique. Your job is to recognize which is which and then write Python to decrypt them, before you open the solution. The data comes from `make_data.py` and was actually run:

```
XOR ciphertext (hex):  34295353293d5d460d2c416b373357462b325a5120204f
RC4 ciphertext (hex):  ff0e15f7a4b880dcaef6bffa2e815a19c83db06649fea703c7b292b03442d2
Custom-Base64:         AncsA6gqwCM9y78uBnUaAGB9C7UhxTssBnE9uJ==
```

A few hints. All three plaintexts have the form `flag{...}`, which is known plaintext you can exploit. The third string looks like Base64 (64-character alphabet, `==` padding) but standard base64 decodes it to garbage, so look for an alphabet that has been shuffled (it is in `make_data.py`). For RC4 the key is `s3cr3t`, on the assumption that you pulled it out of the KSA part of a binary.

For the XOR sample, use `flag{` as known plaintext, find the key and decrypt the whole string. For RC4, copy the algorithm into Python, pass in the key and decrypt. For the custom Base64, take the custom alphabet, map it back to the standard one and decode. You can rerun everything with:

```
python3 -I make_data.py   # regenerate the three ciphertexts
python3 -I solve.py       # the reference solution
```

<div class="lab-box">
<div class="lab-head"><b>LAB 16.2</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/16.2/src/make_data.py" download><i class="fa-solid fa-file-code"></i>src/make_data.py</a>
<a class="lab-file" href="/assets/labs/16.2/src/solve.py" download><i class="fa-solid fa-file-code"></i>src/solve.py</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Everything was actually run with Python 3.11.9, and the full script is `solve.py`.

For the multi-byte XOR, the ciphertext begins with `34 29 53 53 29` and the plaintext is known to begin with `flag{` (`66 6c 61 67 7b`). XORing the two together gives:

```
0x34^0x66=0x52='R'  0x29^0x6c=0x45='E'  0x53^0x61=0x32='2'  0x53^0x67=0x34='4'  0x29^0x7b=0x52='R'
```

The key characters that appear are `R E 2 4 R ...`, repeating after 4 characters, so the real key is `RE24` (length 4). Decrypting the whole string:

```
[XOR] key = b'RE24' -> plaintext = flag{xor_is_everywhere}
```

For RC4, the key `s3cr3t` comes from the KSA code. Copy the KSA and PRGA exactly into Python and XOR the keystream with the ciphertext:

```
[RC4] plaintext = flag{rc4_has_no_magic_constant}
```

Note that there is no constant for findcrypt to catch. You only recognize RC4 by the 256-entry array initialized to 0..255 and the two swapping loops with `& 0xFF`.

For the custom Base64, the alphabet is `ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjihgfedcba9876543210+/`, which reverses the letter and digit parts relative to the standard one. Map the custom alphabet back to the standard one and then call `base64.b64decode`:

```
[B64] plaintext = flag{custom_base64_alphabet}
```

The lessons are that known plaintext is the strongest weapon against XOR, since you only need to guess the first few bytes right, that RC4 is recognized by structure and not by constants, and that a Base64 that "decodes to garbage" is usually a shuffled alphabet and not something other than Base64.

</details>

## Key takeaways
A loop that XORs a buffer with a constant or key array is a string encryption routine, and known-plaintext gets you the key. RC4 has no magic constant: you recognize it by the 256 array initialized 0..255 and then the two permutation loops with mod 256, and finding the key is enough to decrypt because it's symmetric.

For custom Base64, find the 64-character alphabet table in the binary, map it back to the standard table, then decode. The fastest way overall is to understand the algorithm and rewrite it in Python rather than trace byte by byte.
