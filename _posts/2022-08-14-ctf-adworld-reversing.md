---
title: "Adworld Reversing 2022: writeups"
image:
  path: /assets/img/covers/ctf-adworld-reversing.webp
  alt: "Adworld Reversing 2022 writeups"
date: 2022-08-14 20:00:00 +0700
categories: ["CTF Writeups", "Adworld Reversing 2022"]
tags: [ctf, writeup, rev]
render_with_liquid: false
---

This is not a dated competition. It is a practice set of reverse engineering challenges from the Adworld platform that I worked through in 2022, using IDA, static analysis and small C++ or Python scripts to invert the checks. The set has around 52 challenges. This post covers the ones I solved, grouped by technique: byte-wise XOR and arithmetic decoders, strided and table-based decoders, reproducing logic from source or threads, runtime-decoded code, and unpacking. Everything here is static analysis, I did not run the binaries as part of the writeups.

## XOR and arithmetic decoders

### Rev - 666

**Files:** [666.zip](/assets/ctf-files/adworld-reversing/666.zip)

The binary compares the input against an encoded string. The encoder works on groups of three bytes with a key of 18, and each byte of the group gets a different operation. Because every step is invertible, I applied the inverse to the stored string `izwhroz""w"v.K".Ni`.

```cpp
string encode(){
    char a2[100] = "izwhroz\"\"w\"v.K\".Ni";
    char flag[100];
    int key = 18;
    for (int i = 0; i < key; i += 3 ){
        flag[i] = (key ^ *(char *)(a2 + i)) - 6;
        flag[i + 1] = (*(char *)(a2 + i + 1LL)  ^ key) + 6;
        flag[i + 2] = *(char *)(a2 + i + 2LL) ^ 6 ^ key;
    }
    return flag;
}
```

Flag: `unctf{b66_6b6_66b}`

### Rev - xxxorrr

**Files:** [xxxorrr.zip](/assets/ctf-files/adworld-reversing/xxxorrr.zip)

The program XORs a constant string with `2 * i + 65` for each index, and then XORs the result with a stored byte array. Running the same two operations on the constant string produces the flag, since XOR is its own inverse.

```cpp
unsigned char s2[] =
{
0x56, 0x4E, 0x57, 0x58, 0x51, 0x51, 0x09, 0x46, 0x17, 0x46,
0x54, 0x5A, 0x59, 0x59, 0x1F, 0x48, 0x32, 0x5B, 0x6B, 0x7C,
0x75, 0x6E, 0x7E, 0x6E, 0x2F, 0x77, 0x4F, 0x7A, 0x71, 0x43,
0x2B, 0x26, 0x89, 0xFE, 0x00
};

char s1[] = "qasxcytgsasxcvrefghnrfghnjedfgbhn";
for (int i = 0; i <= 33; ++i )
    s1[i] ^= 2 * i + 65;
for(int i = 0; i < strlen(s1); i++){
    s1[i] = s1[i] ^ s2[i];
}
cout << s1;
```

Flag: `flag{c0n5truct0r5_functi0n_in_41f}`

### Rev - IgniteMe

**Files:** [igniteme.zip](/assets/ctf-files/adworld-reversing/igniteme.zip)

The check XORs the input with a table, applies `(x - 72) ^ 0x55`, and then shifts the case of letters. I extracted the 32 byte table from IDA (export result), XORed it with the 24 byte constant `GONDPHyGjPEKruv{{pj]X@rF`, reversed the arithmetic, and then lowercased the uppercase letters to match the case shift. The `EIS{...}` wrapper is added around the result.

```cpp
unsigned char ida_chars[] ={
    13,  19,  23,  17,   2,   1,  32,  29,  12,   2,
    25,  47,  23,  43,  36,  31,  30,  22,   9,  15,
    21,  39,  19,  38,  10,  47,  30,  26,  45,  12,
    34,   4
};
char flag[5] = {'E', 'I', 'S', '{', '}'};
char fl[100] = "";
char c[] = "GONDPHyGjPEKruv{{pj]X@rF";
for(int i = 0; i < 24; i++){
    fl[i] = c[i] ^ ida_chars[i];
    fl[i] = (fl[i] - 72) ^ 0x55;
}
for(int i = 0; i < 24; i++){
    if (fl[i] >= 'A' && fl[i] <= 'Z' )
        fl[i] += 32;
}
cout << flag[0] << flag[1] << flag[2] << flag[3] <<  fl << flag[4];
```

Flag: `EIS{wadx_tdgk_aihc_ihkn_pjlm}`

### Rev - crypt

**Files:** [crypt.zip](/assets/ctf-files/adworld-reversing/crypt.zip)

The binary XORs a 22 byte array with `0x22` before comparing. My `sol.cpp` applies that XOR to the array extracted from IDA.

```cpp
char ida_chars[100] ={
158, 231,  48,  95, 167,   1, 166,  83,  89,  27,
10,  32, 241, 115, 209,  14, 171,   9, 132,  14,
141,  43};
for(int i = 0; i < strlen(ida_chars); i++)
    ida_chars[i] ^= 0x22;
cout << ida_chars;
```

Status: flag not recorded. When I applied only this XOR to the array, the output was not printable text, so this script is an intermediate step and there is no flag file for this challenge. I am not listing a flag for it.

## Strided and table based decoders

### Rev - Reversing-x64Elf-100

**Files:** [reversing-x64elf-100.zip](/assets/ctf-files/adworld-reversing/reversing-x64elf-100.zip)

The check builds 12 characters by reading from three strings in turn, taking every second character of each string, and subtracting 1. The index into the strings is `2 * (i / 3)` and the string is chosen by `i % 3`.

```cpp
v3[0] = (__int64)"Dufhbmf";
v3[1] = (__int64)"pG`imos";
v3[2] = (__int64)"ewUglpt";

for (i = 0; i <= 11; ++i)
     cout <<  char(*(char*)(v3[i % 3] + 2 * (i / 3)) - 1);
