---
title: "Lesson 11.1: Deobfuscating JavaScript, peeling layer by layer until it reads"
date: 2026-10-06 09:09:00 +0700
categories: ["Technique Reverse", "Part 11 · JavaScript, Electron, WebAssembly"]
tags: [reverse-engineering, javascript, wasm]
render_with_liquid: false
---
JavaScript doesn't compile to machine code, it runs right away as text. That sounds like the easiest thing to reverse ever, but precisely because it's text, people put a lot of effort into obfuscation: renaming variables to garbage, hiding strings in encoded arrays, shredding control flow. JS malware, credit card skimmers on websites, adblock-blocking scripts, all of them are obfuscated. This lesson shows how to peel the layers in the right order.

The key point to remember first: **obfuscation doesn't encrypt the logic, it only makes it hard to read.** The code still has to run, so everything you need is there, just covered up. Your job is to remove the cover.

## Four levels, from light to heavy

When you get an unfamiliar JS file, it falls into one of four levels, and each is handled differently:

The first level is minified code, which is only compressed (whitespace removed, variable names shortened to `a`, `b`). It's not real obfuscation, just a way to make the file small, and once you beautify it you can read it almost immediately. The second level is obfuscated code, deliberately made hard with string arrays, control flow flattening and dead code, and it's the most expensive level to deal with. The third is bundled code, where webpack/rollup merges many modules into one giant file and you need to split the modules out. The fourth is compiled code, Electron (V8 bytecode) or WebAssembly, which is lessons [11.2](https://github.com/Haind03/Technique-Reverse/blob/main/phan-11-javascript-electron-wasm/11.2-electron-asar-v8.md) and [11.3](/posts/tr-11-3-webassembly/).

## Level 1: beautify, always the first thing

Whatever level the file is at, the first step is always to reformat it with line breaks and indentation. A 50KB minified single-line file is unreadable, but after beautifying the structure shows up.

```bash
npx js-beautify minified.js
# or Prettier, or the Format button in the browser DevTools ({})
```

For a file that's only minified (not obfuscated), beautify is the whole job. You can read the logic right away, the variable names are just a bit ugly. A lot of "hidden code" is really just minified, so don't use a cleaver to kill a chicken.

## Level 2: identify the obfuscator before removing it

This is where beginners often go wrong: jumping into unpicking by hand before knowing what tool obfuscated it. Most obfuscated code in the wild comes from **obfuscator.io** (the `javascript-obfuscator` library), and it leaves fingerprints that are easy to recognize:

The first is a string array: a function returning a long array of strings, with every string in the code replaced by a call like `_0x4ae3eb(0xc4)`. The second is a rotate function, an IIFE with a `while(true)` loop using `parseInt` and `push/shift`, which rotates the string array into the right order at runtime. The third is control flow flattening, where function bodies turn into `while` + `switch` with shuffled case order, driven by a string like `"4|2|3|0|1"[split]`. The last is variable names in `_0x` hex form.

Spot these four signs and you know right away: this is obfuscator.io, and ready-made deobfuscation tools exist.

## Level 2: run a deobfuscation tool

Two main tools, try them in this order:

webcrack is the strongest right now for obfuscator.io and also webpack bundles: `npx webcrack obf.js -o out`. It resolves the string array, unflattens control flow, inlines, and splits modules. synchrony (the `deobfuscator` package) is specialized for obfuscator.io: `npx deobfuscator file.js` removes the string array and simplifies expressions.

In practice a single tool doesn't always clean it 100%. webcrack runs code in a sandbox to resolve the string array, so sometimes it trips on the environment (isolated-vm on some machines, for example). synchrony may only do part of it: convert hex constants to decimal, simplify, but still leave the control flow flattening. That's fine. **You don't need the tool to clean it completely, you only need it to clean enough that you can read the logic.**

Even when a messy `switch`-case is still there, you read each case and the original logic comes out. In this lesson's lab, after running synchrony the check function still had flattening, but the cases were clear: one case `split('-')`, one case checking the number of parts, one case summing `charCodeAt`, one case `return`ing a comparison of the sum against a constant. Put together, you understand all of it.

## Level 2, advanced: write your own AST transform

When you hit a custom obfuscator that no tool can unpick, you write the transform yourself. JavaScript has a big advantage: it can parse itself. Use **Babel** to turn the code into an AST (syntax tree), modify the tree, then print it back.

The workflow: paste the code into **AST Explorer** (astexplorer.net) to look at the tree, find a repeating pattern (for example every `_0xabc(0x1f)` call), and write a visitor that replaces it with the real value.

```js
// Example: replace every decode function call with the real string
const { parse } = require("@babel/parser");
const traverse = require("@babel/traverse").default;
const generate = require("@babel/generator").default;

const ast = parse(code);
traverse(ast, {
  CallExpression(path) {
    if (path.node.callee.name === "_0x4ae3eb") {
      const idx = path.node.arguments[0].value;
      path.replaceWithSourceString(JSON.stringify(decode(idx)));
    }
  },
});
console.log(generate(ast).code);
```

This is the most powerful way, and it's also how the tools above work inside. Learn to write AST transforms and you can unpick things no tool covers yet.

## The short workflow

```
1. Beautify (js-beautify / Prettier / the {} button in DevTools)
2. Only minified?  -> just read it, done.
3. Identify: string array + rotate + _0x + switch flattening -> obfuscator.io
4. Run webcrack, if it gets stuck use synchrony
5. Control flow still left -> read each case, or write your own Babel transform
6. Webpack bundle -> webcrack splits the modules, then repeat from step 1 for each module
```

## A note on JS malware

JS malware often adds one more layer: `eval`, `Function()`, or `atob` (base64 decode) to run a payload generated at runtime. Don't run it blindly. Replace `eval(x)` with `console.log(x)` to print the payload instead of executing it, which is the safest way to "decode" it. Do this in an isolated environment as in [Lesson 0.3](/posts/tr-0-3-dung-lab-an-toan/).

## Key takeaways
Obfuscation only hides the logic, it doesn't encrypt it, so code that runs means everything you need is there. Always beautify first, since a lot of "hidden" stuff is really just minified. Identify the obfuscator before removing it: string array + rotate + `_0x` + switch flattening is obfuscator.io.

webcrack is the strongest and synchrony is plan B, and you don't need a full cleanup, just readable logic. When the tools give up, write your own Babel/AST transform, which is also how the tools work inside. For payloads in `eval`/`Function`, print them with `console.log` and don't run them.

## Lab
See [labs/11.1/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/11.1). It has a license checker ready, a minified version, a version obfuscated with the real obfuscator.io, and the result after beautifying and running synchrony. The task: peel it back to the original logic and find a valid license key.
