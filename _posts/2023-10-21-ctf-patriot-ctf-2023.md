---
title: "PatriotCTF 2023: writeups"
image:
  path: /assets/img/covers/ctf-patriot-ctf-2023.webp
  alt: "PatriotCTF 2023 writeups"
date: 2023-10-21 20:00:00 +0700
categories: ["CTF Writeups", "PatriotCTF 2023"]
tags: [ctf, writeup, rev, crypto, forensics]
render_with_liquid: false
---

PatriotCTF 2023 was an online CTF held in autumn 2023. These are my notes for the reversing, crypto, forensics and misc challenges I worked on. Most of them are short, so each section is the idea plus the small script that solves it. A few challenges I could not finish are marked as unsolved at the end of their category.

## Rev - python xor

**Files:** [python-xor.zip](/assets/ctf-files/patriot-ctf-2023/python-xor.zip)

The challenge gives a short ciphertext string and a stub `XOR.py` where the key is left blank. The key is a single character from `string.punctuation`. The ciphertext starts with `b`, and the flag is expected to start with `F`, so the key is `ord('b') ^ ord('F')`, which is 36. XOR-ing every byte with 36 gives the plaintext.

```python
enc = "bHEC_T]PLKJ{MW{AdW]Y"
print(ord(enc[0]) ^ ord('F'))
flag = ""
for i in range(len(enc)):
    flag += chr(ord(enc[i]) ^ 36)

print(flag)
```

Output:

```
36
Flag{python_is_e@sy}
```

Flag: `Flag{python_is_e@sy}`

## Rev - suboptimal

**Files:** [suboptimal.zip](/assets/ctf-files/patriot-ctf-2023/suboptimal.zip)

This is an ELF that reads input and runs each character through helper functions (`complex`, `complex2`) in a loop. My script takes the encoded string and subtracts 8 from every byte.

```python
enc = "xk|nF{quxzwkgzgwx|quitH"
flag = ""
for i in range(len(enc)):
    flag += chr(ord(enc[i]) - 8)

print(flag)
```

Output:

```
pctf>simproc_r_optimal@
```

Status: unsolved. The first four characters match the `pctf` prefix, but the fifth and last characters come out as `>` and `@` instead of the braces, so the plain subtract-8 is not the whole transform and the real flag is not confirmed. I did not finish tracing `complex` and `complex2` in the disassembly, and I am not reporting a guessed flag.

## Rev - GoLmoL

**Files:** [golmol.zip](/assets/ctf-files/patriot-ctf-2023/golmol.zip)

A Go binary that builds a secret and compares it with the input. The source in `main.go` shows the whole logic. The secret is every fifth ASCII character from 33 up to 122:

```go
for i := 33; i < 123; i+=5 {
    data := fmt.Sprintf("%c", i)
    sekret = append(sekret, data)
}
```

The input must equal this secret. For each matching character, the program appends `char + 7` to the flag, which starts as `PCTF{`. So the secret is `!&+05:?DINSX]bglqv` and shifting each character by 7 gives the flag body.

Flag: `PCTF{(-27<AFKPUZ_dinsx}`

## Rev - reduced_reduced_instruction_set

**Files:** [reduced-reduced-instruction-set.zip](/assets/ctf-files/patriot-ctf-2023/reduced-reduced-instruction-set.zip)

The challenge gives a small custom VM (`vm`) and a program file `password_checker.smol`. The file starts with the magic `SMOL` followed by 4-byte instructions (opcode, destination register, source register, immediate). `programmer.py` shows how the program was generated: it has instructions for mov, movi, push, pop, mul, addi, cmp, jz, reading a number and printing.

The checker reads 7 integers and compares each against a constant that the program builds with multiplications (large constants are factored into products of values below 0xFF, then multiplied inside the VM). Each integer is a 4-byte ASCII chunk of the flag, so after decoding the instructions, or breaking on the `cmp` instruction, the constants are the flag in big-endian chunks. For example `1885566054` is `0x70637466`, which is `pctf`.

The input used to pass the check is seven numbers piped into the VM:

```bash
echo "1885566054
2071358815
1915975269
1920152425
1850171185
1935635570
2100310064" | ./vm ./password_checker.smol
```

Decoding the seven chunks as 4-byte big-endian ASCII gives the flag. I did not run the VM binary myself, the numbers come from the author's solve script.

Flag: `pctf{vm_r3vers3inG_1s_tr1cky}`

## Rev - reduced_reduced_instruction_set_2

**Files:** [reduced-reduced-instruction-set-2.zip](/assets/ctf-files/patriot-ctf-2023/reduced-reduced-instruction-set-2.zip)

The same VM with more instructions, and a much bigger program (about 300 KB). The password checker program encodes an 840 character message, with the flag inside it, using a running XOR cipher:

```python
def make_flag(password):
    encoded_flag = []
    for x,char in enumerate(password):
        if x != 0:
            val = ord(char) ^ encoded_flag[x-1]
            val = (val + (x % 0xFF)) % 0xFF
        else:
            val = (ord(char) + (x % 0xFF)) % 0xFF
        encoded_flag.append(val)
    return encoded_flag
```

Each output byte depends on the previous encoded byte, so a side channel on the comparison would take far too long for 840 characters, and the key pieces have to be pulled out of the binary with automation. The accepted input is a long text about Caesar and Vigenere ciphers, reversed, with the flag placed in the middle. The solve script just prints that message reversed and pipes it to the VM:

