---
title: "Lesson 6.4: Smali and apktool, modifying an Android app and repacking it"
date: 2026-10-06 08:47:00 +0700
categories: ["Technique Reverse", "Part 06 · Java, Kotlin and Android"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
JADX lets you read Android code as nice Java, but it's only for reading. When you really want to change the app's behavior and reinstall it, you can't edit that Java. The reason is simple: there's no clean path back from decompiled Java to DEX. What you can edit, and repack, is smali. This lesson is the classic patching workflow that almost every Android crackme ends up using.

## What smali is, and why you have to learn it

Android doesn't run JVM bytecode but DEX bytecode (Dalvik/ART). Smali is the assembly language for DEX: each smali instruction corresponds to one bytecode instruction, one for one. It's the lowest level a human can still read and edit comfortably.

The difference to remember compared with the x86 assembly in earlier lessons: DEX is register-based, not stack-based. Meaning instead of push/pop on a stack, each method has a numbered series of virtual registers ready, and instructions operate on them directly.

There are two groups of registers:
- `p0, p1, p2...` are the parameters passed into the method. For a non-static method, `p0` is `this`.
- `v0, v1, v2...` are local registers for computation.

At the start of each method it declares how many local registers it needs, for example `.registers 4` or `.locals 2`.

## Basic smali syntax

You don't need to memorize it all, just recognize the common groups:

```smali
.method public check(Ljava/lang/String;)Z   # takes a String, returns boolean (Z)
    .registers 3                              # p0=this, p1=parameter, v0=local

    const-string v0, "secret123"              # v0 = "secret123"
    invoke-virtual {p1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0                            # put the result of equals() into v0
    return v0                                 # return v0
.end method
```

Compare with Java:

```java
public boolean check(String input) {
    return input.equals("secret123");
}
```

Those abbreviations like `Z`, `Ljava/lang/String;` are DEX type descriptors: `Z`=boolean, `I`=int, `V`=void, `Ljava/lang/String;`=class String. You'll read them smoothly once you're used to them.

The group of instructions you touch often when patching:
- `const/4 v0, 0x1` loads a small constant (here 1) into v0.
- `const/4 v0, 0x0` loads 0.
- `invoke-virtual {...}, ...` calls a method.
- `move-result v0` puts the return value of the last call into v0 (like "rax is the return value" in x86 assembly).
- `if-eqz v0, :label` jumps to the label if v0 equals 0 (equal zero). `if-nez` is not zero.
- `return v0` / `return-void` returns.

Recognizing the `invoke` then `move-result` then `if-eqz` sequence means you're looking at exactly an if statement based on a function's result, just like the `cmp`/`je` pair in x86.

## The classic patching workflow

![APK patching workflow: apktool d, edit smali, apktool b, re-sign](/assets/img/technique-reverse/assets/phan-06/smali-patch-flow.svg)

Say the app has a license check function that returns a boolean, and false blocks you. The goal: make it always return true.

Four steps, remember them and you can do it:

1. Unpack the APK into smali:
   ```
   apktool d target.apk -o target_out
   ```
   apktool translates classes.dex into a tree of `.smali` folders, and also decodes AndroidManifest into a readable form.

2. Find the check function. Use JADX to read the Java to learn the class/method names first, then open the matching smali file in `target_out/smali/...`. Grep the method name to be quick.

3. Edit the smali so the function always returns true. The cleanest way is to replace the whole function body with a return of 1:
   ```smali
   .method public isLicensed()Z
       .registers 2
       const/4 v0, 0x1      # force v0 = true
       return v0            # just return true
   .end method
   ```
   Or if you only want to flip one branch, find the `if-eqz`/`if-nez` and swap them, or change `const/4 v0, 0x0` to `const/4 v0, 0x1` right before the return. Keep the declared register count large enough or the build fails.

4. Rebuild and sign. This is where beginners often forget:
   ```
   apktool b target_out -o patched.apk
   ```
   The APK you just built is NOT signed, and Android refuses to install an unsigned app. You have to sign it again:
   ```
   apksigner sign --ks my.keystore patched.apk
   ```
   or use `uber-apk-signer -a patched.apk` to be quick (it creates a debug key itself). Only after signing can you `adb install patched.apk`.

The biggest trap in the whole workflow isn't in the smali but in the signature: forget to sign and it won't install, and if the app checks its own signature (anti-tamper) then re-signing with a different key gets detected. Getting past anti-tamper is left to the obfuscation lesson [6.8](/posts/tr-6-8-obfuscation-android/) and the Frida part.

## When to patch smali, when to use Frida

Patching smali produces a permanently modified APK, install it and it runs, no tools needed at runtime. The downside: you have to rebuild and re-sign, and you run into anti-tamper.

Frida (lesson [6.6](/posts/tr-6-6-frida-android-hook/)) hooks at runtime, needs no file edits, and is much more flexible for experimenting, but needs the Frida server running on the machine/device. Android RE folks use both: Frida for quick research, smali patching when they want a modified build that stands on its own.

## Lab

See [labs/6.4/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/6.4). You'll take an APK with a check function, use apktool to unpack it into smali, find and patch that function to always return true, rebuild, sign, then verify. The solution is in `solution.md`.

## Key takeaways
- Android runs DEX (register-based), not JVM bytecode. Smali is the assembly for DEX.
- Edit smali, not the decompiled Java, because there's no clean path from Java back to DEX.
- Registers: `p0` is this (non-static method), `p1...` are parameters, `v0...` are locals.
- `move-result` takes the return value of the last call, like rax in x86.
- Patch "always return true": `const/4 v0, 0x1` then `return v0`.
- Workflow: `apktool d`, edit smali, `apktool b`, then you MUST re-sign (apksigner/uber-apk-signer).
