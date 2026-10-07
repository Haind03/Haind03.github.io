---
title: "Lesson 3.5: Lab, solving your first C crackme"
image:
  path: /assets/img/covers/re-3-5-lab-solving-first-c-crackme-from.webp
  alt: "Lesson 3.5: Lab, solving your first C crackme"
date: 2022-06-10 09:41:00 +0700
categories: ["Technique Reverse", "Part 03 · C"]
tags: [reverse-engineering, c]
render_with_liquid: false
---
By now you have the separate pieces, reading assembly (1.3), the stack and parameters (1.4), recognizing if/loop (1.5), IDA/Ghidra (2.2, 2.3) and x64dbg (2.5). This lesson uses all of them on a small crackme written in C. There's no new theory, we just sit down and solve it.

The crackme is `crackme.c`, in the Lab section at the end. I suggest you stop here, try it yourself, and come back to compare. Below I walk through the whole solution, so it's a spoiler.

## The rules

The crackme asks for a password. The right one prints `Correct!`, a wrong one prints `Wrong password.`. You have to find the correct password. The password isn't in the file as plain text, so running strings and copying won't work. You need to understand how it checks.

## Step 1: triage

First I always check what I'm holding. Drag the file into Detect It Easy or run `diec`:

```
$ diec crackme
PE64 / ELF64, compiler GCC (or MSVC), not packed
```

Not packed, so it's a normal C binary. We can go straight to reading.

Run `strings` for clues:

```
$ strings crackme
Enter password: 
Correct! Congratulations.
Wrong password.
check_password
...
```

Two things here. There's a function named `check_password`, which is convenient, that's where we're going. And there's no password in plaintext, so it's compared indirectly and we have to read the logic.

## Step 2: static, from the string to the check function

Open the file in Ghidra (or IDA). After auto-analysis, open the Defined Strings window (Ghidra) or Strings (Shift+F12 in IDA) and look for `Wrong password.`. Click it and check the xref to see who uses it. It leads to `main`, which prints the result based on the return value of `check_password`. Jump into `check_password` and press F5 to decompile.

The pseudocode looks roughly like this:

```c
int check_password(char *input) {
    if (strlen(input) != 10)
        return 0;
    int checksum = 0;
    for (int i = 0; i < 10; i++) {
        unsigned char t = input[i] ^ 0x5A;
        if (t != expected[i])
            return 0;
        checksum += input[i];
    }
    if (checksum != 0x39C)
        return 0;
    return 1;
}
```

There are three checks. The first is the length. The password must be exactly 10 characters, and `strlen(input) != 10` returns 0 right away. You saw this pattern in lesson 1.3.

The second is a per-character transform. Each character gets XORed with `0x5A` and compared with an element of the `expected` array. That's why the password doesn't show up in strings. The file holds the XORed `expected` array, not the original password. The third is a checksum. The sum of the ASCII codes must equal `0x39C`. It's there to stop random guessing, but it doesn't cost us anything. If we get the second check right, the third passes on its own.

The XOR is the important part. Remember from lesson 1.1 that `a ^ k ^ k == a`. If `input[i] ^ 0x5A == expected[i]`, then `input[i] == expected[i] ^ 0x5A`. So take the `expected` array and XOR it with `0x5A` to get the password.

## Step 3: pull out the expected array

In Ghidra, double-click `expected` to go to its address and read 10 bytes. In this lab they are:

```
08 3F 2C 3F 28 29 3F 05 6A 6B
```

XOR each byte with `0x5A`. Doing it by hand is slow, so use Python:

```python
exp = [0x08,0x3F,0x2C,0x3F,0x28,0x29,0x3F,0x05,0x6A,0x6B]
print(''.join(chr(b ^ 0x5A) for b in exp))
# Reverse_01
```

The password is `Reverse_01`. Enter it and the crackme prints `Correct!`. We solved it just by reading the code, without running it once.

## Step 4: the dynamic route

Maybe you don't want to compute by hand, or the logic is messier and you want to see the real values. Then I'd use x64dbg.

Open the crackme in x64dbg and set a breakpoint at `check_password` (or at the `cmp` in the loop). Enter any 10 characters, for example `AAAAAAAAAA`. When it stops in the loop, one register holds `t = input[i] ^ 0x5A` (your input after the XOR). The other operand of `cmp` is `expected[i]`, visible in a register or in the Dump.

