---
title: "Lesson 12.3: Reversing an iOS app, from the IPA file to runtime hooks"
date: 2023-11-09 20:29:00 +0700
categories: ["Technique Reverse", "Part 12 · Swift and Objective-C"]
tags: [reverse-engineering, ios, swift]
render_with_liquid: false
---
Reversing iOS differs from Android in one way that discourages beginners: you don't only need to understand Mach-O and Objective-C/Swift, you first have to get past Apple's encryption layer and almost always need a jailbroken device. This lesson goes from the IPA file to the point where you can hook a running method, and says plainly where you need a real device.

A reminder of the boundary from [Lesson 0.2](/posts/re-0-2-legal-ethics-part-everyone-wants-skip/): everything below is for security testing on your own app or an app you have permission for, not for cracking other people's apps.

## An IPA is just a ZIP file

Like an APK on Android, an `.ipa` file is really a ZIP. Rename the extension to `.zip` and extract it and you see the structure:

```
Payload/
  AppName.app/
    AppName           <- Mach-O binary, the most important part
    Info.plist        <- metadata: bundle id, version, permissions, URL schemes
    embedded.mobileprovision  <- signing profile
    Assets.car        <- compiled assets
    *.nib, *.storyboardc, *.lproj ...
```

The file that matters is the Mach-O binary with the same name as the app (no extension). Read `Info.plist` first to get the bundle identifier, minimum iOS version, permissions (NSCameraUsageDescription...) and URL schemes. It plays a role similar to AndroidManifest.

## The barrier: FairPlay encryption

This is where iOS is completely different. Binaries downloaded from the App Store are encrypted by Apple with FairPlay DRM: the `__TEXT` part (which holds the code) is encrypted, and only decrypted in memory at runtime on a device with the right license. A `cryptid` of 1 in the `LC_ENCRYPTION_INFO` load command is the sign that the binary is still encrypted.

The practical consequence: if you drag a binary straight from an App Store IPA into IDA/Ghidra, the code is just encrypted garbage. You have to get a decrypted copy first.

The way to get a decrypted copy is to let the device decrypt it itself in RAM (like it does when running the app) and then dump that memory region:

The most popular tool right now is frida-ios-dump, a Python script running through Frida. It runs the app, reads the decrypted `__TEXT` region in memory, writes it over the binary, sets `cryptid` back to 0, and repackages it into a decrypted IPA. bagbak is a newer tool with the same idea, also built on Frida. Clutch is an old tool that's often broken on new iOS, and I only mention it so you recognize the name.

All of them need a **jailbroken** device (or an equivalent environment) because they have to read the process memory of another app. This is the biggest blocker for people learning iOS: without a jailbroken device you almost can't go further with App Store apps. An app you build yourself and install through Xcode isn't under FairPlay, which is much more convenient for learning.

## After decryption: analyze it like a Mach-O

Once you have the decrypted binary (`cryptid` = 0), the rest is what you've already learned:

It's a Mach-O, so recall [Lesson 1.8](/posts/re-1-8-elf-mach-o-two-formats-outside/) and remember to check for fat binaries and the arm64 architecture. If the app is written in Objective-C, read it by `objc_msgSend` and selectors like in [Lesson 12.1](/posts/re-12-1-objective-c-where-every-call-goes/) and run class-dump to get the headers. If it's written in Swift, demangle and read the metadata like in [Lesson 12.2](https://github.com/Haind03/Technique-Reverse/blob/main/phan-12-swift-objc-apple/12.2-swift-metadata-demangle.md). The code is ARM64, so see [Lesson 1.9](/posts/re-1-9-arm-arm64-basics-people-who-already/) again.

In other words, FairPlay is just one door. Once you're through, the tools and mindset are the same as analyzing a normal Mach-O.

## Runtime hooking with Frida and objection

Static analysis gives you the map, but iOS is a great fit for dynamic analysis because the ObjC runtime allows clean interference. Install frida-server on the jailbroken device, run frida/objection on the host.

**objection** is an automation layer on top of Frida, doing common tasks quickly without writing scripts:

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

Two classic situations come up when security testing your own app. With jailbreak detection, the app refuses to run when it sees a jailbroken device, so you hook the check function (usually returns a BOOL) to return false, or use `ios jailbreak disable`. With SSL pinning, the app only accepts a specific certificate so a proxy like Burp can't read the traffic, and you disable the pinning to analyze your own app's traffic for testing purposes.

## Common pitfalls

A common mistake is forgetting that App Store apps are still FairPlay encrypted, opening IDA anyway and thinking the binary is broken, so always check `cryptid` first. Trying to analyze an App Store app without a jailbroken device is almost a dead end, so start with an app you build yourself. A version mismatch between frida-server on the device and frida on the host makes hooks silently not run. Swift methods also often don't expose nice selectors like ObjC, so you have to demangle and rely on metadata.

## Lab

See [labs/12.3/](https://github.com/Haind03/Technique-Reverse/blob/main/labs/12.3). You need a jailbroken iOS device and an app you made yourself (or have permission for). The task: dump the decrypted binary, confirm `cryptid` goes to 0, analyze the Mach-O, then hook a method with objection. The file `src/hook.js` has a sample iOS Frida script.

## Key takeaways
An IPA is a ZIP, and the important binary is the Mach-O with the same name as the app, so read Info.plist first. App Store binaries have `__TEXT` encrypted by FairPlay (check for `cryptid` = 1), so you have to dump the decrypted copy from memory with frida-ios-dump or bagbak, which needs a jailbroken device. Apps you build yourself aren't encrypted.

After decryption, analyze it like an ObjC/Swift Mach-O (Lessons 12.1, 12.2) with ARM64 code (Lesson 1.9). Use Frida/objection to hook at runtime and bypass jailbreak detection and SSL pinning when testing your own app.
