---
title: "Lesson 20.2: Solving RE challenges in CTFs and writing a decent write-up"
date: 2023-12-24 15:34:00 +0700
categories: ["Technique Reverse", "Part 20 · Real-World Practice"]
tags: [reverse-engineering, ctf]
render_with_liquid: false
---
After nineteen parts, you have enough tools and techniques. One thing is missing: the rhythm of solving for real under pressure, when nobody tells you in advance what language the challenge uses, which packer, or where the flag is hidden. CTFs are where you train that, and a write-up is how you turn one solve into knowledge you keep. This lesson covers both.

## Where to play

Not every arena suits beginners. Sorted by difficulty and purpose, picoCTF is education-oriented, and its Reverse Engineering category is great for starting. Challenges have hints and there's a big write-up community. This is the first place to go after finishing Part 2.

crackmes.one isn't a tournament-style CTF, but it's an endless practice pool, filterable by difficulty 1 to 6 and by language. Each language part in this series should come with a few crackmes.one challenges in that same language.

Flare-On is Mandiant's annual RE contest, running a few weeks each year and getting harder with each challenge, covering all platforms (Windows native, .NET, Go, shellcode, obfuscation, sometimes even mobile and hardware). The golden point is that after each season Mandiant publishes the official solutions. Redoing old seasons with the official write-ups is a complete and free RE curriculum.

HackTheBox, Root-Me, and the CTFs on CTFtime are harder, for when you're solid.

Honest advice: don't jump into a live CTF before you're used to it. Do old Flare-On seasons first, with answers to compare against, you learn much faster than sitting stuck alone on a live challenge.

## Methodology when opening a rev challenge

Every rev challenge is, at heart, asking one question: "what input makes the program accept". The workflow below applies to almost every challenge, and it's the [reverse workflow](/posts/re-0-4-reverse-engineering-workflow-not-get-lost/) from Lesson 0.4 squeezed down for the contest setting.

First, read the prompt and list the files. Sounds obvious but many people skip it. Does the prompt say "enter the correct flag", "find the password", or "decrypt the file"? Is there an attached file other than the binary (an encrypted file, a network capture)? The flag format is usually given (`flag{...}`, `CTF{...}`), so know it and you'll recognize it when you're close.

Second, triage. Drag it into Detect It Easy: file type, language, packed or not, 32 or 64-bit. Run `strings`. This step decides which way you go, and it's where the whole language stretch of the series pays off. See `.NET` and open dnSpy ([Part 5](https://github.com/Haind03/Technique-Reverse/tree/main/phan-05-csharp-dotnet)), see Go and get GoReSym ready ([Part 8](https://github.com/Haind03/Technique-Reverse/tree/main/phan-08-go)), see `.pyc` and use pycdc ([Part 7](https://github.com/Haind03/Technique-Reverse/tree/main/phan-07-python)), see high entropy and unpack first ([Part 14](https://github.com/Haind03/Technique-Reverse/tree/main/phan-14-packer-obfuscation)).

Third, find the win condition. Go backward from the "Correct" or "Wrong" string to the comparison function, or from the function that prints the flag. This is the string-first technique from [Lesson 0.4](/posts/re-0-4-reverse-engineering-workflow-not-get-lost/), effective enough that it solves most easy challenges on its own.

Fourth, pick the technique by the shape of the challenge. If the check logic can be read straight out, read it statically and then invert it by hand or with Python ([Lesson 16.4](/posts/re-16-4-rewriting-algorithm-python-letting-z3-solve/)). With many constraints on the input bytes, throw it at Z3 or angr ([Lesson 18.3](/posts/re-18-3-symbolic-execution-making-computer-solve-crackme/)). For a complicated transform function that can be isolated, emulate it with Unicorn ([Lesson 18.2](/posts/re-18-2-emulation-running-piece-code-without-whole/)) instead of understanding it. If anti-debug blocks the way, redirect per [Part 15](https://github.com/Haind03/Technique-Reverse/tree/main/phan-15-anti-reverse), or emulate to avoid a real debugger. And when you're totally stuck, run it dynamically and set a breakpoint at the final comparison, since often the correct flag shows up naked in a register.

Fifth, know when to drop a direction. Stuck 30 minutes on one approach, switch approaches, don't keep punching. The fast solver isn't the smarter one but the one who abandons the wrong direction sooner.

## Writing a write-up, the part that turns a solve into knowledge

Solving and then forgetting is a waste. A write-up is how you pin it down, and a good one also helps others learn. A decent write-up starts with the challenge and environment: challenge name, files, hashes, and tools used, so the reader can reproduce it. Then comes the triage, meaning what you recognized at the first step and why you chose that direction.

Next is the process, including the mistakes. This is the most valuable part and the one most often dropped. Don't just copy the straight path to the answer. Write down the directions you tried that failed and why they failed. Readers (and you, later) learn more from the wrong turns than from the polished solution. After that goes the solution and flag, with the script code if there is one, so it can be rerun. Finish with the lessons learned, in one or two sentences: next time I meet this kind of thing, what will I do differently.

A write-up that only says "opened IDA, saw the flag, done" is useless. A write-up that says "I thought it was AES because I saw a 256-byte table, turns out it was RC4 because the table is initialized 0..255 and then permuted, which I recognized thanks to Lesson 16.2" teaches other people.

## The reality of the road

Flare-On challenge number 1 each season is usually solved in ten minutes. Challenges 10 and 11 can eat a whole week of a strong person. That's normal. The goal isn't to solve everything right away but to learn one more technique from each challenge. This year you're stuck on challenge 7, next year you get through it in one sitting, that's measurable progress.

And don't hesitate to read other people's write-ups after you've struggled enough on your own. Seeing how a strong person approached the same challenge you just solved painfully is one of the fastest ways to learn in this trade.

## Lab
The folder is `labs/20.2/`. The task is to pick an old Flare-On challenge (or a picoCTF challenge in the Reverse Engineering category), solve it yourself, then write a write-up following the template in `labs/20.2/solution.md`. Compare with the official solution after you've finished on your own.

## Key takeaways
Every rev challenge asks the same question: which input gets accepted. Always triage first to know which language/technique direction to use, since this is where the whole series converges. Going from the win/lose string back to the check function is the fastest way into a challenge.

Pick the technique by the shape of the challenge: reading by hand, Z3/angr, emulation, or debugging. If you're stuck on one direction, switch, don't keep punching. A write-up must record the mistakes too, since that's the part that teaches the most.
