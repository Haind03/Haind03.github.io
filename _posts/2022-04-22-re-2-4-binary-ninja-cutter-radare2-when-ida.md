---
title: "Lesson 2.4: Binary Ninja, Cutter and radare2"
image:
  path: /assets/img/covers/re-2-4-binary-ninja-cutter-radare2-when-ida.webp
  alt: "Lesson 2.4: Binary Ninja, Cutter and radare2"
date: 2022-04-22 22:33:00 +0700
categories: ["Technique Reverse", "Part 02 · The Toolkit"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
Ask ten people who do RE what tool they use and nine will say IDA or Ghidra. There are other tools, and sometimes one of them fits your job better. This lesson covers three, which are Binary Ninja, Cutter, and radare2/rizin. I'm not suggesting you drop IDA, just that you know when to try something else.

I'm not going to say which one is best. The best tool is the one you're good with and that fits the problem. Try them and decide yourself.

## Binary Ninja

Binary Ninja (BN for short) is a commercial disassembler that came out later than IDA, and its UI is cleaner and smoother. What technical people like about it is BNIL, its multi-level intermediate language system.

Raw assembly is messy and differs between architectures, so BN lifts it through progressively more abstract levels. LLIL (Low Level IL) is close to assembly but normalized, with architecture-specific details removed. MLIL (Medium Level IL) has variables and parameters, with register and stack details gone. HLIL (High Level IL) is nearly C-style pseudocode, easy to read.

You switch between levels to look at the same function in different detail. To inspect every instruction, go down to LLIL. For the overall logic, go up to HLIL. This also makes writing automated analysis scripts on BN pleasant, since its Python API works directly on these IL levels instead of on raw assembly.

A few practical points. There's a commercial version (a one-time payment, updates by year) and a free cloud version that runs in the browser, enough to experiment and learn without spending anything. The Python API is praised as the cleanest among disassemblers, which helps if you plan to automate a lot. The decompiler (producing HLIL) is good, though its handling of complex types is still a bit behind IDA's Hex-Rays.

I'd pick BN if you want a modern UI, often write analysis scripts, and like working on a multi-level IL.

## radare2 and rizin

radare2 (r2 for short) is a fully open source RE toolkit driven from the command line. It's hard to learn, because the command syntax is so short it's hard to remember. rizin is a fork of r2, cleaned up to be more consistent, so if you're just starting you may want to look at rizin.

In r2 everything is a short command, and you combine them in a session. It sounds scary, but about five commands cover the basics:

| Command | What it does |
|---|---|
| `aaa` | Analyze the whole file (analyze all). Almost always run first |
| `afl` | List the functions found (analyze function list) |
| `s <address or name>` | Seek, move the cursor there, for example `s main` |
| `pdf` | Print disassembly of function, prints the disassembly of the current function |
| `VV` | Enter the visual graph view (press `q` to quit) |

The command names have a pattern that helps with remembering. The first letter is the group (`a` analyze, `p` print, `s` seek, `V` visual), and the later letters narrow it down. `pdf` is print (p), disassembly (d), function (f). Once you see that, you don't have to memorize.

r2/rizin is free and open, and it runs anywhere including over SSH on a server with no GUI. Scripting is strong and combines with the shell and pipes, and `r2pipe` lets you drive r2 from Python, C, and many other languages. The downsides are the steep learning curve, and that on a big file a pure command line is more tiring than a GUI.

I'd pick r2/rizin if you like the command line, need to work with no GUI, or want to automate with small quick scripts.

## Cutter

If you like rizin but can't stand the command line, there's Cutter. It's the official GUI built on rizin, with disassembly, graph, hex, strings and imports windows like IDA, but the engine underneath is rizin and it's free.

The most useful part is that Cutter has the jsdec decompiler built in (and can plug in Ghidra's decompiler), so you get pseudocode without paying. For beginners put off by both r2 and IDA's price, Cutter is a reasonable entry point. It has a familiar interface and open tooling, and you can still type rizin commands in the command box when needed.

I'd pick Cutter if you want a full free GUI, or want to use rizin but prefer the mouse.

## What to pick

There's no single right answer, but here's what I usually recommend. Beginners on a small budget should start with Ghidra (lesson 2.3) or Cutter, both free and with a decompiler. If you like a nice UI, often write scripts, and have a budget or use the cloud version, try Binary Ninja. Command-line people who work a lot on servers and like automation will like radare2/rizin. For professional work that needs the strongest Hex-Rays, use IDA Pro (lesson 2.2).

More important than which tool you choose is not to keep jumping between tools while learning. Pick one, use it until the shortcuts are automatic, and only then try another.

## Lab

The goal is to take apart one binary with command-line radare2, then reopen it in Cutter, to see how the same data looks in a CLI and a GUI. If you can, also try the Binary Ninja cloud version. Build the sample binary `crackme_r2.c` first:

```
gcc -O0 -no-pie -o crackme_r2 crackme_r2.c      # Linux
# or on Windows with MinGW:
# gcc -O0 -o crackme_r2.exe crackme_r2.c
```

You also need radare2 (or rizin) and Cutter. For radare2, run `git clone https://github.com/radareorg/radare2 && radare2/sys/install.sh`, or use your distro's package. Rizin can be downloaded from rizin.re, and Cutter as an AppImage or exe from cutter.re.

Open the binary in radare2 with `r2 crackme_r2`. At the prompt, run `aaa` and then `afl` and write down the output, including how many functions there are and what they are called. Then run `s main` and `pdf` to read the disassembly of `main` and find where the password is compared, and `VV` to see the graph view of `main` (move with the arrow keys, `q` to quit). Next, look for strings in the file with `iz` (strings in the data section) and `izz` (the whole file), and decide which one hints at the password. From the message string you find, use `axt <string address>` to see what references it (a cross-reference), and check whether it leads to the check function.

Then open the same binary in Cutter. Find `main` in the Functions panel, look at the graph, and click the Decompiler tab (jsdec) to read the pseudocode. Compare that with what you read by eye in radare2 and note which was faster for you. Optionally, if you have a Binary Ninja cloud account, upload the binary and look at the HLIL of `main`, then compare the three views, r2 disassembly, Cutter pseudocode and Binary Ninja HLIL.

Two questions to think about. What is the correct password, and which tool found it fastest? And which tool do you find more comfortable for this exercise, and why? Do all of it before opening the solution.

<div class="lab-box">
<div class="lab-head"><b>LAB 2.4</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/2.4/src/crackme_r2.c" download><i class="fa-solid fa-file-code"></i>src/crackme_r2.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The correct password is `r2_rocks_2024`. Here is the path to it with all three tools.

A sample radare2 session:

```
$ r2 crackme_r2
 -- Welcome to radare2
[0x00001060]> aaa
[x] Analyze all flags starting with sym. and entry0 (aa)
[x] Analyze function calls (aac)
...
[0x00001060]> afl
0x00001060    1  42  entry0
0x00001149    4  94  sym.check_password
0x000011a7    5  120 main
...
```

`aaa` analyzes the whole file and `afl` lists the functions. There's a `sym.check_password`, with its name intact because the binary isn't stripped. That is the function to look at.

```
[0x00001060]> s sym.check_password
[0x00001149]> pdf
```

In the disassembly of `check_password` you see a pointer to a string being loaded (a `lea` pointing at `str.r2_rocks_2024`), then a call to `strlen` to compare lengths, then `strcmp` to compare contents. radare2 annotates the string name next to the instruction, so the password is visible right here.

An even faster route skips reading the function altogether:

```
[0x00001149]> izz~rocks
0  0x00002008 0x00002008 13 13 .rodata ascii r2_rocks_2024
```

`izz` lists the strings of the whole file, and `~rocks` is r2's built-in grep, filtering lines that contain "rocks". The string `r2_rocks_2024` sits in `.rodata`, and it is the password. To see who uses that string:

```
[0x00001149]> axt 0x00002008
sym.check_password 0x1157 [DATA:r--] lea rax, str.r2_rocks_2024
```

`axt` shows that only `check_password` references the string, which confirms it is the check function.

In Cutter, open the binary and the Functions panel on the left lists `check_password` and `main` just like `afl`. Double-click `check_password` and switch to the Decompiler tab (jsdec) to get pseudocode like this:

```c
int check_password(char *input) {
    if (strlen(input) != strlen("r2_rocks_2024"))
        return 0;
    return strcmp(input, "r2_rocks_2024") == 0;
}
```

If you're used to a GUI, this pseudocode reads faster than the raw disassembly in r2. In Binary Ninja (cloud), upload the binary, open `check_password` and switch to HLIL. The result is close to Cutter's, with two `strlen` calls to compare lengths, then `strcmp`. With BN you can toggle between LLIL, MLIL and HLIL to see the same function at three levels of detail.

All three tools lead to the same answer. The fastest for this exercise is the `izz~` trick that finds the string directly, because the password is compared in plaintext. When the password is encrypted or generated at runtime, the string trick is no longer enough and you have to read the function carefully (or move on to the dynamic analysis of later lessons). Pick the tool you read fastest. Using the harder one earns you nothing.

</details>

## Key takeaways
Binary Ninja has a modern UI, a multi-level IL (LLIL/MLIL/HLIL), a nice Python API, and a free cloud version to try. radare2/rizin is command line, free, and strong at automation, with five core commands, namely `aaa`, `afl`, `s`, `pdf`, `VV`. Its command names follow a pattern (group plus narrowing), and understanding the pattern saves memorizing.

Cutter is a free GUI on top of rizin with the jsdec decompiler, good for beginners who dislike the command line. Pick one tool and get good with it before switching.
