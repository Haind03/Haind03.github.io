---
title: "Lesson 5.7: Combined lab, solving .NET crackmes"
image:
  path: /assets/img/covers/re-5-7-combined-lab-solving-net-crackmes-from.webp
  alt: "Lesson 5.7: Combined lab, solving .NET crackmes"
date: 2022-08-26 14:27:00 +0700
categories: ["Reverse Engineering", "Part 05 · C# and .NET"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
The last five lessons covered theory and single operations. This one puts them together in a full .NET reversing session with three crackmes of increasing difficulty. If you can do all three, you've got the basics of .NET.

The source code and detailed tasks are in the Lab section below. Here I go through the thinking, and you should do the lab yourself before opening the solution.

All three use ILSpy and dnSpy from the earlier lessons. You need the .NET SDK to build them into `.dll` files, so you're taking apart your own build.

## Level 1: just reading

The first crackme compares the entered password to a fixed string. Open the `.dll` in dnSpy and find the method `Check`. .NET decompiles to nearly the original source (the reason is in [Lesson 5.1](/posts/re-5-1-net-internals-why-decompiling-gives-back/)), so you read it directly:

```csharp
static bool Check(string input)
{
    return input == "dotnet_easy_123";
}
```

That's all. The password is right there in the IL `ldstr` instruction. No debugging, no patching. This level shows how weak a lot of .NET software is, which is why people obfuscate.

A tip that's faster than opening each method is to use search in dnSpy, type part of a message string like "Correct", then Analyze to jump to where it's used.

## Level 2: understand the algorithm, write a keygen

The second crackme doesn't compare strings directly. It takes a username and a serial, computes a value from the username and compares it to the serial:

```csharp
static string Expected(string user)
{
    uint acc = 0x1505;
    foreach (char c in user)
        acc = (acc * 33u) + (byte)c;
    return acc.ToString("X8");
}
```

This is the familiar djb2 hash, computed on a `uint` (the 32-bit overflow is intentional). You could patch it to always accept, but writing a keygen is the better way. The serial depends only on the username and everything is forward computation, so we copy the algorithm into Python and generate a serial for any username.

```python
def serial_for(user):
    acc = 0x1505
    for ch in user.encode():
        acc = ((acc * 33) + ch) & 0xFFFFFFFF
    return "%08X" % acc
# alice -> 0F174DC3
```

Newcomers often get stuck on one thing. The hash is one-way, you can't recover the username from the serial. You don't need to, because you choose the username and compute forward exactly like the crackme does. This is the keygen mindset from [Lesson 3.6](/posts/re-3-6-writing-keygen-when-fishing-out-serial/). Keep the difference between inverting an algorithm and recomputing it clear in your head.

## Level 3: hidden strings and obfuscation

The third crackme hides the password. You see no strings, just a byte array and a loop:

```csharp
static readonly byte[] Enc = { 127,83,82,90,73,79,89,99,113,89,99,8,14 };
...
if ((byte)(input[i] ^ 0x3C) != Enc[i]) return false;
```

It XORs each entered character with 0x3C and compares against the array. So the password is the array XORed back with 0x3C. A few lines of Python give `Confuse_Me_42`. String encryption like this (XOR with a constant) only slows you down for a few minutes.

It gets more interesting when the crackme goes through a real obfuscator like ConfuserEx. Reopen it in dnSpy and class and method names become meaningless Unicode characters, strings become calls to a runtime decryption function, and the control flow is scrambled. Run `de4dot -f level3.dll`. It identifies the protector, restores names, decrypts static strings and flattens control flow. Most older ConfuserEx builds are handled fine by de4dot.

If strings are encrypted at runtime and de4dot can't decrypt them, go back to [Lesson 5.3](/posts/re-5-3-debugging-net-without-source-using-dnspy/). Set a breakpoint in dnSpy at the decryption function, run to it and read the decrypted string in the Locals window. .NET always runs on the CLR, so there's always a debugging route to the real value, however it's obfuscated.

Managed code is much harder to hide than native code, because the runtime has to understand the bytecode to run it, and anything the runtime can understand, you can understand too.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 5.7</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/5.7.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/5.7/src/level1/Program.cs" download><i class="fa-solid fa-download"></i>src/level1/Program.cs</a>
<a class="lab-file" href="/assets/labs/5.7/src/level2/Program.cs" download><i class="fa-solid fa-download"></i>src/level2/Program.cs</a>
<a class="lab-file" href="/assets/labs/5.7/src/level2/keygen.py" download><i class="fa-solid fa-download"></i>src/level2/keygen.py</a>
<a class="lab-file" href="/assets/labs/5.7/src/level3/Program.cs" download><i class="fa-solid fa-download"></i>src/level3/Program.cs</a>
</div>
</div>

This lab applies everything from Part 5. You decompile with ILSpy or dnSpy, read the logic, write a keygen and strip obfuscation. It's a .NET crackme in three levels. You need the .NET SDK (`dotnet`) to build it, which you can install from dotnet.microsoft.com. Each level is its own console app. A quick way to build one:

```
cd level1
dotnet new console --force        # creates the project skeleton in the current folder
# (Program.cs is already there, it overwrites the template file)
dotnet build -c Release           # produces bin/Release/.../level1.dll
```

Do the same for level2 and level3, then open the resulting `.dll` (or `.exe`) in `ILSpy.exe` or `dnSpy.exe` to decompile it.

Level 1 is a plain string comparison. Run `level1`, try any password and see "Wrong.". Then open `level1.dll` in dnSpy, find the method `Check` and read the right password from the decompiled C#. Type it in and confirm you get "Correct!".

Level 2 is an algorithm, so you write a keygen. Open `level2.dll`, read the method `Expected` and understand how it turns a username into a serial. Write a keygen (or use `keygen.py` after you've tried yourself) that produces a serial for your own username. Run `level2` with that username and serial and confirm "Valid!".

Level 3 adds obfuscation and a hidden string. Open `level3.dll` and notice that the password isn't in plaintext. Read `Check` and see that it compares `input[i] ^ 0x3C` against a constant array. Reverse the array (XOR it again with 0x3C) to get the key and confirm "Unlocked!". As an advanced step, if you have ConfuserEx, obfuscate `level3.dll`, reopen it to see the scrambled names, then run `de4dot -f level3.dll` and compare before and after.

Do all of it before opening the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Level 1, just read it. Open `level1.dll` in dnSpy and go to `Program.Check`:

```csharp
static bool Check(string input)
{
    return input == "dotnet_easy_123";
}
```

The correct password is `dotnet_easy_123`. The string sits in the IL (an `ldstr` instruction) and shows up when decompiled. No debugging and no patching needed.

Level 2, understand the algorithm and write a keygen. Decompile `Program.Expected`:

```csharp
static string Expected(string user)
{
    uint acc = 0x1505;
    foreach (char c in user)
        acc = (acc * 33u) + (byte)c;
    return acc.ToString("X8");
}
```

This is a variant of the djb2 hash. You start with `acc = 0x1505`, and for each character do `acc = acc*33 + c`, computed on a `uint` (the 32-bit overflow is intentional). The correct serial is the hash value as 8 uppercase hex digits. The hash depends only on the username and uses only operations we can compute, so we reproduce it to generate a serial for any username (see `keygen.py`):

```python
MASK = 0xFFFFFFFF
def serial_for(user):
    acc = 0x1505
    for ch in user.encode():
        acc = ((acc * 33) + ch) & MASK
    return "%08X" % acc
```

Results from actually running it in Python:

```
alice  -> 0F174DC3
REteam -> CC47F9A3
x      -> 0002B61D
```

Entering `username=alice`, `serial=0F174DC3` gives "Valid!". The hash is one-way, so you can't recover the username from the serial, but we don't need to. The keygen only computes forward like the crackme, because we choose the username. That's the keygen mindset (see Lesson 3.6).

Level 3, hidden string and obfuscation. Decompile `Program.Check`:

```csharp
static readonly byte[] Enc = { 127,83,82,90,73,79,89,99,113,89,99,8,14 };
static bool Check(string input)
{
    if (input.Length != Enc.Length) return false;
    for (int i = 0; i < Enc.Length; i++)
        if ((byte)(input[i] ^ 0x3C) != Enc[i]) return false;
    return true;
}
```

The password isn't stored directly, it's stored as bytes XORed with 0x3C. To reverse it, `key[i] = Enc[i] ^ 0x3C`. Checking in Python:

```python
enc = [127,83,82,90,73,79,89,99,113,89,99,8,14]
print("".join(chr(b ^ 0x3C) for b in enc))   # -> Confuse_Me_42
```

The correct password is `Confuse_Me_42`.

On the obfuscation part, if you obfuscate `level3.dll` with ConfuserEx and reopen it in dnSpy, class, method and field names turn into meaningless Unicode characters, the constant array may be converted into a call to a runtime decryption function, and the control flow is tangled. Running `de4dot -f level3.dll -o level3-clean.dll` makes de4dot recognize the protector, restore names (as `Class0.method1`), decrypt static strings and flatten the control flow, and `level3-clean.dll` reads almost like the original. When strings are encrypted at runtime and de4dot can't decrypt them, the manual way is to set a breakpoint in dnSpy on the decryption function, run to it and read the decrypted string in Locals.

In summary, .NET decompiles almost back to source, so Level 1 is just reading. For an algorithm you write a keygen and don't need to patch. Hidden strings only slow you down, since custom XOR or Base64 reverses in minutes. Real obfuscation (ConfuserEx) needs de4dot or runtime tracing, but because .NET still runs on the CLR, there's always a debugging path to the decrypted values.

</details>

## Key takeaways
An easy .NET crackme is just reading the decompiled C#, and the password sits in `ldstr`. For a check algorithm, write a keygen by copying the forward computation, and don't try to invert a one-way function. String encryption like XOR or custom Base64 gets reversed in a few minutes.

For real obfuscation, try de4dot first, and if that fails trace the runtime in dnSpy. Managed code is hard to hide because the CLR has to understand the bytecode.
