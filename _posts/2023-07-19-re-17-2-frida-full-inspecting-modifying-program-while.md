---
title: "Lesson 17.2: Frida in full, inspecting and modifying a program while it runs"
date: 2023-07-19 23:03:00 +0700
categories: ["Technique Reverse", "Part 17 · Patching, Hooking, Injection"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
Sometimes static reading gets you nowhere, and setting breakpoints in a debugger is slow and easily caught by anti-debug. Frida was made for exactly that situation: you inject a small piece of JavaScript into the running process, tell it "every time this function is called, print its parameters", and that's it. No editing files on disk, no recompiling, and it runs on Windows, Linux, macOS, Android, iOS with the same API.

This lesson covers Frida at the level you can use right away for RE. Scope: behavior analysis, security testing of your own software, solving crackmes/CTFs. Use it to observe and understand, not to wreck things.

## Frida from the top down

In essence Frida stuffs an engine called gum into the target process, and that engine runs your JavaScript script (called an agent) right inside the process's address space. Because the script runs inside the process, it sees every function, every memory region, every register the way the process itself does.

There are two ways to get the script in. With attach, you attach to an already running process, which is useful when the program has started and you want to look in from the middle. With spawn, Frida launches the program itself in a suspended state, loads the script, and only then lets it run, which is useful when you need to hook something that happens very early (before main, in an init function).

The command-line tools you'll type a lot are these. `frida-ps -U` lists processes (the `-U` flag is for a USB device like Android, drop it for the local machine). `frida -l hook.js -f ./target` spawns `target` and loads `hook.js`, while `frida -l hook.js target` attaches to the process named `target`. `frida-trace` generates hooks automatically (covered at the end).

## Interceptor, the heart of Frida

99% of your hooking goes through `Interceptor.attach`. It takes a function address and two callbacks: `onEnter` runs on entering the function (you can read the parameters now), `onLeave` runs when the function is about to return (you can read and change the return value now).

How do you find the function address? If the function is exported (like system APIs), use the name:

```javascript
// Hook CreateFileW on Windows to see which files the program opens
const pCreateFileW = Module.findExportByName("kernel32.dll", "CreateFileW");

Interceptor.attach(pCreateFileW, {
    onEnter(args) {
        // The first parameter of CreateFileW is lpFileName (pointer to a UTF-16 string)
        this.name = args[0].readUtf16String();
        console.log("[CreateFileW] opening file: " + this.name);
    },
    onLeave(retval) {
        // retval is the returned HANDLE; INVALID_HANDLE_VALUE = -1
        console.log("   -> handle: " + retval);
    }
});
```

A few important things in the snippet above. `args` is the parameter array, and Frida handles the calling convention for you: `args[0]` is the first parameter whether on Windows it's in rcx or on Linux it's in rdi, which is why the same script runs cross-platform. Each `args[i]` is a `NativePointer`, so you have to interpret it yourself: `.readUtf16String()` for Windows wide strings, `.readCString()` for C strings, `.toInt32()` for numbers. And `this` is shared between `onEnter` and `onLeave`, so save values in onEnter to reuse in onLeave (like `this.name`).

### Changing parameters and return values

Hooks aren't just for looking, you can modify. For example, make a license check function always return "valid":

```javascript
Interceptor.attach(pCheckLicense, {
    onLeave(retval) {
        console.log("check really returned: " + retval);
        retval.replace(1);   // force return 1 (valid)
    }
});
```

Or change a parameter before the function processes it, in onEnter:

```javascript
onEnter(args) {
    // force the 2nd parameter (difficulty) to 0
    args[1] = ptr(0);
}
```

### Interceptor.replace, replacing the whole function

When you want to replace the entire function with your own implementation (not just look/modify), use `Interceptor.replace`:

```javascript
const origStrcmp = new NativeFunction(pStrcmp, 'int', ['pointer', 'pointer']);
Interceptor.replace(pStrcmp, new NativeCallback((a, b) => {
    console.log("strcmp: " + a.readCString() + " vs " + b.readCString());
    return origStrcmp(a, b);   // still call the original
}, 'int', ['pointer', 'pointer']));
```

## NativeFunction and NativePointer, calling back into the process

Sometimes you don't just want to hook but to actively call a function that already exists in the process, for example to try the decryption function with your own input. `NativeFunction` wraps an address into a function callable from JS:

```javascript
const decrypt = new NativeFunction(ptr("0x401500"), 'pointer', ['pointer', 'int']);
const buf = Memory.allocUtf8String("encrypted data");
const result = decrypt(buf, 14);
console.log("decrypted: " + result.readCString());
```

`NativePointer` (shortened to `ptr(...)`) is Frida's pointer type, with `.readByteArray()`, `.writeUtf8String()`, `.add(offset)`, `.readPointer()` so you can read and write memory freely. `Memory.alloc` allocates new memory in the process when you need to pass a buffer.

## Stalker, tracing every instruction

`Interceptor` hooks at function boundaries. When you need to follow the execution flow inside a function (each basic block, which instructions run, measuring code coverage), that's the job of `Stalker`. It follows a thread and reports each block executed. It's used a lot for fuzzing and for finding "which code runs when I enter the right serial versus the wrong one":

```javascript
Stalker.follow(Process.getCurrentThreadId(), {
    events: { block: true },
    onReceive(events) {
        // list of blocks that just ran, used to measure coverage
    }
});
```

Stalker is powerful but heavy and much more complex than Interceptor, so save it for when you really need coverage, don't use it for ordinary hooks.

## frida-trace, lazy but effective

Don't want to write a script by hand? `frida-trace` generates handlers for you:

```
frida-trace -f ./target -i "strcmp" -i "CreateFileW"
```

The `-i` flag picks functions by name (with wildcards, for example `-i "str*"` catches every function starting with str). Frida creates a JS file for each function in the `__handlers__` folder, and you open it to edit and print more parameters. This is the fastest way to get an overall view of "which APIs the program calls".

## What about Android

The foundation is identical, the only difference is you hook Java methods via `Java.perform` and `Java.use` instead of native functions. That part is covered in detail in [Lesson 6.6](/posts/re-6-6-frida-android-changing-app-behavior-while/). For the native `.so` libraries in an Android app you go back to `Interceptor.attach` like this lesson. Remember you need `frida-server` running on the device and the `-U` flag.

## A few common pitfalls

The Frida host and frida-server (on Android/iOS) must be the same version, and a mismatch gives confusing errors. If you hook too early and the module isn't loaded yet, `Module.findExportByName` returns null, so use `spawn` or in some cases wait for the module. Protected software may also probe port 27042, the string "frida", or odd threads. When you hit that, see [Lesson 15.7](/posts/re-15-7-anti-attach-anti-dump-anti-hook/) on anti-hook and consider running Frida in a stealthier mode. Finally, `args[0]` is a pointer, so printing it directly gives an address and not the content, and you have to call `.readUtf8String()` or similar.

## Lab

See `labs/17.2/`. The task: use Frida to hook the compare function of a small program to expose the correct string it's comparing against your input, then try forcing the return value to get past the check. A sample `hook.js` is provided in `src/`.

## Key takeaways
Frida injects a JS agent into the running process, sees everything from the inside, and works cross-platform. `Interceptor.attach` with `onEnter` (parameters) and `onLeave` (return value) is the main tool. `args[i]` is numbered by logical parameter order and Frida handles the calling convention, but each is a NativePointer, so you have to interpret the type yourself.

`retval.replace(x)` changes the return value and assigning to `args[i]` changes a parameter. Use `NativeFunction` to call functions in the process yourself, `Stalker` to trace each block, and `frida-trace` to generate hooks quickly. On Android, hook Java via `Java.use` (Lesson 6.6), while native `.so` still uses Interceptor.