```

Flag: `Code_Talkers`

### Rev - game

**Files:** [game.zip](/assets/ctf-files/adworld-reversing/game.zip)

The flag is stored in the binary as two encoded arrays, and a third array of 57 bytes is used as a keystream. The first 22 bytes are XORed with the first 22 keystream bytes and with `0x13`. The next 34 bytes continue through the keystream and are XORed the same way. I copied the arrays from the decompiler and ran the same loops.

```cpp
int i;
for (i = 0; i < 22; ++i )
{
    v3[i] ^= v6[i];
    v3[i] ^= 0x13u;
}
for (int j = 0; j < 34; ++j )
{
    v4[j] ^= v6[i];
    v4[j] ^= 0x13u;
    i++;
}
cout << v3 << v4;
```

The full byte arrays are in the script, they are long so I only show the decoding loops here.

Flag: `zsctf{T9is_tOpic_1s_v5ry_int7resting_b6t_others_are_n0t}`

### Rev - srm-50

**Files:** [srm-50.zip](/assets/ctf-files/adworld-reversing/srm-50.zip)

The program rebuilds a 26 character key in a buffer by assigning individual bytes (`v11[0]`, `v11[1]`, and so on). I reproduced the assignments in Python to see the key.

```python
v11 = bytearray(b"XXXXXXXXXXXXXXXXXXXXXXXXXX")
v11[0] = ord("C")
v11[1] = ord("Z")
v11[2] = ord("9")
v11[3] = ord("d")
v11[4] = ord("m")
v11[5] = ord("q")
v11[6] = ord("4")
v11[7] = ord("c")
v11[9] = ord("g")
v11[10] = ord("9")
v11[11] = ord("G")
v11[12] = ord("7")
v11[13] = ord("b")
v11[14] = ord("A")
v11[15] = ord("X")
v11[8] = ord("8")
print(v11)
```

Status: the script only reconstructs the first 16 bytes of the key and I did not record a flag, so I am not giving one here.

## Reproducing logic from source or from a thread

### Rev - open-source

**Files:** [open-source.zip](/assets/ctf-files/adworld-reversing/open-source.zip)

This one comes with C source. The program requires `first == 0xcafe`, a `second` value with `second % 5 != 3` and `second % 17 == 8`, and the third argument must be `h4cky0u`. Then it prints a hash. I did not need a valid `second` beyond its modulus, because only `second % 17` enters the hash and that is fixed to 8. Reproducing the formula gives the key. Using `25` as the second value satisfies the checks since `25 % 17 == 8` and `25 % 5 == 0`.

```cpp
int first = 0xcafe;
int second = 25;
char s[] = "h4cky0u";
unsigned int hash = first * 31337 + (second % 17) * 11 + strlen(s) - 1615810207;
printf("Get your key: ");
printf("%x\n", hash);
```

Flag: `c0ffee`

### Rev - parallel-comparator-200

**Files:** [parallel-comparator-200.zip](/assets/ctf-files/adworld-reversing/parallel-comparator-200.zip)

The program takes 20 characters and compares them in parallel threads. Each thread checks that one character equals a base letter plus a delta from a table. The base is a single lowercase letter shared by all positions, so I brute forced the 26 possible bases and applied the delta table to each. I also kept a small `thread.c` test program to confirm how pthread creates a thread that runs alongside the main one.

```python
d = [0, 9, -9, -1, 13, -13, -4, -11, -9, -1, -7, 6, -13, 13, 3, 9, -13, -11, 6, -7]
for j in range(26):
    flag = ""
    for i in range(20):
        fl = (j % 26) + 97
        flag += chr(fl + d[i])
    print(flag)
```

Only one of the 26 lines is a readable phrase, the one using base letter `l`.

Flag: `lucky_hacker_you_are`

## Runtime decoded code

### Rev - BABYRE

**Files:** [babyre.zip](/assets/ctf-files/adworld-reversing/babyre.zip)

The main function reads 14 bytes of input and calls `judge(s)`. In IDA, `judge` showed up as an array of values and not as code. The call is written as `(*(unsigned int (__fastcall **)(char *))judge)(input_flag)`, which means `judge` is data that is called as a function with a `char *` argument, returning `unsigned int`.

![start](/assets/img/ctf/adworld-reversing/start.png)

![judge](/assets/img/ctf/adworld-reversing/judge.png)

Before asking for the flag, the program decodes the bytes of `judge()` in place:

```c
  for ( i = 0; i <= 181; ++i )
    judge[i] ^= 0xCu;
  printf("Please input flag:");
```

Since this happens at runtime, I patched the 182 bytes in the IDA database with an IDAPython script that applies the same XOR.

```python
st = 0x600b00
for i in range(182):
    patch_byte(st + i, ord(get_bytes(st + i, 1))^0xC)
```

![patch](/assets/img/ctf/adworld-reversing/patch.png)

After patching, the original bytes are back. Pressing `c` turns them into code and pressing `p` makes a function out of them, so the decompiler can show the check.

![makecode](/assets/img/ctf/adworld-reversing/makecode.png)

![makefunc](/assets/img/ctf/adworld-reversing/makefunc.png)

From there I reversed the check. The first five bytes are `fmcd` and `127`, each XORed with its index. The rest is `k7d;V`;np`, XORed with a counter that continues from the previous loop.

```cpp
char v2[100];
v2[0] = 'f';
v2[1] = 'm';
v2[2] = 'c';
v2[3] = 'd';
v2[4] = 127;
char v3[10] = "k7d;V`;np";
int i;
for (i = 0; i < strlen(v2); ++i )
    v2[i] ^= i;

for(int j = 0; j < strlen(v3); i++, j++)
    v3[j] ^= i;

