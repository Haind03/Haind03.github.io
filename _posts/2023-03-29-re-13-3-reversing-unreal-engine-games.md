---
title: "Lesson 13.3: Reversing Unreal Engine games"
date: 2023-03-29 22:36:00 +0700
categories: ["Technique Reverse", "Part 13 · Games: Unity, Unreal, Lua"]
tags: [reverse-engineering, game-hacking]
render_with_liquid: false
---
Unity gives you DLLs that read almost like source. Unreal isn't that generous. Unreal Engine is written in C++ and compiled straight to native, so all the logic sits in one huge exe that you have to open in IDA/Ghidra like a normal C++ program (going back to Part 4 helps). In return, UE has its own reflection system and a very strong community tool ecosystem, so there are still plenty of ways in. This lesson draws that map.

Scope: this is for your own offline/single-player games, for learning and research. Touching online multiplayer games is a matter of anti-cheat and terms of service, and is outside the scope of this series.

## Recognizing an Unreal game

Before doing anything, confirm it's really Unreal. The signs are almost unmistakable. The executable is usually named like `GameName-Win64-Shipping.exe`, inside `GameName/Binaries/Win64/`. There's a `Content/Paks/` folder with `.pak` files (sometimes `.utoc` and `.ucas` with the newer IoStore format). Loose assets, if not packed into a pak, have the extensions `.uasset` and `.umap`. And the exe's strings are full of things like `/Game/`, `/Engine/`, class names starting with `U`, `A`, `F` (UObject, AActor, FVector), and the engine version string.

Knowing the UE version (UE4.x or UE5.x) matters a lot because community tools are tightly tied to versions. The strings in the exe or a `.version` file usually say it clearly.

## The three worlds of an Unreal game

When reversing Unreal you work on three different fronts, and you pick the front based on what you need. The first is assets in .pak files: models, textures, audio, and what matters to a reverser, Blueprints and DataTables, using FModel/UModel. The second is native C++ code in the exe: core logic, engine functions, anti-analysis, using IDA/Ghidra helped by an SDK dump. The third is runtime, where you inject into the running game to call functions, read objects, and script, using UE4SS.

### .pak files and AES encryption

A `.pak` is an archive that packs all the assets. Many games leave it unencrypted, and then FModel/UModel opens it directly. But quite a few games encrypt the index (and sometimes the contents too) with AES-256. Then you need the AES key to browse it.

That key is somewhere in the exe, loaded at runtime. There are two common ways to get it. You can use a tool that scans the exe for the key (AES key finders for UE, which look for a 32-byte pattern in regions that often hold keys). Or you can dump the key from memory while the game runs, or set a breakpoint at the pak decryption function. Once you have the key, load it into FModel and you can browse the asset tree like folders.

### FModel and UModel

FModel is a modern asset browser. It supports the IoStore format (.utoc/.ucas) of newer UE, previews, exports textures/models/audio, and can read DataTables (the game's data tables, where item stats, recipes, and so on often live). This is the best place to start. UModel (UE Viewer) is the long-established one, strong at extracting models and textures to view or convert.

For a reverser, DataTables and Blueprints in the pak often answer a lot of questions without opening the exe.

### Blueprint

Blueprint is Unreal's visual scripting, compiled into a form of bytecode that runs on the engine's VM (Kismet bytecode). It's not native code, it lives in the Blueprint asset. Reading Blueprint bytecode is unpleasant and the tools are limited, but a lot of gameplay logic sits here instead of in C++. FModel can show the Blueprint structure to some extent; reading the bytecode in depth takes specialized tools and patience.

## SDK dump: the key to reading the exe

Open an Unreal exe in IDA with no preparation and you drown: hundreds of thousands of functions, no names. The lifeline is Unreal's reflection system. The engine stores info about every UClass, UProperty, UFunction in memory at runtime (to serialize, to let Blueprints call C++, to make the editor work). An SDK dumper walks those structures and generates C++ headers describing all the classes, field offsets, and function addresses of this specific game.

With the SDK, you know the structs of the important objects (what offset the player position is at in AActor, where health is). You also get the names and addresses of UFunctions, which you map back into IDA to name functions.

Dumpers work by starting from GObjects (the global array of every UObject) and GNames (the name table), two globals whose offsets you have to find correctly for the game version. The community has many dumpers, and the most popular one these days is built into UE4SS.

## UE4SS: the runtime multi-tool

UE4SS (Unreal Engine Scripting System) is a DLL injected into the game. It gives you an automatic SDK dump (C++ headers and also forms for other tools) and a live property viewer, where you browse the living UObject tree and view and edit properties directly. It also gives you Lua scripting, so you can write scripts that call UFunctions, hook functions, and change behavior without patching the exe, which is very powerful for quick experiments. On top of that there's a console and many modding utilities.

A typical workflow: inject UE4SS, dump the SDK, open the live viewer to find the objects and properties you care about, then either write a Lua script to intervene, or take the offsets/function addresses over to IDA for deeper static analysis.

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

The key point to remember: Unreal is harder than Unity because there's no "open the DLL and read the source" step. But the engine's own reflection system is the weak point you exploit: it has to describe every class and function in memory for the engine to run, and the SDK dumper just reads that description back.

## Lab

See [labs/13.3/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/13.3). The task: with an offline Unreal game of yours, browse the `.pak` with FModel (get the AES key if it's encrypted), then inject UE4SS to dump the SDK and find a class in the live viewer.

## Key takeaways
Unreal is native C++, so the logic is in the big exe and you open it in IDA/Ghidra like a C++ program (Part 4). You identify it by `-Shipping.exe`, `Content/Paks/*.pak`, `/Game/` strings, and U/A/F classes. Assets in .pak are browsed with FModel/UModel, and you need the AES key if the index is encrypted.

The engine's reflection is the way in: an SDK dumper reads GObjects/GNames and generates C++ headers with offsets and function addresses. UE4SS injects at runtime and gives you the SDK dump, a live property viewer, and Lua scripting. Blueprint is its own bytecode inside an asset, not native code.
