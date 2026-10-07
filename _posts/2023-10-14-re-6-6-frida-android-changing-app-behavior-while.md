---
title: "Lesson 6.6: Frida on Android, changing app behavior while it runs"
date: 2023-10-14 14:03:00 +0700
categories: ["Technique Reverse", "Part 06 · Java, Kotlin and Android"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
Reading an APK statically in JADX tells you what the app intends to do. But often you want to see a value with your own eyes at runtime, or try changing a function's result to see how the app reacts, without patching and repackaging the whole APK. That's when Frida comes in. It lets you step into any Java method while the app runs, read the arguments, change the return value, all in a few lines of JavaScript.

Let me be upfront about the boundary first: what's in this lesson is security testing technique. Use it on your own apps, apps you're authorized to test, or practice apps like OWASP UnCrackable. Hooking to bypass the licensing checks of someone else's app, or cheating in online games, is a different matter and outside the scope of this series. The tool is neutral, the purpose is what counts.

## How Frida works

Frida is a dynamic instrumentation toolkit. On Android, the model has two parts. frida-server is a binary that runs on the device (usually needs root) or on an emulator, the extended arm responsible for injecting code into the app process. frida / objection are the tools that run on your computer (the host), talk to frida-server over USB or TCP, and load your script into the app.

You write scripts in JavaScript. Frida injects a JS engine into the app process, and from inside it your script can call into the Android runtime and grab Java classes and methods as if you were writing Java.

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

If `frida-ps -U` lists the apps, the environment works. The frida-server version has to match the frida-tools version on the host, a version mismatch errors out right away, and this is the number one trap for beginners.

## Hooking Java methods: three patterns you'll use forever

Every Android script starts with `Java.perform`, inside it you get a class with `Java.use`, then override the method's implementation. The three most common jobs:

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

An important tip: `this.validate(input)` calls the original method itself. That lets you observe without breaking the logic, very handy for tracing out the checking algorithm.

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

No need to type long class names by hand. In JADX-GUI (lesson [6.3](/posts/re-6-3-jadx-gui-depth-number-one-tool/)), right-click a method and choose **Copy as Frida snippet**. It generates the `Java.use(...).implementation` skeleton with the right class and signature, and you just paste it into the script and fill in the body. This is the fastest way to go from "found the function in the decompiler" to "hooked it".

## SSL pinning and why you need to bypass it when testing

Many apps pin certificates (SSL pinning) to reject every connection that doesn't use a predefined certificate. Good for security, but when you're testing your own app and want to see the traffic through Burp/mitmproxy, pinning blocks you too. The solution in testing is to hook the certificate checking layer so it accepts your proxy.

The fastest way is objection, an automation layer built on Frida:

```bash
pip install objection
objection -g com.example.app explore
# inside the objection shell:
android sslpinning disable
android root disable
```

These two commands bundle a lot of common hooks for pinning and root detection, so you don't write them yourself. When objection can't handle an unusual mechanism, you go back to writing a manual Frida hook for that exact layer.

## Common pitfalls

The first is a version mismatch between frida-server and frida-tools, which gives confusing errors, so always check it first. The second is a class that isn't loaded yet when you hook: use `-f` to spawn early, or hook the ClassLoader. Third, method names after obfuscation: if the app is renamed by R8/ProGuard (lesson [6.8](/posts/re-6-8-obfuscation-packers-android/)), the class names in the snippet are scrambled too, so just use those exact scrambled names. Last is Frida detection, since a defensive app may probe for frida-server via port 27042 or the process name, and then you need to run a renamed/different-port frida-server, or use an embedded gadget.

## Lab

See [labs/6.6/](https://github.com/Haind03/Technique-Reverse/blob/main/labs/6.6). You'll hook a method in a practice app of your own to change the return value, and watch the app change behavior accordingly. The file `src/hook.js` is a sample script for you to edit.

## Key takeaways
Frida has frida-server on the device and frida/objection on the host, and the versions on both sides must match. The core pattern is `Java.perform` then `Java.use("class").method.implementation = function(){...}`. Call `this.method(...)` to run the original, which you use when you only want to log without changing behavior, and overloaded methods must be specified with `.overload(...)`.

JADX Copy as Frida snippet generates a hook skeleton with the right signature, and objection bundles hooks for SSL pinning and root detection. Only use it on your own apps or ones you're authorized for, since this is security testing and not cheating.
