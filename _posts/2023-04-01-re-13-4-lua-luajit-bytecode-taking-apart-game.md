---
title: "Lesson 13.4: Lua and LuaJIT bytecode"
image:
  path: /assets/img/covers/re-13-4-lua-luajit-bytecode-taking-apart-game.webp
  alt: "Lesson 13.4: Lua and LuaJIT bytecode"
date: 2023-04-01 22:36:00 +0700
categories: ["Reverse Engineering", "Part 13 · Games: Unity, Unreal, Lua"]
tags: [reverse-engineering, game-hacking]
render_with_liquid: false
---
A lot of games don't write gameplay logic in C++ but in Lua, because Lua is light, easy to embed, and can be edited without rebuilding the whole engine. Roblox, Garry's Mod, World of Warcraft (addons), and many mobile games all run Lua scripts. For a reverser that's good news. Lua keeps almost all its information, and decompiling gets you something close to the source. The catches are that there are two different Lua lines (standard Lua and LuaJIT), the bytecode changes with the version, and games often encrypt scripts. This lesson goes through each piece.

## Lua runs on bytecode, like Python

When you write a `.lua` file, the interpreter doesn't run the text directly. It compiles to bytecode first and then runs it on the Lua VM (register-based, unlike stack-based CPython). Most of the time games embed the plain `.lua` text so you can read it right away, but when the author wants to hide it, they ship compiled bytecode (made with `luac`, the Lua compiler). Then you need a decompiler.

There are two completely different bytecode families. Standard Lua (lua.org) produces bytecode with `luac`, and you decompile it with `unluac` (Java, the best one right now) or `luadec`. LuaJIT is a separate implementation, faster, and its bytecode is not compatible with standard Lua. You need a dedicated decompiler, such as `luajit-decompiler`, `ljd`, or the `luajit-decompiler-v2` version.

Pick the wrong one and the decompiler errors out from the first byte. So step one is always identification.

## Identifying: read the magic and version

Open the bytecode file in a hex editor and look at the first few bytes.

Standard Lua starts with the magic `1B 4C 75 61`, i.e. `\x1bLua`. The 5th byte is the version number in hex, where `51` = Lua 5.1, `52` = 5.2, `53` = 5.3, `54` = 5.4. This decides which decompiler you use, because the bytecode differs per version.

```
1B 4C 75 61 54 00 19 93 0D 0A 1A 0A ...
\x1b L  u  a  |  version 0x54 = Lua 5.4
```

LuaJIT starts with the magic `1B 4C 4A`, i.e. `\x1bLJ`, then a bytecode version byte (`01`, `02`...). If you see `LJ`, go to the ljd branch and don't waste time on unluac.

If you see no magic and the file looks like high-entropy junk, the script has probably been encrypted (see the last section).

## Decompiling standard Lua with unluac

A workflow once you know it's standard Lua:

```
# compile (if you're making your own sample to learn)
luac -o script.luac script.lua

# decompile back
java -jar unluac.jar script.luac > script_decompiled.lua
```

