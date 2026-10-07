---
title: "Lesson 5.5: .NET obfuscators and how to strip them"
date: 2022-08-21 15:13:00 +0700
categories: ["Technique Reverse", "Part 05 · C# and .NET"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
In the last four lessons you saw that .NET is so easy to reverse it feels like cheating: decompile and you get C# that reads like the original. That's exactly why people who write .NET software built a whole industry of obfuscators to make life hard for you. The good news is that most popular obfuscators already have tools that strip them almost automatically. The less happy news is there are still layers you have to peel by hand. This lesson gives you the map: recognizing what you're facing, which tool to try first, and what to do when the tools give up.

Before going further, a reminder of the boundary from [Lesson 0.2](/posts/re-0-2-legal-ethics-part-everyone-wants-skip/): the techniques below are only for your own assemblies, learning samples, crackmes, or defensive malware analysis. Stripping protection from commercial software to use it for free is a completely different matter.

## What obfuscators actually do

Obfuscation doesn't encrypt the program, it still has to run on the CLR. It only makes the code hard to read after decompiling. There are a few groups of techniques, and you'll meet them mixed together.

Renaming changes the names of classes, methods, fields, variables from `CheckLicense` into `a`, `b`, or worse, invisible Unicode characters, Chinese characters, or jumbled strings. This is the most common layer and also the most annoying because it wipes out all semantic clues. String encryption encrypts every string (messages, names of dynamically called functions, URLs) and replaces it with calls like `Decrypt(0x1234)`, so you can no longer grep for the string "Invalid license".

Control flow obfuscation inserts fake branches and turns straight flow into a state machine (a switch nested in a while loop) so the decompiler rebuilds it into a tangle of `goto`. Proxy or indirect calls replace direct method calls with indirect calls through an intermediate layer, so Analyze can't trace who calls whom. Anti-tamper makes the assembly check its own integrity at runtime, so changing one byte breaks it or makes it exit. And anti-debug detects dnSpy attached and exits or takes a different branch (see also Part 15).

## Protectors you'll often meet

Know the names so you know what to look up. ConfuserEx is open source, free, and extremely common in crackmes and .NET malware. It has many forks (ConfuserEx2, custom builds), and because it's common there are many dedicated unpack tools. .NET Reactor is commercial and strong, with a native stub wrapped around it and tough anti-tamper and control flow. Eazfuscator.NET is commercial with good string encryption and virtualization. Dotfuscator ships with the community edition of Visual Studio and is light. SmartAssembly (Red Gate) is often seen in commercial software. Then there are the less common names like Agile.NET, Babel and .NET Guard.

## The first step is always identification

Don't guess. Open the file with Detect It Easy or just open it in dnSpy, and look for a few signs. DIE often writes the protector name straight out (ConfuserEx, .NET Reactor...). In dnSpy, if type/method names are all odd characters, there's a `<Module>` containing many suspicious methods, or you see an attribute like `ConfusedByAttribute`, you know right away. Unusually high entropy and a pile of big byte array strings are signs of string/resource encryption.

Only after recognizing the protector do you choose the right tool, because throwing de4dot blindly at a .NET Reactor sample is wasted effort.

## de4dot: the all-purpose knife

de4dot is the classic .NET deobfuscation tool, recognizing and handling many protectors automatically (including old ConfuserEx, Dotfuscator, Babel, Eazfuscator to some extent). It does a few main jobs: decrypts strings, removes proxy calls, restores control flow to some degree, and renames things to be more readable (though it doesn't restore the original names, just clean names like `Class0`, `method_3`).

Very simple to use from the command line:

```
de4dot.exe target.exe
```

It creates `target-cleaned.exe`. Open the cleaned version in dnSpy and you'll see the decompiled C# is far more readable: strings are visible, the flow is straight again.

With modern ConfuserEx, the original de4dot often gives up. Then use the de4dot-cex fork (de4dot specialized for ConfuserEx) or dedicated unpackers for specific ConfuserEx versions. For .NET Reactor specifically there's a dedicated tool called .NET Reactor Slayer that handles it better than de4dot.

## When the tool doesn't strip everything: trace string decryption with dnSpy

The most common case is that the tool strips renaming and control flow but strings are still encrypted, or the tool doesn't support a newer protector version. Here the strongest play is to let the program decrypt for you itself with the dnSpy debugger (a reminder of [Lesson 5.3](/posts/re-5-3-debugging-net-without-source-using-dnspy/)).

First find the string decryption function. It's usually a static method that takes an `int` (or token) and returns a `string`, and is called everywhere. Set a breakpoint right after the `Decrypt(...)` call, or inside the Decrypt function itself at the `return`. Run the program (F5), and each time it stops, look at the return value in Locals, which is the real string. Record the strings matching each parameter, and now you have a map `0x1234 -> "Invalid license"`.

This works because however it's obfuscated, by the time the string is used it has to exist in the clear in memory. This principle holds for every layer of protection: whatever the program needs to use, it has to decrypt, and the place it decrypts is where you lie in wait.

For anti-debug that blocks dnSpy, patch or bypass that check first (techniques in Part 15), or use a dnSpy build that has anti-anti-debug built in, and then trace.

## A suggested rhythm

```
1. Identify the protector  (DIE / dnSpy)
2. Try the automatic tool  (de4dot / de4dot-cex / Reactor Slayer)
3. Open the cleaned file   (dnSpy / ILSpy)
4. Strings still encrypted? -> trace at runtime with the dnSpy debugger
5. Control flow still messy? -> read block by block, or let the debugger run through
```

Don't expect to get beautiful source back as if it had never been obfuscated. The goal is readable enough to understand the logic, not a perfect restoration.

## Lab

Practice at `labs/5.5/`: obfuscate a small assembly yourself with ConfuserEx then use de4dot to strip it and compare, or if you can't install it, follow the string decryption tracing workflow in dnSpy on an obfuscated sample.

## Key takeaways
Obfuscation doesn't encrypt the program, it only makes the decompiled code hard to read, and it still has to run. The four common layers are renaming, string encryption, control flow, and anti-tamper/anti-debug. Always identify the protector first (DIE/dnSpy) and then choose the tool.

de4dot is the first choice, de4dot-cex is for ConfuserEx, and Reactor Slayer is for .NET Reactor. If the tool doesn't strip everything, let the program decrypt itself: set a breakpoint after the Decrypt function and read the real strings in dnSpy. The goal is to read and understand the logic, not to restore perfect source.
