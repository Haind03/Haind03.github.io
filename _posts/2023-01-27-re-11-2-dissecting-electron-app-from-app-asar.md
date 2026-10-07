---
title: "Lesson 11.2: Dissecting an Electron app, from app.asar to V8 bytecode"
image:
  path: /assets/img/covers/re-11-2-dissecting-electron-app-from-app-asar.webp
  alt: "Lesson 11.2: Dissecting an Electron app, from app.asar to V8 bytecode"
date: 2023-01-27 15:53:00 +0700
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

The task is to recover and modify the JavaScript code of an Electron application. You need Node.js (to use `npx asar`) or 7-Zip with an asar plugin, and any Electron app you have the right to analyze: a small app you download to learn from, or a minimal Electron app you create yourself. Don't use this to get around the license of commercial software. A good way to make a practice target is to run `npm init`, install `electron`, write a `main.js` that prints a message, package it with `electron-packager` or `electron-builder`, and then reverse the result yourself.

Begin by confirming the app is Electron: look for `resources/app.asar`, `*.pak` files, Chromium libraries, and a large size. List the archive contents with `asar list app.asar` and extract it with `asar extract app.asar out/`. Read `package.json`, find the `main` field, and open that entry-point file. If the code is minified, run Prettier or js-beautify and read it again. Then pick a message string from the UI and trace backward through the code to where it is produced. Finally change one line (for example a displayed string), repack with `asar pack out/ app.asar` (back up the original first), run the app and confirm the change.

As an extension, if you meet `.jsc` files, the app uses bytenode. Run `strings` on the file to see what it leaks, then try loading it with the exact Node version of the app and intercepting at the `vm` or `Module._compile` layer to get the source back.

Two questions to think about. Why is modifying an Electron app usually much easier than modifying a native C++ app? And bytenode "hides" the code rather than "encrypting" it, so what does that mean for dumping it from the runtime? Do it yourself before opening the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This writeup describes the standard procedure on an Electron app. The paths and file names are the typical forms you will meet, and they differ from app to app.

### Identifying and extracting

The Electron signs in the install folder:

```
MyApp/
  MyApp.exe
  resources/app.asar        <- the code is here
  resources.pak, *.pak       <- Chromium resources
  ffmpeg.dll, libEGL.dll     <- Chromium libraries
  (total size in the hundreds of MB)
```

List and then extract:

```bash
asar list resources/app.asar
asar extract resources/app.asar out/
```

Without Node, open `app.asar` with 7-Zip and the asar plugin, or read the JSON header at the start of the file (asar stores a JSON describing the offset and size of each file at the beginning).

### Finding the entry point

`out/package.json`:

```json
{ "name": "myapp", "main": "dist/main.js", "version": "1.2.3" }
```

The `main` field points to the first file the main process runs. Open `dist/main.js`. If it is one extremely long line with variable names like `a,b,c`, the code is minified. Prettify it:

```bash
npx prettier --write out/dist/main.js
# or
npx js-beautify out/dist/main.js -o out/dist/main.pretty.js
```

### Going from a string to the code

If the UI shows "License invalid", grep the extracted source:

```bash
grep -rn "License invalid" out/
```

The place that matches is usually the license check function. Read around it to understand the valid condition. This is the familiar go-from-the-string technique, like with native code, except here it is directly readable source.

### Modifying and repacking

```bash
cp resources/app.asar resources/app.asar.bak    # back up
# edit out/dist/main.js with an editor
asar pack out/ resources/app.asar
```

Run the app again and the change takes effect. With a practice app you made yourself, you will see the string you edited straight away.

### When it is .jsc (bytenode)

If `main` points to a `.jsc`, or the code contains `require('bytenode')`, the code has become V8 bytecode. `strings out/dist/main.jsc` often leaks function names, string literals and endpoints, and sometimes that is enough to understand the logic. A runtime dump is the winning approach: load the file with the exact Node version of the app and intercept at `Module._compile` or `vm.Script` to get the source back before V8 runs it. Bytenode only hides and does not encrypt strongly, so if the code has to run, you must be able to get it back. The last resort is `node --print-bytecode` to disassemble the V8 bytecode and read opcodes by hand, which is very laborious.

### Answers to the questions

Modifying Electron is easier than native C++ because the code is JavaScript that is not compiled to machine code, only wrapped in an unencrypted asar. There is no assembly to read and no structs or vtables to recover, you just extract and read the source. Bytenode "hiding" means turning JS into bytecode that is hard to read directly, but it is not locked with a secret key. Since V8 still has to execute the code, you can always step in at load time to get it back, so a runtime dump almost always succeeds.

</details>

