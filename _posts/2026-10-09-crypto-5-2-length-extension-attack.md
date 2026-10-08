---
title: "Lesson 5.2: Length Extension Attack"
image:
  path: /assets/img/covers/crypto-5-2-length-extension-attack.webp
  alt: "Length Extension Attack"
date: 2023-07-01 01:30:00 +0700
categories: ["Cryptography", "Crypto · Hashes and MACs"]
tags: [cryptography, hash, length-extension, sha256]
render_with_liquid: false
---

Many people build their own MAC (message authentication code) by hashing the key joined to the message: `tag = H(secret || msg)`. It looks reasonable, because the secret is mixed in and someone without the key should not be able to forge a tag. It is wrong. With MD5, SHA-1 and SHA-256, an attacker can append data to the message and compute a new valid tag without knowing the key. The flaw is in how these hash functions are built. This lesson takes apart the Merkle-Damgard construction, shows why `H(secret || msg)` leaks the internal state, and then rebuilds the hash state by hand to forge a cookie, running from start to end.

![Length extension attack](/assets/img/crypto/crypto-5-2-length-extension-attack.svg)
_The tag of H(secret || msg) is the internal state, so an attacker can load it and keep hashing._

Part 5 (Hashes, MACs and passwords) | Time: about 45 minutes | Difficulty: hard

**Prerequisites:** Lesson 5.1 (hashes, their properties, and SHA-2). Be comfortable with bytes, hex and big-endian.

**Tools:** Python 3 (only `hashlib` and `struct` from the standard library).

## Goals

After this lesson you can explain the Merkle-Damgard construction (the message is split into blocks, the state is updated step by step, and the digest is the final state), see why knowing the digest means you can continue hashing, state the conditions for length extension and what data the attacker needs, rebuild the state from a tag and compute a valid tag for a longer message, and explain why HMAC stops this attack and how to recognize `H(secret || msg)` in a challenge.

## 1. Theory

### Merkle-Damgard: how a hash runs inside

MD5, SHA-1 and SHA-256 all follow a pattern called Merkle-Damgard. The idea:

1. Initialize an internal state `H` with fixed constants (the IV). For SHA-256, `H` is eight 32-bit numbers.
2. Pad the message up to a multiple of the block size (SHA-256 uses 64-byte blocks). The padding is one byte `0x80`, then `0x00` bytes, then eight final bytes holding the original message length in bits (big-endian). Because the length is part of the padding, we will have to reproduce it.
3. Split the padded message into 64-byte blocks. For each block run the compression function: `H = compress(H, block)`. The new state depends on the old state and the current block.
4. After the last block, the digest is `H`.

The key point is that the digest is nothing other than the final internal state. When a server gives you `tag = H(secret || msg)`, it has handed you exactly the state of the hash function right after hashing `secret || msg || padding`.

### Why knowing the digest lets you keep hashing

Suppose I know the state `H` of the hash function at some point. I load `H` as the initial state in place of the IV, then run `compress` on my own block. The result is the digest of "all the earlier data plus the data I appended". I do not need to know the earlier data, only the state and the total length.

Applied to the homemade MAC `H(secret || msg)`:

- I know `tag`, which is the state after hashing `secret || msg || pad1`, where `pad1` is the padding of the `secret || msg` block.
- I load that state and hash a chunk `append` that I choose.
- The result is `H(secret || msg || pad1 || append)`, a valid tag for the new message `msg || pad1 || append`.

When the server receives it, it computes `H(secret || (msg || pad1 || append))` and gets exactly the tag I sent. I forged a tag without ever knowing `secret`.

### What I need and what I do not

Needed: the original message `msg`, its tag, and the length of `secret` in bytes. Not needed: the value of `secret`.

If the secret length is unknown, scan for it. Secrets are usually short (8 to 32 bytes), so try each length, build a forgery for each, and send it to the server. The one that is accepted has the correct length. That is only a few dozen attempts.