cout << v2 << v3;
```

Two notes from my own mistakes on this one. First, I spent a long time on the call expression before understanding that `judge` is the function itself, built at runtime from data. Second, in IDA 7.5 the pointer was treated as plain data, so I had to press `c` and then `p` at the start of `judge` before the decompiler would work on it.

Flag: `flag{n1c3_j0b}`

## Unpacking

### Rev - simple-unpack

**Files:** [simple-unpack.zip](/assets/ctf-files/adworld-reversing/simple-unpack.zip)

The binary is packed with UPX. Running `upx -d <file>` restores the original executable, and the flag then shows up in the unpacked binary.

Flag: `flag{Upx_1s_n0t_a_d3liv3r_c0mp4ny}`

## Solved without a recorded script

These four have a recorded flag but no solve script in my notes, so I only list the flag.

### Rev - easyRE1

**Files:** [easyre1.zip](/assets/ctf-files/adworld-reversing/easyre1.zip)

Flag: `flag{db2f62a36a018bce28e46d976e3f9864}`

### Rev - lucknum

**Files:** [lucknum.zip](/assets/ctf-files/adworld-reversing/lucknum.zip)

Flag: `flag{c0ngr@tul@ti0n_f0r_luck_numb3r}`

### Rev - Shuffle

**Files:** [shuffle.zip](/assets/ctf-files/adworld-reversing/shuffle.zip)

Flag: `SECCON{Welcome to the SECCON 2014 CTF!}`

### Rev - insanity

**Files:** [insanity.zip](/assets/ctf-files/adworld-reversing/insanity.zip)

Flag: `9447{This_is_a_flag}`

## Static analysis and replay - getit

A 64-bit Linux ELF that builds a flag string and writes it into the file `/tmp/flag.txt`, then deletes the file.

The binary never prints the flag. It holds the 32 character string `c61b68366edeb7bdce3c6820314b7498` at 0x6010a0 and a template `SharifCTF{????...????}` at 0x6010e0. The first loop sets `buf[i+10] = s[i] + 1` when `i` is odd and `s[i] - 1` when `i` is even. The second loop only shuffles the bytes into the file through a table of offsets and then removes the file, so the finished template is the flag.

```python
s = b'c61b68366edeb7bdce3c6820314b7498'
b = bytearray(b'SharifCTF{' + b'?'*32 + b'}')
for i in range(32):
    b[i+10] = s[i] + (1 if i & 1 else -1)
print(b.decode())
```

Flag: `SharifCTF{b70c59275fcfa8aebf2d5911223c6589}`

**Files:** [getit.zip](/assets/ctf-files/adworld-reversing/getit.zip)

## XOR decode - logmein

A stripped 64-bit Linux ELF that asks for a password and compares it with a XOR-encoded constant.

The program reads up to 32 characters, checks that the length matches the stored 17 byte blob, then for each index tests `input[i] == blob[i] ^ key[i % 7]`. The key is the string `harambe` at 0x4008d0 and the blob is `:"AL_RT^L*.?+6/46` at 0x4008b0. XOR the blob with the repeating key to get the password.

```python
blob = b':"AL_RT^L*.?+6/46'
print(''.join(chr(c ^ ord('harambe'[i % 7])) for i, c in enumerate(blob)))
```

Flag: `RC3-2016-XORISGUD`

**Files:** [logmein.zip](/assets/ctf-files/adworld-reversing/logmein.zip)

## Wide string decrypt - no-strings-attached

A 32-bit Linux ELF that reads a line with `fgetws` and compares it to a decrypted wide string. The folder also holds an empty `sol.cpp`.

`strings` shows nothing useful because everything is stored as 4 byte wide characters. `authenticate` calls `decrypt(enc, key)` with `enc` at 0x8048aa8 and the 5 character key at 0x8048a90 (0x1401 to 0x1405). `decrypt` subtracts the key from the encrypted characters one by one, cycling the key. The decrypted string is then passed to `wcscmp` against the user input, so decrypting it by hand gives the answer.

```python
# enc = wide ints at 0x8048aa8 (until 0), key = wide ints at 0x8048a90
print(''.join(chr(c - key[i % len(key)]) for i, c in enumerate(enc)))
```

Flag: `9447{you_are_an_international_mystery}`

**Files:** [no-strings-attached.zip](/assets/ctf-files/adworld-reversing/no-strings-attached.zip)

## Static strings - Hello, CTF

A 32-bit Windows console crackme that asks for a serial and prints `success!` or `wrong!`.

The binary reads a serial of at most 17 characters, formats every character with `%02x` into a hex string, and compares that string to a constant copied from 0x408068. That constant is `437261636b4d654a757374466f7246756e`. Decoding it from hex gives the serial. I did not run the exe, the comparison logic was read from the disassembly.

```python
print(bytes.fromhex('437261636b4d654a757374466f7246756e'))
```

Flag: `CrackMeJustForFun`

**Files:** [hello-ctf.zip](/assets/ctf-files/adworld-reversing/hello-ctf.zip)

## Static strings - re1

A 32-bit Windows console program that prompts for a flag and does a plain string compare.

At the start of the function the program copies 24 bytes from 0x413e34 onto the stack, prints the prompts, reads the user input with `scanf` and walks both strings with a byte by byte comparison. The copied bytes are the plaintext `DUTCTF{We1c0met0DUTCTF}` in `.rdata`, so the flag is stored in the clear.

```
.rdata 0x413e34: "DUTCTF{We1c0met0DUTCTF}"
```

Flag: `DUTCTF{We1c0met0DUTCTF}`

**Files:** [re1.zip](/assets/ctf-files/adworld-reversing/re1.zip)

## Crackme run - re2-cpp-is-awesome

A stripped 64-bit C++ ELF that takes the flag as `argv[1]` and walks the argument with a `std::string` iterator.

For each character the program compares `arg[i]` with `table[idx[i]]`, where `table` is the long string at 0x400e58 and `idx` is an array of 31 ints at 0x6020c0. Any mismatch prints `Better luck next time`. Picking the 31 characters named by `idx` out of the table rebuilds the flag. I confirmed it by running the binary with that argument, which printed `You should have the flag by now`.

```python
s = b"L3t_ME_T3ll_Y0u_S0m3th1ng_1mp0rtant_A_{FL4G}_W0nt_b3_3X4ctly_th4t_345y_t0_c4ptur3_H0wev3r_1T_w1ll_b3_C00l_1F_Y0u_g0t_1t"
print(''.join(chr(s[i]) for i in idx))
```

