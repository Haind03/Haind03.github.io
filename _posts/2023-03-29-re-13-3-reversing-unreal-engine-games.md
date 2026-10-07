---
title: "Lesson 13.3: Reversing Unreal Engine games"
image:
  path: /assets/img/covers/re-13-3-reversing-unreal-engine-games.webp
  alt: "Lesson 13.3: Reversing Unreal Engine games"
date: 2023-03-29 22:36:00 +0700
categories: ["Technique Reverse", "Part 13 · Games: Unity, Unreal, Lua"]
tags: [reverse-engineering, game-hacking]
render_with_liquid: false
---
Unity gives you DLLs that read almost like source. Unreal doesn't. Unreal Engine is written in C++ and compiled straight to native, so all the logic sits in one huge exe that you open in IDA/Ghidra like a normal C++ program (going back to Part 4 helps). On the other hand, UE has its own reflection system and a strong community tool ecosystem, so there are still plenty of ways in. This lesson is an overview.

This is for your own offline/single-player games, for learning and research. Touching online multiplayer games involves anti-cheat and terms of service, and is outside the scope of this series.

## Recognizing an Unreal game

Before anything else, confirm it's really Unreal. The signs are easy to spot. The executable is usually named like `GameName-Win64-Shipping.exe`, inside `GameName/Binaries/Win64/`. There's a `Content/Paks/` folder with `.pak` files (sometimes `.utoc` and `.ucas` with the newer IoStore format). Loose assets, if not packed into a pak, have the extensions `.uasset` and `.umap`. And the exe's strings are full of things like `/Game/`, `/Engine/`, class names starting with `U`, `A`, `F` (UObject, AActor, FVector), and the engine version string.

Knowing the UE version (UE4.x or UE5.x) matters a lot because community tools are tied to versions. The strings in the exe or a `.version` file usually tell you.

## Three fronts

When reversing Unreal you work on three different fronts, and pick one based on what you need. The first is assets in .pak files, such as models, textures, audio, and what matters most to a reverser, Blueprints and DataTables, using FModel/UModel. The second is native C++ code in the exe, such as core logic, engine functions, anti-analysis, using IDA/Ghidra helped by an SDK dump. The third is runtime, where you inject into the running game to call functions, read objects, and script, using UE4SS.

### .pak files and AES encryption

A `.pak` is an archive that packs all the assets. Many games leave it unencrypted, and then FModel/UModel opens it directly. But quite a few games encrypt the index (and sometimes the contents too) with AES-256. Then you need the AES key to browse it.

That key is somewhere in the exe, loaded at runtime. There are two common ways to get it. You can use a tool that scans the exe for the key (AES key finders for UE, which look for a 32-byte pattern in regions that often hold keys). Or you can dump the key from memory while the game runs, or set a breakpoint at the pak decryption function. Once you have the key, load it into FModel and you can browse the asset tree like folders.

### FModel and UModel

