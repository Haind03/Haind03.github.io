---
title: "Lesson 6.8: Obfuscation and packers on Android"
date: 2022-10-29 23:05:00 +0700
categories: ["Technique Reverse", "Part 06 · Java, Kotlin and Android"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
So far every APK you open shows clean Java code in JADX. Reality is harsher: commercial apps are almost always obfuscated. You open one and it's all `a.a.a`, strings turn into piles of meaningless characters, and sometimes JADX doesn't even find the code. This lesson helps you recognize which kind of protection you're facing and, more importantly, how to get through it.

There are two very different groups that beginners often lump together: obfuscation (making code hard to read but still there) and packing (hiding the code entirely, only expanding it at runtime). Each group is handled differently.

## R8 and ProGuard: mostly renaming

Almost every Android app built in release mode goes through R8 (formerly ProGuard, now R8 is the default of the Android Gradle plugin). Its main job isn't anti-reversing but shrinking (minify) and optimizing: removing dead code, merging functions, and renaming classes/methods/fields to the shortest names possible to reduce size.

The consequence for a reverser: you open JADX and see `a`, `b`, `c`, `a.a.b.c` everywhere. The logic is still intact and readable, you've just lost all the meaningful names. This is the lightest level, completely readable, it just costs effort to rename things back as you understand each part.

One important detail: when building, R8 produces a `mapping.txt` mapping the original names to the shortened ones. This file is used to decode crash reports. You almost never have it when reversing someone else's app, but remember it exists: if you're analyzing your own app, keeping `mapping.txt` gets you the original names right away.

You recognize R8/ProGuard by class and method names of one or two characters and nested packages like `a.a.a`. The third-party library names and the entry points the framework requires to be kept (Activities in the manifest, `onCreate` methods...) are still there, because those can't be renamed. And the logic code is still continuous and readable.

## DexGuard and commercial obfuscators: much heavier

DexGuard (the commercial version from the same maker as ProGuard) and a few similar tools add layers R8 doesn't. With string encryption, string literals are encrypted and only decrypted at runtime through a decryption function, so in JADX you see `decrypt("...")` or an incomprehensible byte array instead of the original string. Control flow obfuscation inserts junk branches and turns loops and ifs into tangled forms so the decompiler rebuilds them wrong or ugly. Class/API encryption and reflection hide real method calls behind reflection, so static xrefs break. And anti-tamper, anti-debug and anti-Frida check the app signature and detect debuggers and Frida.

At this level, pure static reading is often not enough. The practical way is dynamic analysis: let the app decrypt the strings itself and read the result at runtime, or hook the decryption function with Frida (see [Lesson 6.6](/posts/re-6-6-frida-android-changing-app-behavior-while/)) to print the decrypted strings.

## Packers: when the code isn't in the DEX

This group confuses beginners the most. A packer (or "app shielding", "DEX protection") doesn't just obfuscate but hides the real code entirely: the `classes.dex` you see is just a shell (a loader stub). The real code is compressed or encrypted, stored in assets or a separate section, and only decrypted and loaded into memory at runtime.

Common packers (mostly from China because of the app market there) are Bangcle (SecShell), Qihoo Jiagu, Tencent Legu, Ali (Alibaba) protection, and Baidu. Many are free so malware uses them too.

There are several signs an app is packed. Opening JADX shows almost nothing: only an odd Application class and a few class loaders, with no business logic anywhere. In `AndroidManifest.xml`, the `application` tag points to an odd packer `android:name` class (for example `com.secshell.shellwrapper...`, `com.stub.StubApp`, `com.qihoo...`), which is the loader that runs first. There's an oddly named `.so` file in `lib/`, and a large unexplained file in `assets/` (the encrypted DEX itself). The `classes.dex` is abnormally small for the complexity of the app, and the entropy of the file in assets is very high (a sign of compression/encryption, like PE packers in [Lesson 14.1](/technique-reverse/)).

## Strategy for removing a packer: dump the DEX at runtime

The key: however well it's hidden, before running the real code the packer must decrypt the DEX and load it into memory for the Android runtime (ART) to execute. Meaning at some moment, the decrypted DEX sits right there in the process memory. Your job is to grab it there.

The most popular tool is frida-dexdump: it scans the process memory for DEX magics (`dex\n035` and variants), then dumps each DEX to a file. A tidy workflow:

```
# install frida-server on a rooted device/emulator, frida-dexdump on the host
frida-dexdump -U -f com.example.packed.app     # spawn the app and dump
# or attach to a running app:
frida-dexdump -U -n app_name
```

The result is one or more `.dex` files. Drag them into JADX and you see the real code. For stubborn packers that decrypt piece by piece (lazy), you may need to use the app for a while so the parts all load before dumping, or use more specialized tools (the upgraded FRIDA-DEXDUMP, or dedicated unpackers for each packer family).

This approach is an example of the general principle in unpacking: don't try to decrypt manually, let the program decrypt itself and take the result. You'll meet this exact mindset again with PE packers in [Lesson 14.2](/technique-reverse/).

## When you meet an unfamiliar app, ask in order

Open JADX first and check whether you see business logic. If you do but it's only ugly or renamed, that's obfuscation, so just read and rename gradually, and hook with Frida when you meet encrypted strings. If JADX is completely empty, look at the `android:name` of `application` in the manifest and the files in `assets/lib`. Recognizing a packer's loader tells you that you have to unpack. Then dump the DEX at runtime with frida-dexdump, and go back to the first step with the expanded DEX.

## Lab

See `labs/6.8/`: identify whether an APK is obfuscated or packed purely from the signs, and if there's a packer, dump the DEX with frida-dexdump and reopen it in JADX. The file `solution.md` has the writeup.

## Key takeaways
Tell obfuscation (code still there, just hard to read) from packing (code hidden, only expanded at runtime), because they're handled differently. R8/ProGuard is mostly renaming, the logic is still readable, and mapping.txt belongs to whoever built it. DexGuard and commercial obfuscators add string encryption, control flow, and anti-debug, so use dynamic analysis to decrypt strings.

Packer signs are an empty JADX, an odd application class in the manifest, a large high-entropy file in assets, and an abnormally small classes.dex. Remove a packer by letting the app decrypt itself and then dumping the DEX from memory (frida-dexdump), then open JADX as usual.