Flag: `ALEXCTF{W3_L0v3_C_W1th_CL45535}`

**Files:** [re2-cpp-is-awesome.zip](/assets/ctf-files/adworld-reversing/re2-cpp-is-awesome.zip)

## Static decode - elrond32

A 32-bit Linux ELF (`rev300`) that takes one command line argument and, if it is the right key, prints the flag.

`main` calls a recursive checker with `argv[1]` and state 0. Each state uses a jump table to pick one required character, and the next state is `((state + 1) * 7) % 11`. Starting at 0 the states run 0, 7, 1, 3, 6, 5, 9, 4 and then 2, which accepts. The required characters for those states are `i`, `s`, `e`, `n`, `g`, `a`, `r`, `d`, so the key is `isengard`. After the check passes, the printer XORs 33 dwords stored at `0x8048760` with the key bytes, repeating the 8-byte key. I decoded the table in Python without running the binary because the sandbox has no 32-bit loader.

```python
t = struct.unpack('<33I', data[0x760:0x760+132])
print(''.join(chr(t[i] ^ ord('isengard'[i % 8])) for i in range(33)))
```

Flag: `flag{s0me7hing_S0me7hinG_t0lki3n}`

**Files:** [elrond32.zip](/assets/ctf-files/adworld-reversing/elrond32.zip)

## Static decode - easyxor

A 64-bit Windows console program that reads a line and compares an encoded form of it against a table. I only analysed it statically and did not run it.

For every input character `main` XORs it with the 4-byte key `SCNU` (indexed by position modulo 4), then writes that many `1` bytes into a buffer followed by one `0` byte, so each character is stored as a run length. The rest of the 0xA00-byte buffer is filled with `0xFF` and compared byte by byte to a constant table at `0x403080`. Reversing it means counting the runs of `1` bytes in that table and XORing each count with the key.

```python
runs = [53,47,47,50,40,20,39,59,61,112,60,10,61,115,58,10,31,115,61,102,33,28,109,40]
print(bytes(c ^ b'SCNU'[i % 4] for i, c in enumerate(runs)))
```

Flag: `flag{Winn3r_n0t_L0s3r_#}`

**Files:** [easyxor.zip](/assets/ctf-files/adworld-reversing/easyxor.zip)

## Static decode - simple-check-100

A small 64-bit ELF (a 32-bit ELF and a Windows build of the same task are included) that asks for a key and, if the key passes, prints a decoded string.

`check_key` adds up the first five 32-bit integers of the input and requires the sum to be `0xdeadbeef`, so many different keys work. When the check passes, `interesting_function` takes 28 bytes stored on the stack in `main`, XORs each dword with `0xdeadbeef`, and XORs the resulting bytes (high byte first) with 28 bytes from `.rodata` at `0x4009d0`. The output does not depend on which valid key was typed. I decoded it in Python and then confirmed it by running the ELF with a key whose five dwords sum to `0xdeadbeef`.

```python
for i in range(7):
    v = struct.unpack('<I', data[i*4:i*4+4])[0] ^ 0xdeadbeef
    b = struct.pack('<I', v)
    for j in (3, 2, 1, 0):
        out += chr(rodata[i*4 + j] ^ b[j])
```

Flag: `flag_is_you_know_cracking!!!`

**Files:** [simple-check-100.zip](/assets/ctf-files/adworld-reversing/simple-check-100.zip)

## Static strings - re1-100

A 64-bit ELF (`RE100`) that forks a child, sends it the typed key through a pipe, and checks the key there. It also has ptrace based anti-debug checks, which a static read ignores.

The child requires a 42 character key shaped like `{...}`. It checks that bytes 1 to 10 equal `53fc275d81` and bytes 31 to 40 equal `4938ae4efd`. Then `confuseKey` cuts the key into four 10 character pieces and rebuilds it as `{` + piece at 21 + piece at 31 + piece at 1 + piece at 11 + `}`. That result is compared with the constant `{daf29f59034938ae4efd53fc275d81053ed5be8c}`. Undoing the shuffle gives piece 1 = `53fc275d81`, piece 11 = `053ed5be8c`, piece 21 = `daf29f5903` and piece 31 = `4938ae4efd`, which agrees with the two direct checks. I did not get a clean live run because the fork and ptrace logic stalls in the sandbox, so this comes from the disassembly.

Flag: `{53fc275d81053ed5be8cdaf29f59034938ae4efd}`

**Files:** [re1-100.zip](/assets/ctf-files/adworld-reversing/re1-100.zip)

## Crackme run - re-for-50-plz-50

A statically linked little-endian MIPS ELF (`mipsel`) that takes the flag as `argv[1]`.

`main` loops 31 times and compares `argv[1][i] ^ 0x37` with byte `i` of a table at `0x4a3720`. A mismatch calls the failure path. XORing the table with `0x37` gives the flag. I ran the binary under `qemu-mipsel-static` with that value and it printed the success message.

```python
t = data[0x93720:0x93720 + 31]
print(''.join(chr(b ^ 0x37) for b in t))
```

```
$ qemu-mipsel-static ./re-for-50-plz-50 'TUCTF{but_really_whoisjohngalt}'
C0ngr4ssulations!! U did it.
```

Flag: `TUCTF{but_really_whoisjohngalt}`

**Files:** [re-for-50-plz-50.zip](/assets/ctf-files/adworld-reversing/re-for-50-plz-50.zip)

## Base58 decode - testre

A stripped 64-bit Linux ELF that takes a 16 byte value and compares its Base58 encoding against a hard coded string.

The binary contains the Bitcoin Base58 alphabet and a key string `fake_secret_makes_you_annoyed`. The key is a decoy. It is only used in a XOR and add loop whose result is overwritten before it is ever used. The real check calls `strncmp` six times on pieces of the encoded output, and the pieces sit in `.rodata` as `D9`, `Mp`, `MR`, `cS9N`, `9iHjM` and `LTdA8YS`. Their offsets in the encoded buffer (0, 0x14, 0x12, 2, 6, 0xb) put them in order as `D9cS9N9iHjMLTdA8YSMRMp`, which is 22 characters, the right length for 16 bytes.

