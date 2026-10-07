---
title: "Lesson 4.5: Plugins that rebuild C++ classes, let the machine do the boring part"
date: 2022-07-20 11:16:00 +0700
categories: ["Technique Reverse", "Part 04 · C++"]
tags: [reverse-engineering, cpp]
render_with_liquid: false
---
In lesson 4.2 you built the class tree by hand: find the vtable, read the RTTI, assign types, trace inheritance. Doing one or two classes is fun, but a real C++ program with a few dozen classes is a whole day of repeating the same job. This is exactly the kind of job to hand to a plugin. They don't understand the logic for you, but they clear out the mechanical part so you can focus on the author's code.

This lesson goes over the main plugins for IDA and Ghidra, and more importantly when to trust them and when to roll up your sleeves and do it again by hand.

## Why it can be automated

Recall lesson 4.2: a C++ binary built with RTTI (Run-Time Type Information) carries a lot of structured clues. Each class with virtual functions has a `type_info`, a mangled class name string, and a vtable pointing to it. These sit in a fixed layout dictated by the ABI (Itanium on Linux, MSVC ABI on Windows). A fixed layout means a machine can scan it. The plugin just walks along the RTTI structures, reads class names, connects vtables to classes, and infers parent and child from the base class table.

The practical consequence: if the binary has RTTI, a plugin does 80% of building the class tree in a few seconds. If RTTI is turned off (`/GR-` on MSVC, `-fno-rtti` on g++) or obfuscated, plugins run out of steam and you go back to doing it by hand like in lesson 4.2.

## On the IDA side

### Class Informer

Class Informer is a plugin that scans the whole binary for RTTI structures and lists every class it finds, with vtable addresses and inheritance relationships. Run it once and you immediately have a list of real classes with real names (`Animal`, `Dog`, `BankAccount`) instead of `sub_` and `off_`. It also marks each vtable in IDA so you can jump to see the virtual functions.

This is usually the first step when opening a large C++ binary in IDA: run Class Informer to get the class map, and only then go deeper.

### HexRaysPyTools

If Class Informer gives you the list of classes, HexRaysPyTools helps you turn that list into types usable in the decompiler. It can build a struct from usage: put the cursor on a variable that the decompiler shows as `a1` with a pile of `*(a1 + 8)`, `*(a1 + 16)`, and the plugin gathers those offsets and proposes a struct. Accept it and Hex-Rays immediately shows `obj->field_8` instead of raw pointer arithmetic. It also recognizes vtables and creates vtable structs, hooking virtual methods up in the right place, and it can scan multiple functions to merge what you've learned about the same type.

The pair Class Informer (finds classes) plus HexRaysPyTools (turns them into types) is the standard combo for C++ RE on IDA. See also the [tool collection](/posts/re-resources-reverse-engineering-tool-repository-roundup/).

### Virtuailor

A problem of its own: a virtual call in asm is `call [rax+offset]`, and the decompiler doesn't know which specific function is called because it depends on runtime. Virtuailor tries to solve this by following the vtable to assign function names to virtual calls, so you see `call Dog::speak` instead of `call qword ptr [rax+0x10]`.

## On the Ghidra side

### The built-in RTTIAnalyzer

Ghidra needs nothing extra for the basic step. During auto-analysis, if you enable the RTTI-related analyzers (named something like "Windows x86 PE RTTI Analyzer" or the C++ class analysis part), Ghidra creates the type_info structures, names the vtables, and builds part of the hierarchy. Check the Data Type Manager after analysis and you'll see the classes that were created.

### OOAnalyzer and Kaiju

For binaries without RTTI (where RTTIAnalyzer is helpless), there are stronger approaches. OOAnalyzer (part of CERT's Pharos suite) uses static analysis to infer classes, members, and methods even without RTTI, then exports the results to load into Ghidra via a plugin. Kaiju (CERT) is a Ghidra utility suite bundling many binary analyses, including the part that supports OOAnalyzer. The setup is heavier than an ordinary plugin, but it's worth it when you hit a big C++ binary without RTTI.

Ghidra is also scriptable (Java/Python), so there are many community scripts that recover classes, assign vtables, and name things from RTTI. When the ready-made plugins don't fit, writing a script is the way out.

## When plugins help, when to do it by hand

Plugins aren't a magic button. Know the boundaries so you don't trust them wrongly:

| Situation | Can a plugin help? |
|---|---|
| Binary has RTTI, not obfuscated | Very well, the class tree is built almost automatically |
| RTTI turned off (`-fno-rtti`, `/GR-`) | Poorly, you have to infer classes from vtables and usage, by hand like lesson 4.2 |
| A packer/obfuscator hides the vtables | Unpack first (Part 14), plugins are useless on code that isn't exposed |
| You only need to understand one function, not the whole class tree | Often faster by hand, no need to run a plugin |
| Huge classes, lots of inheritance | A plugin saves hours |

A pitfall: plugins name things from RTTI, but RTTI reflects the class name at compile time, with no guarantee about the logic. Building a pretty class tree doesn't mean you understand what the program does. A class name is only a starting point for reading, not the destination.

## Lab

The lab is at [labs/4.5/](https://github.com/Haind03/Technique-Reverse/blob/main/labs/4.5): reuse the C++ binary with RTTI from lab 4.2, run Class Informer (or Ghidra's RTTIAnalyzer), then compare the time and results with when you built it by hand in 4.2.

## Key takeaways
Class-building plugins mainly rely on RTTI, so with RTTI they're fast and without it they run out of steam. On IDA the standard combo is Class Informer (lists classes from RTTI) plus HexRaysPyTools (turns them into types in the decompiler), with Virtuailor for virtual calls. On Ghidra the built-in RTTIAnalyzer covers the basic step and OOAnalyzer/Kaiju cover binaries without RTTI.

Plugins clear the mechanical part but don't understand the logic for you, and a class name is only a starting point. If the binary is obfuscated or packed, deal with that first, because plugins don't run on code that isn't exposed.
