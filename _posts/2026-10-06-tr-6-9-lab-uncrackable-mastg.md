---
title: "Lesson 6.9: Big lab, solving OWASP UnCrackable Level 1 to 3"
date: 2026-10-06 08:52:00 +0700
categories: ["Technique Reverse", "Part 06 · Java, Kotlin and Android"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
This lesson pulls together everything in Part 6. Instead of a crackme I cooked up myself, this time we play with the standard deck the whole industry uses for practice: the OWASP UnCrackable App for Android, part of the MASTG (Mobile Application Security Testing Guide). Three levels, getting harder, and each level teaches exactly one group of techniques you just learned.

Why use this set and not some app out there: it's completely legal. Open source, made for learning, and OWASP encourages you to break it. There's no copyright or terms-of-service violation like when you touch a commercial app. This is a proper practice ground.

Download it officially from the MASTG repo (link in [labs/6.9/README.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/6.9/README.md)). Don't download random APKs from elsewhere, only the official build is clean and matches the challenge.

## General rules

All three apps show an input box, and if you type the right secret it reports success. The task: find the secret, or make the app believe you entered it correctly. There are two schools, and a good reverser knows both:

- **Static:** open the app in JADX, read the code, pull the secret out directly or understand the checking algorithm and compute backwards. No need to run the app.
- **Dynamic:** run the app on a device/emulator, use Frida to hook the exact checking function to read the real value or force it to return the right result.

The higher the level, the more the static route runs out of steam and the more you have to rely on dynamic, especially when the secret gets pushed down into native or the app actively fights you.

## Level 1: root detection and a secret in Java

Open `UnCrackable-Level1.apk` in JADX-GUI. Read `AndroidManifest.xml` to find the launcher activity (recall [Lesson 6.2](/posts/tr-6-2-cau-truc-apk/)), and from there trace into `MainActivity`.

Two things jump out right away:

1. **Root detection.** In `onCreate`, the app calls a few functions like `c.a()`, `c.b()`, `c.c()` that check whether the device is rooted (looking for the `su` file, checking `test-keys`, the Superuser folder). If it detects it, it shows a dialog and exits. This is the first line of defense, and it's weak.

2. **The verify function.** When you press the button, the app calls a function (usually `a.a(input)`) that compares the string you typed with a secret. Following the usual start-from-strings and find usage (`x`) routine in JADX (recall [Lesson 6.3](/posts/tr-6-3-jadx-gui-chuyen-sau/)), you trace to the comparison function.

### The static route
The check function decrypts the secret with AES using a hardcoded key embedded in the code, then compares against the input. Since both the key and the ciphertext are in the app, you copy the algorithm out, rerun it with Python or a small piece of Java, and print the secret. Once you've read it you have the answer, no need to install the app.

### The dynamic route
If you're too lazy to solve the AES, let the app run and hook it. But the app exits right away because of root detection, so first you have to neutralize that. Use Frida to hook the detection functions to return false, and hook `System.exit` too to be safe. Then hook the verify function to print the string it compares against, which is the secret. A sample script is in [labs/6.9/solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/6.9/solution.md).

Takeaway from Level 1: root detection is just a paper lock on the door. It stops ordinary users, but it can't stop someone holding Frida.

## Level 2: the secret goes down into a native .so

Level 2 looks like Level 1, but when you look for the verify function in JADX, it's declared `native`:

```java
public native boolean bar(byte[] bar);
```

That means the check logic is no longer in Java, it's in `lib/arm64-v8a/libfoo.so`. This is exactly the situation of [Lesson 6.7](/posts/tr-6-7-native-so-jni/).

### The static route
Extract `libfoo.so` (unpack the APK), open it in Ghidra in AArch64 mode (review [Lesson 1.9](/posts/tr-1-9-arm-arm64-co-ban/)). Find the JNI function by the name `Java_sg_vantagepoint_uncrackable2_..._bar` or, if it registers dynamically, go through `JNI_OnLoad` and `RegisterNatives`. Read that function and you'll see it compares the input bytes with a hardcoded string in the `.so`. Pull that string out and you're done.

### The dynamic route
Hooking native is a bit harder than Java but still doable. Two ways:
- Hook libc's `strcmp`/`memcmp` and print both operands when the app compares. The secret is exposed in the open, exactly like the trick of reading the two `cmp` operands in [Lesson 2.5](/posts/tr-2-5-x64dbg/) but at the native level.
- Hook the native `bar` function directly with `Interceptor.attach` at its address in the module.

Takeaway from Level 2: pushing the secret down to native slows down the static reader, but at runtime the bytes still have to pass through a comparison, and the comparison is always a good place for an ambush.

## Level 3: adding anti-tampering and anti-Frida

Level 3 is Level 2 plus active defenses, in the spirit of [Lesson 6.8](/posts/tr-6-8-obfuscation-android/) and a preview of the whole anti-reverse stage (Stage 3):

- **Anti-tampering:** the app checks its own APK signature and checksum. If you repack with apktool and re-sign (the way of [Lesson 6.4](/posts/tr-6-4-smali-apktool-repack/)), the signature changes, the app detects it and refuses to run. So the static repack route trips right here.
- **Anti-Frida:** the app probes for a running frida-server (scanning port 27042, looking for the string "frida" in maps, checking process names). If it sees one, it exits.

### The approach
This is where you have to remove the layers one at a time, in order:

1. **Get past anti-Frida first.** Hook early (early instrumentation, use `frida -f` to spawn rather than attaching late) the Frida-detection functions and make them return negative. Or use a renamed, different-port frida-server to dodge naive detection.
2. **Get past anti-tampering.** Hook the signature-check function to return the original app's value, or hook the checksum comparison function.
3. **Only then verify**, handled just like Level 2 (analyze the .so or hook the comparison).

The order matters: you can't hook verify if the app has already exited after detecting Frida. Remove the outermost defense first and work your way inward. This is exactly the mindset for handling combined layers of anti that [Lesson 15.10](https://github.com/Haind03/Technique-Reverse/tree/main/phan-15-anti-reverse) will cover in detail.

Takeaway from Level 3: when the app fights your tools, the match turns into layer removal. Be patient, one layer at a time, and always save the final comparison as your ambush point.

## Which route to choose

| Situation | Prefer |
|---|---|
| The secret is a hardcoded string in Java | Static, read it directly in JADX |
| There's a clear checking algorithm | Static, compute backwards (like the Lesson 3.6 keygen) |
| The secret is in a native .so | Static reading of the .so, or dynamic hooking of strcmp |
| The app fights you (anti-*) | Dynamic, remove layers one at a time with Frida |

Most beginners jump straight to Frida because it feels cool. My honest advice: try reading statically first. Many times the secret is right there, five minutes in JADX is faster than half an hour wrestling with frida-server.

## Key takeaways
- UnCrackable (MASTG) is a legal Android practice set, download it from the official repo.
- Level 1: weak root detection + secret in Java, reading statically or hooking is enough.
- Level 2: secret in a native .so, analyze the .so or hook strcmp/memcmp at runtime.
- Level 3: adds anti-tampering and anti-Frida, you have to remove layers from the outside in.
- Always consider the static route first, it's often much faster than dynamic.
- The final comparison is always the best ambush point, whether at the Java or native level.