`pad1` is the "glue padding" that you must compute yourself and place between `msg` and `append`. It looks like garbage (`\x80\x00...` and eight length bytes), but for many formats (query strings, cookies) the server still parses the `append` part at the end, for example `&role=admin` overriding `role=user`.

### Why HMAC is immune

HMAC does not hash `secret || msg`. It hashes twice with two derived keys: `HMAC(k, m) = H((k xor opad) || H((k xor ipad) || m))`. The outer hash wraps the inner digest, so the tag the attacker sees is the output of the outer hash, not a state that matches `secret || msg`. There is no state to continue from, so length extension stops working. In short, do not build a MAC by concatenating with a hash, use HMAC. Alternatively use a sponge-style hash (SHA-3), which does not expose its whole state as the digest.

## 2. Demo

To rebuild the state by hand we need a SHA-256 that lets us load an initial state and account for the length already hashed. The script below implements SHA-256 in pure Python for that purpose, sets up a server that signs a cookie with `H(secret || data)`, and then forges the cookie `&role=admin` without the secret. Paste it and run it directly, it only needs the standard library.

```python
# length_ext.py: length extension attack on SHA-256, stdlib only
import struct, hashlib, os

K = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]
R = lambda x,n: ((x>>n)|(x<<(32-n))) & 0xffffffff

def compress(H, blk):
    w = list(struct.unpack(">16I", blk))
    for i in range(16,64):
        s0 = R(w[i-15],7) ^ R(w[i-15],18) ^ (w[i-15]>>3)
        s1 = R(w[i-2],17) ^ R(w[i-2],19) ^ (w[i-2]>>10)
        w.append((w[i-16]+s0+w[i-7]+s1) & 0xffffffff)
    a,b,c,d,e,f,g,h = H
    for i in range(64):
        t1 = (h + (R(e,6)^R(e,11)^R(e,25)) + ((e&f)^(~e&g)) + K[i] + w[i]) & 0xffffffff
        t2 = ((R(a,2)^R(a,13)^R(a,22)) + ((a&b)^(a&c)^(b&c))) & 0xffffffff
        h,g,f,e,d,c,b,a = g,f,e,(d+t1)&0xffffffff,c,b,a,(t1+t2)&0xffffffff
    return [(x+y)&0xffffffff for x,y in zip(H,[a,b,c,d,e,f,g,h])]

def md_pad(total_len):            # Merkle-Damgard padding for a message of total_len bytes
    p = b"\x80" + b"\x00"*((56-(total_len+1))%64) + struct.pack(">Q", total_len*8)
    return p

def sha256(msg, H=None, prelen=0):
    H = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19] if H is None else list(H)
    data = msg + md_pad(prelen+len(msg))
    for i in range(0,len(data),64):
        H = compress(H, data[i:i+64])
    return b"".join(struct.pack(">I",x) for x in H)

# --- server: signs the cookie with H(secret||data), secret is hidden ---
SECRET = os.urandom(16)
sign   = lambda data: hashlib.sha256(SECRET+data).hexdigest()
verify = lambda data,tag: hashlib.sha256(SECRET+data).hexdigest()==tag

data = b"user=guest&role=user"
tag  = sign(data)
print("original cookie:", data.decode())
print("original tag :", tag)

# --- attack: knows data, tag, secret length (=16), does NOT know secret ---
append = b"&role=admin"
slen = 16
H = struct.unpack(">8I", bytes.fromhex(tag))         # reload state from the tag
glue = md_pad(slen + len(data))                      # padding server da them
forged_data = data + glue + append
forged_tag  = sha256(append, H=H, prelen=slen+len(data)+len(glue)).hex()

print("forged cookie:", forged_data)
print("forged tag   :", forged_tag)
print("server accepts?", verify(forged_data, forged_tag))
```

Running it gives this output (the secret is random each time so the tags differ, but the last line is always `True`):

