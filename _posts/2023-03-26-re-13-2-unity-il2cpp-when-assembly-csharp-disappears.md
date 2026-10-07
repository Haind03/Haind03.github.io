---
title: "Lesson 13.2: Unity IL2CPP, when Assembly-CSharp disappears"
image:
  path: /assets/img/covers/re-13-2-unity-il2cpp-when-assembly-csharp-disappears.webp
  alt: "Lesson 13.2: Unity IL2CPP, when Assembly-CSharp disappears"
date: 2023-03-26 15:39:00 +0700
categories: ["Technique Reverse", "Part 13 · Games: Unity, Unreal, Lua"]
tags: [reverse-engineering, game-hacking]
render_with_liquid: false
---
In the last lesson you opened a Unity game built with Mono, saw `Assembly-CSharp.dll`, dragged it into dnSpy and could read almost the source. Nice. Then one day you open a different game, search the whole folder and `Assembly-CSharp.dll` is nowhere to be found, just a huge `GameAssembly.dll` and a strange file called `global-metadata.dat`. That's when you've met IL2CPP, and the game changes completely.

## What IL2CPP does to your C# code

Mono keeps C# as IL inside a .NET DLL, so it decompiles nicely. IL2CPP (Intermediate Language To C++) is different: at build time, Unity takes your IL, translates it to C++, then compiles that C++ into native machine code sitting in `GameAssembly.dll` (Windows), `libil2cpp.so` (Android), or embedded in the binary (iOS).

The blunt consequence is that there's no more IL and no more .NET metadata, so dnSpy and ILSpy are useless. The code is now native, you have to open it in IDA or Ghidra and read it like C++. It's the same turning point as .NET's NativeAOT (Lesson 5.6) or Python's Nuitka (Lesson 7.5): the managed layer is stripped away and you drop down to native.

Sounds discouraging, but there's a very big piece of good news.

## global-metadata.dat, the gift of IL2CPP

IL2CPP needs to know class names, method names, field names at runtime (for reflection, serialization, calling by name...). It keeps all those names in a separate file: `global-metadata.dat` (usually in `GameName_Data/il2cpp_data/Metadata/`).

In other words, the machine code lost all its names, but the table of names is still sitting right there in a file. Our job is to join the two: take the names from `global-metadata.dat` and assign them to the right functions in `GameAssembly.dll`. There are tools that do this automatically.

## Il2CppDumper, the main knife

Il2CppDumper takes two inputs, `GameAssembly.dll` and `global-metadata.dat`, and spits out a few things. `dump.cs` is a pseudo-C# file listing every class, method, field, along with the address (RVA) of each method in the binary, and this is your map. `script.json` and a script (`ida.py` or `ghidra.py`) can be loaded into IDA/Ghidra so it names the functions from the metadata automatically. There are also a few extra files (`il2cpp.h` holding structs) for importing types.

The short workflow:

```
1. Find GameAssembly.dll and global-metadata.dat in the game folder.
2. Run Il2CppDumper, pointing at those two files.
3. Open GameAssembly.dll in IDA/Ghidra, wait for the analysis to finish.
4. Run the script Il2CppDumper generated (ida.py / ghidra.py).
5. Now the sub_xxx functions have real names like PlayerController$$TakeDamage.
6. Read dump.cs to know which functions are worth looking at, jump to that RVA and read the logic.
```

After step 5, the experience is almost back to Mono: you see meaningful function names, the only difference is you have to read native pseudocode (C) instead of clean C#. Still far better than swimming in `sub_18004A2C0`.

## Cpp2IL, the more modern option

