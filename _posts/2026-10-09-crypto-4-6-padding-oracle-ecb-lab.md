---
title: "Lesson 4.6: Padding oracle and byte-at-a-time ECB lab"
image:
  path: /assets/img/covers/crypto-4-6-padding-oracle-ecb-lab.webp
  alt: "Padding oracle and byte-at-a-time ECB lab"
date: 2026-10-09 12:30:00 +0700
categories: ["Cryptography", "Crypto · Symmetric Encryption"]
tags: [cryptography, padding-oracle, ecb, lab]
render_with_liquid: false
---

This is the wrap-up lesson of Part 4. It combines two classic challenges from Cryptopals Set 2 into one lab, with full solve scripts that run from start to finish. The first challenge is byte-at-a-time ECB decryption, which extracts a secret appended after your input one byte at a time, using only the fact that ECB encrypts each block independently. The second rebuilds the padding oracle of Lesson 4.3 into a complete decryption tool. The goal is that you run the scripts, understand every line, and then apply them to harder variants.

![Padding oracle and byte-at-a-time ECB lab](/assets/img/crypto/crypto-4-6-padding-oracle-ecb-lab.svg)
_Both attacks query an oracle repeatedly and never touch the key._

Part 4 (Symmetric Encryption) | Time: about 60 minutes | Difficulty: hard

**Prerequisites:** Lesson 4.1 (ECB, AES), Lesson 4.2 (recognizing ECB), Lesson 4.3 (padding oracle, the CBC formula). You should finish the theory of those three lessons first.

**Tools:** Python 3 and PyCryptodome.

## Goals

After this lesson you can run byte-at-a-time ECB decryption and explain why aligning one byte at a time recovers the secret. You can detect the block size and recognize ECB in code instead of guessing. You can run the full padding oracle decryption over several blocks. You can join the two techniques into one reusable attack toolkit. You can extend them to the variant with a random prefix (Cryptopals Challenge 14) and to an oracle over the network.

## 1. Theory

### Challenge 1: byte-at-a-time ECB decryption, the idea

There is an oracle that encrypts in the form `ECB(attacker_controlled || SECRET)`, where `SECRET` is the string we want to extract, under one fixed key. We control the `attacker_controlled` part. We do not know the key or SECRET.

ECB encrypts each 16-byte block independently. The trick is to feed in exactly 15 bytes of `A`, so the first block holds 15 bytes of `A` plus the first byte of SECRET. We do not know that byte, but we can try. We send `A*15 + guess` for guess from 0 to 255 and compare the first output block with the first block the oracle returns for `A*15`. The guess that produces an identical block is the first byte of SECRET, because ECB is deterministic, so the same 16 input bytes give the same 16 output bytes.

With the first byte known, we shorten the prefix to 14 bytes of `A`, so the first block holds `A*14 + SECRET[0] + SECRET[1]`. Since we now know `SECRET[0]`, we try `A*14 + SECRET[0] + guess` to get `SECRET[1]`. The prefix keeps shrinking, and each time one new byte of SECRET is pushed into the last position of the block to be searched. When the first block is used up, we move on to aligning against the second block, then the third, and so on until all of SECRET is recovered. Each byte costs at most 256 oracle calls.

Three things must be done in code, not guessed, namely detect the block size (send input of growing length and see where the output length jumps; the size of that jump is the block size), confirm it is ECB (send repeated input and see equal ciphertext blocks), and only then run the byte recovery loop.

### Challenge 2: padding oracle, a short reminder

This was covered in detail in Lesson 4.3. Here is a summary so the lab stands alone. With CBC, `Pi = D(Ci) XOR C(i-1)`. We control `C(i-1)`, so we can force the padding of the decrypted block. We probe from the last byte to the first. At each position we force the target padding `N = 16 - pos` and try 256 values. The byte that makes the oracle report valid padding gives the intermediate value, and from that the plaintext. The coincidence at the last byte is handled by flipping one bit of the previous byte and asking again.

### Why both attacks work

Challenge 1 works because ECB exposes the relation "same input gives same output" at the level of each block. Challenge 2 works because plain CBC does not authenticate, so the oracle is willing to decrypt forged ciphertext. The two root causes are different (one is a deterministic mode, the other is missing integrity), but both allow plaintext recovery without the key. This is the lesson that runs through Part 4, where a wrong mode or missing authentication is enough to break the system, and nobody has to break AES.

## 2. Demo

### Script 1: byte-at-a-time ECB decryption, full solution

This file builds the oracle itself (the server part, which knows the key) and the attacker (which only calls `oracle`). SECRET is hidden as base64, exactly like Cryptopals Challenge 12. Paste it and run it.

