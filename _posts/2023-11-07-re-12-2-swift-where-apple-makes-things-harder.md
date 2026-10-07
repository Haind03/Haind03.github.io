---
title: "Lesson 12.2: Swift, where Apple makes things harder for you than Objective-C"
date: 2023-11-07 22:18:00 +0700
categories: ["Technique Reverse", "Part 12 · Swift and Objective-C"]
tags: [reverse-engineering, ios, swift]
render_with_liquid: false
---
The previous lesson on Objective-C was actually the easy one. In ObjC every method goes through `objc_msgSend`, and the metadata keeps the names so `class-dump` gives back almost the whole interface. Swift is different. Apple designed Swift to run fast, so the compiler calls functions directly or through witness tables instead of dynamic dispatch, function names are heavily mangled, and ARC sprinkles retain/release instructions everywhere to clutter your view. This lesson teaches you how to deal with each of those.

## Recognizing a Swift binary

Before complaining about how hard it is, you have to know you're dealing with Swift. A few signs you spot at a glance: symbols start with `$s` or `_$s` (Swift 4.2 onward, older versions use `_T`), there are `__swift5_types`, `__swift5_proto`, `__swift5_fieldmd` sections in the Mach-O (see them with `otool -l` or in IDA/Ghidra), it links to `libswiftCore.dylib`, and there are scattered calls to `swift_retain`, `swift_release`, `swift_allocObject`.

See these and you know you've walked into Swift territory, not plain C or ObjC.

## Name mangling, the first wall

Swift encodes function names with a dense scheme so it can fit the namespace, parameter types, generics, and protocol conformances into one ASCII string. A name like this looks meaningless:

```
$s4Demo10ValidatorC5check6inputSbSS_tF
```

Don't try to read it by eye. There's a demangle tool:

```bash
swift demangle '$s4Demo10ValidatorC5check6inputSbSS_tF'
# or on a machine with Xcode:
xcrun swift-demangle '$s4Demo10ValidatorC5check6inputSbSS_tF'
```

The result is something readable:

```
Demo.Validator.check(input: Swift.String) -> Swift.Bool
```

Now it's clear: this is the `check` method of the class `Validator` in module `Demo`, taking a `String` and returning a `Bool`. Newer IDA and Ghidra also demangle Swift symbols on their own in the function window, but when you meet a stray string in a log or in strings, throwing it at `swift demangle` is the fastest.

Enough rules for a quick guess: a trailing `C` on a name means class, `V` is struct, `F` is function, `S S` is `Swift.String`, `S b` is `Swift.Bool`, `S i` is `Int`. No need to memorize, just recognize them so you don't panic.

## Why Swift is harder than Objective-C

This is the part you need to understand so you don't waste time looking in the wrong place.

In ObjC, every method call goes through `objc_msgSend(receiver, selector, ...)`. You read the selector and know what's called. It's very uniform and very easy to trace. In pure Swift, the compiler knows the exact type at compile time, so it calls the function address directly (static dispatch), or for protocol methods it calls through a **witness table**, a table of function pointers like a C++ vtable. There's no `objc_msgSend` as a landmark anymore and no string selector to read. You have to rely on demangled symbols and witness tables.

The exception is anything marked `@objc` or inheriting from `NSObject`, which still goes through `objc_msgSend`, so many Swift apps mix the two worlds. Seeing `objc_msgSend` is a relief, because that part is as easy as ObjC.

## ARC, the noise you have to learn to ignore

Swift manages memory with ARC (Automatic Reference Counting). The compiler inserts `swift_retain` and `swift_release` around each use of an object to count references. The consequence when reversing: the pseudocode of a simple Swift function can be packed with retain/release calls interleaved with the real logic.

A survival tip: treat `swift_retain`, `swift_release`, `swift_bridgeObjectRetain`, `swift_bridgeObjectRelease` as background noise. When reading, skip them and focus on the other calls and the comparisons. Many beginners think these calls are important logic and get lost there.

## Reading String in Swift

Swift's `String` is not a null-terminated C string. It's a struct with a counter and flags, short strings can be stuffed straight into the struct (small string optimization like `std::string`), and long strings point out to memory. When comparing strings, Swift calls `swift_stringCompare` or similar, not `strcmp`. See one of the `$sSS...` functions related to String and you know a string is being handled.

When Swift talks to ObjC APIs, strings are bridged to `NSString`, and then you see `_bridgeToObjectiveC`. This is a useful clue: the bridge point is often the boundary between the author's Swift code and Apple's frameworks.

## Tools

Hopper has for a long time been the strongest for Mach-O, with good Swift demangling and tidy pseudocode. IDA (newer versions) works with a Swift metadata plugin, and Ghidra with community Swift scripts that parse `__swift5_types` to rebuild types. Keep `swift demangle` / `swift-demangle` ready in the terminal, and use `otool -l` / `-o` to list sections and ObjC/Swift metadata.

## The short workflow

First recognize it's Swift (`$s` symbols, `__swift5_*` sections, links `libswiftCore`). Open it in Hopper or IDA and let it demangle the symbols, and for stray symbols demangle manually with `swift demangle`. When reading a function, skip retain/release and focus on comparisons and named calls. When you hit `objc_msgSend` read it like ObjC (lesson 12.1), and when you hit a witness table follow the table of function pointers.

## Lab

See [labs/12.2/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/12.2). You'll demangle a batch of Swift symbols, and practice spotting retain/release and witness tables in a Swift Mach-O.

## Key takeaways

A Swift binary shows `$s`/`_$s` symbols, `__swift5_*` sections, and a link to `libswiftCore.dylib`. Always demangle with `swift demangle` or let IDA/Ghidra/Hopper do it. Pure Swift calls statically or through witness tables, with no `objc_msgSend` landmark like ObjC, so it's harder, but anything marked `@objc` or inheriting NSObject still goes through `objc_msgSend` and that part is easy.

ARC sprinkles retain/release everywhere, so treat it as noise and skip it. Swift String isn't null-terminated, and comparison goes through its own functions, not strcmp.
