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

## Status of the rest

This set is ongoing practice. About two dozen of the challenges in the folder are still bare binaries that I have not written up, so there is more to add as I work through them.
