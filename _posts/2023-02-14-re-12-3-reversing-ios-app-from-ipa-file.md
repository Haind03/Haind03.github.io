---
title: "Lesson 12.3: Reversing an iOS app from the IPA file"
image:
  path: /assets/img/covers/re-12-3-reversing-ios-app-from-ipa-file.webp
  alt: "Lesson 12.3: Reversing an iOS app from the IPA file"
date: 2023-02-14 10:47:00 +0700
categories: ["Reverse Engineering", "Part 12 · Swift and Objective-C"]
tags: [reverse-engineering, ios, swift]
render_with_liquid: false
---
Reversing iOS differs from Android in a way that puts beginners off, since you need to understand Mach-O and Objective-C/Swift, you first have to get past Apple's encryption layer, and you almost always need a jailbroken device. This lesson goes from the IPA file to hooking a running method, and says plainly where you need a real device.

A reminder of the boundary from [Lesson 0.2](/posts/re-0-2-legal-ethics-part-everyone-wants-skip/), which is that everything below is for security testing on your own app or an app you have permission for, not for cracking other people's apps.

## An IPA is a ZIP file

Like an APK on Android, an `.ipa` file is a ZIP. Rename the extension to `.zip` and extract it and you see the structure:

```
Payload/
  AppName.app/
    AppName           <- Mach-O binary, the most important part
    Info.plist        <- metadata: bundle id, version, permissions, URL schemes
    embedded.mobileprovision  <- signing profile
    Assets.car        <- compiled assets
    *.nib, *.storyboardc, *.lproj ...
```

The file that matters is the Mach-O binary with the same name as the app (no extension). Read `Info.plist` first to get the bundle identifier, minimum iOS version, permissions (NSCameraUsageDescription...) and URL schemes. It's similar to AndroidManifest.

## FairPlay encryption

This is where iOS is different. Binaries downloaded from the App Store are encrypted by Apple with FairPlay DRM, so the `__TEXT` part (which holds the code) is encrypted, and only decrypted in memory at runtime on a device with the right license. A `cryptid` of 1 in the `LC_ENCRYPTION_INFO` load command means the binary is still encrypted.

In practice, if you drag a binary straight from an App Store IPA into IDA/Ghidra, the code is just encrypted garbage. You have to get a decrypted copy first.

To get one, let the device decrypt it in RAM (like it does when running the app) and then dump that memory region:

The most popular tool right now is frida-ios-dump, a Python script running through Frida. It runs the app, reads the decrypted `__TEXT` region in memory, writes it over the binary, sets `cryptid` back to 0, and repackages it into a decrypted IPA. bagbak is a newer tool with the same idea, also built on Frida. Clutch is an old tool that's often broken on new iOS, and I only mention it so you recognize the name.

All of them need a jailbroken device (or an equivalent environment) because they have to read the process memory of another app. This blocks a lot of people learning iOS, since without a jailbroken device you almost can't go further with App Store apps. An app you build yourself and install through Xcode isn't under FairPlay, which is much easier for learning.

## After decryption: analyze it as a Mach-O

Once you have the decrypted binary (`cryptid` = 0), the rest is what you've already learned.

It's a Mach-O, so recall [Lesson 1.8](/posts/re-1-8-elf-mach-o-two-formats-outside/) and remember to check for fat binaries and the arm64 architecture. If the app is written in Objective-C, read it by `objc_msgSend` and selectors like in [Lesson 12.1](/posts/re-12-1-objective-c-where-every-call-goes/) and run class-dump to get the headers. If it's written in Swift, demangle and read the metadata like in [Lesson 12.2](/reverse-engineering/). The code is ARM64, so see [Lesson 1.9](/posts/re-1-9-arm-arm64-basics-people-who-already/) again.

So FairPlay is just one obstacle. Once you're past it, the tools and approach are the same as for a normal Mach-O.

## Runtime hooking with Frida and objection

Static analysis gives you the map, but iOS also suits dynamic analysis because the ObjC runtime makes hooking easy. Install frida-server on the jailbroken device, run frida/objection on the host.

objection is an automation layer on top of Frida, doing common tasks quickly without writing scripts:

```
objection -g com.example.myapp explore
# inside the objection shell:
ios hooking list classes                 # list classes
ios hooking watch class LoginViewController   # watch a class's methods
ios hooking set return_value "...:isJailbroken" false   # force a return value
ios sslpinning disable                    # disable SSL pinning to see traffic
ios jailbreak disable                     # bypass jailbreak detection
```

When you need finer control, write a Frida script. ObjC methods are hooked through `ObjC.classes`:

```js
if (ObjC.available) {
  var LoginVC = ObjC.classes.LoginViewController;
  Interceptor.attach(LoginVC['- checkPassword:'].implementation, {
    onEnter: function (args) {
      // args[0]=self, args[1]=selector, args[2]=first parameter
      var pw = new ObjC.Object(args[2]);
      console.log('[+] checkPassword called with: ' + pw.toString());
    },
    onLeave: function (retval) {
      console.log('[+] returned: ' + retval);
      retval.replace(ptr(1));   // force return true
    }
  });
}
```

Two situations come up when security testing your own app. With jailbreak detection, the app refuses to run when it sees a jailbroken device, so you hook the check function (usually returns a BOOL) to return false, or use `ios jailbreak disable`. With SSL pinning, the app only accepts a specific certificate so a proxy like Burp can't read the traffic, and you disable the pinning to analyze your own app's traffic for testing.

## Common pitfalls

