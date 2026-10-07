---
title: "Lesson 3.5: Lab, solving your first C crackme from start to finish"
date: 2022-06-10 09:41:00 +0700
categories: ["Technique Reverse", "Part 03 · C"]
tags: [reverse-engineering, c]
render_with_liquid: false
---
By now you have all the separate pieces: reading assembly (1.3), understanding the stack and parameters (1.4), recognizing if/loop (1.5), using IDA/Ghidra (2.2, 2.3), using x64dbg (2.5). This lesson puts them all together on a real target: a small crackme in C. There's no new theory, just sitting down and getting it done.

The crackme is in `labs/3.5/`. I suggest you stop reading here, go solve it yourself first, and only then come back to compare approaches. Below I walk through the whole process, so it's a spoiler.

## The rules

The crackme asks for a password. Enter the right one and it prints `Correct!`, a wrong one and it prints `Wrong password.`. Your task is to find the correct password. The twist: the password isn't sitting plainly in the file, so the "run strings and copy" tactic will fail. You have to understand how it checks.

## Step 1: triage

The first habit, always, is to know what you're holding. Drag the file into Detect It Easy or run `diec`:

```
$ diec crackme
PE64 / ELF64, compiler GCC (or MSVC), not packed
```

Not packed, a normal C binary. Good, go straight into reading.

Run `strings` to pick up clues:

```
$ strings crackme
Enter password: 
Correct! Congratulations.
Wrong password.
check_password
...
```

Two takeaways. One, there's a function named `check_password`, very convenient, that's the destination. Two, no password in plaintext. That means it's compared indirectly, and you have to read the logic.

## Step 2: static, go from the string to the check function

Open the file in Ghidra (or IDA). After auto-analysis, use the Defined Strings window (Ghidra) or Strings (Shift+F12 in IDA), and look for the string `Wrong password.`. Click it and look at the xref (who uses this string). The xref leads to `main`, where it prints the result based on the return value of `check_password`. Jump into `check_password` and press F5 to decompile.

The pseudocode will look roughly like this:

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

Read it layer by layer. Layer 0 is the length: the password must be exactly 10 characters, and `strlen(input) != 10` returns 0 right away. You've seen exactly this in lesson 1.3.

Layer 1 is a per-character transform. Each character entered gets XORed with `0x5A`, then compared with an element of the `expected` array. This is where the password "disappears" from strings: what's in the file is the XORed `expected` array, not the original password. Layer 2 is a checksum. The sum of the password's ASCII codes must equal `0x39C`. This layer is there to stop random guessing, but for us it's a gift: if we solve layer 1 correctly, layer 2 is satisfied automatically.

The key is the XOR. Remember the property from lesson 1.1: `a ^ k ^ k == a`. If `input[i] ^ 0x5A == expected[i]`, then `input[i] == expected[i] ^ 0x5A`. Just take the `expected` array and XOR it back with `0x5A` to get the password.

## Step 3: pull out the expected array

In Ghidra, double-click `expected` to go to its address and read 10 bytes. The values (in this lab) are:

```
08 3F 2C 3F 28 29 3F 05 6A 6B
```

Now XOR each byte with `0x5A`. Doing it by hand is slow, so let Python do it:

```python
exp = [0x08,0x3F,0x2C,0x3F,0x28,0x29,0x3F,0x05,0x6A,0x6B]
print(''.join(chr(b ^ 0x5A) for b in exp))
# Reverse_01
```

The password is `Reverse_01`. Enter it into the crackme and it prints `Correct!`. You just solved a crackme entirely by static reading, without running it once.

## Step 4: the dynamic route, seeing it with your own eyes

Suppose you don't want to compute by hand, or the logic is messier and you want to see the real values. This is where x64dbg comes in.

Open the crackme in x64dbg, and set a breakpoint at `check_password` (or at the `cmp` instruction in the loop). Enter a random password of 10 characters, for example `AAAAAAAAAA`. When it stops in the loop, you see the register holding `t = input[i] ^ 0x5A` (the value you entered after the XOR). The other operand of `cmp` is `expected[i]`, showing up right in the register or in the Dump.

By looking at both sides of the `cmp` at each iteration, you read the `expected` array without having to find it statically. From there you still XOR it back as above. Dynamic here doesn't replace static, it confirms things and hands you the constant array directly.

There's an even faster trick for this kind of crackme: set a breakpoint at the checksum layer or right before `return 1`, and once you know the length and the pattern, sometimes you only need to patch the `jne` branch into `je` to get past the check. But patching only makes it accept any input, it doesn't give you the real password. With a crackme, the goal is usually to find the password, so XORing back is the nicer solution. Patching is saved for Part 17.

## Why work in this order

Notice the rhythm: triage first so you don't waste effort reading a packed file, static to understand the logic and narrow things down, dynamic to confirm when needed. This is exactly the loop from lesson 0.4, this time applied to a real target. Beginners often jump straight into debugging and step through instructions from the start of the program, getting lost in the CRT startup for a whole session. Someone used to the work reads statically up to the suspicious spot and only then places one breakpoint in exactly the right place.

## Key takeaways
Always triage and then strings first. Function names like `check_password` are gifts, and the `Correct` string leads straight to the logic. A password not appearing in strings means it's transformed, so you have to read how it's checked.

XOR goes both ways: `input = expected ^ key`. When you see a per-byte XOR loop followed by comparison with a constant array, think of XORing back. Getting the solution from static reading is the nicest, and dynamic is for confirming or for when the logic is complex. Patching the jump makes it "always right" but doesn't give you the real password.
