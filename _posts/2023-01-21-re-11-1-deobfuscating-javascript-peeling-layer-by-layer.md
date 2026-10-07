---
title: "Lesson 11.1: Deobfuscating JavaScript"
image:
  path: /assets/img/covers/re-11-1-deobfuscating-javascript-peeling-layer-by-layer.webp
  alt: "Lesson 11.1: Deobfuscating JavaScript"
date: 2023-01-21 16:43:00 +0700
categories: ["Technique Reverse", "Part 11 · JavaScript, Electron, WebAssembly"]
tags: [reverse-engineering, javascript, wasm]
render_with_liquid: false
---
JavaScript doesn't compile to machine code, it runs as text. That sounds like the easiest thing to reverse, but because it's text, people put a lot of effort into obfuscating it, such as renaming variables to garbage, hiding strings in encoded arrays, shredding control flow. JS malware, credit card skimmers on websites and adblock-blocking scripts are all obfuscated. This lesson covers how to take the layers off in the right order.

Remember this first. Obfuscation doesn't encrypt the logic, it only makes it hard to read. The code still has to run, so everything you need is there, just covered up. Your job is to remove the cover.

## Four levels, from light to heavy

An unfamiliar JS file falls into one of four levels, and each is handled differently.

The first level is minified code, which is only compressed (whitespace removed, variable names shortened to `a`, `b`). It's not real obfuscation, just a way to make the file small, and once you beautify it you can read it almost immediately. The second level is obfuscated code, deliberately made hard with string arrays, control flow flattening and dead code. It takes the most work. The third is bundled code, where webpack/rollup merges many modules into one giant file and you need to split the modules out. The fourth is compiled code, Electron (V8 bytecode) or WebAssembly, covered in lessons [11.2](/posts/re-11-2-dissecting-electron-app-from-app-asar/) and [11.3](/posts/re-11-3-webassembly-reading-bytecode-that-runs-browser/).

## Level 1: beautify

Whatever level the file is at, the first step is always to reformat it with line breaks and indentation. A 50KB minified single-line file is unreadable, but after beautifying the structure shows up.

```bash
npx js-beautify minified.js
# or Prettier, or the Format button in the browser DevTools ({})
```

For a file that's only minified (not obfuscated), beautify is the whole job. You can read the logic right away, the variable names are just a bit ugly. A lot of "hidden code" is really just minified, so don't bring heavy tools to a simple problem.

## Level 2: identify the obfuscator first

Beginners often jump into unpicking by hand before knowing what tool obfuscated the code. Most obfuscated code in the wild comes from obfuscator.io (the `javascript-obfuscator` library), and it leaves patterns that are easy to recognize.

The first is a string array, which is a function returning a long array of strings, with every string in the code replaced by a call like `_0x4ae3eb(0xc4)`. The second is a rotate function, an IIFE with a `while(true)` loop using `parseInt` and `push/shift`, which rotates the string array into the right order at runtime. The third is control flow flattening, where function bodies turn into `while` + `switch` with shuffled case order, driven by a string like `"4|2|3|0|1"[split]`. The last is variable names in `_0x` hex form.

If you see these four signs, it's obfuscator.io, and ready-made deobfuscation tools exist.

## Level 2: run a deobfuscation tool

Two main tools, try them in this order.

webcrack is the strongest right now for obfuscator.io and also webpack bundles, run as `npx webcrack obf.js -o out`. It resolves the string array, unflattens control flow, inlines, and splits modules. synchrony (the `deobfuscator` package) is specialized for obfuscator.io, and `npx deobfuscator file.js` removes the string array and simplifies expressions.

In practice a single tool doesn't always clean it 100%. webcrack runs code in a sandbox to resolve the string array, so on some machines that layer (isolated-vm, for example) can fail to load or run. synchrony may only do part of it, such as converting hex constants to decimal and simplifying, but it may still leave the control flow flattening. That's fine. You don't need the tool to clean everything, only enough that you can read the logic.

