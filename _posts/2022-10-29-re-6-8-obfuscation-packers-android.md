---
title: "Lesson 6.8: Obfuscation and packers on Android"
image:
  path: /assets/img/covers/re-6-8-obfuscation-packers-android.webp
  alt: "Lesson 6.8: Obfuscation and packers on Android"
date: 2022-10-29 23:05:00 +0700
categories: ["Technique Reverse", "Part 06 · Java, Kotlin and Android"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
So far every APK you've opened shows clean Java code in JADX. Real apps are different: commercial apps are almost always obfuscated. You open one and it's all `a.a.a`, strings turn into piles of meaningless characters, and sometimes JADX doesn't even find the code. This lesson helps you recognize which kind of protection you're facing and how to get through it.

Beginners often lump two different things together: obfuscation (code is hard to read but still there) and packing (code is hidden entirely and only expanded at runtime). Each is handled differently.

## R8 and ProGuard: mostly renaming

Almost every Android app built in release mode goes through R8 (formerly ProGuard, now the default of the Android Gradle plugin). Its main job isn't anti-reversing but shrinking (minify) and optimizing: removing dead code, merging functions, and renaming classes/methods/fields to the shortest names possible to reduce size.

For a reverser it means you open JADX and see `a`, `b`, `c`, `a.a.b.c` everywhere. The logic is still intact and readable, you've just lost the meaningful names. This is the lightest level. It costs effort to rename things back as you understand each part, but it's all readable.

When building, R8 produces a `mapping.txt` mapping the original names to the shortened ones. It's used to decode crash reports. You almost never have it when reversing someone else's app, but if you're analyzing your own app, keeping `mapping.txt` gets you the original names right away.

You recognize R8/ProGuard by class and method names of one or two characters and nested packages like `a.a.a`. The third-party library names and the entry points the framework requires to be kept (Activities in the manifest, `onCreate` methods...) are still there, because those can't be renamed. The logic code is still continuous and readable.

## DexGuard and commercial obfuscators

DexGuard (the commercial version from the same maker as ProGuard) and a few similar tools add layers R8 doesn't. With string encryption, string literals are encrypted and only decrypted at runtime through a decryption function, so in JADX you see `decrypt("...")` or an incomprehensible byte array instead of the original string. Control flow obfuscation inserts junk branches and turns loops and ifs into tangled forms so the decompiler rebuilds them wrong or ugly. Class/API encryption and reflection hide real method calls behind reflection, so static xrefs break. And anti-tamper, anti-debug and anti-Frida check the app signature and detect debuggers and Frida.

At this level, pure static reading is often not enough. The practical way is dynamic analysis: let the app decrypt the strings itself and read the result at runtime, or hook the decryption function with Frida (see [Lesson 6.6](/posts/re-6-6-frida-android-changing-app-behavior-while/)) to print the decrypted strings.

## Packers: when the code isn't in the DEX

Packers confuse beginners the most. A packer (or "app shielding", "DEX protection") doesn't just obfuscate but hides the real code entirely. The `classes.dex` you see is just a shell (a loader stub). The real code is compressed or encrypted, stored in assets or a separate section, and only decrypted and loaded into memory at runtime.

Common packers (mostly from China because of the app market there) are Bangcle (SecShell), Qihoo Jiagu, Tencent Legu, Ali (Alibaba) protection, and Baidu. Many are free so malware uses them too.

Signs of a packed app: JADX shows almost nothing, only an odd Application class and a few class loaders, with no business logic anywhere. In `AndroidManifest.xml`, the `application` tag points to an odd packer `android:name` class (for example `com.secshell.shellwrapper...`, `com.stub.StubApp`, `com.qihoo...`), which is the loader that runs first. There's an oddly named `.so` file in `lib/`, and a large unexplained file in `assets/` (the encrypted DEX itself). The `classes.dex` is abnormally small for the complexity of the app, and the entropy of the file in assets is very high (a sign of compression/encryption, like PE packers in [Lesson 14.1](/technique-reverse/)).

## Removing a packer: dump the DEX at runtime

However well it's hidden, before running the real code the packer must decrypt the DEX and load it into memory for the Android runtime (ART) to execute. So at some moment, the decrypted DEX sits in the process memory. Your job is to grab it there.

The most popular tool is frida-dexdump. It scans the process memory for DEX magics (`dex\n035` and variants), then dumps each DEX to a file. The workflow:

```
# install frida-server on a rooted device/emulator, frida-dexdump on the host
frida-dexdump -U -f com.example.packed.app     # spawn the app and dump
# or attach to a running app:
frida-dexdump -U -n app_name
```

The result is one or more `.dex` files. Drag them into JADX and you see the real code. For stubborn packers that decrypt piece by piece (lazy), you may need to use the app for a while so the parts all load before dumping, or use more specialized tools (the upgraded FRIDA-DEXDUMP, or dedicated unpackers for each packer family).

This is the general idea in unpacking: don't try to decrypt manually, let the program decrypt itself and take the result. It comes back with PE packers in [Lesson 14.2](/technique-reverse/).

## When you meet an unfamiliar app

Open JADX first and check whether you see business logic. If you do but it's only ugly or renamed, that's obfuscation, so read and rename gradually, and hook with Frida when you meet encrypted strings. If JADX is completely empty, look at the `android:name` of `application` in the manifest and the files in `assets/lib`. If you recognize a packer's loader, you have to unpack. Dump the DEX at runtime with frida-dexdump, then go back to the first step with the expanded DEX.

## Lab

The task is to look at an APK and classify the level of protection it has, and if it's packed, to get the real DEX out. You need JADX-GUI. For the dump part, optionally have a rooted Android device or an emulator with `frida-server` running on it, and `frida` and `frida-dexdump` on the host (`pip install frida-tools frida-dexdump`). It helps to have a few APKs to compare: a debug build of your own app (not obfuscated), a release app from the Play Store (usually R8), and, if you can get one, an app that uses a packer. Only practice on your own apps or apps you're allowed to analyze.

Start with a quick classification. Open several APKs in JADX one after another and, for each one, answer whether the class and method names are meaningful or have become `a/b/c`, and whether you can read the business logic. From that, place it as not obfuscated, R8/ProGuard, a heavy obfuscator, or packed. For an app you suspect is packed, open `AndroidManifest.xml` in JADX and look at the `android:name` attribute of the `<application>` tag. Which class does it point to, and does the name match a known packer (StubApp, SecShell, qihoo, legu and so on)? Then list the files in `assets/` and `lib/` and ask which are large and hard to understand. Check them with an entropy tool (or DIE): an entropy close to 8.0 means the data is compressed or encrypted, so it may hold the real DEX.

If there's a packer, dump the DEX:

```
frida-dexdump -U -f <package_name>
```

Use the app for a few actions so the code gets fully loaded, then let the tool dump. Drag the resulting `.dex` files into JADX and confirm you now see the real logic. Finally put the two side by side, the JADX view of the packed app (nearly empty) and the dumped DEX (full code), and note the differences.

Two questions to think about. Why does a packer, however strong, have to let the real DEX appear in memory at least once? And if the packer decrypts the DEX piece by piece when needed (lazy loading), is one dump enough, and how do you get everything? Try it before opening the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Try it yourself before reading.

### Quick classification

This table lets you place each APK:

| What you see in JADX | Conclusion |
|---|---|
| Meaningful class, method and variable names, code reads like source | Not obfuscated (usually a debug build) |
| Names turned into `a`, `b`, `c`, packages like `a.a.a`, but the logic is still continuous and readable | R8/ProGuard (minify + rename) |
| Strings turned into `decrypt(...)` calls or byte arrays, tangled flow, lots of reflection | Heavy obfuscator (DexGuard and similar) |
| JADX almost empty, only an odd Application class and a few loaders | Packed |

To avoid mixing them up: R8 still lets you read the logic, just with ugly names, while a packer takes the logic away entirely.

### The loader in the manifest

In `<application android:name="...">`, the class it points to runs before any Activity. In a clean app this is usually the app's own Application class (or absent, using the default). In a packed app it's the packer's loader. Some common names are `com.stub.StubApp` (Jiagu / Qihoo 360), `com.secshell.shellwrapper.SecShellApplication` (Bangcle), `com.tencent.StubShell...` (Tencent Legu), and `s.h.e.l.l...` or random-looking names. If you see one of these, the app is almost certainly packed. This loader class decrypts and loads the real DEX.

### Assets and lib

A packer stashes the real DEX somewhere and encrypts it. Common places are a large file in `assets/` with a name like `ijiami.dat` or `libjiagu.so`, an unidentifiable blob, and a `.so` in `lib/<abi>/` doing the decryption (the decryption code is native to make it harder to read). Check the entropy (DIE, `ent`, or a small Python script): a value close to 8.0 bits/byte means the data is compressed or encrypted. A normal unencrypted DEX file has lower entropy and starts with the magic `dex\n035`, while a packer's blob doesn't.

### Dumping the DEX

```
frida-dexdump -U -f com.example.packed
```

`-U` uses the USB device and `-f` spawns the app by package name. The tool scans the process memory for the DEX magic and writes out `*.dex` files in the current directory. To attach to an already running app, use `-n <process name>` or `-p <pid>`. Drag the resulting `.dex` files into JADX and you now see the full classes and real logic, unlike the empty shell at the start. If the dump produces several DEX files, load them all into JADX (open multiple files at once), because the real code is scattered across them.

### Comparing

Side by side, the packed version in JADX has only the loader and no business code, while the dump has full classes and only now can you reverse the real logic. That's the difference between what you see on disk and what really runs.

### Answers to the questions

The real code has to appear in memory because the CPU and ART can only execute valid DEX bytecode. A packer can encrypt it on disk, but at run time it must decode it into a DEX form the runtime understands and load it. That moment is your chance to dump. With lazy loading, where the packer only decrypts a part when it's called, a single dump at startup will be incomplete. The fix is to use the app through many screens and functions to force the parts to load and then dump, or to hook the DEX load point (for example `DexFile` or `InMemoryDexClassLoader`) with Frida and grab each piece as it's loaded, instead of scanning once.

To sum up, classify before choosing your approach: for obfuscation you read and hook, for a packer you have to dump. The manifest `application` name and high-entropy assets are the two clearest packer signs. As with PE packers, let the program decrypt itself and then take the result from memory.

</details>

## Key takeaways
Tell obfuscation (code still there, just hard to read) from packing (code hidden, only expanded at runtime), because they're handled differently. R8/ProGuard is mostly renaming, the logic is still readable, and mapping.txt belongs to whoever built the app. DexGuard and commercial obfuscators add string encryption, control flow, and anti-debug, so use dynamic analysis to decrypt strings.

Packer signs are an empty JADX, an odd application class in the manifest, a large high-entropy file in assets, and an abnormally small classes.dex. Remove a packer by letting the app decrypt itself and then dumping the DEX from memory (frida-dexdump), then open JADX as usual.
