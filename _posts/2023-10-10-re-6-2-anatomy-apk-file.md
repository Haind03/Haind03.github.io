---
title: "Lesson 6.2: Anatomy of an APK file"
date: 2023-10-10 20:27:00 +0700
categories: ["Technique Reverse", "Part 06 · Java, Kotlin and Android"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
The first time someone hands you an `.apk` file and says "take a look at what this app does", the common reflex is to drag it straight into JADX and get lost in thousands of classes. Hold on. An APK is a box with a clear layout, and looking at the right place first saves a whole session. This lesson opens that box up to see what's inside.

## An APK is really just a ZIP file

![Inside an APK file: manifest, classes.dex, lib, resources, assets, META-INF](/assets/img/technique-reverse/assets/phan-06/apk-structure.svg)

The first thing that surprises many people: an APK has no mysterious format at all, it's a renamed ZIP file. Change the `.apk` extension to `.zip` and extract it with any tool and you see all its guts. Try it right now with any app on your phone.

Inside a typical APK:

```
app.apk  (ZIP)
├── AndroidManifest.xml     declares the app: components, permissions, entry points
├── classes.dex             Java/Kotlin bytecode (may also have classes2.dex...)
├── resources.arsc          compiled resource table (strings, layout ids...)
├── res/                    resources: layout, drawable, values
├── lib/                    native .so libraries, split by ABI
│   ├── arm64-v8a/
│   ├── armeabi-v7a/
│   └── x86_64/
├── assets/                 raw files the app reads itself (models, config, scripts...)
└── META-INF/               signature and manifest of the ZIP file itself
```

Not everything is equally worth looking at. When triaging, the order I look in is: AndroidManifest first (to know the entry point), then classes.dex (the main logic), then lib/ if there's native code (sensitive logic often gets pushed down here), and finally assets/ when I suspect data hidden in there.

## AndroidManifest.xml, read this first

The manifest is the app's declaration: which components it has, which permissions it asks for, and most important for a reverser, which screen runs first.

There's a trap: the manifest in an APK isn't plain-text XML but binary XML (AXML) encoded in binary, and opening it in a text editor gives garbage characters. You have to use a decoding tool. Drag the APK into JADX and it automatically shows the manifest in readable form, or run `apktool d app.apk` and apktool decodes the manifest and resources into text form.

What to look for in the manifest is the launcher activity first, which is the activity with an intent-filter containing `android.intent.action.MAIN` and `android.intent.category.LAUNCHER`. This is the opening screen, where you start following the flow. Next is the application class (the `android:name` attribute in the `<application>` tag): if there is one, this class runs even before the first activity, and many apps put initialization and even anti-analysis here. Then the permissions, since `<uses-permission>` tells what the app touches (internet, SMS, contacts, location), and the permission list gives you a quick picture of what type of app it is, like reading the imports of a PE. Finally there are the exported components: a component with `android:exported="true"` is a surface that can be called from outside, worth noting when assessing security.

## classes.dex, where the logic lives

Java and Kotlin code after compilation doesn't live in loose `.class` files like on the desktop, but is merged and converted into a single file: `classes.dex`, holding DEX bytecode (Dalvik Executable).

The core difference from ordinary JVM bytecode is that JVM .class is stack-based, where instructions push operands onto a stack and then operate, while DEX is register-based, where instructions work directly on virtual registers (v0, v1, v2...). That's closer to real assembly, and more compact.

You rarely read raw DEX. The usual toolchain is that a decompiler (JADX, CFR...) rebuilds the DEX back into almost readable Java. When you need to modify, people drop down to the intermediate level smali (the text form of DEX bytecode), covered in Lesson 6.4.

### Multidex

A single DEX file has a historical limit of about 65536 methods (the limit of the 16-bit method reference index). Large apps get past it with multidex: `classes.dex`, `classes2.dex`, `classes3.dex`... When analyzing, remember the code may be scattered across several dex files, don't only look at the first one. JADX merges them all for you so you usually don't need to worry, but when using apktool manually you have to pay attention.

## lib/, when logic hides down in native

The `lib/` folder holds native libraries as `.so` (ELF shared objects, like Linux), split by CPU architecture (ABI): `arm64-v8a` for today's 64-bit phones, `armeabi-v7a` for older devices, `x86_64` for emulators.

Reversers care because sensitive logic (license checks, encryption, anti-cheat, the core of a game) is often written in C/C++ via JNI and stuffed into a `.so` to make it much harder to read than Java. Seeing an app with a large `.so` tells you the interesting part may not be in Java but in native. Then you move the `.so` file to IDA or Ghidra and reverse it like a normal ARM binary (recall Lesson 1.9 on ARM64). The bridge from Java calling down into native is JNI, the topic of Lesson 6.7.

## assets/ and resources, don't skip them

`assets/` holds raw files the app reads at runtime: configuration, machine learning models, scripts, sometimes even a secondary dex/so that gets loaded dynamically (a sign of a packer, see Lesson 6.8). `res/` and `resources.arsc` hold UI resources and strings, and strings in `res/values/strings.xml` often contain URLs, keys, error messages that are useful for tracing.

## META-INF, the signature

`META-INF/` holds the APK's signature (`.RSA`/`.SF`/`.MF` files with the v1 scheme, while v2 and later sign in a separate block of the ZIP file). You don't read it to understand logic, but remember one important thing: every APK installed on a device must be signed. When you modify an app and repackage it (Lesson 6.4), the old signature breaks, and you have to re-sign with your own key before it will install. That's the reason for the re-sign step.

## Lab

Practice is in `labs/6.2/`. Summary of the task: take any APK (a free app you download, or an APK you build yourself), unzip it as a ZIP file, identify each component, open AndroidManifest with JADX or apktool to find the launcher activity and the permission list, then list the native libs in `lib/`. The goal is to get familiar with the layout before diving into reading code.

## Key takeaways
An APK is a ZIP file, so you can extract it and see all the components. Read AndroidManifest first to find the launcher activity, application class, and permissions, and remember it's binary XML, so open it with JADX/apktool and not a text editor. classes.dex holds the code as register-based DEX bytecode (unlike stack-based JVM), and large apps use multidex. lib/ holds native `.so` files by ABI, where sensitive logic often hides, so switch to IDA/Ghidra for those. Every APK must be signed, so after modifying it you have to re-sign before it will install.