```python
enc_msg = """A Caesar cipher, also known as Caesar's cipher, ...
pctf{vM_r3v3rs1ng_g0t_a_l1ttl3_harder}
The Vigenere cipher is a method of encrypting alphabetic text ..."""

print(enc_msg[::-1], end="")
```

```bash
python solve.py | ./vm2 password_checker2.smol
```

Flag: `pctf{vM_r3v3rs1ng_g0t_a_l1ttl3_harder}`

## Rev - patchwork

**Files:** [patchwork.zip](/assets/ctf-files/patriot-ctf-2023/patchwork.zip)

The challenge is an ELF named `patchwork`. The only thing I kept for it is the flag file, I do not have a script or notes on the method.

Flag: `PCTF{JuMp_uP_4nd_g3t_d0Wn}`

## Rev - garbage

**Files:** [garbage.zip](/assets/ctf-files/patriot-ctf-2023/garbage.zip)

`garbage.py` is a Python script whose source is full of Brainfuck comments after every line (noise). The real logic is three stages that are applied to the flag, and the challenge output is the result:

- stage 1: XOR each character with its index, then reverse the string.
- stage 2: seed the random generator with 10, and add `randint(0,5)` to every character, after a prefix string cut out of a Brainfuck line.
- final stage: swap characters in adjacent pairs, then reverse.

The solve script calls the stages in a different order on the given string, using the same seeded generator, and it gives the original text back. Running my copy of `solve.py` locally prints:

```
PCTF{H0w_D1d_y0U_br34k_my_1337_c0de?}
```

The key bit is that `seed(10)` makes the random additions deterministic, so the same sequence can be regenerated.

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
    return "".join(x for x in a)

print(stage1(stage2(finalstage("^seqVVh+]>z(jE=%oK![b$\\NSu86-8fXd0>dy"))))
```

Flag: `PCTF{H0w_D1d_y0U_br34k_my_1337_c0de?}`

## Rev - Coffee shop

**Files:** [coffee-shop.zip](/assets/ctf-files/patriot-ctf-2023/coffee-shop.zip)

This one is a Java program (`CoffeeShop.jar`) with a decompiled `CoffeeShop.java` from Procyon.

Status: unsolved. I did not work through the decompiled source for this write up, and there is no flag or solve script in my files, so I am not reporting a flag.

## Crypto - ReReCaptcha

**Files:** [rerecaptcha.zip](/assets/ctf-files/patriot-ctf-2023/rerecaptcha.zip)

The challenge gives RSA material as images and text: the ciphertext `c`, and the two primes `p` and `q` (stored as text in `P.txt`, `Q.txt` and `CT.txt`, with matching PNG screenshots). With both primes known, RSA is trivial to break. Compute `phi = (p-1)(q-1)`, the private exponent `d = e^-1 mod phi` (with `e = 65537`), and decrypt.

```python
from Crypto.Util.number import *
c = 5475900459964702612251440685646325915737874208657676542124440368105729666783...
e = 65537
q = 8803989692514528873086609175044861825628469040762871212917631687192741367465...
p = 7527565288418755379118789957530427076474039495543602083672348770256244095402...
n = p * q
fi = (p-1) * (q-1)
d = pow(e, -1, fi)
fl = pow(c, d, n)
print(long_to_bytes(fl))
```

(The long numbers are truncated here, the full values are in the challenge files.) Running the script gives:

```
b'PCTF{I_H0P3_U_U53D_0CR!}'
```

Flag: `PCTF{I_H0P3_U_U53D_0CR!}`

## Crypto - binary

**Files:** [binary.zip](/assets/ctf-files/patriot-ctf-2023/binary.zip)

The challenge file `Binary.txt` is a long string of 1444 zeros and ones. My script `s.py` is a helper that turns a binary string into hex by grouping 4 bits at a time with a lookup table.

Status: unsolved. Reading the bits as 7-bit or 8-bit ASCII (also inverted) does not give readable text, and 1444 is 38 squared but the data does not form a valid QR code when I render it as a 38 by 38 grid. I did not find the right encoding, so no flag.

## Forensics - wpa

**Files:** [wpa.zip](/assets/ctf-files/patriot-ctf-2023/wpa.zip)

The challenge is a packet capture (`savedcap.cap`) with a WPA handshake for the network `Pctf wifi challenge`. The standard approach is to run a dictionary attack against the handshake with `aircrack-ng` and the rockyou wordlist:

```
aircrack-ng savedcap.cap -w /usr/share/wordlists/KaliLists/rockyou
...
KEY FOUND! [ qazwsxedc ]
```

The cracked Wi-Fi password is `qazwsxedc`. My notes only keep the aircrack output, not the submitted flag, so I am not stating the flag text.

Status: partially done. The key is recovered, the flag string itself is not recorded in my files.

## Misc - ML_Pyjail

**Files:** [ml-pyjail.zip](/assets/ctf-files/patriot-ctf-2023/ml-pyjail.zip)

A Python jail challenge with a tflearn model and training data (`good_code.txt`, `bad_code.txt`). The `flag.txt` in the folder is a placeholder, not the real flag.

Status: unsolved. The challenge needs the live service, and I only have the local copy with a fake flag, so I have no real flag.

## Misc - flag find

The challenge is a remote service where the flag is guessed character by character against `chal.pctf.competitivecyber.club`. My `s.py` uses pwntools to try candidates such as `pctf{Tim3ingI8N3at}`, and `x.py` just prints guesses.

Status: unsolved. The service is a live remote, and I only have partial guesses, so I cannot confirm any flag.