Decoding that string as a big Base58 number gives the 16 input bytes directly.

```python
A="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
n=0
for c in "D9cS9N9iHjMLTdA8YSMRMp": n=n*58+A.index(c)
print(n.to_bytes(16,'big'))   # b'base58_is_boring'
```

Running the ELF with `base58_is_boring` on stdin prints `correct!`.

Flag: `base58_is_boring`

**Files:** [testre.zip](/assets/ctf-files/adworld-reversing/testre.zip)

## Shellcode strings - tt3441810

A small text file that is a hex dump of raw x86-64 shellcode starting at 0x400080. It does a series of `write` syscalls and then `exit`.

Each block is `push imm` followed by `write(1, rsp, 2)`. The pushed 16 bit immediates are ASCII pairs, so the output can be read straight out of the bytes without running anything. The pairs in order are `fl`, `ag`, `{p`, `op`, `po`, `pr`, `et`, then `}` and a newline.

```
68 66 6C   -> "fl"
68 61 67   -> "ag"
68 7B 70   -> "{p"
68 6F 70   -> "op"
68 70 6F   -> "po"
68 70 72   -> "pr"
68 65 74   -> "et"
68 7D 0A   -> "}\n"
```

Flag: `flag{poppopret}`

**Files:** [tt3441810.zip](/assets/ctf-files/adworld-reversing/tt3441810.zip)

## Reverse and XOR - EasyRE

A 32-bit Windows console program that reads a string, transforms it and compares it with a constant.

The input must be exactly 24 characters. The program copies it into a global buffer in reverse order, then for every byte does `inc` followed by `xor 6`. The result is compared with the 24 bytes at `0x402124`. A plain `flag{NP2NiaNXx1ClGYVQ50}` string sits in `.rdata` next to it, but that one is a decoy because it is never used in the comparison. One byte of the target is 0x7f, which a hex dump shows as a dot, so the target has to be read as raw bytes.

To invert the check, XOR each target byte with 6, subtract 1, then reverse the result. The file was analysed statically and not run.

```python
t=bytes.fromhex("78497243 6a7e3c72 7c327457 73763350 74497f7a 6e646b61".replace(" ",""))
print(bytes(((c^6)-1)&255 for c in t)[::-1])
# b'flag{xNqU4otPq3ys9wkDsN}'
```

Flag: `flag{xNqU4otPq3ys9wkDsN}`

**Files:** [easyre.zip](/assets/ctf-files/adworld-reversing/easyre.zip)

## Lookup table decode - Replace

A UPX packed 32-bit Windows console program that asks for a key and checks it with a byte substitution table.

After `upx -d` the check function is easy to read. The key must be 35 characters. For each character `c` the program takes `table[c]`, where the 256 byte table lives at `0x4021a0`, and compares it with `hexpair ^ 0x19`. The hex pairs come from the 70 character string `2a49f69c38395cde96d6de96d6f4e025484954d6195448def6e2dad67786e21d5adae6` at `0x402150`. The table is a permutation of all 256 values, so every target byte maps back to exactly one character. I only unpacked and read the file and did not run it.

```python
t=[int(s[2*i:2*i+2],16)^0x19 for i in range(35)]
inv={table[c]:c for c in range(256)}
print(''.join(chr(inv[x]) for x in t))
```

Flag: `flag{Th1s_1s_Simple_Rep1ac3_Enc0d3}`

**Files:** [replace.zip](/assets/ctf-files/adworld-reversing/replace.zip)

## Base64 and XOR - ReverseMe-120

A 32-bit Windows console program that prints `please input your flah:`, reads a line, and prints `correct` or `wrong`.

The program Base64 decodes the input with a standard table (checked against the 128 byte table at `0x414e40`), XORs every decoded byte with `0x25` (the SSE loop uses sixteen copies of `0x25`), and compares the result with the string at `0x414edc`. Most of the code in the binary is junk that never affects this path. To get the accepted input, XOR the target with `0x25` and Base64 encode it. The file was analysed statically and not run.

```python
import base64
s=b"you_know_how_to_remove_junk_code"
print(base64.b64encode(bytes(c^0x25 for c in s)))
# b'XEpQek5LSlJ6TUpSelFKeldASEpTQHpPUEtOekZKQUA='
```

The program accepts the Base64 string above. The hidden plaintext it decodes to is the flag text.

Flag: `you_know_how_to_remove_junk_code`

**Files:** [reverseme-120.zip](/assets/ctf-files/adworld-reversing/reverseme-120.zip)

## Emulation - Newbie_calculations

A 32-bit Windows console program with no input. It prints `Your flag is:` and then `CTF{`, 32 characters computed at run time, and `}`.

Natively the program would take a very long time. The main function builds 32 values through three helper functions at `0x401000`, `0x401100` and `0x401220`, and each helper is written as a counting loop that runs billions of times (a loop counter that starts at a negative number and is decremented until it wraps to zero). Reading the loops shows what each one really computes on its first argument `*p` and second argument `n`, with 32-bit wraparound. The rest of each function is dead arithmetic.

- `0x401000` sets `*p = *p + n`
- `0x401100` sets `*p = *p * n`
- `0x401220` sets `*p = *p - n`

I did not run the exe. Instead I loaded the PE image into a CPU emulator, replaced the three helpers with these one line operations, stubbed out the print and cookie check calls, and ran `main` from `0x4012f0`. A hook on the `%c` print call collected the 32 characters.

```
helpers: add / mul / sub on *p (mod 2^32)
emulate main -> daf8f4d816261a41a115052a1bc21ade
```

Flag: `CTF{daf8f4d816261a41a115052a1bc21ade}`

**Files:** [newbie-calculations.zip](/assets/ctf-files/adworld-reversing/newbie-calculations.zip)

## Static analysis - Mysterious

A 32-bit Windows GUI program that reads a string from an edit box and shows a message box saying "well done" if the string passes a few checks.

