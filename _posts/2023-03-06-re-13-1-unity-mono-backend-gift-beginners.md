---
title: "Lesson 13.1: Unity with the Mono backend, a gift for beginners"
image:
  path: /assets/img/covers/re-13-1-unity-mono-backend-gift-beginners.webp
  alt: "Lesson 13.1: Unity with the Mono backend, a gift for beginners"
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

This is exactly the Part 5 workflow, applied to a game. Drag `Assembly-CSharp.dll` into dnSpy. You see the namespace and class tree just like a normal .NET project.

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

This lab stays strictly on an offline, single-player Unity game, either one of your own or a small sample you build yourself, never an online game. You need a Unity game built with the Mono backend, meaning its data folder has `<Game>_Data/Managed/Assembly-CSharp.dll`. The surest way to get one is to make it yourself: install Unity, build a small scene with a `gold` and a `health` variable, and build a Windows version with the Mono backend selected in Player Settings, not IL2CPP. You also need dnSpy and AssetStudio or AssetRipper.

Start by confirming the backend. Open the `<Game>_Data` folder and check whether it has `Managed/Assembly-CSharp.dll` (Mono) or a `GameAssembly.dll` (IL2CPP) instead, and only continue if it's Mono. Back up `Assembly-CSharp.dll` to a separate location before changing anything. Open it in dnSpy and use Search (Ctrl+Shift+K) to find a field such as `gold`, `coin`, `score`, `health` or `hp`. Right-click that field, choose Analyze, and look at "Used By" to find the methods that read or write it. Read the logic of one of those methods, for example a purchase function with something like `if (gold >= price)`, and understand what it does. Then use Edit Method (C#) to change it so the condition always holds, or pin a value inside `Update()`, and save the module, overwriting the file. Run the game again and confirm the change took effect. Finally, open the `.assets` file inside `_Data` with AssetStudio and export a texture or a text asset.

A few questions worth thinking through. Why don't variable names in a Mono build usually get mangled into a/b/c the way R8 does to Android apps? If Save Module reports a strong name error, how do you deal with it (see Lesson 5.4)? And how is pinning health every frame different from blocking the function that applies damage in the first place, and which is the cleaner approach?


<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The steps below describe the standard real-world procedure, and each one is an ordinary dnSpy or AssetStudio operation. Names and layout will differ from build to build.

Confirming the backend. Inside `<Game>_Data/`, seeing `Managed/Assembly-CSharp.dll` means Mono, so you continue. Seeing `GameAssembly.dll` next to the exe along with an `il2cpp_data/` folder means IL2CPP, so you stop and use the IL2CPP lesson instead (13.2). Dragging `Assembly-CSharp.dll` into Detect It Easy confirms it again by identifying it as a ".NET assembly".

Backing up and opening it. Copy `Assembly-CSharp.dll` to `Assembly-CSharp.dll.bak`, then open the original in dnSpy and search for `gold` with Ctrl+Shift+K. A typical result looks like this:

```csharp
public class PlayerStats : MonoBehaviour {
    public int gold;
    public float health;
    public float maxHealth;
}
```

The names aren't obfuscated because a Mono build doesn't enable renaming by default, which is exactly why Unity Mono is so approachable.

Analyzing usage. Right-click `gold`, choose Analyze, then Used By, and you'll see methods such as `Shop.TryBuy(int)` and `Pickup.OnTriggerEnter(Collider)`, which are where gold gets spent and earned.

Reading and editing. A purchase function usually looks like:

```csharp
public bool TryBuy(int price) {
    if (stats.gold >= price) {
        stats.gold -= price;
        return true;
    }
    return false;
}
```

One approach is to make purchases always succeed without spending gold, using Edit Method (C#):

```csharp
public bool TryBuy(int price) {
    return true;
}
```

Another is a god mode that pins health inside `PlayerStats.Update()`:

```csharp
void Update() {
    health = maxHealth;
}
```

Save the module, overwriting `Assembly-CSharp.dll`.

Checking the result. Running the game again, the first approach lets you buy things without losing gold, and the second keeps health from dropping.

Extracting assets. Open AssetStudio, use File, Load folder, and point it at `<Game>_Data`. The Asset List tab lists Texture2D, TextAsset, AudioClip and more. Pick a texture and use Export selected assets to get a PNG. A TextAsset sometimes reveals configuration data or an interesting hidden string.

On why names survive: a Mono build compiles `Assembly-CSharp.dll` directly with no obfuscator in the pipeline. Renaming requires integrating a separate tool, and most indie games don't bother, unlike Android where R8 is on by default once minification is enabled.

On the strong name error: dnSpy usually handles it automatically on Save Module, and if it doesn't, remove the strong name or re-sign it, as covered in Lesson 5.4. Most Mono games aren't strong-name signed, so this rarely comes up in practice.

On pinning health versus blocking damage: pinning health every frame still lets damage happen and then yanks health back up afterward, which can flicker or even let you die if a single frame's damage is large enough. Blocking the function that applies damage (turning `TakeDamage` into a no-op) is cleaner, since health never changes at all. The function that receives damage is the better target.

</details>

## Key takeaways
Unity has two backends: Mono (`Managed/Assembly-CSharp.dll`, easy) and IL2CPP (`GameAssembly.dll`, hard). Mono is .NET, so you open it in dnSpy to read nearly the source, then edit and Save Module. Gameplay logic lives in classes inheriting `MonoBehaviour`, so look at `Start()`/`Update()`, and go from variable names (gold, health) through Search and Analyze to reach the logic.

AssetStudio extracts textures/models/audio/text. Always back up the original file, and only do this on your own offline games.