Even when a messy `switch`-case is still there, you read each case and the original logic comes out. In this lesson's lab, after running synchrony the check function still had flattening, but the cases were clear, with one case `split('-')`, one case checking the number of parts, one case summing `charCodeAt`, one case `return`ing a comparison of the sum against a constant. Put them together and you have all of it.

## Level 2, advanced: write your own AST transform

When you hit a custom obfuscator that no tool can unpick, you write the transform yourself. JavaScript can parse itself, which helps. Use Babel to turn the code into an AST (syntax tree), modify the tree, then print it back.

The workflow is to paste the code into AST Explorer (astexplorer.net) to look at the tree, find a repeating pattern (for example every `_0xabc(0x1f)` call), and write a visitor that replaces it with the real value.

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

This is the most flexible way, and it's how the tools above work inside. If you learn to write AST transforms you can unpick things no tool covers yet.

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

JS malware often adds one more layer, such as `eval`, `Function()`, or `atob` (base64 decode) to run a payload generated at runtime. Don't run it blindly. Replace `eval(x)` with `console.log(x)` to print the payload instead of executing it, which is the safest way to decode it. Do this in an isolated environment as in [Lesson 0.3](/posts/re-0-3-set-up-safe-lab-before-touching/).

## Key takeaways
Obfuscation only hides the logic, it doesn't encrypt it, so if the code runs, everything you need is there. Beautify first, since a lot of "hidden" stuff is really just minified. Identify the obfuscator before removing it, since string array + rotate + `_0x` + switch flattening is obfuscator.io.

webcrack is the strongest and synchrony is plan B, and you don't need a full cleanup, just readable logic. When the tools give up, write your own Babel/AST transform, which is also how the tools work inside. For payloads in `eval`/`Function`, print them with `console.log` and don't run them.

## Lab

The task is to take a JavaScript license checker from its obfuscated form back to readable logic, and then find a valid license key. There are five versions of the checker. `original.js` is the original, which you should only open to check your work after solving it yourself. `minified.js` has only been minified (level 1). `obfuscated.js` was obfuscated with `javascript-obfuscator` (obfuscator.io) using a string array and control flow flattening. `obfuscated.beautified.js` is the previous file after `js-beautify`, so you can see the structure of the string array and the rotate function. `after-synchrony.js` is the result of running `npx deobfuscator`, with hex converted to decimal and partly simplified.

Start by beautifying `minified.js` and reading the logic, and work out what a valid license key looks like. Then open `obfuscated.js` and identify the string array, the rotate function and the control flow flattening, and which signs tell you this is obfuscator.io. Run `npx js-beautify obfuscated.js` and then `npx deobfuscator obfuscated.js`, and compare the result with `after-synchrony.js`.

After deobfuscation there is still a messy `switch`-case. Read each case and put the original logic back together. Using the recovered logic, build a valid license key and run it with `node` to confirm.

Two hints. The sum of the `charCodeAt` values of the first part must equal one specific constant, so work out what that sum is for the sample key `ABCD-...`. The middle part and the length of the last part are checked as well. Try it yourself before opening the solution.

<div class="lab-box">
<div class="lab-head"><b>LAB 11.1</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/11.1/src/after-synchrony.js" download><i class="fa-solid fa-file-code"></i>src/after-synchrony.js</a>
<a class="lab-file" href="/assets/labs/11.1/src/minified.js" download><i class="fa-solid fa-file-code"></i>src/minified.js</a>
<a class="lab-file" href="/assets/labs/11.1/src/obfuscated.beautified.js" download><i class="fa-solid fa-file-code"></i>src/obfuscated.beautified.js</a>
<a class="lab-file" href="/assets/labs/11.1/src/obfuscated.js" download><i class="fa-solid fa-file-code"></i>src/obfuscated.js</a>
<a class="lab-file" href="/assets/labs/11.1/src/original.js" download><i class="fa-solid fa-file-code"></i>src/original.js</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