The dialog procedure calls the CRT atoi on the input and adds 1, then requires the result to be 0x7b (123). It also requires the characters at offsets 3, 4 and 5 to be `x`, `y` and `z`. The flag is built at run time with strcat from pieces stored in .rdata: the string `flag`, then `{`, then the number printed with itoa, then `_`, then the constant `Buff3r_0v3rf|0w`, then `}`. The valid input is therefore `122xyz`, because atoi stops at the first letter and returns 122.

```
atoi(input) + 1 == 123      -> input starts with 122
input[3..5] == "xyz"        -> 122xyz
flag = "flag" + "{" + itoa(123) + "_" + "Buff3r_0v3rf|0w" + "}"
```

Flag: `flag{123_Buff3r_0v3rf|0w}`

**Files:** [mysterious.zip](/assets/ctf-files/adworld-reversing/mysterious.zip)

## Caesar and SHA1 hint - answer_to_everything

A tiny x86-64 ELF (named main.exe) that asks for a number and prints a hint if the number is 42.

`not_the_flag` compares the input against 0x2a (42). On a match it prints `Cipher from Bill`, `Submit without any tags` and `#kdudpeh`. Any other input prints `YOUSUCK`. The printed text is the real data. `kdudpeh` is a Caesar shift of 3 over the word `harambe`, but the hint "Cipher from Bill" and "submit without any tags" point to hashing the string `kdudpeh` with SHA1 and submitting the digest. The binary itself only prints the hint, so the SHA1 step comes from the hint text and not from a check in the code.

```
$ echo -n kdudpeh | sha1sum
80ee2a3fe31da904c596d993f7f1de4827c1450a
```

Flag: `flag{80ee2a3fe31da904c596d993f7f1de4827c1450a}`

**Files:** [answer-to-everything.zip](/assets/ctf-files/adworld-reversing/answer-to-everything.zip)

## Crackme run - crazy

A C++ ELF that asks for a 32 character key, transforms it, compares it with a hard coded MD5-looking hex string and then prints the flag.

The `HighTemplar` class keeps two copies of the input. `calculate` transforms the first copy byte by byte with `((c ^ 0x50) + 0x17)` and then `((c ^ 0x13) + 0xb)`. `getSerial` compares each transformed byte with the constant `327a6c4304ad5938eaf0efb6cc3e53dc` stored in .rodata. The second, untouched copy is what `getFlag` prints inside `flag{}`. The main function also runs `func1`, `func2` and `func3` but they only work on copies and do not change the result. Each byte is inverted by brute forcing the 256 possible values against the formula, then the key is run through the program to confirm.

```python
t = b'327a6c4304ad5938eaf0efb6cc3e53dc'
key = ''.join(chr(next(x for x in range(256)
      if ((((x ^ 0x50) + 0x17) & 255) ^ 0x13) + 0xb & 255 == c)) for c in t)
# tMx~qdstOs~crvtwb~aOba}qddtbrtcd
```

Running `./crazy` with that key prints `Pass 0` to `Pass 31` and then the flag line.

Flag: `flag{tMx~qdstOs~crvtwb~aOba}qddtbrtcd}`

**Files:** [crazy.zip](/assets/ctf-files/adworld-reversing/crazy.zip)

## Crackme run - hackme

A statically linked, stripped x86-64 ELF that asks for a password and prints `Congras` or `Oh no!`.

The check function requires a length of exactly 22. It then loops 10 times and each time picks a random index `r = rand() % 22`. For that index it builds a byte by running the generator `x = x * 0x6d01788d + 0x3039` (r+1) times starting from 0, and requires `table[r] == input[r] ^ (x & 0xff)`. The table is 22 bytes at 0x6b4270. The random index does not matter because every index has a fixed expected value, so each byte of the password can be recovered directly.

```python
t = bytes.fromhex('5ff25e8b4e0ea3aac793813d5f74a309912b49289367')
s = ''
for i in range(22):
    x = 0
    for _ in range(i + 1):
        x = (x * 0x6d01788d + 0x3039) & 0xffffffff
    s += chr(t[i] ^ (x & 255))
print(s)
```

Running the binary with this string prints `Congras`.

Flag: `flag{d826e6926098ef46}`

**Files:** [hackme.zip](/assets/ctf-files/adworld-reversing/hackme.zip)

## Static analysis - notsequence

A stripped 32-bit ELF that reads integers until a 0 and runs two checks on them. The flag is the MD5 of the input numbers written without spaces or newlines.

Check 1 treats the input as a triangle. Row k has k+1 numbers and the numbers in row k must add up to 2^k, and the check stops at the first row that starts with 0. Check 2 requires exactly 20 rows (0x14) and for every column i it requires the entry in the last row to equal the sum of column i-1 over the earlier rows. Both conditions hold for Pascal's triangle by the row sum identity and the hockey stick identity. I rebuilt both checks in Python and confirmed that rows 0 to 19 of Pascal's triangle followed by a 0 pass them. The 32-bit loader is not available in the sandbox, so the binary itself was not run. The binary accepts more than one triangle, and Pascal's triangle is the intended one.

```python
from math import comb
import hashlib
v = [comb(k, m) for k in range(20) for m in range(k + 1)]
print(hashlib.md5(''.join(map(str, v)).encode()).hexdigest())
```

Flag: `RCTF{37894beff1c632010dd6d524aa9604db}`

**Files:** [notsequence.zip](/assets/ctf-files/adworld-reversing/notsequence.zip)

## Patching a loop bound - secret-galaxy-300

The challenge ships a 64-bit ELF, a 32-bit ELF and a Windows build of the same program. It prints a "galaxy database" with five galaxies.

The strings contain a sixth name, `DARK SECRET GALAXY`, that never shows up in the output. `fill_starbase` and `print_starbase` both loop with `cmp [counter], 4 ; jle`, so they only handle indexes 0 to 4, even though the pointer table in `.data` holds six names. Each entry stores a name pointer and a `random()` value with no seed call, so the numbers are the default glibc sequence. Raising both loop bounds from 4 to 5 makes the program fill and print the hidden entry.