```
original cookie: user=guest&role=user
original tag : 6c81f2503987250234dbffb5f5a4d1318c1905090b3f6bd1cd5a7b50b4a0c8de
forged cookie: b'user=guest&role=user\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01 &role=admin'
forged tag   : b666a4040eb4987fdb3934cb7accbc32b8947e70af860d3752c3a3b1d84717ca
server accepts? True
```

Reading the output, we never touch `SECRET`. We only reload eight 32-bit numbers from the original `tag` with `struct.unpack(">8I", ...)` and hash on the segment `&role=admin`. The forged cookie contains the glue padding in the middle, which looks like garbage, but because the query string takes the last occurrence of a key, `role=admin` overrides `role=user`. The server recomputes `H(SECRET || forged_data)`, gets exactly the forged tag, and accepts it.

## 3. Lab

- Task: An API accepts `GET /order?data=<data>&sig=<tag>` with `tag = SHA256(secret || data)`. The `data` field looks like `item=book&qty=1`. Append `&qty=1000&admin=1` and produce a valid signature without knowing the secret. The server treats the later occurrence of a key as the effective one.
- Files: write a self-contained `solve.py` with a pure Python SHA-256, a server, and a `forge` function, as in the demo. If the secret length is unknown, the scan for it goes in the same script.
- Hints, step by step:
  1. Use a SHA-256 that lets you load a state and set the already-hashed length. Check that it matches `hashlib.sha256` on a few inputs before you trust it.
  2. From the tag, `struct.unpack(">8I", ...)` gives the eight state words.
  3. Compute the glue padding for the `secret || data` block with an assumed secret length. Remember the length is in bits and big-endian.
  4. Hash `append` from the loaded state with `prelen = len(secret) + len(data) + len(glue)`. If the secret length is unknown, scan from 8 to 32.
- Done when: the server accepts the forged cookie, and you can explain why the glue padding sits in the middle and the message is still valid.

## 4. Key takeaways

- MD5, SHA-1 and SHA-2 follow Merkle-Damgard: the digest is the final internal state.
- Knowing the digest and the length is enough to continue hashing, without the original data.
- `H(secret || msg)` is not a safe MAC because of length extension.
- Needed: `msg`, `tag`, and the length of `secret`. Not needed: the value of `secret`. If the length is unknown, scan it.
- Glue padding (`\x80`, the `\x00` bytes, eight bytes of bit length) must be inserted between `msg` and `append`.
- Defense: use HMAC, or SHA-3 (sponge). Putting the key at the end, `H(msg || secret)`, also blocks this attack, but HMAC remains the standard.

## 5. Common pitfalls

- Forgetting that the length in the padding is in BITS, not bytes. Multiply by eight. A mistake here makes the forgery fail with no clear reason.
- Mixing up endianness. SHA-256 uses big-endian for both the state words and the length field. MD5 and SHA-1 differ: MD5 uses little-endian for the length field. Using the wrong one breaks the forgery.
- Computing the glue padding from the length of `data` only and forgetting to add the length of `secret`. `prelen` must be `len(secret) + len(data)`.
- Thinking that HMAC is vulnerable too. It is the opposite: HMAC is what blocks length extension. This attack only works on homemade `H(secret || msg)`.
- In a real challenge the server may reject non-printable bytes in `data`. In that case pick a format that allows them (hex, base64) or find a place that accepts raw bytes.
- Using SHA-3 and still worrying about length extension. There is no need: the sponge does not expose the whole state as the digest.

## 6. Further reading

- Wikipedia, "Length extension attack", a short description that lists which hashes are affected.
- The `hashpump` tool and the Python package `hashpumpy` build forgeries automatically for MD5/SHA-1/SHA-256 (depending on the Python version it may not build, in which case code the state continuation yourself as in the demo).
- Cryptopals Set 4, Challenge 29 (Break a SHA-1 keyed MAC using length extension), the standard practice exercise.
- RFC 2104 (HMAC) to see how the two-layer hash design blocks this attack.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 5.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/5.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/5.2/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>
