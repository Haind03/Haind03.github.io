---
title: "Lesson 13.2: Unity IL2CPP"
image:
  path: /assets/img/covers/re-13-2-unity-il2cpp-when-assembly-csharp-disappears.webp
  alt: "Lesson 13.2: Unity IL2CPP"
date: 2023-03-26 15:39:00 +0700
categories: ["Technique Reverse", "Part 13 · Games: Unity, Unreal, Lua"]
tags: [reverse-engineering, game-hacking]
render_with_liquid: false
---
In the last lesson you opened a Unity game built with Mono, found `Assembly-CSharp.dll`, dragged it into dnSpy and could read almost the source. Then you open a different game and search the whole folder, and `Assembly-CSharp.dll` isn't there. Instead there's a huge `GameAssembly.dll` and a strange file called `global-metadata.dat`. That's IL2CPP, and it changes things a lot.

## What IL2CPP does to your C# code

Mono keeps C# as IL inside a .NET DLL, so it decompiles well. IL2CPP (Intermediate Language To C++) works differently. At build time Unity translates your IL to C++, then compiles that C++ into native machine code in `GameAssembly.dll` (Windows), `libil2cpp.so` (Android), or inside the binary (iOS).

So there's no IL and no .NET metadata anymore, and dnSpy and ILSpy are useless. The code is native, you open it in IDA or Ghidra and read it like C++. It's the same change as .NET's NativeAOT (Lesson 5.6) or Python's Nuitka (Lesson 7.5): the managed layer is gone and you're down to native.

That sounds bad, but there's good news.

## global-metadata.dat

IL2CPP needs class names, method names and field names at runtime (for reflection, serialization, calling by name and so on). It keeps all those names in a separate file, `global-metadata.dat`, usually in `GameName_Data/il2cpp_data/Metadata/`.

The machine code lost its names, but the table of names is still in a file next to it. We just have to join the two: take the names from `global-metadata.dat` and assign them to the right functions in `GameAssembly.dll`. There are tools that do this automatically.

## Il2CppDumper

Il2CppDumper takes two inputs, `GameAssembly.dll` and `global-metadata.dat`, and produces a few things. `dump.cs` is a pseudo-C# file listing every class, method and field, along with the address (RVA) of each method in the binary. That's your map. `script.json` and a script (`ida.py` or `ghidra.py`) can be loaded into IDA/Ghidra so it names the functions from the metadata automatically. There are also extra files like `il2cpp.h` with structs, for importing types.

The workflow:

```
1. Find GameAssembly.dll and global-metadata.dat in the game folder.
2. Run Il2CppDumper, pointing at those two files.
3. Open GameAssembly.dll in IDA/Ghidra, wait for the analysis to finish.
4. Run the script Il2CppDumper generated (ida.py / ghidra.py).
5. Now the sub_xxx functions have real names like PlayerController$$TakeDamage.
6. Read dump.cs to know which functions are worth looking at, jump to that RVA and read the logic.
```

After step 5 it's almost like Mono again. You see meaningful function names, you just read native pseudocode (C) instead of clean C#. Still much better than `sub_18004A2C0`.

## Cpp2IL