```
# patch two bytes in a copy of the 64-bit ELF
0x400868: 83 7d e4 04  ->  83 7d e4 05
0x40094f: 83 7d fc 04  ->  83 7d fc 05
$ ./patched
...
DARK SECRET GALAXY |  IS NOT INHABITED | 424238335
```

The distance of the hidden galaxy is the flag.

Flag: `424238335`

**Files:** [secret-galaxy-300.zip](/assets/ctf-files/adworld-reversing/secret-galaxy-300.zip)

## RSA with a factored modulus - SignIn

A 64-bit PIE ELF that reads a flag with `scanf("%99s")` and uses GMP to check it.

The program turns the input into a hex string, treats it as a big integer m, and computes `m^65537 mod n`. It then compares the result with a hard coded hex value. The modulus is a 256-bit decimal number stored in the binary, so the check is plain textbook RSA. The modulus factors into two 128-bit primes, which gives the private exponent.

```python
p = 282164587459512124844245113950593348271
q = 366669102002966856876605669837014229419
n = 103461035900816914121390101299049044413950405173712170434161686539878160984549
assert p * q == n
c = 0xad939ff59f6e70bcbfad406f2494993757eee98b91bc244184a377520d06fc35
d = pow(65537, -1, (p - 1) * (q - 1))
print(bytes.fromhex(format(pow(c, d, n), 'x')))
```

Flag: `suctf{Pwn_@_hundred_years}`

**Files:** [signin.zip](/assets/ctf-files/adworld-reversing/signin.zip)

## Table lookup inversion - 流浪者

A 32-bit MFC GUI program that asks for a password and shows a good or bad message box.

The code maps each input character to an index. Digits give `c - 0x30`, lowercase letters give `c - 0x57` and uppercase letters give `c - 0x1d`, so the indexes run from 0 to 61. Each index selects a character from the table `abcdefghiABCDEFGHIJKLMNjklmn0123456789opqrstuvwxyzOPQRSTUVWXYZ`. The resulting string is passed to `strcmp` against `KanXueCTF2019JustForhappy`. To solve it, find each target character in the table and convert its position back to the input character.

```python
T = "abcdefghiABCDEFGHIJKLMNjklmn0123456789opqrstuvwxyzOPQRSTUVWXYZ"
tg = "KanXueCTF2019JustForhappy"
inv = lambda i: chr(0x30+i) if i < 10 else chr(0x57+i) if i < 36 else chr(0x1d+i)
print(''.join(inv(T.index(c)) for c in tg))
```

Flag: `j0rXI4bTeustBiIGHeCF70DDM`

**Files:** [liu-lang-zhe.zip](/assets/ctf-files/adworld-reversing/liu-lang-zhe.zip)

## Reading Java source - Guess-the-Number

A jar with a Procyon-decompiled `guess.java` and a Python port in `s.py`. The program takes an integer argument and prints the flag if it is right.

The check is `1545686892 / 5 == guess_number`, so the number to pass is 309137378. When it matches, the program prints the XOR of two hex constants. The decompiled source and `s.py` both show this, so the flag can be computed directly without running the jar.

```python
print(format(0x4b64ca12ace755516c178f72d05d7061 ^ 0xecd44646cfe5994ebeb35bf922e25dba, 'x'))
```

Flag: `a7b08c546302cc1fd2a4d48bf2bf2ddb`

**Files:** [guess-the-number.zip](/assets/ctf-files/adworld-reversing/guess-the-number.zip)

## Python bytecode - re4-unvm-me

A Python 2.7 `.pyc` that asks for a flag of at most 69 characters whose length is a multiple of 5.

Decompiling the file shows the flag is split into 5 character chunks. Each chunk's MD5 hex digest, read as an integer, must equal one of 13 constants. The decompiler prints the constants wrongly, so they were read from `co_consts` with `xdis`. Each chunk is only 5 characters, so brute force works. A C program with OpenSSL MD5 tried every 5 character string over letters, digits and common symbols (about 1.7 billion candidates) and matched all 13 targets in about two minutes on 22 cores.

```
0 ALEXC   1 TF{dv   2 5d4s2   3 vj8nk   4 43s8d   5 8l6m1   6 n5l67
7 ds9v4   8 1n52n   9 v37j4  10 81h3d  11 28n4b  12 6v3k}
```

Flag: `ALEXCTF{dv5d4s2vj8nk43s8d8l6m1n5l67ds9v41n52nv37j481h3d28n4b6v3k}`

**Files:** [re4-unvm-me.zip](/assets/ctf-files/adworld-reversing/re4-unvm-me.zip)

## Python bytecode - bad_python

A Python 3.6 `.pyc` that asks for a 32 character flag and compares it against eight encrypted 32-bit words.

The file has a damaged header. The magic number reads `33 0d 00 00` instead of `33 0d 0d 0a`, and the first byte of the code object (the `c` type marker, `0xe3`) is zeroed. The `.bak` copy shows the same damage, so nothing can be copied from it. After patching those bytes the file decompiles cleanly with uncompyle6. The code is a TEA style cipher with a custom delta (195935983), 32 rounds and the key `[255, 187, 51, 68]`. It encrypts the flag in four blocks of eight characters and checks the result against the `enc` list. Python operator precedence matters here, because `+` binds tighter than `^`, so each round is `((v1<<4 ^ v1>>7) + v1) ^ (sum + k[...])`.

Decryption runs the rounds backwards with the same expressions. I checked every block by re-encrypting the recovered plaintext and comparing with `enc`.

```python
# header fix
d[2:4] = b'\r\n'; d[12] = 0xe3

def dec(v0, v1):
    s = (delta*32) & M
    for _ in range(32):
        v1 = (v1 - ((((v0<<4)&M) ^ (v0>>7)) + v0 ^ (s + k[s>>9&3]))) & M
        s = (s - delta) & M
        v0 = (v0 - ((((v1<<4)&M) ^ (v1>>7)) + v1 ^ (s + k[s&3]))) & M
    return v0, v1
```

Flag: `flag{Th1s_1s_A_Easy_Pyth0n__R3veRse_0}`

**Files:** [bad-python.zip](/assets/ctf-files/adworld-reversing/bad-python.zip)

