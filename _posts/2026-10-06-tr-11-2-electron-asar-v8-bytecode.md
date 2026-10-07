---
title: "Lesson 11.2: Dissecting an Electron app, from app.asar to V8 bytecode"
date: 2026-10-06 09:10:00 +0700
categories: ["Technique Reverse", "Part 11 · JavaScript, Electron, WebAssembly"]
tags: [reverse-engineering, javascript, wasm]
render_with_liquid: false
---
A lot of the desktop apps you use every day (Discord, VS Code, Slack, Postman) are really a Chromium browser packaged together with Node.js, called Electron. Good news for reversers: most of their logic is JavaScript, and JavaScript is almost readable in its original form. Less good news: a few apps wrap their code in V8 bytecode to make life hard for you. This lesson goes from easy to hard.

## What Electron is under the shell

An Electron app has three pieces:

Chromium renders the UI, it's literally a browser. Node.js lets the code access files, network and system like a real desktop program. The third piece is your app code, written in JavaScript (sometimes transpiled TypeScript) and split into the main process (runs on Node) and the renderer process (runs inside Chromium).

The key point for reversing: the app code isn't compiled to machine code. It's just packaged. Your job is mostly to find that package and open it.

## Finding the code: resources/app.asar

Install an Electron app and go into its install folder, and you'll see a `resources/` folder. Inside there's usually either `app.asar`, an archive file holding all the JS, HTML, CSS, JSON source, or an `app/` folder left unpackaged (even easier, just read it directly).

`asar` is just Electron's simple packaging format, with no encryption at all, it only concatenates the files with a JSON header describing where they are. That means opening it is as easy as extracting an archive.

How to tell an app is Electron: it has `resources/app.asar`, Chromium's `*.pak` files, `ffmpeg.dll`/`libffmpeg`, and an unusually large install size (a hundred MB or more for a simple app).

## Extracting app.asar

The standard way, with the official tool:

```bash
# install asar if you don't have it
npm install -g asar

# extract
asar extract app.asar app_extracted/

# or list the contents before extracting
asar list app.asar
```

No Node is fine too, `app.asar` can be opened with 7-Zip (with a plugin), or you can parse the JSON header at the start of the file yourself. But `asar extract` is the fastest and cleanest.

After extracting you have a readable JS directory tree. Open `package.json` and look for the `main` field, which is the entry file of the main process (usually `main.js` or `index.js`). From there you trace the logic: where the license is checked, where the API is called, where the data is processed. If the code is minified (squeezed onto one line, one-letter variable names), use Prettier or js-beautify to clean it up before reading (details on JS deobfuscation are in Lesson 11.1).

## Modifying and repacking

Since it's plain JS, you edit the files directly and pack them again:

```bash
# edit files in app_extracted/ with any editor
asar pack app_extracted/ app.asar
```

Overwrite the old `app.asar` (back up the original first). On the next run, Electron loads your modified code. This is why patching an Electron app is often just changing a few lines of JS, with no need to touch assembly. This is for security testing of your own apps or apps you have permission for, not for bypassing commercial licenses.

## When you hit V8 bytecode (.jsc)

Some apps wrap their code more carefully with **bytenode**: it compiles JavaScript to V8 bytecode, saves it as a `.jsc` file, and loads that bytecode at runtime. Open it and you no longer see JS, just a binary blob. This is a clearly harder step.

A few things are worth knowing about V8 bytecode. It's not stable across V8/Node versions: a `.jsc` file built for Node 18 won't necessarily run on Node 20, so to run or analyze it you need the exact V8 version the app uses. It also doesn't keep the original source, but it still keeps a lot of information: function names, string literals, and variable names in many cases. Running `strings` on a `.jsc` file often exposes quite a few clues.

For the approach, this is the order I'd try. First, get strings and constants: `strings file.jsc` often shows function names, message strings, endpoints, and sometimes that's already enough to understand the logic. Second, dump from runtime, which is the strongest way. Since V8 still has to execute the code in the end, you can hook into the loading process to get the source or AST back. Use the exact same Node version to load the `.jsc` file and intercept at the `vm`/`Module._compile` layer, or use community tools made for dumping bytenode. Third, disassemble the bytecode. Node has an internal flag `--print-bytecode` that prints V8 bytecode in a readable form, and you can combine it with the V8 opcode docs to read it by hand. It's very painful, so only do it when you really need to.

In practice, with bytenode, route number 2 (runtime dump) almost always wins, because bytenode only hides and doesn't encrypt strongly: if the code has to run, you must be able to get it back.

## Key takeaways
An Electron app is Chromium + Node.js + packaged JavaScript code, not compiled to native. The code lives in `resources/app.asar`, which you extract with `asar extract` or 7-Zip, and there's no encryption. Read the `main` field in `package.json` to find the entry point, beautify if it's minified, and edit the JS directly and `asar pack` to repack.

On `.jsc` (bytenode, V8 bytecode), try strings first. Dumping from runtime is the winning way and disassembly is the last resort.

## Lab
See [labs/11.2/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/11.2): find and extract the `app.asar` of an Electron app, read the code, try modifying it and repacking.
