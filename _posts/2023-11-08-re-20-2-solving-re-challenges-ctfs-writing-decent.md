---
title: "Lesson 20.2: Solving RE challenges in CTFs and writing a write-up"
image:
  path: /assets/img/covers/re-20-2-solving-re-challenges-ctfs-writing-decent.webp
  alt: "Lesson 20.2: Solving RE challenges in CTFs and writing a write-up"
date: 2022-09-28 21:45:00 +0700
categories: ["Reverse Engineering", "Part 20 · Real-World Practice"]
tags: [reverse-engineering, ctf]
render_with_liquid: false
---
After nineteen parts you have enough tools and techniques. What's missing is the rhythm of solving under pressure, when nobody tells you in advance what language the challenge uses, which packer, or where the flag is hidden. CTFs are where you practice that, and a write-up is how you keep what you learned from a solve. This lesson covers both.

![Rev challenge workflow](/assets/img/re/re-20-2-solving-re-challenges-ctfs-writing-decent.svg)
_The workflow for a rev challenge, ending in a write-up._

## Where to play

Not every arena suits beginners. picoCTF is education-oriented, and its Reverse Engineering category is a good place to start. Challenges have hints and there's a big write-up community. I'd go there first after finishing Part 2.

crackmes.one isn't a tournament-style CTF, but it's an endless practice pool, filterable by difficulty 1 to 6 and by language. Each language part in this series should come with a few crackmes.one challenges in that same language.

Flare-On is Mandiant's annual RE contest, running a few weeks each year and getting harder with each challenge, covering all platforms (Windows native, .NET, Go, shellcode, obfuscation, sometimes even mobile and hardware). After each season Mandiant publishes the official solutions, so redoing old seasons with the official write-ups is a complete and free RE curriculum.

HackTheBox, Root-Me, and the CTFs on CTFtime are harder, for when you're solid.

Don't jump into a live CTF before you're used to it. Do old Flare-On seasons first, with answers to compare against. You learn much faster than sitting stuck alone on a live challenge.

## Methodology when opening a rev challenge

Every rev challenge asks one question, which is what input makes the program accept. The workflow below applies to almost every challenge, and it's the [reverse workflow](/posts/re-0-4-reverse-engineering-workflow-not-get-lost/) from Lesson 0.4 shortened for contests.

First, read the prompt and list the files. It sounds obvious but many people skip it. Does the prompt say "enter the correct flag", "find the password", or "decrypt the file"? Is there an attached file other than the binary (an encrypted file, a network capture)? The flag format is usually given (`flag{...}`, `CTF{...}`), so know it and you'll recognize it when you're close.

Second, triage. Drag it into Detect It Easy and note the file type, language, whether it is packed, and whether it is 32 or 64-bit. Run `strings`. This step decides which way you go, and it's where the language parts of the series pay off. See `.NET` and open dnSpy ([Part 5](/reverse-engineering/)), see Go and get GoReSym ready ([Part 8](/reverse-engineering/)), see `.pyc` and use pycdc ([Part 7](/reverse-engineering/)), see high entropy and unpack first ([Part 14](/reverse-engineering/)).

Third, find the win condition. Go backward from the "Correct" or "Wrong" string to the comparison function, or from the function that prints the flag. This is the string-first technique from [Lesson 0.4](/posts/re-0-4-reverse-engineering-workflow-not-get-lost/), and it solves most easy challenges on its own.

Fourth, pick the technique by the shape of the challenge. If the check logic can be read directly, read it statically and then invert it by hand or with Python ([Lesson 16.4](/posts/re-16-4-rewriting-algorithm-python-letting-z3-solve/)). With many constraints on the input bytes, throw it at Z3 or angr ([Lesson 18.3](/posts/re-18-3-symbolic-execution-making-computer-solve-crackme/)). For a complicated transform function that can be isolated, emulate it with Unicorn ([Lesson 18.2](/posts/re-18-2-emulation-running-piece-code-without-whole/)) instead of understanding it. If anti-debug blocks the way, redirect per [Part 15](/reverse-engineering/), or emulate to avoid a real debugger. And when you're totally stuck, run it dynamically and set a breakpoint at the final comparison, since often the correct flag shows up in plain view in a register.

Fifth, know when to drop a direction. If you're stuck 30 minutes on one approach, switch. The fast solver isn't smarter, he just abandons the wrong direction sooner.

## Writing a write-up

Solving and then forgetting is a waste. A write-up is how you pin it down, and a good one also helps others learn. A decent write-up starts with the challenge and environment, meaning challenge name, files, hashes, and tools used, so the reader can reproduce it. Then comes the triage, meaning what you recognized at the first step and why you chose that direction.

Next is the process, including the mistakes. This is the most valuable part and the one most often dropped. Don't just copy the straight path to the answer. Write down the directions you tried that failed and why they failed. Readers (and you, later) learn more from the wrong turns than from the polished solution. After that goes the solution and flag, with the script code if there is one, so it can be rerun. Finish with the lessons learned, in one or two sentences on what you will do differently next time you meet this kind of thing.

