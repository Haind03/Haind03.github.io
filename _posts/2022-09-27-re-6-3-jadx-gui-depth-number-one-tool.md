---
title: "Lesson 6.3: JADX-GUI in depth"
image:
  path: /assets/img/covers/re-6-3-jadx-gui-depth-number-one-tool.webp
  alt: "Lesson 6.3: JADX-GUI in depth"
date: 2022-09-27 15:29:00 +0700
categories: ["Reverse Engineering", "Part 06 · Java, Kotlin and Android"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
.NET reversing has dnSpy, Android reversing has JADX. Open an APK, wait a few seconds, and almost the whole Java source shows up. But most beginners only use it as "open it and scroll", and miss the features that turn a whole session into ten minutes. This lesson covers those features.

JADX comes as a portable download. Just run `jadx-gui.exe`, no installation needed.

## What it can open

JADX takes quite a lot of formats, and you just drag and drop. With an APK, it unpacks it, merges every `classes.dex` (including multidex), decompiles to Java, and also parses `AndroidManifest.xml` and the resources. It also opens a bare DEX file, ordinary JVM bytecode in JAR or .class files, and other packaging forms like AAB, ZIP, and XAPK.

With an APK, the first thing I do is open `AndroidManifest.xml` in the Resources tree and look for the activity with `android.intent.action.MAIN` to know the launch screen, which is the app's entry point. It's like looking for `main` when reversing native code.

## The left tree and two ways of viewing code

The left panel has two main branches, Source code (the decompiled Java packages) and Resources (manifest, strings, layouts, files in assets). Click a class and the right panel shows Java.

Many people don't know you can view smali side by side. Right-click a class and choose to view bytecode/smali, or turn on the mode that shows both. When JADX decompiles wrong (tangled or obfuscated code), smali is the real thing and Java is just a translation that can be faulty. When in doubt, drop down to smali to cross-check.

## Three shortcuts

Like the `N`/`X`/comment keys in IDA, JADX has its own set. See also the [cheatsheet](/posts/re-resources-cheatsheet-shortcuts-quick-reference/).

Global search (Ctrl+Shift+F) searches text across all the decompiled code, and it's the one I use most. If the app shows "License invalid", search that string and jump straight to the class that uses it. Find usage (`x`) works when you put the cursor on a method, field, or class and press `x` to see everywhere it's used. This is JADX's xref, and it's how you trace backwards from a function to where it's called.

Rename (`n`) changes the name of classes, methods, fields, and variables. JADX remembers the names you set for the whole session, and each good name makes the code around it easier to read. For an app obfuscated into `a.a.a`, rename is the only way to stay sane.

## Start from strings

Like on every other platform, the fastest way to find important logic is to start from strings the user sees. On Android, strings usually live in two places. If they're hard-coded in code, search directly with Ctrl+Shift+F. If they're in `res/values/strings.xml` and the displayed string is a resource, find the resource name (for example `login_failed`), get the resource ID, then search for that ID (as `R.string.login_failed` or the hex value `0x7f...`) in the code.

Finding a string like "Wrong password" or "Premium activated" gets you almost exactly to the check. From there press `x` to trace back up to the calling function.

## Automatic deobfuscation

Real apps almost always go through R8/ProGuard, which turns names into `a`, `b`, `c`. JADX has an automatic renaming feature. Go to Preferences, turn on Deobfuscation, and set the minimum/maximum name length thresholds. JADX generates consistent fake names (like `C0001a`) in place of colliding one-character names, so you can tell them apart. It doesn't restore the original names (they were lost at build time), but it makes the code less chaotic and lets you rename gradually.

For heavier obfuscation (string encryption, control flow) JADX gives up on that part, and you have to go dynamic (Frida, see [Lesson 6.6](/reverse-engineering/)) or use other tools. Details on the types of obfuscation are in [Lesson 6.8](/reverse-engineering/).

## Copy as Frida snippet

Mobile people really like this JADX feature. Right-click a method and choose Copy as Frida snippet, and JADX generates a ready-made piece of JavaScript that hooks that method with Frida, with the right class name and parameter signature. You paste it into a Frida script and add logic to print the parameters or change the return value.

For example it generates a template like:

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

This connects static (JADX reading the code) to dynamic (Frida observing/modifying at runtime). Find the function in JADX, generate the snippet, then hook it to see the real values or force it to return `true`.

## Export the source to grep

When you want stronger searching than the GUI offers, or want to open it in a familiar editor, use File > Save all (Ctrl+Shift+S) so JADX exports the whole Java source to a folder. Then `grep -r` freely, or open it in VS Code. It helps when you want to find a complex pattern (for example everywhere that calls `Cipher.getInstance`).

## Lab

The goal is to use JADX-GUI's main features instead of just scrolling and reading. You need JADX-GUI (it needs a Java runtime) and an APK to practice on. A safe choice is an open-source APK, for example from F-Droid, or a practice app such as OWASP UnCrackable Level 1, which comes back in Lesson 6.9. Avoid commercial copyrighted APKs.

Drag the APK into JADX-GUI and open `Resources/AndroidManifest.xml`. Find the activity whose `intent-filter` has `action.MAIN` and `category.LAUNCHER` and write down the launcher activity class. Next, pick a string that the app displays (an error message, a button label) and search for it with Ctrl+Shift+F. If it's a resource, find its name in `strings.xml`, search for `R.string.<name>` and jump to the class that uses it. Then put the cursor on a suspicious method, for example one whose name contains `check`, `verify` or `login`, and press `x` to see every place that calls it, tracing back to where the logic is decided.

After that, rename at least three obfuscated classes or methods (one-letter names) to meaningful ones and see how the code around them gets clearer. Open Preferences, turn on deobfuscation, set the name threshold, and compare the class tree before and after. Right-click a method and choose Copy as Frida snippet, save the JavaScript and work out what it hooks. Finally, export the source with File > Save all (Ctrl+Shift+S), run `grep -r "Cipher.getInstance"` or `grep -ri "http"` on the exported folder, and see what turns up that is hard to spot by scrolling.

Some questions to think about. Why is starting from strings faster than reading sequentially from the top? When the Java that JADX shows looks absurd (extra variables, strange flow), how do you verify it? And does JADX's deobfuscation give back the original names, and why or why not?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This describes the standard workflow, and the concrete results depend on the APK you chose.

To locate the entry point, the launcher activity block in `AndroidManifest.xml` looks like this:

```xml
<activity android:name="com.example.app.MainActivity">
    <intent-filter>
        <action android:name="android.intent.action.MAIN"/>
        <category android:name="android.intent.category.LAUNCHER"/>
    </intent-filter>
</activity>
```

The class `com.example.app.MainActivity` is where the app starts. Double-click the name to jump to it in Source code, and `onCreate` is the first point of execution.

To go from a string to code, press Ctrl+Shift+F on the displayed string. There are two cases. If the string is hard-coded, JADX jumps straight to the line that uses it. If it's a resource, find it in `res/values/strings.xml`, for example `<string name="login_failed">Wrong credentials</string>`, take the name `login_failed` and search for `R.string.login_failed`. JADX also shows the resource ID in the form `0x7f...`, and searching for that ID works too. The place that uses the "failure" string usually sits right after an `if` condition, and that condition is the check itself.

For find usage, press `x` on a method such as `checkPassword` to get the list of every caller. Often there's a single caller, the handler of the Login button. Go there and you see the whole flow, which is to take the input, call the check, branch on the result.

For renaming, an obfuscated app shows things like `a.a.b(String)`. Once you understand what `b` does, press `n` and rename it to `validateSerial`. JADX updates every reference. After a few of these you can read the logic.

With deobfuscation on, classes `a`, `b`, `c` that share names across different packages get consistent fake names such as `C0001a`, `C0002b`. These aren't the original names, which R8 removed at build time, but they tell the entities apart and avoid confusion.

The Frida snippet is a template like the one in the lesson. It hooks the right class and method and prints the arguments and return value. You can change `return ret;` to `return true;` to force the check to pass when running on a real device (Frida details are in Lesson 6.6).

After Save all, you can search the export:

```bash
grep -rl "Cipher.getInstance" jadx_output/sources/   # find every use of crypto
grep -rn "http://" jadx_output/sources/               # find hard-coded URLs
grep -rn "SharedPreferences" jadx_output/sources/     # find where state is stored
```

This catches patterns that are hard to see while scrolling in the GUI, for example an app that stores a "purchased" flag in SharedPreferences.

On the questions, starting from strings is faster because a string is a clue the user can see and it connects straight to the relevant logic, whereas reading sequentially means wading through a lot of unrelated initialization and UI code. You verify suspicious Java by comparing against smali (what the bytecode really says), or by hooking dynamically with Frida to see the real values at runtime. Deobfuscation doesn't restore the original names, because R8 and ProGuard delete them at build time unless you have a mapping file. JADX only generates consistent fake names to make things easier to tell apart.

</details>

## Key takeaways
JADX opens APK/DEX/JAR/AAB, merges multidex automatically, and parses the manifest. Open AndroidManifest and look for the MAIN activity to find the app's entry point. The three main keys are Ctrl+Shift+F (global search), `x` (find usage, which is the xref), and `n` (rename).

Start from the strings the user sees, going through the resource ID if needed, then press `x` to trace back to the check function. Turn on Deobfuscation to soften one-character names, though the original names are gone. Use Copy as Frida snippet to connect to dynamic hooking, and Save all to export the source for grepping outside the GUI. When the decompiled Java looks wrong, cross-check with smali.