Cpp2IL goes further than Il2CppDumper. It tries to rebuild IL (and from that, approximate C#) from the machine code, not just assign names. On newer Unity versions where Il2CppDumper sometimes fails (the metadata format changes between versions), Cpp2IL usually copes better and gives output closer to the source. There are even plugins that export a form dnSpy can open.

I try Il2CppDumper first because it's fast and reliable, and if it can't parse the metadata (it reports a version error) I switch to Cpp2IL. The two tools complement each other.

## Common pitfalls

The first is the wrong metadata version. `global-metadata.dat` has a version number that changes with the Unity version, and old tools can't read new ones. Update the tool or try Cpp2IL.

The second is obfuscated metadata. Some games deliberately encrypt or shuffle `global-metadata.dat` (changed header, encrypted strings) to block Il2CppDumper. Then you have to recover the metadata first. There are forks of the tool for this, or you dump it from memory while the game runs, similar to the unpacking approach in Part 14.

The third is looking for the wrong file. On Android, the equivalent of `GameAssembly.dll` is `lib/arm64-v8a/libil2cpp.so` in the APK, and `global-metadata.dat` is in `assets/bin/Data/Managed/Metadata/`.

## Native background helps

After you dump and assign names, what's left is reading native ARM64 or x64 code. This is where Parts 1 to 4 pay off: you need to read assembly, recognize structs and understand pointers. IL2CPP isn't hard because it's cryptic, it just moves you from the managed side back to the native side. If you're solid on native, IL2CPP is one extra dump step at the start.

## Lab

The goal of this lab is to recover function names from a Unity game built with IL2CPP, then read the logic in Ghidra or IDA. Use your own game, a demo you build yourself, or a free game that allows research, and don't apply this to a commercial online game. You need the latest Il2CppDumper (or Cpp2IL), Ghidra or IDA, and a Unity IL2CPP game. The easiest way to get a sample is to create an empty Unity project, add a few `MonoBehaviour` classes with memorable names, and build with Scripting Backend set to IL2CPP.

Open the game folder and confirm it's IL2CPP by looking for `GameAssembly.dll` (Windows) and `global-metadata.dat` (in `<Game>_Data/il2cpp_data/Metadata/`). For an APK, look for `lib/arm64-v8a/libil2cpp.so` and `assets/bin/Data/Managed/Metadata/global-metadata.dat`. Try opening `GameAssembly.dll` in dnSpy and confirm it's not readable because it isn't a .NET assembly, and note the error message. Then run Il2CppDumper on those two files and look at what it generates: `dump.cs`, `script.json`, `il2cpp.h` and the scripts for IDA and Ghidra.

Open `dump.cs`, find a class you named yourself (for example `PlayerController`) and one of its methods (for example `TakeDamage`), and write down that method's RVA. Open `GameAssembly.dll` in Ghidra, wait for auto-analysis to finish, and run the script Il2CppDumper produced to apply the names. Jump to the method by its assigned name and read the pseudocode, comparing it to the C# you originally wrote. If Il2CppDumper reports a metadata version error, retry with Cpp2IL and compare the output.

Two questions to think about. Why does `global-metadata.dat` exist, and can the game run without it? And if a game encrypts `global-metadata.dat`, is there still a way to get the metadata? (Hint: the game has to decrypt it at runtime.)

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This writeup describes the standard workflow with Il2CppDumper and Cpp2IL. The specific names and RVAs below show the shape and are not from a fixed binary. When you do it yourself the real numbers will differ but the form is the same.

A typical IL2CPP game folder on Windows looks like this:

```
MyGame.exe
GameAssembly.dll              <- native code, the main analysis target
MyGame_Data/
  il2cpp_data/
    Metadata/
      global-metadata.dat     <- table of class/method/field names
```

The pair `GameAssembly.dll` plus `global-metadata.dat` means it's IL2CPP for sure. If you see `MyGame_Data/Managed/Assembly-CSharp.dll` instead, it's Mono (Lesson 13.1).

Dragging `GameAssembly.dll` into dnSpy gets it refused with a message like "GameAssembly.dll is not a .NET module". That's expected: the file is a pure native PE with no CLI header and no IL, which shows the managed layer has been removed.

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

The RVA is the function's address in the binary, so note it to get to the right place. `dump.cs` also shows the game's structure at a glance: which classes inherit `MonoBehaviour`, which fields hold health or score, and which method names hint at important logic.

In Ghidra, go to Window > Script Manager and run the script Il2CppDumper generated (after importing `il2cpp.h` through the Data Type Manager as the tool's instructions say). The script walks `script.json` and renames each function from `FUN_18004a2c0` to a form like `PlayerController$$TakeDamage`. Jump to that function and read the pseudocode. It's still native code (maybe ragged with pointers and casts), but now it has names, so you can see how it subtracts health, what it compares, and which function it calls next.

If Il2CppDumper says "Metadata version not supported" (common with Unity 2022+ and 2023+), run Cpp2IL:

```
Cpp2IL --game-path <game folder>
```

Cpp2IL rebuilds something close to IL and exports it in a form dnSpy can open (via its action plugins), giving output closer to C#. In exchange it's slower and function bodies are sometimes incomplete.

On the questions: `global-metadata.dat` exists because the IL2CPP runtime needs names for reflection, serialization and type mapping at runtime, and without it the game can't start. Because it's mandatory, it's also a weak point. If the metadata is encrypted on disk, the game still has to decrypt it in RAM at runtime. So you let the game run and dump the memory region that holds the decrypted metadata (with a debugger or Frida), the same unpacking approach as Part 14. There are Il2CppDumper forks that support reading from a memory dump.

IL2CPP isn't mysterious. It moves you from the managed side to the native side and adds one metadata dump step at the start. After the dump it's all native code, which is what Parts 1 through 4 trained you for.

</details>

## Key takeaways
No `Assembly-CSharp.dll` but a `GameAssembly.dll` plus `global-metadata.dat` means IL2CPP. IL2CPP translates C# to C++ and then to native, so dnSpy is useless and you use IDA or Ghidra. `global-metadata.dat` holds the class, method and field names and is how you get the names back. Il2CppDumper joins the binary and the metadata, producing `dump.cs` and a script that assigns names in IDA/Ghidra, while Cpp2IL is stronger on newer Unity and can rebuild near-IL. Obfuscated metadata and the wrong version are the two biggest pitfalls.
