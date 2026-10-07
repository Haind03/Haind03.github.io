---
title: "Lesson 17.2: Frida, inspecting and modifying a running program"
image:
  path: /assets/img/covers/re-17-2-frida-full-inspecting-modifying-program-while.webp
  alt: "Lesson 17.2: Frida, inspecting and modifying a running program"
date: 2023-07-19 23:03:00 +0700
categories: ["Technique Reverse", "Part 17 · Patching, Hooking, Injection"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
Sometimes static reading gets you nowhere, and breakpoints in a debugger are slow and easy for anti-debug to catch. Frida is made for that. You inject a small piece of JavaScript into the running process and tell it "every time this function is called, print its parameters". No editing files on disk, no recompiling, and it runs on Windows, Linux, macOS, Android and iOS with the same API.

This lesson covers Frida at the level you can use right away for RE. The scope is behavior analysis, security testing of your own software, and solving crackmes/CTFs. Use it to observe and understand, not to break things.

## How Frida works

Frida puts an engine called gum into the target process, and that engine runs your JavaScript script (called an agent) inside the process's address space. Since the script runs inside the process, it sees every function, memory region and register the way the process does.

There are two ways to get the script in. With attach, you attach to an already running process, which is useful when the program has started and you want to look in from the middle. With spawn, Frida launches the program itself in a suspended state, loads the script, and only then lets it run. That's useful when you need to hook something that happens very early (before main, in an init function).

The command-line tools you'll type a lot: `frida-ps -U` lists processes (the `-U` flag is for a USB device like Android, drop it for the local machine). `frida -l hook.js -f ./target` spawns `target` and loads `hook.js`, while `frida -l hook.js target` attaches to the process named `target`. `frida-trace` generates hooks automatically (covered at the end).

## Interceptor

Almost all of your hooking goes through `Interceptor.attach`. It takes a function address and two callbacks: `onEnter` runs on entering the function (you can read the parameters now), `onLeave` runs when the function is about to return (you can read and change the return value now).

To find the function address, if the function is exported (like system APIs), use the name:

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

A few things in that snippet. `args` is the parameter array, and Frida handles the calling convention for you: `args[0]` is the first parameter whether it's in rcx on Windows or rdi on Linux, so the same script runs cross-platform. Each `args[i]` is a `NativePointer`, so you have to interpret it yourself: `.readUtf16String()` for Windows wide strings, `.readCString()` for C strings, `.toInt32()` for numbers. And `this` is shared between `onEnter` and `onLeave`, so save values in onEnter to reuse in onLeave (like `this.name`).

### Changing parameters and return values

Hooks aren't just for looking, you can modify things too. For example, make a license check function always return "valid":

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

### Interceptor.replace

When you want to replace the entire function with your own implementation (not just look or modify), use `Interceptor.replace`:

```javascript
const origStrcmp = new NativeFunction(pStrcmp, 'int', ['pointer', 'pointer']);
Interceptor.replace(pStrcmp, new NativeCallback((a, b) => {
    console.log("strcmp: " + a.readCString() + " vs " + b.readCString());
    return origStrcmp(a, b);   // still call the original
}, 'int', ['pointer', 'pointer']));
```

## NativeFunction and NativePointer

Sometimes you don't just want to hook, you want to call a function that already exists in the process, for example to try the decryption function with your own input. `NativeFunction` wraps an address into a function you can call from JS:

```javascript
const decrypt = new NativeFunction(ptr("0x401500"), 'pointer', ['pointer', 'int']);
const buf = Memory.allocUtf8String("encrypted data");
const result = decrypt(buf, 14);
console.log("decrypted: " + result.readCString());
```

`NativePointer` (shortened to `ptr(...)`) is Frida's pointer type, with `.readByteArray()`, `.writeUtf8String()`, `.add(offset)`, `.readPointer()` so you can read and write memory freely. `Memory.alloc` allocates new memory in the process when you need to pass a buffer.

## Stalker

`Interceptor` hooks at function boundaries. When you need to follow the execution flow inside a function (each basic block, which instructions run, code coverage), use `Stalker`. It follows a thread and reports each block executed. It's used a lot for fuzzing and for finding which code runs when you enter the right serial versus the wrong one:

```javascript
Stalker.follow(Process.getCurrentThreadId(), {
    events: { block: true },
    onReceive(events) {
        // list of blocks that just ran, used to measure coverage
    }
});
```

Stalker is heavy and much more complex than Interceptor, so save it for when you need coverage, and don't use it for ordinary hooks.

## frida-trace

If you don't want to write a script by hand, `frida-trace` generates handlers for you:

```
frida-trace -f ./target -i "strcmp" -i "CreateFileW"
```

The `-i` flag picks functions by name (with wildcards, for example `-i "str*"` catches every function starting with str). Frida creates a JS file for each function in the `__handlers__` folder, and you open it to edit and print more parameters. It's the fastest way to get an overview of which APIs the program calls.

## Android

The foundation is the same, the only difference is that you hook Java methods via `Java.perform` and `Java.use` instead of native functions. That part is covered in [Lesson 6.6](/posts/re-6-6-frida-android-changing-app-behavior-while/). For the native `.so` libraries in an Android app you go back to `Interceptor.attach` like in this lesson. You need `frida-server` running on the device and the `-U` flag.

## A few common pitfalls

The Frida host and frida-server (on Android/iOS) must be the same version, and a mismatch gives confusing errors. If you hook too early and the module isn't loaded yet, `Module.findExportByName` returns null, so use `spawn` or in some cases wait for the module. Protected software may also probe port 27042, the string "frida", or odd threads. When you hit that, see [Lesson 15.7](/posts/re-15-7-anti-attach-anti-dump-anti-hook/) on anti-hook and consider running Frida in a stealthier mode. Finally, `args[0]` is a pointer, so printing it directly gives an address and not the content, and you have to call `.readUtf8String()` or similar.

## Lab

The goal is to use Frida to hook the compare function of a program so that you (1) see the correct string it compares your input against, and (2) force the return value to pass the check without knowing the password. Install Frida with `pip install frida-tools` (you need `frida` and `frida-trace` on your PATH). Then build the target, `target.c`. On Linux:

```
gcc -O0 target.c -o target
```

On Windows, with MSVC or with MinGW:

```
cl /Od target.c
gcc -O0 target.c -o target.exe
```

Run `target` normally first, enter a wrong password and see it print `Nope.`. Then spawn the target under Frida with the sample script `hook.js`:

```
frida -l hook.js -f ./target
```

Enter any string and watch the line `[strcmp] '...' vs '...'`. One side is your input and the other is the correct password. Enter the password that was just revealed and confirm you get `Correct!`. Then open `hook.js` and uncomment the line `retval.replace(0);` in `onLeave`. Run again, enter any wrong string, and this time it still prints `Correct!` because every `strcmp` is forced to return 0.

Some questions to think about. Why does hooking `strcmp` in libc catch the password comparison without your needing to know where `main` is? If the program wrote its own byte-by-byte comparison loop instead of calling `strcmp`, would this still work, and where would you hook then? And does forcing `retval` past the check reveal the real password? When do you need the real password and when is passing the check enough?

<div class="lab-box">
<div class="lab-head"><b>LAB 17.2</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/17.2/src/hook.js" download><i class="fa-solid fa-file-code"></i>src/hook.js</a>
<a class="lab-file" href="/assets/labs/17.2/src/target.c" download><i class="fa-solid fa-file-code"></i>src/target.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The target `target.c` compares the input with the string `Fr1da_H00k_Me` using `strcmp`: entering `Fr1da_H00k_Me` prints `Correct!` and entering anything else prints `Nope.`.

To reveal the password through the `strcmp` hook, run:

```
frida -l hook.js -f ./target
```

When you enter any string, the `onEnter` of the hook prints both sides of `strcmp`:

```
[strcmp] 'abc'  vs  'Fr1da_H00k_Me'
```

The first side is the input you just typed and the second is the `secret` the program compares against. The correct password shows up immediately without reading a line of assembly. `strcmp` is an exported libc function, so `Module.findExportByName("libc.so.6", "strcmp")` finds its address even though your own program has no symbols at all. Every `strcmp` call in the process goes through that one point, so hooking one place catches them all. Entering `Fr1da_H00k_Me` then makes the program print `Correct!`, which is the real answer.

To force the check without the password, uncomment the line in `onLeave`:

```javascript
onLeave(retval) {
    retval.replace(0);   // strcmp == 0 means the two strings are equal
}
```

`strcmp` returns 0 when the two strings match. Forcing every call to return 0 makes `if (strcmp(...) == 0)` always true, so whatever you enter prints `Correct!`. That passes the check without the answer.

On the questions, the hook catches the comparison without needing `main` because the comparison goes through libc's `strcmp`, a common exported point, and Frida hooks by export name, independent of the author's code. If the program wrote its own comparison loop, hooking `strcmp` would miss it because there is no `strcmp` call. Then you have to find the program's own compare function (read it statically in Ghidra or IDA to get an address, for example `0x401234`) and use `Interceptor.attach(ptr("0x401234"), ...)`, or hook at a higher level such as the function that reads the input. Forcing `retval` doesn't reveal the real password: it only makes the program believe it matched, and you still don't know the password. When the goal is just to get past the check, forcing `retval` is enough and the fastest. When you need the password itself (for example to solve a later layer that uses the password as a key) you have to get the real value as in the first step.

The Frida output lines above are representative samples that follow Frida's standard behavior, so your own output will differ in the details.

</details>

## Key takeaways
Frida injects a JS agent into the running process, sees everything from the inside, and works cross-platform. `Interceptor.attach` with `onEnter` (parameters) and `onLeave` (return value) is the main tool. `args[i]` is numbered by logical parameter order and Frida handles the calling convention, but each is a NativePointer, so you have to interpret the type yourself.

`retval.replace(x)` changes the return value and assigning to `args[i]` changes a parameter. Use `NativeFunction` to call functions in the process yourself, `Stalker` to trace each block, and `frida-trace` to generate hooks quickly. On Android, hook Java via `Java.use` (Lesson 6.6), while native `.so` still uses Interceptor.