FModel is a modern asset browser. It supports the IoStore format (.utoc/.ucas) of newer UE, previews, exports textures/models/audio, and can read DataTables (the game's data tables, where item stats, recipes, and so on often live). It's the best place to start. UModel (UE Viewer) has been around longer and is good at extracting models and textures to view or convert.

DataTables and Blueprints in the pak often answer a lot of questions without opening the exe.

### Blueprint

Blueprint is Unreal's visual scripting, compiled into bytecode that runs on the engine's VM (Kismet bytecode). It's not native code, it lives in the Blueprint asset. Reading Blueprint bytecode is unpleasant and the tools are limited, but a lot of gameplay logic sits here instead of in C++. FModel can show the Blueprint structure to some extent. Reading the bytecode in depth takes specialized tools and patience.

## SDK dump

Open an Unreal exe in IDA with no preparation and you drown in hundreds of thousands of functions with no names. What saves you is Unreal's reflection system. The engine stores info about every UClass, UProperty, UFunction in memory at runtime (to serialize, to let Blueprints call C++, to make the editor work). An SDK dumper walks those structures and generates C++ headers describing all the classes, field offsets, and function addresses of this specific game.

With the SDK, you know the structs of the important objects (what offset the player position is at in AActor, where health is). You also get the names and addresses of UFunctions, which you map back into IDA to name functions.

Dumpers start from GObjects (the global array of every UObject) and GNames (the name table), two globals whose offsets you have to find correctly for the game version. The community has many dumpers, and the most popular one now is built into UE4SS.

## UE4SS

UE4SS (Unreal Engine Scripting System) is a DLL injected into the game. It gives you an automatic SDK dump (C++ headers and also formats for other tools) and a live property viewer, where you browse the living UObject tree and view and edit properties directly. It also has Lua scripting, so you can write scripts that call UFunctions, hook functions, and change behavior without patching the exe, which is good for quick experiments. There's also a console and many modding utilities.

A typical workflow is to inject UE4SS, dump the SDK, open the live viewer to find the objects and properties you care about, then either write a Lua script to intervene, or take the offsets/function addresses over to IDA for deeper static analysis.

## The workflow side by side

```
   Identify UE (exe name, Content/Paks, version)
            |
   +--------+-----------------------------+
   |                                      |
  Assets?                               Logic?
   |                                      |
  FModel/UModel                   UE4SS inject
  (get the AES key if needed)     dump SDK
   |                                      |
  DataTable, Blueprint,          live viewer +
  texture, model                 Lua script, or
                                 take offsets over to IDA/Ghidra
                                 and read native C++ (Part 4)
```

Unreal is harder than Unity because there's no "open the DLL and read the source" step. But the engine's own reflection system is the weak point, since it has to describe every class and function in memory for the engine to run, and the SDK dumper just reads that description back.

## Lab

The goal is to get familiar with the three fronts of Unreal reversing (assets, SDK, runtime) on an offline game of your own. Pick a single-player or offline game made with Unreal Engine that you own. Don't use an online multiplayer game, since anti-cheat and terms of service are outside what we're learning here. The tools are FModel (browsing paks), UE4SS (runtime injection and SDK dumping), and optionally IDA or Ghidra for the native part.

First confirm it's Unreal and find the version. Look for an executable named like `*-Win64-Shipping.exe` in `Binaries/Win64/` and the `Content/Paks/` folder. Write down the engine version (UE4.x or UE5.x), because the tools are tied closely to the version. Then browse the `.pak` with FModel. Point FModel at the `Content/Paks/` folder. If the index is encrypted, FModel says it needs an AES key, and when it isn't encrypted you can browse the asset tree. Find a DataTable and look at its contents (they often hold item stats, recipes and prices), and try exporting a texture or a model.

If the `.pak` is encrypted, get the AES key. Use an AES key finder for Unreal to scan the exe, or dump it from memory at run time. Load the key into FModel and browse again. Next dump the SDK with UE4SS. Install UE4SS for the game, run the game, and use the dump feature to generate C++ SDK headers. Open the dump, find a familiar class (for example the player character class) and note a few of its fields and offsets. Then open the UE4SS live viewer, browse the tree of live UObjects, find the player object and try viewing (and, if you like, editing) a property such as health or position.

As an advanced step, go native. Take the address of a UFunction from the SDK dump, open the exe in IDA or Ghidra at that address and read the C++ logic (applying Part 4).

Three questions to think about. Why is Unreal reversing so different from Unity Mono, even though both are game engines? The engine's reflection is both a feature for developers and a weakness for reversers, so explain this paradox. And how does logic in Blueprint differ from logic in C++ in how hard it is to analyze?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This writeup describes the standard procedure on a real Unreal game. Since no specific game is attached to the lab, the offsets and class names will differ with each game and engine version, so what follows gives the method and the shape of the results, not figures from a particular title.

The sure signs of Unreal are `GameName/Binaries/Win64/GameName-Win64-Shipping.exe`, `GameName/Content/Paks/*.pak` (UE4) or additionally `*.utoc` and `*.ucas` (UE5 IoStore), and `strings exe | grep -iE "/Game/|/Engine/|UnrealEngine|\+UE"` returning plenty of results. For the version, look at the strings in the exe or the `*.version` file in the game folder. Record it exactly (UE4.27, UE5.1 and so on), because FModel and UE4SS need the right one selected.

In FModel, open Settings and point Game Directory at `Content/Paks/`, choose the right UE version and load. If nothing is encrypted, the asset tree appears by `/Game/...` path. DataTables usually live under `/Game/Data/...`, and opening one gives a JSON-like table with one row per item or unit and columns of stats. You can grab game data quickly here without touching the exe. To export a texture, right-click the asset and choose Export.

When the `.pak` is AES encrypted, FModel says "encrypted" and needs an AES key of the form `0x` plus 64 hex digits (32 bytes). You can get it by using an AES key finder for Unreal, which scans the exe for data matching the key pattern, or by attaching a debugger, setting a breakpoint at the pak decryption function (the one that receives the index buffer) and reading the key from the parameters or memory. Paste the key into the AES section of FModel and reload, and now you can browse.

To dump the SDK, install UE4SS into the game folder following the instructions for your version. Run the game and UE4SS loads. Use the dump command or hotkey to generate the SDK, which is a set of C++ headers describing classes, enums and structs with field offsets and function RVAs. Open the headers and find the player character class (usually inheriting from `ACharacter` or `APawn`). The result looks like:

```cpp
class ABP_PlayerCharacter_C : public ACharacter {
    float Health;        // offset 0x0abc
    int32 Gold;          // offset 0x0ad0
    ...
    void TakeDamage(float Amount);  // RVA 0x1234560
};
```

Write down the offsets of `Health` and `Gold` and the RVA of a function you care about. In the live property viewer of UE4SS, browse the UObject tree and find the player instance (filter by the class name from the previous step). Select it and the property table shows the running values. Editing `Health` here shows the effect in the game at once, which is the fastest way to confirm you found the right field.

For the native step, take the RVA of a UFunction from the SDK dump, open the exe in IDA or Ghidra and jump to the address (ImageBase + RVA). Read the pseudocode as an ordinary C++ function, where `this` is in rcx (Win64), and the fields accessed through `[this+offset]` match the offsets in the SDK. From here you use the Part 4 skills (C++, vtables).

On the questions, Unity Mono keeps its code in Assembly-CSharp.dll as .NET and dnSpy reads it almost like source, while Unreal compiles C++ to native with no managed DLL, so you have to read assembly. Unity's IL2CPP is similar to Unreal in this respect. The reflection paradox is that the engine needs to describe every class and function in memory to serialize, to let Blueprint call C++ and to make the editor work, and that same description lets an SDK dumper rebuild the entire structure. A feature for developers becomes an entry point for the reverser. As for Blueprint versus C++, Blueprint is a bytecode VM stored in assets, which you can pull from the pak but the tools that read the bytecode are still limited, while C++ is native code in the exe, harder to read but with an SDK dump and decompilers to help. Many games mix both, so you have to know which layer the logic you're looking for lives in.

</details>

## Key takeaways
Unreal is native C++, so the logic is in the big exe and you open it in IDA/Ghidra like a C++ program (Part 4). You identify it by `-Shipping.exe`, `Content/Paks/*.pak`, `/Game/` strings, and U/A/F classes. Assets in .pak are browsed with FModel/UModel, and you need the AES key if the index is encrypted.

The engine's reflection is the way in. An SDK dumper reads GObjects/GNames and generates C++ headers with offsets and function addresses. UE4SS injects at runtime and gives you the SDK dump, a live property viewer, and Lua scripting. Blueprint is its own bytecode inside an asset, not native code.
