---
title: "Lesson 6.3: JADX-GUI in depth, the number one tool for taking apart APKs"
date: 2023-10-11 20:35:00 +0700
categories: ["Technique Reverse", "Part 06 · Java, Kotlin and Android"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
If .NET reversing has dnSpy, Android reversing has JADX. Open an APK, wait a few seconds, and almost the whole Java source shows up. But most beginners only use JADX at the level of "open it and scroll to read", wasting the features that make the difference between sitting there for a whole session and finding what you need in ten minutes. This lesson is about those features.

JADX is already in this repo at `jadx-gui-1.5.1-win`, just run `jadx-gui.exe`, no installation needed.

## What it can open

JADX swallows quite a lot of formats, and you just drag and drop. With an APK, it unpacks it itself, merges every `classes.dex` (including multidex), decompiles to Java, and also parses `AndroidManifest.xml` and the resources. It also opens a bare DEX file, ordinary JVM bytecode in JAR or .class files, and other packaging forms like AAB, ZIP, and XAPK.

With an APK, the first thing to do is open `AndroidManifest.xml` in the Resources tree and look for the activity with `android.intent.action.MAIN` to know the launch screen, which is the app's entry point. This habit is like looking for `main` when reversing native code.

## The left tree and two ways of viewing code

The left panel has two main branches: Source code (the decompiled Java packages) and Resources (manifest, strings, layouts, files in assets). Click a class and the right panel shows Java.

Something many people don't know: you can view smali side by side. Right-click a class and choose to view bytecode/smali, or turn on the mode that shows both. When JADX decompiles wrong (with tangled or obfuscated code), smali is the truth and Java is just a translation that can be faulty. When in doubt, drop down to smali to cross-check.

## Three shortcuts that make the speed

Like the `N`/`X`/comment trio in IDA, JADX has its own set of keys. See also the [cheatsheet](/posts/re-resources-cheatsheet-shortcuts-quick-reference/).

Global search (Ctrl+Shift+F) searches text across all the decompiled code, and it's the number one weapon. See the app show "License invalid"? Search that string and jump straight to the class that uses it. Find usage (`x`) works when you put the cursor on a method, field, or class and press `x` to see everywhere it's used. This is JADX's xref, how you trace backwards from a function to where it's called.

Rename (`n`) changes the name of classes, methods, fields, and variables to make them readable. JADX remembers the names you set for the whole session, and each good name makes the code around it light up. For an app obfuscated into `a.a.a`, rename is the only way to keep your head from exploding.

## Start from strings, the fastest way into the work

Like every other platform, the fastest way to find important logic is to start from strings the user sees. On Android, strings usually live in two places. If they're hard-coded in code, search directly with Ctrl+Shift+F. If they're in `res/values/strings.xml` and the displayed string is a resource, find the resource name (for example `login_failed`), get the resource ID, then search for that ID (as `R.string.login_failed` or the hex value `0x7f...`) in the code.

Finding a string like "Wrong password" or "Premium activated" gets you almost exactly to the check. From there press `x` to trace back up to the calling function.

## Automatic deobfuscation

Real apps almost always go through R8/ProGuard, turning names into `a`, `b`, `c`. JADX has an automatic renaming feature: go to Preferences, turn on Deobfuscation, and set the minimum/maximum name length thresholds. JADX will generate consistent fake names (like `C0001a`) in place of colliding one-character names, helping you tell them apart. It doesn't restore the original names (they were lost at build time), but it makes the code less chaotic and lets you rename gradually.

For heavier obfuscation (string encryption, control flow) JADX gives up on that part, and you have to go the dynamic route (Frida, see [Lesson 6.6](https://github.com/Haind03/Technique-Reverse/blob/main/phan-06-java-kotlin-android/6.6-frida-android-hook-bypass.md)) or other tools. Details on the types of obfuscation are in [Lesson 6.8](https://github.com/Haind03/Technique-Reverse/blob/main/phan-06-java-kotlin-android/6.8-obfuscation-android-r8-packer.md).

## Copy as Frida snippet, the bridge to dynamic hooking

This is a JADX feature mobile people really like. Right-click a method and choose Copy as Frida snippet, and JADX generates a ready-made piece of JavaScript that hooks that method with Frida, with the right class name and the right parameter signature. You just paste it into a Frida script and add logic to print the parameters or change the return value.

For example it generates a skeleton like:

```javascript
Java.perform(function () {
    var LoginActivity = Java.use("com.example.app.LoginActivity");
    LoginActivity.checkPassword.implementation = function (input) {
        console.log("checkPassword called with: " + input);
        var ret = this.checkPassword(input);
        console.log("returned: " + ret);
        return ret;
    };
});
```

This is how you connect static (JADX reading the code) to dynamic (Frida observing/modifying at runtime). Find the function in JADX, generate the snippet, hook it to see the real values or force it to return `true`.

## Export the source to grep

When you want stronger searching than the GUI offers, or want to open it in a familiar editor, use File > Save all (Ctrl+Shift+S) so JADX exports the whole Java source to a folder. Then `grep -r` freely, or open it in VS Code to navigate. Very handy when you want to find a complex pattern (for example everywhere that calls `Cipher.getInstance`).

## Lab

Do it in [labs/6.3/](https://github.com/Haind03/Technique-Reverse/blob/main/labs/6.3): open an APK with JADX-GUI, go from a string to the code, rename things to make them readable, generate a Frida snippet for a method, and export the source to grep.

## Key takeaways
JADX opens APK/DEX/JAR/AAB, merges multidex automatically, and parses the manifest. Open AndroidManifest and look for the MAIN activity to know the app's entry point. The three main keys are Ctrl+Shift+F (global search), `x` (find usage, which is the xref), and `n` (rename).

Start from the strings the user sees, going through the resource ID if needed, then press `x` to trace back to the check function. Turn on Deobfuscation to soften one-character names, though the original names are gone. Use Copy as Frida snippet to connect to dynamic hooking, and Save all to export the source for grepping outside the GUI. When the decompiled Java looks wrong, cross-check with smali.
