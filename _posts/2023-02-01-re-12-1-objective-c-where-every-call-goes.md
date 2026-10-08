---
title: "Lesson 12.1: Objective-C and objc_msgSend"
image:
  path: /assets/img/covers/re-12-1-objective-c-where-every-call-goes.webp
  alt: "Lesson 12.1: Objective-C and objc_msgSend"
date: 2023-02-01 14:30:00 +0700
categories: ["Reverse Engineering", "Part 12 · Swift and Objective-C"]
tags: [reverse-engineering, ios, swift]
render_with_liquid: false
---
Open a macOS or iOS app written in Objective-C in IDA for the first time and it looks strange because there are almost no direct function calls. Instead there's `call objc_msgSend` repeated thousands of times. If you don't know what's going on, you'd think the whole program calls a single function. This lesson explains the mechanism and why it actually helps the reverser.

## Objective-C sends messages

In C or C++, calling a function is a `call` straight to its address. Objective-C works differently, because every method call is translated into a message sent through a single function called `objc_msgSend`.

A familiar line of Objective-C:

```objc
[account checkPassword:input];
```

is turned by the compiler into:

```objc
objc_msgSend(account, @selector(checkPassword:), input);
```

It means "send the object `account` a message named `checkPassword:`, with the parameter `input`". Only at runtime does the Objective-C runtime look up whether the class of `account` has a method named `checkPassword:` and jump to it. This is dynamic dispatch, and it's why you see `objc_msgSend` everywhere.

## Reading objc_msgSend in assembly

Since everything goes through `objc_msgSend`, you need to read its first two parameters. Following the macOS/iOS calling convention (System V on x64, or AAPCS on ARM64), the parameters sit in the registers you already know from [Lesson 1.3](/posts/re-1-3-x86-x64-assembly-1-registers-instructions/). The first parameter (`rdi` on x64, `x0` on ARM64) is the receiver, the object receiving the message. The second (`rsi` on x64, `x1` on ARM64) is the selector, the method name as a string. From the third onward (`rdx`/`x2`...) come the real parameters of the method.

A typical x64 snippet looks like this:

```asm
lea  rsi, selRef_checkPassword_   ; rsi = selector "checkPassword:"
mov  rdi, rbx                     ; rdi = receiver (the account object)
mov  rdx, r14                     ; rdx = input parameter
call objc_msgSend
```

Look at `rsi` (or `x1`) to know which method is being called. IDA and Ghidra usually annotate the selector next to the call themselves, so you read `objc_msgSend(account, "checkPassword:", input)` almost as readable as a line of the original code. When the tool doesn't, you trace `rsi` back to the `__objc_selrefs` region yourself to get the name.

ARM64 is the same, just with different registers:

```asm
adrp x1, selRef_checkPassword_@PAGE
...
mov  x0, x19                      ; receiver
bl   _objc_msgSend
```

## The metadata keeps the names

Objective-C is much easier to reverse than C++ because the runtime needs class names, method names and parameter types to dispatch at runtime, so the compiler embeds all of that information into the Mach-O file. Going back to [Lesson 1.8](/posts/re-1-8-elf-mach-o-two-formats-outside/) on Mach-O, you'll see dedicated sections. `__objc_classlist` holds the list of classes in the binary, `__objc_methname` the names of all methods (as selectors), `__objc_classname` the class names, and `__objc_selrefs` the selector references that the code uses.

So names like `checkPassword:`, `AccountManager`, `validateLicense` are still sitting in the binary, not mangled like C++ and not stripped like native C. You almost get a table of contents for the program.

## class-dump: getting the whole interface back

Since the metadata is intact, there's a tool that rebuilds the header files almost completely, `class-dump` (and `class-dump-swift` for Swift support). Run it on an ObjC Mach-O:

```
class-dump /path/to/MyApp.app/Contents/MacOS/MyApp
```

The result is full `@interface` declarations, covering every class, its list of methods, properties and instance variables. It's like having the program's `.h` files back. From there you know which classes matter (for example `LicenseManager`) and which methods are the targets (`-isValidLicense:`), and only then open IDA/Ghidra to read the bodies.

## The practical workflow

First identify the file, because a Mach-O with `__objc_*` sections that imports `objc_msgSend` is an Objective-C app. Run `class-dump` to get the interface and read it to narrow down the classes and methods of interest. Then open IDA/Ghidra and jump to the target method (IDA names methods like `-[AccountManager checkPassword:]`).

Read the method body, and at each `objc_msgSend` look at the selector in `rsi`/`x1` to see what it calls. Follow the chain of messages to understand the logic, and rename variables as you go, like the habit from [Lesson 0.4](/posts/re-0-4-reverse-engineering-workflow-not-get-lost/).

## A few pitfalls

`objc_msgSend` has relatives, `objc_msgSendSuper` (calls up to the superclass), `objc_msgSend_stret` (method returns a struct), and `objc_msgSend_fpret` (returns a float). When you meet a variant, you read the selector the same way. A selector is just a name, not an address, so two different classes can have the same `init` selector and you have to look at the receiver too to know which method actually runs.

