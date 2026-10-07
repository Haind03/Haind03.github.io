---
title: "Lesson 2.4: Binary Ninja, Cutter and radare2, when IDA and Ghidra aren't the only options"
image:
  path: /assets/img/covers/re-2-4-binary-ninja-cutter-radare2-when-ida.webp
  alt: "Lesson 2.4: Binary Ninja, Cutter and radare2, when IDA and Ghidra aren't the only options"
date: 2022-04-22 22:33:00 +0700
categories: ["Technique Reverse", "Part 02 · The Toolkit"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
Ask ten people who do RE what tool they use and nine will say IDA or Ghidra. But stopping there misses a whole ecosystem, and sometimes the "unpopular" tool fits your job better. This lesson covers three names worth having in your toolbox: Binary Ninja, Cutter, and radare2/rizin. Not so you drop IDA, but so you know when to reach for something else.

A small note before we start: I'm not trying to convince you which one is "best". The best tool is the one you're good with and that fits the problem. The goal here is to give you enough information to try them and decide yourself.

## Binary Ninja, the young challenger

Binary Ninja (BN for short) is a commercial disassembler that came out later, so it learned from its elders and built a much cleaner, smoother UI. But what makes technical people love it isn't the interface, it's BNIL, its multi-level intermediate language system.

The idea of an IL is this: raw assembly is messy and differs between architectures. BN lifts assembly up through progressively more abstract levels. LLIL (Low Level IL) is close to assembly but normalized, with architecture-specific junk removed. MLIL (Medium Level IL) has variables and parameters, with register and stack details gone. HLIL (High Level IL) is nearly C-style pseudocode, easy to read.

You switch back and forth between levels to look at the same function at different levels of detail. When you need to inspect every instruction, go down to LLIL; when you want the overall logic, go up to HLIL. This is what makes writing automated analysis scripts on BN so pleasant, since its Python API works directly on these IL levels instead of on raw assembly.

A few practical points about BN. There's a commercial version (a one-time payment, updates by year) and a free cloud version that runs in the browser, enough to experiment and learn without spending a cent, so beginners can just play with the cloud version first. The Python API is praised as the cleanest and easiest to use among disassemblers, which suits you if you plan to automate a lot. The decompiler (producing HLIL) is good, though its handling of complex types is still a notch behind IDA's Hex-Rays.

Pick BN when you want a modern UI, often write analysis scripts, and like working on a multi-level IL.

## radare2 and rizin, the power of the command line

radare2 (r2 for short) is a fully open source RE toolkit driven from the command line. It's famous for being both powerful and hard to learn, because its command syntax is so short it's hard to remember. rizin is a fork split off from r2, cleaned up to be more consistent and approachable, so if you're just starting you may want to consider rizin.

The philosophy of r2 is that everything is a short command, combined into a working session. Sounds scary, but you only need to know about five commands to do the basics:

| Command | What it does |
|---|---|
| `aaa` | Analyze the whole file (analyze all). Almost always run first |
| `afl` | List the functions found (analyze function list) |
| `s <address or name>` | Seek, move the cursor there, for example `s main` |
| `pdf` | Print disassembly of function, prints the disassembly of the current function |
| `VV` | Enter the visual graph view (press `q` to quit) |

Reading the command names helps a lot with remembering: the first letter is the group (`a` analyze, `p` print, `s` seek, `V` visual), and the later letters narrow it down. `pdf` is print (p), disassembly (d), function (f). Once you understand this pattern you don't have to memorize.

r2/rizin is completely free and open, and it runs anywhere including over SSH on a server with no GUI. Its scripting is extremely strong and combines freely with the shell and pipes, and `r2pipe` lets you drive r2 from Python, C, and many other languages. The weaknesses are a steep learning curve, and that when analyzing a big file by eye, a pure command line is more tiring than a GUI.

Pick r2/rizin when you like the command line, need to work in an environment with no GUI, or want to automate with small quick scripts.

## Cutter, the graphical face of rizin

If you like the power of rizin but can't stand the command line, Cutter is the answer. It's the official GUI built on rizin, giving you disassembly, graph, hex, strings, imports windows like IDA, but the engine underneath is rizin and it's completely free.

The most valuable point: Cutter has the jsdec decompiler built in (and can plug in Ghidra's decompiler), so you get pseudocode without paying. For beginners put off by both r2 and IDA's price, Cutter is a very reasonable entry point: a familiar interface, open tooling, and you can still type rizin commands in the command box when needed.

Pick Cutter when you want a full free GUI experience, or want to use rizin but prefer the mouse over the keyboard.

## So what to pick in the end

There's no absolutely right answer, but here's what I usually recommend. Beginners on a small budget should start with Ghidra (lesson 2.3) or Cutter, both free and with a decompiler. If you like a nice UI, often write scripts, and have a budget or use the cloud version, try Binary Ninja. Command-line people who do a lot on servers and love automation will like radare2/rizin. Professional environments needing the strongest Hex-Rays should use IDA Pro (lesson 2.2).

More important than which tool you choose: don't keep jumping between tools while learning. Pick one, use it until the shortcuts become instinct, and only then try another. Jumping back and forth is a sure way to not get good at any of them.

## Lab

The goal is to take apart one binary with command-line radare2, then reopen it in Cutter, to see how the same data appears differently in a CLI and a GUI. If you can, also try the Binary Ninja cloud version. Build the sample binary `crackme_r2.c` first:

```
gcc -O0 -no-pie -o crackme_r2 crackme_r2.c      # Linux
# or on Windows with MinGW:
# gcc -O0 -o crackme_r2.exe crackme_r2.c
```

You also need radare2 (or rizin) and Cutter. For radare2, run `git clone https://github.com/radareorg/radare2 && radare2/sys/install.sh`, or use your distro's package. Rizin can be downloaded from rizin.re, and Cutter as an AppImage or exe from cutter.re.

Open the binary in radare2 with `r2 crackme_r2`. At the prompt, run `aaa` and then `afl` and write down the output: how many functions are there, and what are they called? Then run `s main` and `pdf` to read the disassembly of `main` and find where the password is compared, and `VV` to see the graph view of `main` (move with the arrow keys, `q` to quit). Next, look for strings in the file with `iz` (strings in the data section) and `izz` (the whole file), and decide which one hints at the password. From the message string you find, use `axt <string address>` to see what references it (a cross-reference), and check whether it leads to the check function.

Then open the very same binary in Cutter. Find `main` in the Functions panel, look at the graph, and click the Decompiler tab (jsdec) to read the pseudocode. Compare that with what you read by eye in radare2: which was faster for you? Optionally, if you have a Binary Ninja cloud account, upload the binary and look at the HLIL of `main`, then compare the three views: r2 disassembly, Cutter pseudocode and Binary Ninja HLIL.

Two questions to reflect on. What is the correct password, and which tool found it fastest? And which tool do you personally find more comfortable for this exercise, and why? Do all of it before opening the solution.

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

`aaa` analyzes the whole file and `afl` lists the functions. Notice right away that there is a `sym.check_password`, with its name intact because the binary isn't stripped. That is the function to look at.

```
[0x00001060]> s sym.check_password
[0x00001149]> pdf
```

In the disassembly of `check_password` you see a pointer to a string being loaded (a `lea` pointing at `str.r2_rocks_2024`), then a call to `strlen` to compare lengths, then `strcmp` to compare contents. radare2 annotates the string name next to the instruction, so the password is exposed right here.

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

For someone used to a GUI, this pseudocode reads faster than the raw disassembly in r2. In Binary Ninja (cloud), upload the binary, open `check_password` and switch to HLIL. The result is close to Cutter's: two `strlen` calls to compare lengths, then `strcmp`. The nice thing about BN is that you can toggle between LLIL, MLIL and HLIL to see the same function at three levels of detail.

All three tools lead to the same answer. The fastest for this exercise is the `izz~` trick that finds the string directly, because the password is compared in plaintext. When the password is encrypted or generated at runtime, the string trick is no longer enough and you have to read the function carefully (or move on to the dynamic analysis of later lessons). The lesson about tools is to pick the one you read fastest. There is no prize for using the harder tool.

</details>

## Key takeaways
Binary Ninja has a modern UI, a multi-level IL (LLIL/MLIL/HLIL), a nice Python API, and a free cloud version to try. radare2/rizin is command line, free, and strong at automation, with five core commands: `aaa`, `afl`, `s`, `pdf`, `VV`. Its command names follow a pattern (group plus narrowing), and understanding the pattern saves memorizing.

Cutter is a free GUI on top of rizin with the jsdec decompiler, good for beginners who dislike the command line. Pick one tool and get good with it before switching.