Cpp2IL goes further than Il2CppDumper: it tries to rebuild IL (and from that, approximate C#) from the machine code, not just assign names. For newer Unity versions where Il2CppDumper sometimes stumbles (the metadata format keeps changing by version), Cpp2IL usually handles them better and gives output closer to the source. There are even plugins that export a form you can open with dnSpy.

In practice, try Il2CppDumper first because it's fast and solid, and if it can't parse the metadata (it reports a version error) switch to Cpp2IL. The two tools complement each other.

## Common pitfalls

The first is the wrong metadata version. `global-metadata.dat` has a version number that changes with the Unity version, and old tools can't read the new one, so update the tool or try Cpp2IL.

The second is obfuscated metadata. Some games deliberately encrypt or shuffle `global-metadata.dat` (changed header, encrypted strings) to block Il2CppDumper. Then you have to recover the metadata first (there are forks of the tool built for this, or you dump it from memory while the game is running, similar to the unpacking mindset in Part 14).

The third is looking for the wrong file. On Android, the equivalent of `GameAssembly.dll` is `lib/arm64-v8a/libil2cpp.so` in the APK, and `global-metadata.dat` is in `assets/bin/Data/Managed/Metadata/`.

## Why a native background is the lifesaver

Once you've dumped and assigned names, what's left is purely reading native ARM64 or x64 code. This is exactly where Parts 1 to 4 pay off: you need to read assembly, recognize structs, understand pointers. IL2CPP isn't hard because it's cryptic, it just takes you from the forgiving managed playground back to the native one. If you're solid on native, IL2CPP is just one extra dump step at the start.

## Lab

The goal of this lab is to recover function names from a Unity game built with IL2CPP, then read the logic in Ghidra or IDA. Use your own game, a demo you build yourself, or a free game that allows research, and don't apply this to a commercial online game. You need the latest Il2CppDumper (or Cpp2IL), Ghidra or IDA, and a Unity IL2CPP game. The surest way to get a sample is to create an empty Unity project, add a few `MonoBehaviour` classes with memorable names, and build with Scripting Backend set to IL2CPP.

Open the game folder and confirm it is IL2CPP by looking for `GameAssembly.dll` (Windows) and `global-metadata.dat` (in `<Game>_Data/il2cpp_data/Metadata/`). For an APK, look for `lib/arm64-v8a/libil2cpp.so` and `assets/bin/Data/Managed/Metadata/global-metadata.dat`. Try opening `GameAssembly.dll` in dnSpy and confirm it is NOT readable because it is not a .NET assembly, noting the error message. Then run Il2CppDumper on those two files and look at what it generates: `dump.cs`, `script.json`, `il2cpp.h` and the scripts for IDA and Ghidra.

Open `dump.cs`, find a class you named yourself (for example `PlayerController`) and one of its methods (for example `TakeDamage`), and write down that method's RVA. Open `GameAssembly.dll` in Ghidra, wait for auto-analysis to finish, and run the script Il2CppDumper produced to apply the names. Jump to the method by its assigned name and read the pseudocode, comparing it to the C# you originally wrote. If Il2CppDumper reports a metadata version error, retry with Cpp2IL and compare the output.

Two questions to think about. Why does `global-metadata.dat` exist, and can the game run without it? And if a game encrypts `global-metadata.dat`, is there still a way to get the metadata? (Hint: the game has to decrypt it at runtime.)

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This writeup describes the standard workflow with Il2CppDumper and Cpp2IL. The specific names and RVAs below illustrate the shape and are not from a fixed binary. When you do it yourself the real numbers will differ but the form is identical.

A typical IL2CPP game folder on Windows looks like this:

```
MyGame.exe
GameAssembly.dll              <- native code, the main analysis target
MyGame_Data/
  il2cpp_data/
    Metadata/
      global-metadata.dat     <- table of class/method/field names
```

Having the `GameAssembly.dll` plus `global-metadata.dat` pair means it is IL2CPP for sure. If you see `MyGame_Data/Managed/Assembly-CSharp.dll` instead, it is Mono (Lesson 13.1).

Dragging `GameAssembly.dll` into dnSpy gets it refused with a message like "GameAssembly.dll is not a .NET module". That is as expected: the file is a pure native PE with no CLI header and no IL, which is direct evidence that the managed layer has been removed.

Running the dumper:

```
Il2CppDumper.exe GameAssembly.dll global-metadata.dat
```

The tool asks for, or detects, the Unity version and the metadata version, then creates an output folder containing `dump.cs` (the whole API as pseudo-C#), `script.json` (address data), `il2cpp.h` (structs for importing types), and `ida.py` or `ghidra.py` (`Il2CppDumper-ghidra.py`), the scripts that apply names.

In `dump.cs`, a method appears like this:

```
// RVA: 0x4A2C0 Offset: 0x4A2C0 VA: 0x1800...
public void TakeDamage(int amount) { }
```

The RVA is the function's address in the binary, so note it to get to the right spot. `dump.cs` also shows the game's structure at once: which classes inherit `MonoBehaviour`, which fields hold health or score, and which method names hint at important logic.

In Ghidra, go to Window > Script Manager and run the script Il2CppDumper generated (after importing `il2cpp.h` through the Data Type Manager as the tool's instructions say). The script walks `script.json` and renames each function from `FUN_18004a2c0` to a form like `PlayerController$$TakeDamage`. Jump to that function and read the pseudocode. It is still native code (possibly ragged with pointers and casts), but now it has names, so you immediately understand how it subtracts health, what it compares, and which function it calls next.

If Il2CppDumper says "Metadata version not supported" (common with Unity 2022+ and 2023+), run Cpp2IL:

```
Cpp2IL --game-path <game folder>
```

Cpp2IL rebuilds something close to IL and exports it in a form dnSpy can open (via its action plugins), giving output closer to C#. In exchange it is slower and sometimes function bodies are incomplete.

On the questions: `global-metadata.dat` exists because the IL2CPP runtime needs names for reflection, serialization and type mapping at runtime, and without it the game cannot start. Precisely because it is mandatory, it is a weakness we can exploit. If the metadata is encrypted on disk, the game still has to decrypt it in RAM at runtime. The way to get it is to let the game run and dump the memory region that holds the decrypted metadata (with a debugger or Frida), which is the same unpacking mindset as Part 14. There are Il2CppDumper forks that support reading from a memory dump.

The takeaway is that IL2CPP is not mysterious. It moves you from the managed side to the native side and adds one metadata dump step at the start. Once dumped, everything comes down to reading native code, exactly what Parts 1 through 4 trained you for.

</details>

## Key takeaways
No `Assembly-CSharp.dll` but a `GameAssembly.dll` plus `global-metadata.dat` means IL2CPP. IL2CPP translates C# to C++ then to native, so dnSpy is useless and you have to use IDA/Ghidra. `global-metadata.dat` holds the class/method/field names and is the key to getting the names back. Il2CppDumper joins the binary and the metadata, producing `dump.cs` and a script that assigns names in IDA/Ghidra, while Cpp2IL is stronger on newer Unity and can rebuild near-IL. Obfuscated metadata or the wrong version are the two biggest pitfalls.
