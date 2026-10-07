---
title: "Lesson 13.1: Unity with the Mono backend, a gift for beginners"
date: 2023-03-06 22:31:00 +0700
categories: ["Technique Reverse", "Part 13 · Games: Unity, Unreal, Lua"]
tags: [reverse-engineering, game-hacking]
render_with_liquid: false
---
Of all the kinds of games to practice reversing on, Unity with the Mono backend is the easiest, so easy it feels almost like cheating. The reason: all the gameplay code sits in a single .NET file called `Assembly-CSharp.dll`, and as you already know from Part 5, .NET decompiles to nearly the original source. Open it in dnSpy and you can read class names, variable names, logic, then edit directly and save. You never need to touch a single line of assembly.

This lesson assumes you're working on an offline, single-player game of your own. Modifying online games is a completely different matter, both technically and legally, and isn't covered here.

## Recognizing a Unity game

The signs are right in the install folder. Next to the game's exe there's always a folder named `<GameName>_Data`. Open it and you can tell the backend right away. If there's a `<GameName>_Data/Managed/` folder full of `.dll` files, including `Assembly-CSharp.dll`, this is the Mono backend. That's the case in this lesson, and the easiest case. If there's a `GameAssembly.dll` (a huge one) next to the exe and a `global-metadata.dat` in `il2cpp_data/Metadata/`, this is the IL2CPP backend. The code has been compiled to native, which is much harder, so it's saved for lesson [13.2](/posts/re-13-2-unity-il2cpp-when-assembly-csharp-disappears/).

Just glance at whether `Managed/Assembly-CSharp.dll` or `GameAssembly.dll` is there and you know which kind you're dealing with. Dragging `Assembly-CSharp.dll` into Detect It Easy also confirms it's a .NET assembly.

## Opening Assembly-CSharp.dll in dnSpy

This is exactly the Part 5 workflow, applied to a game. Drag `Assembly-CSharp.dll` into dnSpy (it's included in this repo at `dnSpy-net-win64`). You see the namespace and class tree just like a normal .NET project.

What's different in Unity: most gameplay classes inherit `MonoBehaviour`, and the logic lives in the familiar Unity methods. `Start()` runs once when the object is created, `Update()` runs every frame, and there are other callbacks like `Awake()`, `OnEnable()` and `OnTriggerEnter()`.

Knowing this helps you narrow things down fast. Want the logic that adds score every frame? Look in `Update()`. Want the initial health setup? Look in `Start()` or `Awake()`.

## Hunting for the value to change

Say you want to find where gold is managed. The most effective way is still to start from what's easiest to grasp. Search by name first: dnSpy has Search (Ctrl+Shift+K), so type `gold`, `coin`, `money`, `health`, `hp`. Game developers rarely obfuscate variable names in the Mono build, so you'll often see `public int gold;` or `private float health;` right away. Then use Analyze: right-click the `gold` field, choose Analyze, and look at "Used By" to see which methods read/write it. The function that subtracts gold when buying and the function that adds gold when picking it up all show up. Finally, read the logic. Go into the method with a check like `if (gold >= price)`, because that's where you step in.

## Modifying and saving

dnSpy lets you edit directly in C# (Edit Method), exactly as in [Lesson 5.4](/posts/re-5-4-editing-net-assembly-saving-where-dnspy/). A few classic edits:

```csharp
// Original: subtract gold when buying
public bool TryBuy(int price) {
    if (gold >= price) { gold -= price; return true; }
    return false;
}

// Modified: always able to buy, no gold deducted
public bool TryBuy(int price) {
    return true;
}
```

Or for health, edit `Update()` to pin health to max every frame (a crude god mode):

```csharp
void Update() {
    health = maxHealth;   // add this line
    // ... the rest
}
```

After editing, right-click the module and Save Module, overwriting `Assembly-CSharp.dll`. Run the game again and you'll see the effect. Back up the original file before overwriting, always.

If the game uses strong name signing or has integrity checks you'll need extra handling, but most Mono indie games don't do that.

## Extracting assets with AssetStudio

Besides code, you might want to view or extract resources: textures, models, audio, text. They're in the `.assets` files and asset bundles in the `_Data` folder. **AssetStudio** (or AssetRipper) opens these files, lists them, and exports the resources into common formats. Useful when you want to understand the game's data, find hidden text strings, or just out of curiosity.

## Why Mono is so much easier than IL2CPP

It all comes down to Mono keeping the IL and metadata intact in `Assembly-CSharp.dll`, like any .NET assembly. When the developer picks IL2CPP, the C# code is translated to C++ and compiled natively into `GameAssembly.dll`, most names are gone, and you lose the gift of decompiling to source. That's why the next lesson needs a completely different set of tools.

## Lab

See [labs/13.1/](https://github.com/Haind03/Technique-Reverse/blob/main/labs/13.1). The task: with an offline Unity Mono game of your own, open `Assembly-CSharp.dll` in dnSpy, find a value like score or health, edit it with dnSpy, save and test it, then extract an asset with AssetStudio.

## Key takeaways
Unity has two backends: Mono (`Managed/Assembly-CSharp.dll`, easy) and IL2CPP (`GameAssembly.dll`, hard). Mono is .NET, so you open it in dnSpy to read nearly the source, then edit and Save Module. Gameplay logic lives in classes inheriting `MonoBehaviour`, so look at `Start()`/`Update()`, and go from variable names (gold, health) through Search and Analyze to reach the logic.

AssetStudio extracts textures/models/audio/text. Always back up the original file, and only do this on your own offline games.
