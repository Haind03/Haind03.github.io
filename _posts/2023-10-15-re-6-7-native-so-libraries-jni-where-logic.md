---
title: "Lesson 6.7: Native .so libraries and JNI, where the logic hides from JADX"
date: 2023-10-15 23:22:00 +0700
categories: ["Technique Reverse", "Part 06 · Java, Kotlin and Android"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
You open the APK in JADX, look for the license check function, and it's exactly one line: `public native boolean checkLicense(String s);`. That's it. There's no function body to read. The real logic has been pushed down into a native library `lib/arm64-v8a/libcheck.so`, where JADX gives up because that's ARM64 machine code and no longer Java bytecode. This is the most common way to make life hard for someone reversing an Android app: whatever's important gets written in C/C++.

Good news: you already learned ARM64 in [Lesson 1.9](/posts/re-1-9-arm-arm64-basics-people-who-already/). All that's left is knowing how to bridge from the Java method to the right function in the .so file.

## JNI is the bridge between Java and native

![JNI bridging from Java to a native function in a .so file](/assets/img/technique-reverse/assets/phan-06/jni-bridge.svg)

JNI (Java Native Interface) is the mechanism that lets Java call C/C++ code. The basic flow is that a Java class loads the library, since `System.loadLibrary("check")` loads `libcheck.so`. The method is then declared `native` with no body: `public native boolean checkLicense(String s);`. Inside `libcheck.so` there's a C function that actually implements that method.

When Java calls `checkLicense`, the runtime finds the matching native function and jumps in. Your job is to find that native function in the .so file.

## Two ways Java finds the native function

This is the key point, and also where app authors like to play tricks.

### Way 1: naming by convention (static linking)

By default, JNI looks for the C function by a very long name made from package + class + method:

```
Java_<package>_<class>_<method>
```

For example the method `checkLicense` in the class `com.example.app.Native` corresponds to a C function named:

```
Java_com_example_app_Native_checkLicense
```

Dots in the package become underscores. The nice part is that you open the .so in Ghidra, go to the export/symbol list, search for `Java_` and all the native functions show up right away, with full names saying which Java method each belongs to. Very easy.

### Way 2: dynamic registration through RegisterNatives (harder)

An author who wants to hide doesn't use the conventional name. Instead, in the special function `JNI_OnLoad` (which runs as soon as the library is loaded), they call `RegisterNatives` to map the Java method name to an arbitrary function pointer by hand:

```c
JNIEXPORT jint JNI_OnLoad(JavaVM *vm, void *reserved) {
    // ... get JNIEnv ...
    JNINativeMethod methods[] = {
        { "checkLicense", "(Ljava/lang/String;)Z", (void*)sub_1234 }
    };
    (*env)->RegisterNatives(env, clazz, methods, 1);
    return JNI_VERSION_1_6;
}
```

Now the real function can have any name (for example `sub_1234`), and there's no `Java_` to search for. The process is to find `JNI_OnLoad` in the .so (it's always an export, always present if the app uses this approach), read the code in it, and find the `RegisterNatives` call. `RegisterNatives` takes an array of `JNINativeMethod` structs, each element made of a pointer to the method name, a pointer to the signature string, and a pointer to the implementing function. Reading that array tells you which function the `checkLicense` method maps to.

A tip for reading JNI signatures: `(Ljava/lang/String;)Z` means takes a String, returns boolean (`Z`). Type table: `Z`=boolean, `I`=int, `J`=long, `[`=array, `L...;`=object.

## The first two parameters always belong to JNI

However you found it, every JNI function has two hidden parameters ahead of your own:

```c
jboolean checkLicense(JNIEnv *env, jobject thiz, jstring s)
```

The first, `env` (in `x0` on ARM64), is a pointer to the JNI function table, used to call back into Java (get strings, call methods...). The second, `thiz` (`x1`), is the Java object that called the method, like `this`. Your real parameters start at `x2`.

So when you open the function in Ghidra, don't be confused when the first two parameters have nothing to do with the logic. The string parameter `s` is in `x2`. To read that string's contents, the native code calls `env->GetStringUTFChars`, and you'll see an indirect call through the `env` table (an `ldr` from `x0` then `blr`), which is the sign it's pulling the string out to process it.

## Getting the .so into Ghidra

An APK is a ZIP file, so extract it and take `lib/arm64-v8a/lib<name>.so` (prefer arm64-v8a, the most common ABI today). Drag the .so into Ghidra and run auto-analysis. Ghidra recognizes the ARM64 ELF (tying back to [Lesson 1.8](/posts/re-1-8-elf-mach-o-two-formats-outside/) and [1.9](/posts/re-1-9-arm-arm64-basics-people-who-already/)). Open the Symbol Tree and filter for `Java_` to find conventionally named functions, and if there are none, look for `JNI_OnLoad`. Then read the decompiler, remembering to skip the first two JNI parameters.

## Key takeaways
A Java method declared `native` means the logic lives in a `.so` file, which JADX can't read. JNI functions follow the naming convention `Java_package_Class_method`, so search for the string `Java_` in the .so. If you don't see it, look for `JNI_OnLoad` and read `RegisterNatives` to see which function the method maps to.

Every JNI function has two hidden leading parameters, `JNIEnv* env` (x0) and `jobject thiz` (x1), and real parameters start at x2. Read JNI signatures with the type table: `Z` boolean, `I` int, `L...;` object, `[` array. Analyzing the .so is just ordinary ARM64 reversing, so see Lesson 1.9 again.

## Lab
See [labs/6.7/](https://github.com/Haind03/Technique-Reverse/blob/main/labs/6.7): extract the .so from an APK, open it in Ghidra, find the JNI function both ways, and compare against a JNI C example you write yourself.