A write-up that only says "opened IDA, saw the flag, done" is useless. A write-up that says "I thought it was AES because I saw a 256-byte table, turns out it was RC4 because the table is initialized 0..255 and then permuted, which I recognized thanks to Lesson 16.2" teaches other people.

## What to expect

Flare-On challenge number 1 each season is usually solved in ten minutes. Challenges 10 and 11 can take a strong person a whole week. That's normal. The goal isn't to solve everything right away but to learn one more technique from each challenge. This year you're stuck on challenge 7, next year you get through it in one sitting, and that's measurable progress.

Read other people's write-ups after you've struggled enough on your own. Seeing how a strong person approached the same challenge you just solved with difficulty is one of the fastest ways to learn.

## Lab

The goal is to practice the rhythm of working a real reverse engineering challenge and to learn to write a write-up that keeps the knowledge. Pick a source, preferably one with an official solution so you can compare after doing it yourself. You can take an old Flare-On season (download the challenge from the official Flare-On site, flare-on.com, where earlier seasons have published PDF solutions), picoCTF in the Reverse Engineering category (choose by points, from low to high), or crackmes.one (filter difficulty 1 to 2 if you're just starting). Only use binaries provided by the competition or author for learning, and don't download commercial software to crack.

Choose a reasonable reverse engineering challenge, starting from the easiest one you haven't done. Apply the process from Lesson 20.2, which is to read the prompt, triage with DIE, identify the language and platform, go from the win/lose strings, and pick a technique. Solve until you get the flag, and write down every direction you tried, including the failed ones. Then write a write-up following the template in the solution below (the "write-up template" part). Only after you've solved it yourself, open the official solution (if there is one) and compare approaches.

Some questions to think about. Did the triage step help you rule out wrong directions early? Which direction did you try that failed, and what sign should have told you sooner? If you meet this kind of challenge again, what will you do differently? And a few hints. If you're stuck on static reading, switch to running it dynamically and set a breakpoint at the final comparison. If there are many constraints on the input, think of Z3 or angr before solving by hand. And always check the flag you found by entering it back into the program.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This is not an answer to one specific challenge (the one you pick will be different). It's a sample write-up so you can see the structure and voice. The content is based on a self-made crackme called `checkme` for illustration. Do your own challenge first, and only then read this sample to compare how it's presented.

## Write-up: checkme (a hypothetical crackme, level 2)

The file is `checkme` (ELF 64-bit, Linux). The tools are Detect It Easy, Ghidra and Python 3. The prompt says "Enter the right key to get the flag" and gives the format `flag{...}`.

For triage, I dragged it into DIE and it reported ELF x86-64, compiler GCC, not packed, normal entropy. `strings` shows two notable strings, `Correct! Here is your flag:` and `Wrong key.`. There's no plaintext key, so this isn't a straight string comparison. The triage conclusion is a native C binary with no protection, with the check logic in the code, so static reading is needed.

My first direction failed. I grepped for the string `Correct`, followed the xref to `main`, and saw it call `check_key(input)` and then branch. I assumed reading `check_key` would be all it took. Opening it, I found a loop that transforms each character and compares it with a constant array, but I misread the operation as XOR, so I tried decoding with XOR and got garbage. That cost about twenty minutes.

The turning point was rereading the assembly of the loop carefully instead of trusting the pseudocode. The real operation is `(c + i) ^ 0x3C`, not a plain XOR. The sign that should have told me sooner was an instruction in the decompiler that adds the index `i`, which I skipped over because I only skimmed.

For the solution, the expected constant array is in `.rodata`, 12 bytes. Since the transformation is reversible, I inverted it with `c = ((expected[i]) ^ 0x3C) - i`.

```python
expected = [0x6e, 0x08, 0x44, 0x5e, 0x6d, 0x5a, 0x45, 0x47, 0x51, 0x47, 0x07, 0x01]
key = "".join(chr(((b ^ 0x3C) - i) & 0xFF) for i, b in enumerate(expected))
print(key)   # R3v_Master12
```

It gives the key `R3v_Master12`, and entering it into `checkme` makes the program print `Correct! Here is your flag: flag{...}`. Confirmed.

Three lessons came out of it. Don't blindly trust pseudocode in the arithmetic part, and drop down to assembly when the decode result is garbage. An instruction adding the index `i` inside a loop is a sign of a position-dependent transformation, not a plain XOR. And always enter the key you found back into the program to confirm it, rather than trusting only your script.

## A write-up template to reuse

```
## Prompt and environment
File, hash, tools, goal.

## Triage
What you recognized in the first step, which direction you chose, and why.

## Process
The directions you tried, INCLUDING the failed ones and why they failed.
The "aha" moment that made everything clear.

## Solution
Reproducible code/script. The flag.

## Lessons learned
One or two sentences: what you would do differently next time with this kind of challenge.
```

</details>

## Key takeaways
Every rev challenge asks the same question, namely which input gets accepted. Always triage first to know which language/technique direction to use, since this is where the whole series comes together. Going from the win/lose string back to the check function is the fastest way into a challenge.

Pick the technique by the shape of the challenge, which can be reading by hand, Z3/angr, emulation, or debugging. If you're stuck on one direction, switch. A write-up must record the mistakes too, since that's the part that teaches the most.
