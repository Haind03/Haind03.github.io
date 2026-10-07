---
title: "Lesson 5.7: Combined lab, solving .NET crackmes from easy to obfuscated"
date: 2022-08-26 14:27:00 +0700
categories: ["Technique Reverse", "Part 05 · C# and .NET"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
The last five lessons were theory and individual operations. This one puts it all together into a complete .NET reversing session, through three crackmes that get harder. If you can do all three, the .NET part counts as done for the basics.

The source code and detailed tasks are at `labs/5.7/`. Here I walk through the thinking, and you go down to the lab and do it by hand before opening the solution.

All three use the ILSpy and dnSpy already in the repo (the parent folder). You need the .NET SDK to build them into `.dll` form, and then you take apart your own product.

## Level 1: when reversing is just reading

The first crackme compares the entered password to a fixed string. Open the `.dll` in dnSpy, find the method `Check`, and since .NET decompiles to nearly the original source (the reason was covered in [Lesson 5.1](/posts/re-5-1-net-internals-why-decompiling-gives-back/)), you read it directly:

```csharp
static bool Check(string input)
{
    return input == "dotnet_easy_123";
}
```

That's it. The password is exposed right in the IL `ldstr` instruction. No debugging, no patching, nothing. The point of this level is to show you a harsh truth: a lot of .NET software out there protects its logic this weakly, and that's why people have to obfuscate.

A tip faster than opening each method: in dnSpy hit search, type part of a message string like "Correct", then Analyze to jump to where it's used.

## Level 2: understand the algorithm, write a keygen

The second crackme doesn't compare strings directly. It takes a username and a serial, then computes a value from the username and compares it to the serial:

```csharp
static string Expected(string user)
{
    uint acc = 0x1505;
    foreach (char c in user)
        acc = (acc * 33u) + (byte)c;
    return acc.ToString("X8");
}
```

This is the familiar djb2 hash, computed on a `uint` (the 32-bit overflow is intentional). Now there are two options. Patching it to always accept works, but it's less elegant. The right way is to write a keygen: since the serial depends only on the username and it's all forward computation, we copy the algorithm exactly into Python and generate a serial for any username.

```python
def serial_for(user):
    acc = 0x1505
    for ch in user.encode():
        acc = ((acc * 33) + ch) & 0xFFFFFFFF
    return "%08X" % acc
# alice -> 0F174DC3
```

Watch out for a trap newcomers often fall into: this hash is one-way, you can't recover the username from the serial. But you don't need to, because you choose the username. You just compute forward exactly like the crackme. This is the keygen mindset from [Lesson 3.6](/posts/re-3-6-writing-keygen-when-fishing-out-serial/), repeated here so it becomes reflex: tell "inverting the algorithm" apart from "recomputing the algorithm".

## Level 3: hidden strings and obfuscation

The third crackme hides the password. Open it and you see no strings, just a byte array and a loop:

```csharp
static readonly byte[] Enc = { 127,83,82,90,73,79,89,99,113,89,99,8,14 };
...
if ((byte)(input[i] ^ 0x3C) != Enc[i]) return false;
```

The logic is clear: it XORs each entered character with 0x3C and compares against the array. So the password is the array XORed back with 0x3C. A few lines of Python give `Confuse_Me_42` right away. String encryption like this (XOR with a constant) only slows you down a few minutes, it doesn't stop you.

The interesting part is when the crackme is run through a real obfuscator like ConfuserEx. Reopen it in dnSpy and you'll see class and method names turn into meaningless Unicode characters, strings turn into runtime decryption function calls, and the control flow is scrambled. At this point, run `de4dot -f level3.dll` so it identifies the protector, restores names, decrypts static strings, and flattens control flow. Most older ConfuserEx builds get handled cleanly by de4dot.

If strings are encrypted at runtime and de4dot can't decrypt them, go back to [Lesson 5.3](/posts/re-5-3-debugging-net-without-source-using-dnspy/): set a breakpoint in dnSpy at the decryption function, run to it, and read the decrypted string in the Locals window. Since .NET always runs on the CLR, there's always a debugging route to grab the real value, however it's obfuscated.

That's both the strength and the weakness of managed code: much harder to hide than native, because the runtime has to understand the bytecode to run it, and whatever the runtime can understand, you can understand too.

## Key takeaways
An easy-level .NET crackme is just reading the decompiled C#, and the password sits in `ldstr`. For a check algorithm, write a keygen by copying the forward-computation logic, and don't try to invert a one-way function. String encryption like XOR or custom Base64 gets reversed in a few minutes.

For real obfuscation, try de4dot first, and if that fails trace the runtime in dnSpy. Managed code is hard to hide because the CLR has to understand the bytecode, so you always have a way in.
