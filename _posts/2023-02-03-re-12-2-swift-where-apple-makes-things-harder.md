---
title: "Lesson 12.2: Swift, where Apple makes things harder for you than Objective-C"
image:
  path: /assets/img/covers/re-12-2-swift-where-apple-makes-things-harder.webp
  alt: "Lesson 12.2: Swift, where Apple makes things harder for you than Objective-C"
date: 2023-02-03 20:08:00 +0700
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

The aim of this lab is to get used to Swift name mangling, to use `swift demangle`, and to spot retain/release calls and witness tables in a Swift Mach-O. Ideally you have a Mac with Xcode, which gives you `swift demangle` and lets you build your own sample. Without a Mac you can still do the demangling part by reading the rules, and the analysis part with Hopper, IDA or Ghidra on a downloaded Swift Mach-O.

Start by demangling by hand and then with the tool. For each of the symbols below, guess the meaning first and then check it with `swift demangle` (or `xcrun swift-demangle`).

```
$s4Demo10ValidatorC5check6inputSbSS_tF
$s4Demo4UserV4nameSSvg
$ss27_finalizeUninitializedArrayySayxGABnlF
```

Then recognize a Swift binary. Take a Swift Mach-O (a Swift command-line app you built yourself, or a downloaded binary) and run the commands below, confirming that you see `__swift5_*` sections and a link to `libswiftCore`.

```bash
otool -l binary | grep -A2 swift5
otool -L binary | grep swift
nm binary | grep '\$s' | head
```

Next, filter out the ARC noise. Open the binary in Hopper, IDA or Ghidra, pick one of the author's functions and count the calls to `swift_retain` and `swift_release`. Practice reading the function by skipping them and looking only at comparisons and named calls. After that, find a witness table: look for a function that calls a method through a protocol. You will see an instruction that loads a table of pointers followed by `call [reg+offset]`, just like a C++ vtable. Write down the offset and guess which method it corresponds to. If the binary also has an `@objc` part, look for `objc_msgSend` and compare, deciding which part is easier to read and why.

If you have Xcode, you can create a sample yourself.

```bash
cat > demo.swift <<'EOF'
class Validator {
    func check(input: String) -> Bool { return input == "SwiftRev" }
}
let v = Validator()
print(v.check(input: CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : ""))
EOF
swiftc -O demo.swift -o demo
nm demo | grep '\$s'
```

Then open `demo` in Hopper and find `Validator.check`. Try it yourself before opening the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The demangling below is based on Swift's official mangling scheme. If you have a Mac, run `swift demangle` yourself to check, and the results will match.

For the first symbol, `$s4Demo10ValidatorC5check6inputSbSS_tF` demangles to `Demo.Validator.check(input: Swift.String) -> Swift.Bool`. Reading it piece by piece, `4Demo` is the module Demo, `10Validator` plus `C` is the class Validator, `5check` is the method check, `6input` is the parameter label input, `SS` is the type Swift.String, `Sb` is the return type Swift.Bool, and `F` means function.

The second, `$s4Demo4UserV4nameSSvg`, demangles to `Demo.User.name.getter : Swift.String`. Here `4UserV` is the struct User (V = struct), `4name` is the property name, `SS` is the type String, and `vg` is the getter of the property.

The third, `$ss27_finalizeUninitializedArrayySayxGABnlF`, demangles to `Swift._finalizeUninitializedArray<A>(_: __owned Swift.Array<A>) -> Swift.Array<A>`. It is an internal stdlib function (module `s` = Swift), generic (`l`), related to array initialization. You meet this kind a lot when reading code with array literals, and you can treat it as stdlib boilerplate.

A tip for reading these: `C` = class, `V` = struct, `O` = enum, `F` = function, `vg` and `vs` = getter and setter, `SS` = String, `Sb` = Bool, `Si` = Int.

To recognize a Swift binary, the sure signs are these. `otool -l` shows the sections `__swift5_types`, `__swift5_proto` and `__swift5_fieldmd`. `otool -L` shows `/usr/lib/swift/libswiftCore.dylib`. `nm` shows a lot of `$s...` symbols. If you only see `__objc_*` and no `__swift5_*`, it is pure ObjC and you should go back to Lesson 12.1.

For filtering ARC, a small decompiled Swift function often interleaves things like this.

```
swift_retain(x)
... a few instructions of logic ...
swift_release(x)
swift_bridgeObjectRelease(y)
```

The way to read it is to mentally grey out every `swift_retain`, `swift_release` and `swift_bridgeObject*` line. What remains is the logic. For the `check` function in the example, after removing ARC you are left with exactly one string comparison call and one branch returning a Bool.

For witness tables, when a method is called through a protocol (for example `someProtocol.doWork()`), the code loads the protocol witness table and then calls indirectly.

```
mov  rax, [rbx+0x8]   ; load the witness table pointer
call [rax+0x10]       ; call the 3rd slot in the table
```

It is exactly like the C++ vtable in Lesson 4.2: `call [reg+offset]` with the offset telling you the slot. Rebuild the table by looking at the function pointers the witness table points to (IDA and Ghidra have often already named them if they could read `__swift5_proto`).

Compared with ObjC, the `@objc` part goes through `objc_msgSend(receiver, selector, ...)`, and by reading the selector (the second parameter, usually a pointer to a string in `__objc_methname`) you know which method is being called, as in Lesson 12.1. Pure Swift has no such landmark, so you rely on the demangled symbols and witness tables. So with a hybrid app, work on the `@objc` part first, because it is cheaper.

The takeaway is that Swift makes you do an extra demangling step and get used to ARC noise, but once demangled, the function names tell you almost everything. The best anchors are still the demangled symbols, the strings (including panic and assert messages), and the bridge boundary into ObjC.

</details>

## Key takeaways

A Swift binary shows `$s`/`_$s` symbols, `__swift5_*` sections, and a link to `libswiftCore.dylib`. Always demangle with `swift demangle` or let IDA/Ghidra/Hopper do it. Pure Swift calls statically or through witness tables, with no `objc_msgSend` landmark like ObjC, so it's harder, but anything marked `@objc` or inheriting NSObject still goes through `objc_msgSend` and that part is easy.

ARC sprinkles retain/release everywhere, so treat it as noise and skip it. Swift String isn't null-terminated, and comparison goes through its own functions, not strcmp.
