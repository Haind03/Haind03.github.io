---
title: "Lesson 6.6: Frida on Android"
image:
  path: /assets/img/covers/re-6-6-frida-android-changing-app-behavior-while.webp
  alt: "Lesson 6.6: Frida on Android"
date: 2022-10-21 21:39:00 +0700
categories: ["Reverse Engineering", "Part 06 · Java, Kotlin and Android"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
Reading an APK statically in JADX tells you what the app intends to do. But often you want to see a value at runtime, or change a function's result to see how the app reacts, without patching and repackaging the whole APK. That's what Frida is for. It lets you step into any Java method while the app runs, read the arguments and change the return value, all in a few lines of JavaScript.

First, the boundary. This lesson is security testing technique. Use it on your own apps, apps you're authorized to test, or practice apps like OWASP UnCrackable. Hooking to bypass the licensing checks of someone else's app, or cheating in online games, is a different matter and outside the scope of this series.

## How Frida works

Frida is a dynamic instrumentation toolkit. On Android there are two parts. frida-server is a binary that runs on the device (usually needs root) or on an emulator, and it injects code into the app process. frida / objection run on your computer (the host), talk to frida-server over USB or TCP, and load your script into the app.

You write scripts in JavaScript. Frida injects a JS engine into the app process, and from inside it your script can call into the Android runtime and grab Java classes and methods using Java syntax.

## Setting up the environment

The minimum steps, assuming you already have an emulator or a rooted device:

```bash
# on the host
pip install frida-tools

# download frida-server for the device's architecture (e.g. arm64) from Frida's GitHub
# push it to the device and run it
adb push frida-server /data/local/tmp/
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "su -c /data/local/tmp/frida-server &"

# check that the host sees the device
frida-ps -U        # list processes over USB
```

If `frida-ps -U` lists the apps, the environment works. The frida-server version has to match the frida-tools version on the host. A mismatch errors out right away, and it's the most common mistake for beginners.

## Hooking Java methods: three patterns

Every Android script starts with `Java.perform`. Inside it you get a class with `Java.use`, then override the method's implementation. The three most common jobs:

### 1. Change the return value

Say the app has `SecurityCheck.isRooted()` returning `true` when it detects a rooted device, and the app refuses to run. You hook it so it always returns `false`:

```javascript
Java.perform(function () {
    var SecurityCheck = Java.use("com.example.app.SecurityCheck");
    SecurityCheck.isRooted.implementation = function () {
        console.log("[*] isRooted() called, forcing false");
        return false;   // ignore the real value, return what we want
    };
});
```

### 2. Log arguments and the real result

When you want to understand what a function takes and returns without changing behavior, call the original method and then print:

```javascript
Java.perform(function () {
    var Checker = Java.use("com.example.app.LicenseChecker");
    Checker.validate.implementation = function (input) {
        console.log("[*] validate() input = " + input);
        var ret = this.validate(input);   // call the original
        console.log("[*] validate() returned = " + ret);
        return ret;
    };
});
```

`this.validate(input)` calls the original method. That lets you observe without breaking the logic, which is handy for tracing out a checking algorithm.

### 3. Overloaded methods

If a method has several overloads, Frida makes you specify the signature, otherwise it errors with ambiguous:

```javascript
var Util = Java.use("com.example.app.Util");
Util.check.overload("java.lang.String", "int").implementation = function (s, n) {
    return true;
};
```

Run the script:

```bash
frida -U -f com.example.app -l hook.js        # spawn the app with the script
# or attach to a running app:
frida -U com.example.app -l hook.js
```

`-f` spawns the app from the start (catching early-running code too), while attach hooks into a live process.

## JADX generates the snippet for you

You don't need to type long class names by hand. In JADX-GUI (lesson [6.3](/posts/re-6-3-jadx-gui-depth-number-one-tool/)), right-click a method and choose **Copy as Frida snippet**. It generates the `Java.use(...).implementation` template with the right class and signature, and you paste it into the script and fill in the body. It's the fastest way to go from "found the function in the decompiler" to "hooked it".

## SSL pinning

Many apps pin certificates (SSL pinning) to reject every connection that doesn't use a predefined certificate. That's good for security, but when you're testing your own app and want to see the traffic through Burp/mitmproxy, pinning blocks you too. In testing you hook the certificate checking layer so it accepts your proxy.

The fastest way is objection, an automation layer built on Frida:

```bash
pip install objection
objection -g com.example.app explore
# inside the objection shell:
android sslpinning disable
android root disable
```

These two commands bundle a lot of common hooks for pinning and root detection, so you don't write them yourself. When objection can't handle an unusual mechanism, go back to writing a manual Frida hook for that layer.

## Common pitfalls

The first is a version mismatch between frida-server and frida-tools, which gives confusing errors, so check it first. The second is a class that isn't loaded yet when you hook it. Use `-f` to spawn early, or hook the ClassLoader. Third is obfuscated names. If the app is renamed by R8/ProGuard (lesson [6.8](/posts/re-6-8-obfuscation-packers-android/)), the class names in the snippet are scrambled too, so just use those exact names. Last is Frida detection. A defensive app may probe for frida-server via port 27042 or the process name, and then you need to run a renamed/different-port frida-server, or use an embedded gadget.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 6.6</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/6.6.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/6.6/src/hook.js" download><i class="fa-solid fa-download"></i>src/hook.js</a>
</div>
</div>

The goal is to use Frida to change the return value of a method while the app is running, and see the app change its behavior, without patching and repackaging the APK. Only do this on your own practice app, an app you're authorized to test, or a public app meant for learning such as OWASP UnCrackable (see Lesson 0.2 on legal and ethical limits).

You need a rooted Android emulator (Genymotion, or an AVD with a rooted image) or a rooted device, and `frida-tools` on the host.

```
pip install frida-tools objection
```

You also need the frida-server build for the right architecture, pushed to the device and running (see the setup section above). Check that everything is connected with `frida-ps -U`, which should list the apps. A good target is OWASP UnCrackable-Level1, downloaded from the official OWASP MASTG UnCrackable apps page (https://mas.owasp.org/crackmes/). It has a function that checks for root and then exits, and a function that verifies a secret string, which makes it good for practicing hooks.

Open the APK in JADX-GUI and find the class and method that check for root (or the condition that makes the app quit early). Use Copy as Frida snippet to get the hook template for that method, then edit `hook.js` to force the method to return the value that lets the app continue. The file is a sample script with three patterns, which are forcing a root check to return false, logging the arguments and real result of a verification function, and hooking an overloaded method where you must spell out the signature. Adjust the class and method names to your target. Run it with the command below and check that the app no longer exits.

```
frida -U -f <package> -l hook.js
```

For an extra step, hook the string verification function and log its argument and real return value to understand what it compares. You can also try the quick route with objection by running `objection -g <package> explore` and then `android root disable`.

Two questions to think about afterwards. Why is a runtime hook more convenient than patching smali while exploring, and why is a patch better when you want a permanent change? And if the app detects Frida and quits, how would you deal with it? Try it yourself before opening the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Instead of editing the APK, we step into the runtime. Frida loads a JS script into the app process, we grab a Java class with `Java.use`, and we overwrite the `implementation` of the method we want to change. The steps below use OWASP UnCrackable-Level1.

First, find the blocker. Open the APK in JADX. The main Activity has a section that checks for root or a debugger and then calls `System.exit(0)` through a dialog. A typical class is named like `sg.vantagepoint.a.c`, with a method `a(...)` that returns a boolean saying whether the device is rooted.

Second, get the snippet. Right-click that method in JADX and choose Copy as Frida snippet. JADX fills in the obfuscated class name (use that scrambled name exactly) and the signature.

Third, force it to return false. In `hook.js`:

```javascript
Java.perform(function () {
    var c = Java.use("sg.vantagepoint.a.c");
    c.a.overload("java.lang.String").implementation = function (s) {
        return false;   // pretend there is no root binary
    };
    var b = Java.use("sg.vantagepoint.a.b");
    b.a.overload("java.lang.String").implementation = function (s) {
        return false;   // same for the other checks
    };
});
```

Fourth, run it by spawning the app from the start so you catch checks that run early.

```bash
frida -U -f owasp.mstg.uncrackable1 -l hook.js
```

The app no longer shows the exit dialog and reaches the main screen.

Fifth, work out the secret string. Hook the verification function, which is usually a function that takes the String the user typed, decrypts a byte array with AES and compares. Log the argument and the result.

```javascript
var verifier = Java.use("sg.vantagepoint.uncrackable1.a");
verifier.a.implementation = function (input) {
    console.log("[*] input = " + input);
    var r = this.a(input);
    console.log("[*] result = " + r);
    return r;
};
```

Enter a test string, read the log, then follow the decryption function (see the crypto lessons in Part 16) to recover the secret, or simply hook the comparison function to return true.

For a faster route, use objection.

```bash
objection -g owasp.mstg.uncrackable1 explore
# inside the shell:
android root disable
```

objection ships ready-made hooks for many root detection mechanisms, so you don't have to find each class yourself.

On the questions, a runtime hook is fast, needs no repacking or re-signing, and can change many places in one session, which is good while exploring. But a hook only lives while Frida is attached. For a permanent change that doesn't depend on Frida, patch the smali and rebuild (Lesson 6.4). If the app detects Frida, you can run a renamed frida-server on a different port than the default 27042, or embed frida-gadget in a repacked APK, or hook the Frida detection function itself so that it sees nothing.

One caveat is that the class names and structure of UnCrackable-Level1 above follow the familiar public version of that app. After obfuscation the method names may differ slightly depending on the build you download, so use exactly what JADX shows.

</details>

## Key takeaways
Frida has frida-server on the device and frida/objection on the host, and the versions on both sides must match. The core pattern is `Java.perform` then `Java.use("class").method.implementation = function(){...}`. Call `this.method(...)` to run the original, which you use when you only want to log without changing behavior. Overloaded methods must be specified with `.overload(...)`.

JADX Copy as Frida snippet generates a hook template with the right signature, and objection bundles hooks for SSL pinning and root detection. Only use it on your own apps or ones you're authorized for, since this is security testing and not cheating.
