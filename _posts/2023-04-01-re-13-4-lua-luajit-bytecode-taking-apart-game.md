---
title: "Lesson 13.4: Lua and LuaJIT bytecode, taking apart in-game scripts"
date: 2023-04-01 22:36:00 +0700
categories: ["Technique Reverse", "Part 13 · Games: Unity, Unreal, Lua"]
tags: [reverse-engineering, game-hacking]
render_with_liquid: false
---
A lot of games don't write gameplay logic in C++ but in Lua, because Lua is light, easy to embed, and can be edited without rebuilding the whole engine. Roblox, Garry's Mod, World of Warcraft (addons), and a forest of mobile games all run Lua scripts. For a reverser this is good news: Lua keeps almost all its information, and decompiling gets you back something close to the source. The bad news: there are two different Lua lines (standard Lua and LuaJIT), the bytecode changes with the version, and games often encrypt scripts to make life hard for you. This lesson untangles each piece.

## Lua runs on bytecode, like Python

When you write a `.lua` file, the interpreter doesn't run the text directly. It compiles to bytecode first and then runs it on the Lua VM (register-based, unlike stack-based CPython). Most of the time games embed the plain `.lua` text so you can read it right away, but when the author wants to hide it, they ship compiled bytecode (made with `luac`, the Lua compiler). Then you need a decompiler.

The key point to remember right away: there are two completely different bytecode families. Standard Lua (lua.org) produces bytecode with `luac`, and you decompile it with `unluac` (Java, the best one right now) or `luadec`. LuaJIT is a separate implementation, faster, and its bytecode is not compatible with standard Lua. You must use a dedicated decompiler: `luajit-decompiler`, `ljd`, or the `luajit-decompiler-v2` version.

Pick the wrong branch and the decompiler errors out from the very first byte. So step one is always identification.

## Identifying: read the magic and version

Open the bytecode file in a hex editor and look at the first few bytes.

Standard Lua starts with the magic `1B 4C 75 61`, i.e. `\x1bLua`. The 5th byte is the version number in hex: `51` = Lua 5.1, `52` = 5.2, `53` = 5.3, `54` = 5.4. This decides which decompiler you use, because the bytecode differs per version.

```
1B 4C 75 61 54 00 19 93 0D 0A 1A 0A ...
\x1b L  u  a  |  version 0x54 = Lua 5.4
```

LuaJIT starts with the magic `1B 4C 4A`, i.e. `\x1bLJ`, then a bytecode version byte (`01`, `02`...). Seeing `LJ` tells you right away to turn to the ljd branch, don't waste time on unluac.

If you see no magic and the file looks like high-entropy junk, the script has probably been encrypted (see the last section).

## Decompiling standard Lua with unluac

A tidy workflow once you know it's standard Lua:

```
# compile (if you're making your own sample to learn)
luac -o script.luac script.lua

# decompile back
java -jar unluac.jar script.luac > script_decompiled.lua
```

unluac gives back code very close to the original: it keeps local variable names (if the bytecode hasn't had its debug info stripped), function names, string constants, and the if/for/while structure. If the bytecode is stripped (`luac -s`), local variable names are lost and you get `A0_1`, `L1_2`... but the logic is still complete and still readable.

`luadec` is the older alternative, good with Lua 5.1 but struggles with newer versions. If you hit Lua 5.1 and unluac misbehaves, try luadec.

## Decompiling LuaJIT with ljd

LuaJIT is more stubborn. `ljd` (and its rewrite `luajit-decompiler-v2`) is the main tool:

```
python3 ljd/main.py -f script_ljbc.luac
```

Output quality is usually worse than unluac on standard Lua: some complex control structures may come out unclean, and you have to read alongside the bytecode disassembly to understand them. But for ordinary gameplay scripts it's good enough.

## Structures to know when reading

A few Lua-specific things you'll see in decompiled code. The table is Lua's central data type, serving as array, dictionary, and object (through metatables), so seeing `t[1]`, `t.field`, `t:method()` all means tables. Strings in Lua are interned and stored in the constant pool of each function prototype, so API function names, keys, and messages leak out quite a lot. Going from a string to where it's used is the familiar tactic, same as every earlier part. And `t:method(a)` is just syntactic sugar for `t.method(t, a)`, so self is a hidden first parameter, like `this`.

## Finding Lua scripts in a game

Before decompiling, you have to get the bytecode out first. In the game folder, look for `.lua`, `.luac`, `.lc` files, or a dedicated archive (`.pak`, `.rbxl`, asset bundle). Use `strings` and look for the magic `\x1bLua` / `\x1bLJ` to locate the bytecode block even when it's embedded in a large file. It may also be embedded in a native binary, so grep for the magic in the exe/so itself. Otherwise, unpack the game's archive with the matching tool and then scan.

## When the script is encrypted

Many games don't leave the bytecode bare but encrypt it (XOR, a custom cipher) and decrypt in memory right before loading into the Lua VM. Then decompiling the file on disk is useless.

One approach is to dump from runtime. Let the game decrypt it itself, then pull the decrypted bytecode out of memory. Hook the script loading function (for example `luaL_loadbuffer`, `lua_load`, `luaL_loadbufferx`) with Frida and print the buffer at the moment it's clean bytecode. This is exactly the dynamic unpacking spirit from Part 14. The other case is when the key sits in the binary. If the cipher is simple, find the decryption function in the native code, get the key, and decrypt offline.

The general principle is the same as for every kind of packer: find where the data is in its cleanest form and grab it there, instead of wrestling with the encryption layer.

## Lab

See `labs/13.4/`. The task: compile a Lua script with `luac`, identify the magic and version in hex, then decompile it back with `unluac` and compare with the original. The solution is at `solution.md`.

## Key takeaways
Embedded Lua is usually plain text you can read directly, and only the bytecode form needs a decompiler. There are two different families: standard Lua (magic `\x1bLua`, use unluac/luadec) and LuaJIT (magic `\x1bLJ`, use ljd), so identify first. The version byte after the magic (`51`/`52`/`53`/`54`) decides the decompiler.

Stripped bytecode only loses local variable names, the logic is still there. For encrypted scripts, dump from runtime by hooking `luaL_loadbuffer`/`lua_load` with Frida to get the clean bytecode. Tables are central to Lua, and in `t:method()` self is the hidden first parameter.
