---
title: "Lesson 4.5: Plugins that rebuild C++ classes"
image:
  path: /assets/img/covers/re-4-5-plugins-that-rebuild-c-classes-let.webp
  alt: "Lesson 4.5: Plugins that rebuild C++ classes"
date: 2022-07-20 11:16:00 +0700
categories: ["Reverse Engineering", "Part 04 · C++"]
tags: [reverse-engineering, cpp]
render_with_liquid: false
---
In lesson 4.2 you built the class tree by hand, which meant finding the vtable, reading the RTTI, assigning types and tracing inheritance. One or two classes is fine, but a real C++ program with a few dozen classes is a whole day of repeating the same job. That job is better handed to a plugin. Plugins don't understand the logic for you, but they clear out the mechanical part so you can focus on the author's code.

This lesson goes over the main plugins for IDA and Ghidra, and when to trust them and when to do it by hand again.

## Why it can be automated

Recall that in lesson 4.2 a C++ binary built with RTTI (Run-Time Type Information) carries a lot of structured clues. Each class with virtual functions has a `type_info`, a mangled class name string, and a vtable pointing to it. These sit in a fixed layout set by the ABI (Itanium on Linux, MSVC ABI on Windows), so a machine can scan it. The plugin walks the RTTI structures, reads class names, connects vtables to classes, and infers parent and child from the base class table.

If the binary has RTTI, a plugin does about 80% of building the class tree in a few seconds. If RTTI is turned off (`/GR-` on MSVC, `-fno-rtti` on g++) or obfuscated, plugins run out of steam and you go back to doing it by hand like in lesson 4.2.

## On the IDA side

### Class Informer

Class Informer scans the whole binary for RTTI structures and lists every class it finds, with vtable addresses and inheritance relationships. Run it once and you have a list of real classes with real names (`Animal`, `Dog`, `BankAccount`) instead of `sub_` and `off_`. It also marks each vtable in IDA so you can jump to the virtual functions.

When I open a large C++ binary in IDA, the first step is usually to run Class Informer to get the class map, then go deeper.

### HexRaysPyTools

Class Informer gives you the list of classes, and HexRaysPyTools helps turn that list into types usable in the decompiler. It can build a struct from usage. Put the cursor on a variable that the decompiler shows as `a1` with many `*(a1 + 8)`, `*(a1 + 16)`, and the plugin gathers those offsets and proposes a struct. Accept it and Hex-Rays shows `obj->field_8` instead of raw pointer arithmetic. It also recognizes vtables and creates vtable structs, hooking virtual methods up in the right place, and it can scan multiple functions to merge what you've learned about the same type.

Class Informer (finds classes) plus HexRaysPyTools (turns them into types) is the standard combo for C++ RE on IDA. See also the [tool collection](/posts/re-resources-reverse-engineering-tool-repository-roundup/).

### Virtuailor

A virtual call in asm is `call [rax+offset]`, and the decompiler doesn't know which function is called because it depends on runtime. Virtuailor follows the vtable to assign function names to virtual calls, so you see `call Dog::speak` instead of `call qword ptr [rax+0x10]`.

## On the Ghidra side

### The built-in RTTIAnalyzer

Ghidra needs nothing extra for the basic step. During auto-analysis, if you enable the RTTI-related analyzers (named something like "Windows x86 PE RTTI Analyzer" or the C++ class analysis part), Ghidra creates the type_info structures, names the vtables, and builds part of the hierarchy. Check the Data Type Manager after analysis to see the classes it created.

### OOAnalyzer and Kaiju

For binaries without RTTI (where RTTIAnalyzer can't help), there are stronger approaches. OOAnalyzer (part of CERT's Pharos suite) uses static analysis to infer classes, members, and methods even without RTTI, then exports the results to load into Ghidra via a plugin. Kaiju (CERT) is a Ghidra utility suite that bundles many binary analyses, including the part that supports OOAnalyzer. The setup is heavier than an ordinary plugin, but it's worth it when you hit a big C++ binary without RTTI.

Ghidra is also scriptable (Java/Python), so there are many community scripts that recover classes, assign vtables, and name things from RTTI. When the ready-made plugins don't fit, writing a script is the way out.

## When plugins help, when to do it by hand

Plugins aren't a one-click fix. Know their limits:

| Situation | Can a plugin help? |
|---|---|
| Binary has RTTI, not obfuscated | Very well, the class tree is built almost automatically |
| RTTI turned off (`-fno-rtti`, `/GR-`) | Poorly, you have to infer classes from vtables and usage, by hand like lesson 4.2 |
| A packer/obfuscator hides the vtables | Unpack first (Part 14), plugins are useless on code that isn't exposed |
| You only need to understand one function, not the whole class tree | Often faster by hand, no need to run a plugin |
| Huge classes, lots of inheritance | A plugin saves hours |