If you look at both sides of the `cmp` on each iteration, you read the `expected` array without finding it statically. You still XOR it back as above. So dynamic doesn't replace static here, it confirms it and gives you the constant array directly.

There's a faster trick for this kind of crackme too. Set a breakpoint at the checksum or right before `return 1`, and sometimes you can just patch the `jne` into `je` to get past the check. But that only makes it accept any input, it doesn't give you the real password. For a crackme the goal is usually the password, so XORing back is the better solution. Patching comes in Part 17.

## Order of work

Triage first so you don't waste time on a packed file, static to understand the logic and narrow things down, dynamic to confirm when needed. It's the loop from lesson 0.4 on a real target. Beginners often jump straight into debugging and step from the start of the program, then spend a whole session lost in the CRT startup. I read statically up to the suspicious spot and then put one breakpoint in the right place.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 3.5</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/3.5.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/3.5/src/crackme.c" download><i class="fa-solid fa-download"></i>src/crackme.c</a>
</div>
</div>

The task is to find the correct password of `crackme.c`. It's a summary exercise for Parts 1 through 3.4. Build it with one of these commands. On Linux:

```
gcc -O0 -no-pie -fno-stack-protector -o crackme crackme.c
```

On Windows with MinGW:

```
x86_64-w64-mingw32-gcc -O0 -o crackme.exe crackme.c
```

On Windows with an MSVC Developer Prompt:

```
cl /Od crackme.c
```

Work in this order. Triage with Detect It Easy to see which compiler built it and whether it's packed. Run `strings` and check whether the password shows up in plaintext, and whether any function name hints at the destination. Open it in Ghidra or IDA and go from the result strings to the checking function by xref. Read the check logic and work out how long the password is and how each character is transformed before the comparison. Take the constant array used in the comparison and compute the password backwards. Enter it and confirm the program prints `Correct!`. Optionally, open it in x64dbg, put a breakpoint at the comparison loop and watch the two operands of `cmp`, so you can read the constant array without hunting for it statically.

A hint is that the password isn't in the file as readable text. It's transformed, so you have to understand the transformation and undo it. Look at the properties of XOR in [Lesson 1.1](/posts/re-1-1-reading-hexdump-like-text/) if you need a refresher. Do all the steps yourself before opening the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The correct password is `Reverse_01`. Entering it prints `Correct! Congratulations.`, and a wrong input or a wrong length prints `Wrong password.`.

The `check_password` function does three checks. First, the length must be exactly 10 (`strlen(input) != 10`). Second, for each character, `input[i] ^ 0x5A` must equal `expected[i]`. Third, the sum of the ASCII codes of the password must equal `0x39C`. The constant array `expected` in the binary is:

```
08 3F 2C 3F 28 29 3F 05 6A 6B
```

Since `input[i] ^ 0x5A == expected[i]`, it follows that `input[i] == expected[i] ^ 0x5A`:

```python
exp = [0x08,0x3F,0x2C,0x3F,0x28,0x29,0x3F,0x05,0x6A,0x6B]
pw = ''.join(chr(b ^ 0x5A) for b in exp)
print(pw)                      # Reverse_01
print(hex(sum(ord(c) for c in pw)))  # 0x39c  -> the checksum layer is satisfied on its own
```

The result is `Reverse_01`. The ASCII sum equals `0x39C`, so the checksum check passes too and needs no separate handling. To verify:

```
$ gcc -O0 -o crackme crackme.c
$ echo "Reverse_01" | ./crackme
Enter password: Correct! Congratulations.
$ echo "Reverse_02" | ./crackme
Enter password: Wrong password.
```

A few notes. The password is XORed, so it never appears in `strings`, and the way to the real password is to understand the transformation and reverse it. That's faster and cleaner than patching. The checksum is redundant if you solve the XOR correctly, but it blocks blind guessing, and many real crackmes stack several checks like this. If all you need is for the program to accept any input, you can patch `jne` into `je` or NOP the jump, but that doesn't give you the original password.

</details>

## Key takeaways
Always triage first, then strings. Function names like `check_password` help a lot, and the `Correct` string leads straight to the logic. If the password doesn't appear in strings, it's transformed, so you have to read how it's checked.

XOR goes both ways, which gives `input = expected ^ key`. A per-byte XOR loop followed by a comparison with a constant array usually means you can XOR back. Solving from static reading is the cleanest, and dynamic is for confirming or for complex logic. Patching the jump makes the check always pass but doesn't give you the real password.