An app can also call methods through dynamic strings (`NSSelectorFromString`), in which case the selector doesn't show up statically and you have to watch it at runtime. Obfuscated code may rename selectors to nonsense, but in most ordinary commercial apps the names are still very clear.

## Lab

The task is to practice extracting the interface with class-dump and reading method calls through `objc_msgSend` in Ghidra or IDA. You need a macOS machine (or any Objective-C Mach-O you are allowed to analyze, which can be a small system binary in `/usr/bin` or a simple ObjC app you build with `clang`), `class-dump` (or `class-dump-swift`) from the official source or through Homebrew, and Ghidra or IDA with a Mach-O loader. If you build your own sample on macOS, write a small class with a password-checking method as the target, in a file such as `accountdemo.m`, and build it with:

```
clang -framework Foundation -o accountdemo accountdemo.m
```

First confirm that the file is a Mach-O and is Objective-C, using `file`, then `otool -l` to find the sections `__objc_classlist` and `__objc_methname`, which ties back to Lesson 1.8. Run `class-dump <binary>` and read the output, listing the classes and methods and picking out which class looks related to the main logic (for example one with "verify", "license" or "password" in a name). Then open the binary in Ghidra or IDA, find the import `objc_msgSend`, and see how many places call it. Choose a target method from the class-dump output and jump to its body. For each `objc_msgSend`, read the selector at `rsi` (x64) or `x1` (ARM64) and rewrite the original line of code in the form `[receiver selector:arg]`. Follow the chain of messages to understand what the method does.

Two questions to think about. Why is reversing Objective-C usually easier than C++ even though both are native code? And if the app calls a method through `NSSelectorFromString(someString)`, does the static reading above still work, and what would you have to do differently? Do it yourself before opening the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The procedure below describes the standard way of working on macOS, and the exact output will differ from binary to binary.

### Task 1: confirming Objective-C

```
file accountdemo
# accountdemo: Mach-O 64-bit executable arm64 (or x86_64)

otool -l accountdemo | grep -A2 __objc
# you see the sections: __objc_classlist, __objc_methname, __objc_classname, __objc_selrefs
```

The `__objc_*` sections mean the binary contains Objective-C metadata. That is the data source for class-dump and for IDA and Ghidra's automatic annotation.

### Task 2: class-dump

```
class-dump accountdemo
```

Sample output (the shape of it):

```objc
@interface AccountManager : NSObject
{
    NSString *_storedHash;
}
- (BOOL)checkPassword:(NSString *)arg1;
- (void)reset;
@end
```

The class `AccountManager` with a `checkPassword:` method returning `BOOL` is an obvious target. The method names and types are intact because ObjC metadata is not mangled.

### Task 3: finding objc_msgSend

In Ghidra, go to Symbol Tree > Imports > `_objc_msgSend`, right-click > Show References. In IDA, jump to `objc_msgSend` and look at the xrefs. A medium-sized app has hundreds to thousands of calls, which is normal because every method call goes through here.

### Task 4: reading selectors

IDA usually names functions like `-[AccountManager checkPassword:]` for you. Inside the body, a typical x64 excerpt:

```asm
lea  rsi, selRef_length            ; selector "length"
mov  rdi, r14                      ; receiver = the input string
call objc_msgSend                  ; = [input length]
mov  r15, rax                      ; save the length
...
lea  rsi, selRef_isEqualToString_  ; selector "isEqualToString:"
mov  rdi, rbx                      ; receiver = _storedHash
mov  rdx, r14                      ; arg = input (processed)
call objc_msgSend                  ; = [_storedHash isEqualToString:input]
test al, al
```

Rewritten as the original code:

```objc
NSUInteger len = [input length];
...
if ([_storedHash isEqualToString:input]) { ... }
```

On ARM64 you read it the same way, with the selector in `x1` and the receiver in `x0`.

### Task 5: understanding the logic

The chain of messages shows that the method takes the length of the input, may hash or transform it, and then compares it against `_storedHash` with `isEqualToString:`. So this is a string comparison, and to find the correct value you would next trace where `_storedHash` is assigned (usually in `init` or a setup method).

### Answers to the questions

It's easier than C++ because the ObjC runtime forces the compiler to keep class names, method names and selectors in the binary for dispatch at run time. C++ mangles the names and resolves most things at compile time, so it has no need to keep them. As for dynamic selectors, no, because if the selector is built from a dynamic string through `NSSelectorFromString`, the name does not appear next to the static call. You have to run it dynamically (a debugger, or a Frida hook on `objc_msgSend`) to catch the actual selector at run time.

</details>

## Key takeaways
Objective-C dispatches via `objc_msgSend(receiver, selector, args)`, not a direct call. Read the selector at `rsi` (x64) or `x1` (ARM64) to know which method is called, with the receiver in `rdi`/`x0`.

The ObjC metadata embedded in the Mach-O (`__objc_classlist`, `__objc_methname`...) keeps the class and method names, and `class-dump` extracts the whole `@interface` from it, like getting the header files back. The workflow is class-dump to narrow down, then read method bodies in IDA/Ghidra by selector.
