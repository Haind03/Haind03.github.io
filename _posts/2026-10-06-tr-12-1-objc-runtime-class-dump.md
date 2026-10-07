---
title: "Lesson 12.1: Objective-C, where every call goes around through the runtime"
date: 2026-10-06 09:12:00 +0700
categories: ["Technique Reverse", "Part 12 · Swift and Objective-C"]
tags: [reverse-engineering, ios, swift]
render_with_liquid: false
---
Open a macOS or iOS app written in Objective-C in IDA for the first time and you'll see something strange: there are almost no direct function calls. Instead there's `call objc_msgSend` repeated thousands of times. If you don't understand what's going on, you'll think the whole program only calls a single function. This lesson explains that mechanism and why it's actually good news for the reverser.

## Objective-C doesn't call methods, it sends messages

In C or C++, calling a function is a `call` straight to its address. Objective-C does something completely different: every method call is translated into a message sent through a single intermediate function called `objc_msgSend`.

A familiar line of Objective-C:

```objc
[account checkPassword:input];
```

is actually turned by the compiler into:

```objc
objc_msgSend(account, @selector(checkPassword:), input);
```

Meaning: "send the object `account` a message named `checkPassword:`, with the parameter `input`". Only at runtime does the Objective-C runtime look up whether the class of `account` has a method named `checkPassword:` and jump to it. This is dynamic dispatch, and it's why you see `objc_msgSend` everywhere.

## Reading objc_msgSend in assembly

Since everything goes through `objc_msgSend`, the key is to read its first two parameters. Following the macOS/iOS calling convention (System V on x64, or AAPCS on ARM64), the parameters sit in the registers you already know from [Lesson 1.3](/posts/tr-1-3-assembly-1-thanh-ghi-lenh-co-ban/). The first parameter (`rdi` on x64, `x0` on ARM64) is the receiver, the object receiving the message. The second (`rsi` on x64, `x1` on ARM64) is the selector, the method name as a string. From the third onward (`rdx`/`x2`...) come the real parameters of the method.

A typical x64 snippet looks like this:

```asm
lea  rsi, selRef_checkPassword_   ; rsi = selector "checkPassword:"
mov  rdi, rbx                     ; rdi = receiver (the account object)
mov  rdx, r14                     ; rdx = input parameter
call objc_msgSend
```

The key point: **look at `rsi` (or `x1`) to know which method is being called.** IDA and Ghidra usually annotate the selector next to the call themselves, so you read `objc_msgSend(account, "checkPassword:", input)` almost like a line of the original code. When the tool doesn't do it, you trace `rsi` back to the `__objc_selrefs` region yourself to get the name.

ARM64 is the same, just with different registers:

```asm
adrp x1, selRef_checkPassword_@PAGE
...
mov  x0, x19                      ; receiver
bl   _objc_msgSend
```

## Why this is good news: the metadata keeps the names

What makes Objective-C much easier to reverse than C++: the runtime needs to know class names, method names, and parameter types to dispatch at runtime, so the compiler **embeds all of that information into the Mach-O file**. Tying back to [Lesson 1.8](/posts/tr-1-8-elf-va-mach-o/) on Mach-O, you'll see dedicated sections. `__objc_classlist` holds the list of classes in the binary, `__objc_methname` the names of all methods (as selectors), `__objc_classname` the class names, and `__objc_selrefs` the selector references that the code uses.

In other words, names like `checkPassword:`, `AccountManager`, `validateLicense` are still sitting bare in the binary, not mangled like C++ and not wiped clean like native C. You almost get a table of contents for the program.

## class-dump: getting the whole interface back

Since the metadata is intact, there's a tool that rebuilds the header files almost completely: `class-dump` (and `class-dump-swift` for Swift support). Run it on an ObjC Mach-O:

```
class-dump /path/to/MyApp.app/Contents/MacOS/MyApp
```

The result is full `@interface` declarations: every class, its list of methods, properties, instance variables. It's like having the program's `.h` files back. From there you know right away which classes matter (for example `LicenseManager`) and which methods are the targets (`-isValidLicense:`), and only then open IDA/Ghidra to read the bodies.

## The practical workflow

Put together, the rhythm goes like this. First identify the file: a Mach-O with `__objc_*` sections that imports `objc_msgSend` is an Objective-C app. Run `class-dump` to get the interface and read it to narrow down the classes and methods of interest. Then open IDA/Ghidra and jump to the target method (IDA names methods like `-[AccountManager checkPassword:]`).

Read the method body, and at each `objc_msgSend` look at the selector in `rsi`/`x1` to see what it calls. Follow the chain of messages to understand the logic, renaming variables as you understand, like the habit from [Lesson 0.4](/posts/tr-0-4-quy-trinh-reverse/).

## A few pitfalls

`objc_msgSend` has relatives: `objc_msgSendSuper` (calls up to the superclass), `objc_msgSend_stret` (method returns a struct), and `objc_msgSend_fpret` (returns a float). When you meet a variant, reading the selector works the same way. A selector is just a name, not an address, so two different classes can have the same `init` selector and you have to look at the receiver too to know which method actually runs.

An app can also call methods through dynamic strings (`NSSelectorFromString`), in which case the selector doesn't show up statically and you have to watch it at runtime. Obfuscated code may rename selectors to nonsense, but in most ordinary commercial apps the names are still very clear.

## Key takeaways
Objective-C dispatches via `objc_msgSend(receiver, selector, args)`, not a direct call. Read the selector at `rsi` (x64) or `x1` (ARM64) to know which method is called, with the receiver in `rdi`/`x0`.

The ObjC metadata embedded in the Mach-O (`__objc_classlist`, `__objc_methname`...) keeps the class and method names, and `class-dump` extracts the whole `@interface` from it, like getting the header files back. The workflow is class-dump to narrow down, then read method bodies in IDA/Ghidra by selector.