unluac gives back code very close to the original. It keeps local variable names (if the bytecode hasn't had its debug info stripped), function names, string constants, and the if/for/while structure. If the bytecode is stripped (`luac -s`), local variable names are lost and you get `A0_1`, `L1_2`..., but the logic is still complete and readable.

`luadec` is the older alternative, good with Lua 5.1 but it struggles with newer versions. If you hit Lua 5.1 and unluac misbehaves, try luadec.

## Decompiling LuaJIT with ljd

LuaJIT is more stubborn. `ljd` (and its rewrite `luajit-decompiler-v2`) is the main tool:

```
python3 ljd/main.py -f script_ljbc.luac
```

Output quality is usually worse than unluac on standard Lua. Some complex control structures may come out unclean, and you have to read alongside the bytecode disassembly to understand them. For ordinary gameplay scripts it's good enough.

## Things to know when reading

A few Lua-specific things you'll see in decompiled code. The table is Lua's central data type, serving as array, dictionary, and object (through metatables), so `t[1]`, `t.field`, `t:method()` all mean tables. Strings in Lua are interned and stored in the constant pool of each function prototype, so API function names, keys, and messages leak out a lot. Going from a string to where it's used works here like everywhere else. And `t:method(a)` is just syntactic sugar for `t.method(t, a)`, so self is a hidden first parameter, like `this`.

## Finding Lua scripts in a game

Before decompiling, you have to get the bytecode out. In the game folder, look for `.lua`, `.luac`, `.lc` files, or a dedicated archive (`.pak`, `.rbxl`, asset bundle). Use `strings` and look for the magic `\x1bLua` / `\x1bLJ` to locate the bytecode block even when it's embedded in a large file. It may also be embedded in a native binary, so grep for the magic in the exe/so itself. Otherwise, unpack the game's archive with the matching tool and then scan.

## When the script is encrypted

Many games don't leave the bytecode bare but encrypt it (XOR, a custom cipher) and decrypt in memory right before loading into the Lua VM. Then decompiling the file on disk is useless.

One approach is to dump from runtime. Let the game decrypt it itself, then pull the decrypted bytecode out of memory. Hook the script loading function (for example `luaL_loadbuffer`, `lua_load`, `luaL_loadbufferx`) with Frida and print the buffer at the moment it's clean bytecode. It's the same dynamic unpacking idea as Part 14. The other case is when the key sits in the binary. If the cipher is simple, find the decryption function in the native code, get the key, and decrypt offline.

The principle is the same as for every kind of packer, which is to find where the data is in its cleanest form and grab it there, instead of working against the encryption layer.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 13.4</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/13.4.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/13.4/src/guard.lua" download><i class="fa-solid fa-download"></i>src/guard.lua</a>
</div>
</div>

The goal is to go through the full text to bytecode to decompiled cycle yourself, recognize the magic bytes, and recover the logic straight from bytecode. You need `lua` and `luac` (Lua 5.3 or 5.4, installable on Ubuntu with `apt install lua5.4`, or a prebuilt Windows binary), `unluac.jar` (needs Java, downloadable from the unluac repo), and a hex editor such as HxD or ImHex, or just `xxd`.

The file to work with is `guard.lua`, a Lua script that checks a license key. The valid key gets transformed with `(byte + position) % 256` and compared against an array called `EXPECTED`, so the key itself doesn't sit plainly in the bytecode.

Compile it to bytecode both with and without debug info:

```
luac -o guard.luac guard.lua
luac -s -o guard_strip.luac guard.lua
```

Open `guard.luac` in a hex editor and confirm the magic bytes `1B 4C 75 61` (`\x1bLua`) and read the fifth byte, the version (`53` or `54`). Then decompile it:

```
java -jar unluac.jar guard.luac > guard_out.lua
```

Compare `guard_out.lua` with the original `guard.lua`. How much survives? Are the local variable names still there? Repeat the decompile on `guard_strip.luac`, the stripped build, and see what differs, and whether the logic is still readable. Finally, using only the `EXPECTED` array and the transform, work out the valid license key yourself by inverting the transform in a few lines of Python, then run `lua guard.lua` and type it in to confirm.

Two questions to think about. Why does stripping remove local variable names but not the logic? And if the file turned out to be LuaJIT (`\x1bLJ` instead), would unluac read it, and which tool would you need instead?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Compiling and recognizing the magic. After `luac -o guard.luac guard.lua`, opening it with `xxd guard.luac | head` shows:

```
00000000: 1b4c 7561 5400 1993 0d0a 1a0a ...
          \x1b L u a |version byte 0x54 = Lua 5.4
```

`1B 4C 75 61` is `\x1bLua`, confirming this is standard Lua and not LuaJIT (which would be `\x1bLJ`). The fifth byte, `54`, means Lua 5.4 (it would be `53` with luac from Lua 5.3). This identification step matters because picking the wrong decompiler breaks everything right away.

Decompiling the unstripped build. Running `java -jar unluac.jar guard.luac > guard_out.lua` gives back code very close to the original. Because the unstripped bytecode still carries debug info, unluac recovers the local variable names (`transform`, `EXPECTED`, `check`, `key`), the string constants (`"Enter license key: "`, `"Correct! Welcome."`, `"Nope."`), and the loop and if structure. The array `EXPECTED = {109, 119, 100, 99, 55, 54, 57, 60, 42}` shows up intact in the constant pool.

Decompiling the stripped build. With `guard_strip.luac` (compiled with `-s`), the debug info is gone. unluac still decompiles it, but the local variable names are gone, replaced by generated names like `A0_1`, `L1_2`, `L2_3`, and local function names are gone too. The string constants and the `EXPECTED` array are still there, since they live in the constant pool rather than in debug info. The entire logic, the for loop, the `(c + i) % 256` operation, the comparison, is still complete and readable. Stripping only removes labels meant for human readers, not instructions. The bytecode still has to contain every opcode needed to run, so the logic can always be recovered.

Computing the valid license key. The check is `EXPECTED[i] == (byte(key[i]) + i) % 256`, with `i` counting from 1. Inverting it gives `byte(key[i]) = (EXPECTED[i] - i) % 256`:

```python
EXPECTED = [109, 119, 100, 99, 55, 54, 57, 60, 42]
key = ''.join(chr((EXPECTED[i] - (i + 1)) % 256) for i in range(len(EXPECTED)))
print(key)   # lua_2024!
```

The valid license key is `lua_2024!`. I checked this in Python both ways. Building `EXPECTED` from `lua_2024!` with the forward formula gives exactly the array in `guard.lua`, and inverting it gives exactly `lua_2024!` back. With `lua` installed, running `lua guard.lua` and typing `lua_2024!` prints `Correct! Welcome.`

On why stripping loses names but not logic, variable and function names are metadata for humans, while the Lua virtual machine runs on register indices. Removing names doesn't affect execution, so the bytecode still has every instruction it needs and the logic can always be rebuilt.

On LuaJIT, the answer is no, unluac only understands standard Lua bytecode. A `\x1bLJ` file needs `ljd` or `luajit-decompiler-v2` instead.

</details>

## Key takeaways
Embedded Lua is usually plain text you can read directly, and only the bytecode form needs a decompiler. There are two different families, standard Lua (magic `\x1bLua`, use unluac/luadec) and LuaJIT (magic `\x1bLJ`, use ljd), so identify first. The version byte after the magic (`51`/`52`/`53`/`54`) decides the decompiler.

Stripped bytecode only loses local variable names, the logic is still there. For encrypted scripts, dump from runtime by hooking `luaL_loadbuffer`/`lua_load` with Frida to get the clean bytecode. Tables are central to Lua, and in `t:method()` self is the hidden first parameter.