A common mistake is forgetting that App Store apps are still FairPlay encrypted, opening IDA anyway and thinking the binary is broken, so always check `cryptid` first. Analyzing an App Store app without a jailbroken device is almost impossible, so start with an app you build yourself. A version mismatch between frida-server on the device and frida on the host makes hooks silently not run. Swift methods also often don't expose nice selectors like ObjC, so you have to demangle and rely on metadata.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 12.3</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/12.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/12.3/src/hook.js" download><i class="fa-solid fa-download"></i>src/hook.js</a>
</div>
</div>

The task is to dump, analyze and hook an iOS app. You need a jailbroken iOS device (or an equivalent virtual device), because that is required to dump the decrypted binary and hook the runtime. On the device `frida-server` must be running, along with OpenSSH. On the host you need Python, `frida`, `frida-tools`, `objection` and `frida-ios-dump`. Use an app you made yourself or one you have permission to test, never someone else's app. Set up the host with:

```
pip install frida-tools objection
git clone https://github.com/AloneMonkey/frida-ios-dump
```

Start with the IPA structure. If you already have an IPA, rename it to `.zip` and unzip it. Find `Payload/*.app/` and read `Info.plist` to get the bundle identifier, the version and the permissions. Then check the FairPlay encryption. On the Mach-O binary inside the app, run the following on macOS and look at `cryptid`. A value of 1 means it is still encrypted and 0 means it is decrypted.

```
otool -l AppName | grep -A5 LC_ENCRYPTION_INFO
```

For an App Store app that is still encrypted, run frida-ios-dump to get a decrypted IPA, and afterwards check that `cryptid` has gone to 0.

```
python3 dump.py com.example.myapp
```

For static analysis, open the decrypted binary in Ghidra or IDA (arm64). If it is ObjC, run class-dump to get the headers and read by selector (Lesson 12.1). If it is Swift, demangle the symbols (Lesson 12.2). For runtime hooking, use objection, pick a method to follow and watch its arguments:

```
objection -g com.example.myapp explore
ios hooking list classes
ios hooking watch class <ClassName>
```

Last, hook with a Frida script. Use `hook.js` (change the class and method names to match your app) to hook a method and change its return value:

```
frida -U -f com.example.myapp -l hook.js
```

A few questions to think about. Why can't you skip the dump step and analyze the App Store binary directly? What is `args[1]` in an ObjC hook, and why do the real parameters start at `args[2]`? And if you don't have a jailbroken device, what other ways are there to learn iOS RE?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Try it before reading. This lab needs a jailbroken iOS device, so what follows is the standard procedure with notes on how to interpret the output.

Unzipping the IPA gives `Payload/AppName.app/`. In `Info.plist` the important keys are `CFBundleIdentifier`, the bundle id used in every Frida and objection command (`-g <id>`), then `CFBundleShortVersionString` and `MinimumOSVersion`, the `NS*UsageDescription` keys that list the permissions the app asks for (camera, location and so on), and `CFBundleURLTypes`, the URL schemes, which are often an attack entry point.

For the FairPlay check, the output of `otool -l AppName | grep -A5 LC_ENCRYPTION_INFO` containing `cryptid 1` means `__TEXT` is still encrypted and only garbage shows up if you drag it into IDA. `cryptid 0` means it is decrypted and can be analyzed.

For the dump, `python3 dump.py com.example.myapp` makes frida-ios-dump run the app, read the `__TEXT` region that iOS has already decrypted in RAM, write it over the binary, set `cryptid` to 0 and pack it into a new IPA. Checking again with `otool -l` and seeing `cryptid 0` means success. An app you built through Xcode is already `cryptid 0`, so you can skip this step.

For static analysis, open the decrypted binary in Ghidra (pick the right arm64 slice if it is a fat binary). For ObjC, run `class-dump AppName > headers.h` to get every @interface, then in Ghidra read by `objc_msgSend` plus selector (Lesson 12.1). For Swift, demangle the `$s...` symbols with `swift demangle` (Lesson 12.2).

With objection, `ios hooking watch class LoginViewController` prints every time a method of that class is called, together with its arguments. It is the fastest way to learn the execution flow without writing a script. With the Frida script, `frida -U -f com.example.myapp -l hook.js` hooks `- checkPassword:`, logs the first argument (`args[2]`) and forces a return of true (`retval.replace(ptr(1))`).

On the questions, you can't analyze the App Store binary directly because the `__TEXT` part is encrypted by FairPlay, and the code is only garbage until iOS decrypts it in RAM at run time, so you have to dump the decrypted version to read it. `args[1]` is the selector because in ObjC every method is a C function of the form `method(self, SEL, ...)`, where `args[0]` is self and `args[1]` is the selector (SEL), so the parameters the developer declared start at `args[2]`. Without a jailbroken device you can learn with an app you build and install through Xcode (it isn't subject to FairPlay, and you can debug and hook freely on the simulator or a dev device), or practice on crackmes and deliberately vulnerable apps such as DVIA-v2 and iGoat.

</details>

## Key takeaways
An IPA is a ZIP, and the important binary is the Mach-O with the same name as the app, so read Info.plist first. App Store binaries have `__TEXT` encrypted by FairPlay (check for `cryptid` = 1), so you have to dump the decrypted copy from memory with frida-ios-dump or bagbak, which needs a jailbroken device. Apps you build yourself aren't encrypted.

After decryption, analyze it like an ObjC/Swift Mach-O (Lessons 12.1, 12.2) with ARM64 code (Lesson 1.9). Use Frida/objection to hook at runtime and bypass jailbreak detection and SSL pinning when testing your own app.
