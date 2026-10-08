---
title: "Lesson 6.9: Big lab, solving OWASP UnCrackable Level 1 to 3"
image:
  path: /assets/img/covers/re-6-9-big-lab-solving-owasp-uncrackable-level.webp
  alt: "Lesson 6.9: Big lab, solving OWASP UnCrackable Level 1 to 3"
date: 2022-04-29 04:07:00 +0700
categories: ["Reverse Engineering", "Part 06 · Java, Kotlin and Android"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
This lesson pulls together everything in Part 6. Instead of a crackme I made myself, we use the standard practice set the industry uses, the OWASP UnCrackable App for Android, part of the MASTG (Mobile Application Security Testing Guide). There are three levels, each harder than the last, and each one uses a group of techniques you just learned.

![OWASP UnCrackable levels and approaches](/assets/img/re/re-6-9-big-lab-solving-owasp-uncrackable-level.svg)
_The three UnCrackable levels, each with its static and dynamic route, converge on the final comparison._

I like this set because it's legal. It's open source, made for learning, and OWASP encourages you to break it. There's no copyright or terms-of-service problem like with a commercial app.

Download it from the official OWASP MASTG UnCrackable apps page (https://mas.owasp.org/crackmes/). Don't download random APKs from elsewhere, only the official build is clean and matches the challenge.

## General rules

All three apps show an input box, and if you type the right secret it reports success. The task is to find the secret, or make the app believe you entered it correctly. There are two approaches and you should know both. The static one is to open the app in JADX, read the code, pull the secret out directly or understand the checking algorithm and compute backwards, without running the app. The dynamic one is to run the app on a device or emulator and use Frida to hook the checking function, either to read the real value or to force it to return the right result.

The higher the level, the less the static route works and the more you need dynamic, especially when the secret is pushed down into native code or the app actively resists analysis.

## Level 1: root detection and a secret in Java

Open `UnCrackable-Level1.apk` in JADX-GUI. Read `AndroidManifest.xml` to find the launcher activity (see [Lesson 6.2](/posts/re-6-2-anatomy-apk-file/)), and from there trace into `MainActivity`.

Two things stand out. The first is root detection. In `onCreate`, the app calls a few functions like `c.a()`, `c.b()`, `c.c()` that check whether the device is rooted (looking for the `su` file, checking `test-keys`, the Superuser folder). If it detects root, it shows a dialog and exits. It's the first line of defense, and a weak one.

The second is the verify function. When you press the button, the app calls a function (usually `a.a(input)`) that compares the string you typed with a secret. Use the usual routine in JADX of starting from strings and finding usages with `x` (see [Lesson 6.3](/posts/re-6-3-jadx-gui-depth-number-one-tool/)) and you get to the comparison function.

### The static route
The check function decrypts the secret with AES using a hardcoded key in the code, then compares it against the input. Since both the key and the ciphertext are in the app, you copy the algorithm out, rerun it in Python or a small piece of Java, and print the secret. You don't even need to install the app.

### The dynamic route
If you don't want to bother with the AES, let the app run and hook it. It exits right away because of root detection, so neutralize that first. Use Frida to hook the detection functions to return false, and hook `System.exit` too to be safe. Then hook the verify function to print the string it compares against, which is the secret.

Root detection stops ordinary users, but it doesn't stop someone with Frida.

## Level 2: the secret goes down into a native .so

Level 2 looks like Level 1, but when you look for the verify function in JADX, it's declared `native`:

```java
public native boolean bar(byte[] bar);
```

That means the check logic is no longer in Java, it's in `lib/arm64-v8a/libfoo.so`. This is the situation from [Lesson 6.7](/posts/re-6-7-native-so-libraries-jni-where-logic/).

### The static route
Extract `libfoo.so` (unpack the APK) and open it in Ghidra in AArch64 mode (see [Lesson 1.9](/posts/re-1-9-arm-arm64-basics-people-who-already/)). Find the JNI function by the name `Java_sg_vantagepoint_uncrackable2_..._bar` or, if it registers dynamically, go through `JNI_OnLoad` and `RegisterNatives`. Read that function and you'll see it compares the input bytes with a hardcoded string in the `.so`. Pull that string out and you're done.

### The dynamic route
Hooking native code is a bit harder than Java but still doable. One way is to hook libc's `strcmp`/`memcmp` and print both operands when the app compares. The secret shows up in the clear, same idea as reading the two `cmp` operands in [Lesson 2.5](/posts/re-2-5-x64dbg-reversers-dynamic-scalpel-windows/) but at the native level. The other way is to hook the native `bar` function directly with `Interceptor.attach` at its address in the module.

Pushing the secret into native code slows down the static reader, but at runtime the bytes still have to go through a comparison, and the comparison is a good place to hook.

## Level 3: anti-tampering and anti-Frida

Level 3 is Level 2 plus active defenses, like in [Lesson 6.8](/posts/re-6-8-obfuscation-packers-android/) and a preview of the whole anti-reverse stage (Stage 3). The app does anti-tampering, checking its own APK signature and checksum. If you repack with apktool and re-sign (see [Lesson 6.4](/posts/re-6-4-smali-apktool-modifying-android-app-repacking/)), the signature changes, the app detects it and refuses to run, so the static repack route fails here. It also does anti-Frida checks, and it probes for a running frida-server (scanning port 27042, looking for the string "frida" in maps, checking process names) and exits if it sees one.

### The approach
You remove the layers one at a time, in order. Get past anti-Frida first. Hook early (use `frida -f` to spawn the app rather than attaching late) the Frida-detection functions and make them return negative, or use a renamed frida-server on a different port to dodge naive detection. Then get past anti-tampering by hooking the signature-check function to return the original app's value, or hooking the checksum comparison function. Only then do verify, handled just like Level 2 (analyze the .so or hook the comparison).

The order matters. You can't hook verify if the app has already exited after detecting Frida. Remove the outermost defense first and work inward. [Lesson 15.10](/reverse-engineering/) covers handling combined layers of anti in detail.

When the app resists your tools, it turns into layer removal. Be patient, go one layer at a time, and keep the final comparison as your hook point.

## Which route to choose

| Situation | Prefer |
|---|---|
| The secret is a hardcoded string in Java | Static, read it directly in JADX |
| There's a clear checking algorithm | Static, compute backwards (like the Lesson 3.6 keygen) |
| The secret is in a native .so | Static reading of the .so, or dynamic hooking of strcmp |
| The app resists analysis (anti-*) | Dynamic, remove layers one at a time with Frida |

Most beginners jump straight to Frida because it feels cool. I'd try reading statically first. Often the secret is right there, and five minutes in JADX is faster than half an hour troubleshooting frida-server.

## Lab

This lab uses the official OWASP MASTG practice apps, UnCrackable Level 1 to 3. They are legal, open source and built for practicing analysis. Download them only from the official MASTG sources, the crackme page at https://mas.owasp.org/crackmes/ or the GitHub repo https://github.com/OWASP/owasp-mastg (the Crackmes folder). You need three files, `UnCrackable-Level1.apk`, `UnCrackable-Level2.apk` and `UnCrackable-Level3.apk`.

For tooling you need JADX-GUI, an emulator or test device (an emulator is safer, see Lesson 0.3), Frida plus a frida-server matching the emulator architecture for the dynamic route, Ghidra for Level 2 to analyze the bundled native library, and apktool plus apksigner if you want to try the repack route.

On Level 1, open the APK in JADX and read the manifest to find the launcher activity. Find the root detection code in `onCreate`, then find the function that checks the string you type. For the static route, work out how the reference value is produced and compute it by hand. For the dynamic route, write a Frida script that neutralizes the root detection and the process exit call, then observes the check function so you can see what it compares against.

On Level 2, find the check function and confirm it is declared `native`. Extract `lib/arm64-v8a/libfoo.so` from the APK, open it in Ghidra (AArch64), and find the matching JNI function, either by name or through `JNI_OnLoad` plus `RegisterNatives`. For the static route, read the native function and work out the comparison value it holds. For the dynamic route, observe libc's `strcmp`/`memcmp` calls and their arguments, or observe the native function directly.

On Level 3, identify the two extra defensive layers, a tamper check (comparing a signature or checksum) and a check that looks for Frida itself. Deal with the Frida-detection layer first, typically by spawning the app under Frida so your script attaches before that check runs, and by observing the detection function. Then deal with the tamper check by observing the signature-check function. Once both layers are quiet, work through the verification the same way as on Level 2.

Some questions worth thinking through afterward are why the apktool repack route fails on Level 3 while an attach-time Frida session doesn't, when static reading is faster than a dynamic hook and when it is the other way around, and why the final comparison call is always a natural point to observe.

Do the levels yourself first. The walkthrough is in the solution below.


<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Try it yourself before reading this. The write-up below describes the approach rather than exact bypass code, since class names and offsets shift a little between APK builds. The method matters more than any one address. It follows OWASP's own public MASTG material and the documented structure of these three training apps. Run the steps on your own emulator and confirm each result there.

On Level 1, the launcher activity is `sg.vantagepoint.uncrackable1.MainActivity`. In `onCreate` it runs three root checks (looking for test-keys in the build tags, looking for an `su` binary on PATH, looking for the Superuser package), and if any of them trips it shows a "Root detected!" message and exits. Pressing the button runs a helper class that decrypts a hardcoded, base64-encoded value with AES using a key that is also hardcoded, and compares the result against what you typed. Because both the ciphertext and the key sit in the decompiled code, you can reproduce the same AES/ECB decryption offline with a short script and read the plaintext it produces. On the dynamic route, a Frida script attached before the checks run can neutralize the exit call and the root-detection branch, and then observe the comparison itself (for example by watching calls to `String.equals`) to see the reference value the app is comparing against, without ever needing to find the key or ciphertext by hand.

On Level 2, `MainActivity` loads a native library and declares a native method. The check has moved out of Java and into `libfoo.so`. After extracting the .so and opening it in Ghidra, you look for the matching JNI function, either directly by its `Java_...` name or, if the app registers natives dynamically, by reading `JNI_OnLoad` to find the `RegisterNatives` table that maps the Java method name to the real function pointer. Reading that function shows it comparing the input byte by byte against a fixed array, which you can decode by hand. On the dynamic route, hooking libc's `strcmp` (or `memcmp`, depending on the build) and printing both arguments on every call gets the same result without reading any disassembly. Type an arbitrary string and the log shows the real value the app compares it against.

Level 3 adds two more layers on top of the same underlying check. The anti-Frida layer typically scans for signs of a frida-server process, such as a listening port or a recognizable string in `/proc/self/maps`. The usual way around it is to attach before the app has a chance to run that check (spawning rather than attaching to an already-running process), and to observe or neutralize the specific detection function once you've located it. The tamper-detection layer reads the APK's own signature through the Android package manager and compares it against a hardcoded expected value baked in at build time. That's why a repack-and-resign approach fails here, because changing and resigning the APK produces a different signature, and this check catches it immediately. Working purely in memory at runtime, the way Frida does, never touches the signature on disk, so it isn't caught the same way. Once both layers are out of the way, the underlying verification is read and solved exactly as in Level 2.

On the reflection questions, repacking fails because it changes the file on disk and therefore its signature, which the tamper check is built to catch, while an attached debugger or instrumentation tool modifies only runtime behavior and leaves the on-disk file and its signature untouched. Static reading tends to win when the reference value or algorithm is simple and sits in reachable code. Dynamic observation tends to win once the app pushes the logic into native code, encrypts it, or otherwise makes static reading expensive compared with just watching the comparison happen. The final comparison call is a reliable place to watch because no matter how well a value is hidden earlier in the program, by the time it's compared against your input both sides have to exist as plain data in memory for that instant.

</details>

## Key takeaways
UnCrackable (MASTG) is a legal Android practice set, so download it from the official OWASP MASTG UnCrackable apps page. Level 1 has weak root detection plus a secret in Java, and reading statically or hooking is enough. Level 2 has the secret in a native .so, so analyze the .so or hook strcmp/memcmp at runtime. Level 3 adds anti-tampering and anti-Frida, and you have to remove layers from the outside in.

Try the static route first, since it's often much faster than dynamic. The final comparison is the best place to hook, whether at the Java or native level.