```python
# solve_ecb_byte_at_a_time.py: recover SECRET byte by byte through an ECB oracle
import os, base64
from Crypto.Cipher import AES

KEY = os.urandom(16)   # secret, the attacker does NOT know it
BS = 16
SECRET = base64.b64decode(
    "Um9sbGluJyBpbiBteSA1LjAKV2l0aCBteSByYWctdG9wIGRvd24gc28gbXkg"
    "aGFpciBjYW4gYmxvdwpUaGUgZ2lybGllcyBvbiBzdGFuZGJ5IHdhdmluZyBq"
    "dXN0IHRvIHNheSBoaQpEaWQgeW91IHN0b3A/IE5vLCBJIGp1c3QgZHJvdmUgYnkK")

# --- server side: oracle ECB(attacker || SECRET) ---
def oracle(attacker: bytes) -> bytes:
    data = attacker + SECRET
    pad_len = BS - (len(data) % BS)        # PKCS#7
    data = data + bytes([pad_len]) * pad_len
    return AES.new(KEY, AES.MODE_ECB).encrypt(data)

# --- attacker side: only uses oracle ---
def detect_block_size() -> int:
    base = len(oracle(b""))
    i = 1
    while True:
        n = len(oracle(b"A" * i))
        if n != base:                      # output length jumps
            return n - base
        i += 1

def is_ecb() -> bool:
    ct = oracle(b"A" * 64)                 # long enough repeated input
    blocks = [ct[i:i+BS] for i in range(0, len(ct), BS)]
    return len(blocks) != len(set(blocks)) # a repeated block -> ECB

def attack() -> bytes:
    bs = detect_block_size()
    assert bs == BS, "unexpected block size"
    assert is_ecb(), "not ECB"
    total = len(oracle(b""))               # length of SECRET (after padding)
    recovered = b""
    for _ in range(total):
        pad_len = bs - 1 - (len(recovered) % bs)   # push the byte to search to the end of a block
        prefix = b"A" * pad_len
        block_index = (pad_len + len(recovered)) // bs
        lo, hi = block_index * bs, block_index * bs + bs
        target = oracle(prefix)[lo:hi]             # block that holds the next secret byte
        found = None
        for b in range(256):
            guess = prefix + recovered + bytes([b])
            if oracle(guess)[lo:hi] == target:
                found = b
                break
        if found is None:                          # reached the padding bytes, stop
            break
        recovered += bytes([found])
    if recovered and recovered[-1] == 1:           # drop the 0x01 padding byte if present
        recovered = recovered[:-1]
    return recovered

if __name__ == "__main__":
    print("block size:", detect_block_size())
    print("is ECB    :", is_ecb())
    out = attack()
    print("--- SECRET recovered ---")
    print(out.decode(errors="replace"))
    assert out == SECRET
    print("--- OK, recovered all of SECRET without knowing the key ---")
```

Run it:

```
block size: 16
is ECB    : True
--- SECRET recovered ---
Rollin' in my 5.0
With my rag-top down so my hair can blow
The girlies on standby waving just to say hi
Did you stop? No, I just drove by

--- OK, recovered all of SECRET without knowing the key ---
```

Worth noting, we never sent SECRET to the oracle. We only sent `A` characters and guessed bytes. ECB reveals that "these 16 bytes encrypt to this block", and we use that by aligning one unknown byte at the end of a block, which turns recovering one byte into trying 256 possibilities.

### Script 2: padding oracle, full multi-block solution

This is the complete version of Lesson 4.3, packaged as a decryption tool. The `attack` function only calls `padding_ok` and never touches the key.

```python
# solve_padding_oracle.py: decrypt CBC through a padding oracle
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

KEY = os.urandom(16)
BS = 16

def encrypt(msg: bytes) -> bytes:
    iv = os.urandom(BS)
    return iv + AES.new(KEY, AES.MODE_CBC, iv).encrypt(pad(msg, BS))

def padding_ok(ct: bytes) -> bool:         # oracle: only reports whether the padding is valid
    iv, body = ct[:BS], ct[BS:]
    try:
        unpad(AES.new(KEY, AES.MODE_CBC, iv).decrypt(body), BS)
        return True
    except ValueError:
        return False

def decrypt_block(prev: bytes, cur: bytes) -> bytes:
    inter = bytearray(BS)      # intermediate value D(cur)
    out = bytearray(BS)
    for pad_val in range(1, BS + 1):
        pos = BS - pad_val
        forged = bytearray(BS)
        for i in range(pos + 1, BS):
            forged[i] = inter[i] ^ pad_val         # force known bytes to the target padding
        for guess in range(256):
            forged[pos] = guess
            if padding_ok(bytes(forged) + cur):
                if pad_val == 1:                   # rule out a coincidence
                    forged[pos - 1] ^= 1
                    if not padding_ok(bytes(forged) + cur):
                        continue
                inter[pos] = guess ^ pad_val
                out[pos] = inter[pos] ^ prev[pos]  # real plaintext = Ii XOR real prev
                break
        else:
            raise RuntimeError(f"stuck at position {pos}")
    return bytes(out)

def attack(ct: bytes) -> bytes:
    blocks = [ct[i:i+BS] for i in range(0, len(ct), BS)]
    out = b"".join(decrypt_block(blocks[i-1], blocks[i]) for i in range(1, len(blocks)))
    return unpad(out, BS)

if __name__ == "__main__":
    secret = b"flag{ecb_and_padding_oracle_both_fall_without_the_key}"
    ct = encrypt(secret)
    rec = attack(ct)
    print("recovered:", rec)
    assert rec == secret
    print("OK, decrypted without knowing the key")
```

