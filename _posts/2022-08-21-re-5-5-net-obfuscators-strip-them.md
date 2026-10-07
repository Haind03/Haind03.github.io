---
title: "Lesson 5.5: .NET obfuscators and how to strip them"
image:
  path: /assets/img/covers/re-5-5-net-obfuscators-strip-them.webp
  alt: "Lesson 5.5: .NET obfuscators and how to strip them"
date: 2022-08-21 15:13:00 +0700
categories: ["Technique Reverse", "Part 05 · C# and .NET"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
In the last four lessons you saw that .NET is very easy to reverse: decompile it and you get C# that reads like the original. Because of that, people who write .NET software use obfuscators to make it harder. Most popular obfuscators already have tools that strip them almost automatically. Some layers you still have to deal with by hand. This lesson covers how to recognize what you're facing, which tool to try first, and what to do when the tools give up.

First, a reminder of the boundary from [Lesson 0.2](/posts/re-0-2-legal-ethics-part-everyone-wants-skip/): the techniques below are only for your own assemblies, learning samples, crackmes, or defensive malware analysis. Stripping protection from commercial software to use it for free is a different matter.

## What obfuscators do

Obfuscation doesn't encrypt the program, it still has to run on the CLR. It only makes the code hard to read after decompiling. There are a few groups of techniques, and you'll often meet them mixed together.

Renaming changes the names of classes, methods, fields and variables from `CheckLicense` into `a`, `b`, or invisible Unicode characters, Chinese characters, or jumbled strings. It's the most common layer and the most annoying, because it wipes out all the hints about what things do. String encryption encrypts every string (messages, names of dynamically called functions, URLs) and replaces it with calls like `Decrypt(0x1234)`, so you can no longer grep for "Invalid license".

Control flow obfuscation inserts fake branches and turns straight flow into a state machine (a switch nested in a while loop), so the decompiler rebuilds it as a tangle of `goto`. Proxy or indirect calls replace direct method calls with calls through an intermediate layer, so Analyze can't trace who calls whom. Anti-tamper makes the assembly check its own integrity at runtime, so changing one byte breaks it or makes it exit. Anti-debug detects dnSpy attached and exits or takes a different branch (see also Part 15).

## Protectors you'll meet

Know the names so you know what to look up. ConfuserEx is open source, free, and very common in crackmes and .NET malware. It has many forks (ConfuserEx2, custom builds), and because it's common there are many dedicated unpack tools. .NET Reactor is commercial and strong, with a native stub wrapped around it and tough anti-tamper and control flow. Eazfuscator.NET is commercial with good string encryption and virtualization. Dotfuscator ships with the community edition of Visual Studio and is light. SmartAssembly (Red Gate) is often seen in commercial software. Then there are less common ones like Agile.NET, Babel and .NET Guard.

## Identify first

Don't guess. Open the file with Detect It Easy or just open it in dnSpy and look for a few signs. DIE often prints the protector name directly (ConfuserEx, .NET Reactor...). In dnSpy, if type and method names are all odd characters, there's a `<Module>` containing many suspicious methods, or you see an attribute like `ConfusedByAttribute`, you know right away. Unusually high entropy and many big byte array strings point to string or resource encryption.

Only after you know the protector should you pick a tool. Running de4dot blindly on a .NET Reactor sample is wasted effort.

## de4dot

de4dot is the classic .NET deobfuscation tool. It recognizes and handles many protectors automatically (old ConfuserEx, Dotfuscator, Babel, and Eazfuscator to some extent). It decrypts strings, removes proxy calls, restores control flow to some degree, and renames things to be more readable. It doesn't restore the original names, only clean ones like `Class0` and `method_3`.

It's simple to use from the command line:

```
de4dot.exe target.exe
```

It creates `target-cleaned.exe`. Open the cleaned version in dnSpy and the decompiled C# is much more readable: strings are visible, the flow is straight again.

With modern ConfuserEx, the original de4dot often gives up. Then use the de4dot-cex fork (de4dot specialized for ConfuserEx) or dedicated unpackers for specific ConfuserEx versions. For .NET Reactor there's a dedicated tool called .NET Reactor Slayer that handles it better than de4dot.

## When the tool doesn't strip everything: trace string decryption with dnSpy

A common case is that the tool strips renaming and control flow but strings are still encrypted, or the tool doesn't support a newer protector version. Then I let the program decrypt the strings itself under the dnSpy debugger (see [Lesson 5.3](/posts/re-5-3-debugging-net-without-source-using-dnspy/)).

First find the string decryption function. It's usually a static method that takes an `int` (or token) and returns a `string`, and it's called everywhere. Set a breakpoint right after the `Decrypt(...)` call, or inside the Decrypt function at the `return`. Run the program (F5), and each time it stops, look at the return value in Locals. That's the real string. Record the string for each parameter and you have a map `0x1234 -> "Invalid license"`.

This works because however it's obfuscated, the string has to exist in the clear in memory by the time it's used. The same holds for every layer of protection: whatever the program needs to use, it has to decrypt first, and that's where you wait for it.

If anti-debug blocks dnSpy, patch or bypass that check first (techniques in Part 15), or use a dnSpy build with anti-anti-debug built in, and then trace.

## A suggested order

```
1. Identify the protector  (DIE / dnSpy)
2. Try the automatic tool  (de4dot / de4dot-cex / Reactor Slayer)
3. Open the cleaned file   (dnSpy / ILSpy)
4. Strings still encrypted? -> trace at runtime with the dnSpy debugger
5. Control flow still messy? -> read block by block, or let the debugger run through
```

Don't expect to get clean source back in its original form. The goal is code readable enough to understand the logic.

## Lab

The goal is to see how obfuscation deforms code, use de4dot to bring it back to a readable form, and when strings are still encrypted, pull them out with the dnSpy debugger. This lab runs on Windows. You need the dotnet SDK (or .NET Framework plus `csc`) to build, ConfuserEx (a release build from GitHub), de4dot or de4dot-cex for newer ConfuserEx, and dnSpy.

First build the original assembly from `LicenseCheck.cs`:

```
dotnet build
csc /out:LicenseCheck.exe LicenseCheck.cs
```

The first line is for a project setup and the second for a quick compile. Run it: a wrong key prints "Wrong key" and the correct one (`REVERSE-2024`) prints "Valid key". Open it in ILSpy or dnSpy and confirm that the code reads like the source: the name `CheckKey` is visible, and the strings "REVERSE-2024" and "Valid key" sit there in plain sight. This is the baseline for comparison.

Then obfuscate it with ConfuserEx. Open ConfuserEx, add `LicenseCheck.exe`, enable the rename, control flow and constants (string encryption) presets, and press Protect. It writes the result into a `Confused/` folder. Open the obfuscated build in dnSpy and observe that class and method names have turned into strange characters, that the string "REVERSE-2024" has disappeared and been replaced by a call to a decryption routine, and that the flow of `CheckKey` has been bent into a hard-to-read state machine.

Next strip it with de4dot by running `de4dot.exe LicenseCheck.exe` on the obfuscated file. If it is a newer ConfuserEx that the original de4dot doesn't recognize, try de4dot-cex. Open `LicenseCheck-cleaned.exe` in dnSpy and compare with the previous step: the strings are back, the control flow is straighter, and the names, while not restored, are at least clean (`Class0.method_1`).

If you still have a sample where de4dot can't decrypt the strings, find the function `Decrypt(int)` that returns a string, set a breakpoint at its `return`, run with F5, and read the returned value in Locals for each call. Write down a table of token to string.

Two questions to finish. Why, despite obfuscation, must strings still appear in clear form in memory at runtime? And de4dot renames things to `Class0` and `method_1` instead of restoring `CheckKey`, so why can't it recover the original names?

<div class="lab-box">
<div class="lab-head"><b>LAB 5.5</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/5.5/src/LicenseCheck.cs" download><i class="fa-solid fa-file-code"></i>src/LicenseCheck.cs</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The baseline before obfuscating. Build `LicenseCheck.cs` and open it in ILSpy or dnSpy. You see exactly what the source says:

```csharp
private static bool CheckKey(string key)
{
    if (key == null || key.Length != 12)
        return false;
    return key == "REVERSE-2024";
}
```

The names `CheckKey` and `Main` are intact. The strings `"REVERSE-2024"`, `"Valid key"` and `"Wrong key"` are right there in the Strings view. If all you want is the key, you read it in ten seconds. That's why people obfuscate.

After obfuscating with ConfuserEx. With the rename, control flow and constants presets, the obfuscated build in dnSpy shows several things. `CheckKey` becomes a name like `a` or a run of odd Unicode characters, and the type tree is nearly meaningless. The string `"REVERSE-2024"` is gone, replaced by a call like `<Module>.a(1234)` that returns a string, which is string encryption. The body of `CheckKey` is bent into a `switch` inside a `while(true)` with a state variable, which is control flow flattening, and the decompiler produces a lot of `goto`. Reading it directly is almost hopeless at this point.

Stripping with de4dot:

```
de4dot.exe <obfuscated-file>.exe
```

This produces `...-cleaned.exe`. Open the cleaned build in dnSpy and compare with the previous step. The strings are back, `"REVERSE-2024"` and `"Valid key"`, since de4dot ran static string decryption. The control flow is flattened back to something nearly linear, so you can read the logic `if (key.Length != 12) ... return key == "REVERSE-2024"`. The names don't go back to the originals but become `Class0`, `method_0`, `method_1`. That's enough to read, though not as nice as the source. If the original de4dot says it doesn't recognize the protector (a newer ConfuserEx), switch to de4dot-cex or a ConfuserEx unpacker matching the version. For .NET Reactor, use .NET Reactor Slayer. The correct key is `REVERSE-2024` (12 characters, which satisfies both the length check and the string comparison).

Tracing string decryption when the tool gives up. Say you meet a sample where de4dot removed the renaming but couldn't decrypt the strings. In dnSpy, first look for a static method of the form `string Xxx(int)` that is called everywhere, which is the decryption function. Set a breakpoint at its `return` and press F5. Each time it stops, Locals shows the real string and the input parameter. Build a `token -> string` table, for example `Xxx(1234)` returns `"REVERSE-2024"`. This works because by the time the key is compared, the program must have the clear string in memory.

Why must the string appear in clear at runtime? Because the CLR has to compare the key you typed with the original string, and to compare, the original has to exist as a `System.String` in memory at that moment. Encryption only postpones this. Whatever the program needs to use, it has to decrypt, and that's where we wait.

Why doesn't de4dot give back the original name `CheckKey`? Because renaming loses information. ConfuserEx throws the original name away and writes the new one into the metadata, and the old name is stored nowhere. de4dot can only generate new consistent, more readable names (`Class0`, `method_1`), and has no way of knowing what the original was. String encryption can be reversed because the algorithm and key sit inside the assembly, but a lost original name is gone for good.

</details>

## Key takeaways
Obfuscation doesn't encrypt the program, it only makes the decompiled code hard to read, and the program still has to run. The four common layers are renaming, string encryption, control flow, and anti-tamper/anti-debug. Identify the protector first (DIE/dnSpy) and then choose the tool.

de4dot is the first choice, de4dot-cex is for ConfuserEx, and Reactor Slayer is for .NET Reactor. If the tool doesn't strip everything, let the program decrypt itself: set a breakpoint after the Decrypt function and read the real strings in dnSpy. The goal is to read and understand the logic, not to restore perfect source.