One pitfall is that plugins name things from RTTI, but RTTI only reflects the class name at compile time and says nothing about the logic. A pretty class tree doesn't mean you understand what the program does. A class name is a starting point for reading.

## Lab

The goal is to see how much effort a plugin saves compared with building the classes by hand in the lab from Lesson 4.2, and to learn where the plugins stop working. Reuse the C++ binary with RTTI from that lab. If you haven't built it yet, go back and do that first, with RTTI enabled, which means a default build without `-fno-rtti`. You need one of two environments, which are IDA (Free or Pro) with the Class Informer plugin, plus HexRaysPyTools if you have the Pro version, or Ghidra, which needs nothing extra because its RTTIAnalyzer is built in.

If you haven't done the Lesson 4.2 lab yet, first build the class tree by hand. Find the vtables, read the RTTI, assign types, and note how long it takes. Then run the plugin and time that too. In IDA, install Class Informer by copying it into the `plugins` folder and run it from Edit > Plugins > Class Informer, which opens a window listing the classes and vtables. In Ghidra, enable the RTTI analyzer on import (in the Analysis Options dialog, look under C++/RTTI), and after analysis open the Data Type Manager to see the classes it created and the Symbol Tree to see the vtables.

Now compare. Did the plugin find exactly the number of classes you know are in the source? Is the inheritance right? How long did it take compared with doing it by hand? Then try to break the plugin by rebuilding the binary with RTTI turned off, using `-fno-rtti` with g++ or `/GR-` with MSVC, and run the plugin again to see whether it still recognizes any classes. You'll see why the plugins depend on RTTI. If you have HexRaysPyTools, go into a method and use its feature that builds a struct from usage, and watch the decompiler change from `*(a1 + 8)` to `obj->field_8`.

Some questions to think about afterwards. Why does the `-fno-rtti` build take away the plugin's ability to name classes? Once the plugin has built the class tree, do you understand what the program does, and why not? When would you skip the plugin and work by hand?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Do all the tasks above before reading this.

For manual versus plugin, take the C++ binary with RTTI from the Lesson 4.2 lab (one base class and a few derived classes with virtual functions). By hand you find the vtables through xrefs to address constants, read the mangled RTTI strings, demangle them, assign pointer types and trace the base classes. With 3 or 4 classes that takes roughly 15 to 30 minutes if you're practiced, and much longer if you're new. Class Informer or Ghidra's RTTIAnalyzer produces the class list with vtables in a few seconds to a minute, including auto-analysis time. The gap grows with the number of classes, which is why on a real C++ binary running a plugin is almost always the first step.

On the results, the plugin should find the classes that exist in the source, but check two things. First, whether it found all of them. A class with no virtual functions has no vtable and no RTTI, so the plugin can miss it. That's a normal limit, because only polymorphic classes show up through RTTI. Second, whether the inheritance is right. For single inheritance the plugin is usually correct. Multiple inheritance and virtual inheritance are more complicated and the plugin sometimes gets them wrong, so check by hand.

After rebuilding with `-fno-rtti` (g++) or `/GR-` (MSVC), the class name strings disappear from the binary and the type_info structures are gone. Class Informer and RTTIAnalyzer have nothing left to scan and return empty or nearly empty results. The vtables still exist, since virtual functions still work, but they have no names. You have to do what Lesson 4.2 taught, which is to recognize a vtable as a group of adjacent function pointers referenced from a constructor, then name it yourself. Plugins read RTTI, not bare vtables. Losing RTTI means losing names, not structure.

With HexRaysPyTools, in a method the decompiler shows something like `*(_QWORD *)(a1 + 8)` before you build the struct. Using "Create new struct from this variable" (or scan then finalize), the plugin gathers the accessed offsets into a struct and the display changes to `a1->field_8`. Once you also name the fields by meaning, the pseudocode reads almost like the original C.

On the questions, the `-fno-rtti` build stops the plugin from naming classes because class names live in the RTTI structures (type_info), not in the vtable, and turning RTTI off removes the only source of names the plugin relies on. Having the class tree doesn't mean you understand the program. The tree only gives you the frame, meaning which classes exist and who inherits from whom. The logic is in the method bodies, which you still have to read, so class names are a starting point and not a conclusion. You drop the plugin and work by hand when RTTI is disabled or obfuscated, when you only need to understand one function rather than a whole tree, or when the plugin gets multiple inheritance wrong and you need accuracy.

</details>

## Key takeaways
Class-building plugins mainly rely on RTTI, so with RTTI they're fast and without it they run out of steam. On IDA the standard combo is Class Informer (lists classes from RTTI) plus HexRaysPyTools (turns them into types in the decompiler), with Virtuailor for virtual calls. On Ghidra the built-in RTTIAnalyzer covers the basic step and OOAnalyzer/Kaiju cover binaries without RTTI.

Plugins clear the mechanical part but don't understand the logic for you, and a class name is only a starting point. If the binary is obfuscated or packed, deal with that first, because plugins don't work on code that isn't exposed.