## Maze solve and run - reverse_re3

A stripped x86-64 Linux ELF that reads a string of moves and prints `success! the flag is flag{md5(your input)}` when the moves finish a three level maze.

The maze lives in `.data` as 3 levels of 15 by 15 dwords, indexed as `level*225 + row*15 + col`. The values are 1 for a walkable cell, 3 for the player, 4 for the exit and 0 for a wall. The handlers for `w`, `s`, `a` and `d` change the row or column by one. A move is allowed only when the target cell is 1, and a move into a 4 cell finishes the level. The binary succeeds when the third level is finished, so the input is the concatenated path through all three levels.

I dumped the three grids from the file, ran a breadth first search from the 3 cell to the 4 cell on each level, and joined the paths. Running the binary with that string prints the success message, and the flag is the MD5 of the string.

```
ddsssddddsssdssdddddsssddddsssaassssdddsddssddwddssssssdddssssdddss
md5 = aeea66fcac7fa80ed8f79f38ad5bb953
```

Flag: `flag{aeea66fcac7fa80ed8f79f38ad5bb953}`

**Files:** [reverse-re3.zip](/assets/ctf-files/adworld-reversing/reverse-re3.zip)

## RC4 and custom Base64 - ereere

A statically linked, stripped MIPS32 big-endian ELF. It reads a line, transforms it and compares the result with a stored string, then prints `correct!` or `wrong!`. I ran it with `qemu-mips-static`.

The main function at `0x400bc8` calls three routines. The first (`0x4009dc`) is the RC4 key schedule and keystream XOR, keyed with the string `flag{123321321123badbeef012}` that sits in `.data`. That string is only the key and not the answer, since entering it prints `wrong!`. The second (`0x400550`) is a Base64 encoder that uses a custom alphabet stored at `0x473e00`, which is the normal alphabet with the order changed (`ZYXW...ABabc...z/+9876543210`). The result is compared with `ScDZC1cNDZaxnh/2eW1UdqaCiJ0ijRIExlvVEgP43rpxoxbYePBhpwHDPJ==`.

To reverse it I decoded the target with the custom alphabet and ran RC4 with the same key, since RC4 is symmetric.

```python
raw = decode_b64(target, custom_table)
print(rc4(b'flag{123321321123badbeef012}', raw))
```

Feeding the result back into the binary under qemu prints `correct!`.

Flag: `flag{RC_f0ur_And_Base_s1xty_f0ur_Encrypt_!}`

**Files:** [ereere.zip](/assets/ctf-files/adworld-reversing/ereere.zip)

## Android smali - easyEZbaby_app

An Android app with a single login screen. `FirstActivity` checks a username and a 15 character password, and on success shows `flag{` + username + password + `}`.

I unpacked the APK with apktool and read `FirstActivity.smali`. The username check computes the MD5 of the constant `zhishixuebao` as a hex string, keeps every second character (positions 0, 2, 4 and so on) and compares that with the input. The password check requires length 15, and for each index `i` it computes `255 - i + 2 - 0x62 - password[i]` and requires the result to equal `0x30` (`'0'`). That gives `password[i] = 111 - i`, which is `onmlkjihgfedcba`.

```python
h = md5(b'zhishixuebao').hexdigest()   # 7da5fec345fecde5fdcd641f68e0b6d1
user = h[::2]                          # 7afc4fcefc616ebd
pwd  = ''.join(chr(111 - i) for i in range(15))
```

Flag: `flag{7afc4fcefc616ebdonmlkjihgfedcba}`

**Files:** [easyezbaby-app.zip](/assets/ctf-files/adworld-reversing/easyezbaby-app.zip)

## Static data lookup - toddler_regs

A Windows x64 console program (debug build, PDB included) that walks the player through debugger tasks such as "set the argument of the next function called equal to 23". I did not run it, since it is a Windows binary, and read the disassembly instead.

The flag is built at the end of the last stage by concatenating `flag{`, an entry from a table at `0x14001e000` (7 bytes per entry) indexed by a global, the fixed text `_1s_n1c3_but_`, an entry from a table at `0x14001e1c0` (10 bytes per entry) indexed by the constant 184 (`0xb8`), and `_is_we1rd}`. The global is written by the task 1 function, which only stores it when its argument equals `0x17` (23). So the first index is 23 and both indexes are known statically. The tables hold every upper and lower case spelling of the same words, so the exact index is what picks the right casing.

```
table1[23]  = "Xp0int"
table2[184] = "Xp0intJNU"
```

Flag: `flag{Xp0int_1s_n1c3_but_Xp0intJNU_is_we1rd}`

**Files:** [toddler-regs.zip](/assets/ctf-files/adworld-reversing/toddler-regs.zip)

## Static strings and click counter - 1000Click

A 32-bit MFC GUI program. A button handler counts clicks, and at exactly 1000 clicks it shows a message box. The binary also holds 40 decoy strings of the form `flag{...}` in `.data`, so searching for `flag{` alone gives many wrong answers.

The click handler at `0x402790` increments a counter in the dialog object, compares it with `0x3e8` and then calls the message box routine with the string at `0x5c4b68`. A second handler at `0x4027d0` compares an edit box with the same address. Mapping `0x5c4b68` to the file (`.data` raw offset `0x1c0a00` for address `0x5c3000`) gives file offset `0x1c2568`, which is the 26th of the 40 strings. Only that address is referenced by code, and nothing modifies it at run time, so it is the string the program displays after 1000 clicks.

```
VA 0x5c4b68 -> file 0x1c2568 -> flag{TIBntXVbdZ4Z9VRtoOQ2wRlvDNIjQ8Ra}
```

Flag: `flag{TIBntXVbdZ4Z9VRtoOQ2wRlvDNIjQ8Ra}`

**Files:** [1000click.zip](/assets/ctf-files/adworld-reversing/1000click.zip)

## Status of the rest

This set is ongoing practice. A few challenges in the folder are still open: dmd-50 (its MD5 key is not recoverable by brute force here), easyre-153, Mine-, and CatFly. The rest are written up above.