It prints `recovered: b'flag{ecb_and_padding_oracle_both_fall_without_the_key}'`. To see the number of oracle calls, wrap `padding_ok` with a counter. For this message it comes to a few thousand.

## 3. Lab

The two scripts above are the easy versions (empty prefix, oracle inside the same process). Your job is to raise the difficulty:

- Task A (ECB with a random prefix, Cryptopals Challenge 14): the oracle is now `ECB(random_prefix || attacker || SECRET)`, where `random_prefix` has a fixed length that you do not know. You still need to recover SECRET.
  - Hint 1: first find the prefix length. Send two inputs that differ in the first byte, and see where the first ciphertext block starts to differ, which tells you up to which block the prefix extends.
  - Hint 2: find the partial remainder of the prefix in that block by adding padding bytes until two inputs `X` and `Y` produce equal ciphertext blocks at the boundary. At that point you know how much padding is needed to make the prefix fill whole blocks.
  - Hint 3: treat `prefix + your padding` as a new prefix of whole blocks, then apply the same byte-at-a-time algorithm, only shifting the block index.

- Task B (padding oracle over the network): wrap `padding_ok` in an HTTP service (Flask) that returns 200 for valid padding and 403 otherwise. Write an attack client that calls it with `requests`. Add timing measurement if the oracle does not return a clear error code.
  - Hint 1: keep `decrypt_block` as it is and only replace the body of `padding_ok` with a request.
  - Hint 2: the attack is expensive in requests (up to 256 per byte). Parallelize over guess values, or cache, or run several blocks in parallel.
  - Hint 3: if the signal is timing, measure several times and take the median to filter network noise.

- Lab files: the Lab section below has `solve_ecb_byte_at_a_time.py` and `solve_padding_oracle.py` (the two easy versions from section 2, ready to run) with `transcript.txt`. Use them as the starting point for tasks A and B.
- Done when: you recover SECRET in task A even when the random prefix length changes at every start, and you decrypt the ciphertext in task B over HTTP and obtain the flag.

<div class="lab-box">
<div class="lab-head"><b>LAB 4.6</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/4.6.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/4.6/solve_ecb_byte_at_a_time.py" download><i class="fa-solid fa-file-code"></i>solve_ecb_byte_at_a_time.py</a>
<a class="lab-file" href="/assets/labs-crypto/4.6/solve_padding_oracle.py" download><i class="fa-solid fa-file-code"></i>solve_padding_oracle.py</a>
</div>
</div>

## Key takeaways

- Byte-at-a-time ECB: align the next secret byte at the end of a block, try 256 values, compare ciphertext blocks.
- Always detect the block size and confirm ECB in code before running the byte recovery loop.
- Padding oracle: probe from the last byte to the first, force target padding N, and handle the coincidence at N = 1.
- Neither attack touches the key. They only ask the oracle again and again.
- ECB with a random prefix can still be solved by measuring and neutralizing the prefix first.
- Defense: do not use ECB for user data, and use AEAD to stop padding oracles.

## Common pitfalls

- In byte-at-a-time ECB, a padding character equal to the first byte of SECRET can cause confusion at the confirmation step. This is usually harmless, but if you get stuck, change the padding character.
- Forgetting to stop at the padding. The last byte recovered is usually the `0x01` of PKCS#7 padding. If you do not drop it, SECRET has one extra junk byte. The script handles this by cutting the trailing `0x01`.
- Mixing up the block index when SECRET is longer than one block. Recompute `block_index` from the number of bytes recovered, as the script does.
- With the padding oracle, forgetting that the IV is block 0, so the first plaintext block cannot be decrypted if the challenge does not send the IV.
- With a random prefix, a wrong prefix length shifts everything. Determine the prefix exactly, byte by byte, before recovering.
- Giving up because the network attack is slow. Cache, parallelize, and stop the loop as soon as you hit. Do not send all 256 requests if you already found the byte at guess 30.

## Further reading

- Cryptopals Set 2, Challenge 12 (byte-at-a-time ECB decryption, simple) and Challenge 14 (harder, with a random prefix).
- Cryptopals Set 3, Challenge 17 (CBC padding oracle), the network version of Script 2.
- Lesson 4.3 (padding oracle) and Lesson 4.4 (CBC bit flipping), to connect the theory.
- NCC Group and other write-ups of real padding oracles in ASP.NET (MS10-070), to see this attack outside CTFs.
- CryptoHack, the Symmetric section, the ECB and CBC challenges for more variants.