All the files were really produced and tested with Node v20.20.2. `obfuscated.js` was generated with `javascript-obfuscator original.js --control-flow-flattening true --string-array true --string-array-threshold 1`, and running `node obfuscated.js` prints `true` (the sample key is valid), which confirms the obfuscation did not change the logic. `obfuscated.beautified.js` is `npx js-beautify obfuscated.js`, and `after-synchrony.js` is `npx deobfuscator obfuscated.js` (the synchrony package).

If `webcrack` fails on your machine in its isolated-vm sandbox layer while resolving the string array, that's an environment problem, not a weakness of the tool, and on a working setup it usually cleans up better than synchrony. The task is still fully solvable with synchrony plus reading by hand. You don't need a tool that cleans everything.

Reading the minified version first, `minified.js` after beautifying is just `original.js`. The logic is this.

```js
function checkLicense(key) {
  var parts = key.split("-");
  if (parts.length !== 3) return false;      // must be exactly 3 parts A-B-C
  var sum = 0;
  for (var i = 0; i < parts[0].length; i++)
    sum += parts[0].charCodeAt(i);           // sum of the ASCII codes of the first part
  return sum === 266                          // sum = 266
      && parts[1] === "PRO"                   // middle part = "PRO"
      && parts[2].length === 4;               // last part is 4 characters long
}
```

To recognize obfuscator.io, look at `obfuscated.beautified.js`. The function `a0_0x2c73(_0x4ae3eb, _0x7c52ba) { ... var _0x4017e2 = a0_0x4017(); return _0x4017e2[_0x4ae3eb]; }` is the string array accessor, and every string has been replaced by `a0_0x2c73(0x...)`. `a0_0x4017` is the function that returns the string array. The IIFE `(function(_0x3bbb98, _0x3bab1d){ ... while(!![]){ try{ ...parseInt... push(shift()) ... } } }(a0_0x4017, 0x6c32f))` is the rotate function, which rotates the array until a checksum matches `0x6c32f`. The variable names are in `_0x` hex style, and you will see control flow flattening inside `checkLicense`. These four signs confirm obfuscator.io.

After synchrony (`after-synchrony.js`), the hex constants have become decimal and the code is tidier, but `checkLicense` is still flattened.

```js
var _0x3ce6eb = _0x47e645(197).split('|');   // order of the cases, e.g. "4|2|3|0|1"
while (true) {
  switch (_0x3ce6eb[_0x29a5da++]) {
    case '4': var _0xb24b61 = _0x963ecc.split('-'); continue;   // split '-'
    case '2': if (_0xb24b61.length !== 3) return false; continue;
    case '0': var _0x3f6997 = 0; continue;
    case '3': for (...) _0x3f6997 += _0xb24b61[0].charCodeAt(_0x32ce62); continue;  // add charCodes
    case '1': return eq(_0x3f6997, 266) && eq(_0xb24b61[1], "PRO") && _0xb24b61[2].length === 4;
  }
  break;
}
```

Read the cases in the order given by the `split('|')` string and you get the original logic back. It splits on `-`, checks there are 3 parts, adds the charCodes of the first part, compares with 266, requires the middle part to be `"PRO"`, and requires the last part to be 4 long. Control flow flattening only shuffles the order of the blocks and doesn't change the meaning.

To build a valid key you need the charCode sum of the first part to be 266, the middle part `"PRO"` and the last part 4 characters long. `"ABCD"` gives 65+66+67+68 = 266, which works, so a valid key is `ABCD-PRO-2024` (the last part `2024` is 4 characters long). Checking it:

```
$ node original.js
true
$ node obfuscated.js
true
```

Both the original and the obfuscated versions accept `ABCD-PRO-2024`, so the logic was recovered correctly. Any other first part whose charCodes sum to 266 is valid too, but the sum must be exactly 266 (for example `"BBCD"` = 66+66+67+68 = 267 doesn't work). A small keygen is handy here to enumerate the combinations whose sum is 266.

</details>

