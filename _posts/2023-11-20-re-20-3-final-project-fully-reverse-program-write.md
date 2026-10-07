---
title: "Lesson 20.3: Final project, fully reverse a program and write the report"
date: 2023-11-20 22:22:00 +0700
categories: ["Technique Reverse", "Part 20 · Real-World Practice"]
tags: [reverse-engineering, ctf]
render_with_liquid: false
---
This is the last lesson of the whole series. Everything you learned from Part 0 until now, reading assembly, rebuilding structs, unpacking, getting past anti-debug, writing keygens, extracting configs, now comes together into one single job: take a program you've never seen the inside of, and tell other people how it works. Not a ten-minute crackme, but a target big enough that you have to plan, keep notes over several days, and then write it up as a report that others can read and understand.

Solving crackmes is a sprint. This project is a long run. They're different skills, and the real RE job lives in the long run.

## Pick the right target

Pick the wrong target and the whole project falls apart, either too easy so you learn nothing, or too hard so you give up halfway. A few reasonable and legal choices come to mind. You can use a program of your own: build it, throw away the source, and reverse it yourself. It sounds a bit fake, but you have the answer key to grade yourself, which is great for a first time. You can take a multi-layer crackme from crackmes.one at level 4 or above, the kind that has both a serial algorithm and a layer of protection. A large CTF rev challenge also works, for example a late-season Flare-On challenge (challenges 7 to 10 are often a whole real program). Or you can pick an open-source program, reverse it and then compare with the source to check whether you read it correctly.

A reminder of the boundary in [Lesson 0.2](/posts/re-0-2-legal-ethics-part-everyone-wants-skip/): don't pick a commercial product and crack it, and don't touch someone else's system without permission. This project is to prove your skills, not to cause trouble.

One sign of a right-sized target is that you finish triage in one evening and you're still curious, not discouraged.

## The project workflow

This is the [four-step process](/posts/re-0-4-reverse-engineering-workflow-not-get-lost/) from Part 0, but stretched out for a large target.

### 1. Define the scope and questions

Don't say "I'll reverse this whole program". A real program has thousands of functions, most of them libraries and boilerplate, and you don't need to read them all. Instead write down a few concrete questions. What algorithm does the program use to check the license? Where does it store data, and in what format? Which server does it talk to, and with what protocol? Are there any anti-analysis mechanisms?

With clear questions you know when you're done. Without questions, you'll read assembly until morning for nothing.

### 2. Triage

Apply [Lesson 2.1](/posts/re-2-1-five-minute-triage-die-strings-pe/): file type, language, compiler, packed or not, 32 or 64 bit, notable strings, imports. The triage result decides which toolset you use (dnSpy for .NET, JADX for Android, IDA/Ghidra for native, GoReSym for Go...). Record the file hash right away for later cross-checking.

### 3. Map the functionality

Before digging deep, draw the overall map. Find the real `main` ([Lesson 3.1](/posts/re-3-1-hello-world-under-microscope-finding-real/)), and work from important strings and imports to carve out the big functional blocks (initialization, UI, data handling, network, protection). Rename and annotate right in IDA/Ghidra as you understand things. The goal of this step isn't to understand every line, but to know "where the interesting part is" so the next step digs in the right place.

Tip: a simple block diagram drawn by hand or in a notes file, one line per block, pulls you out of the feeling of being lost in a sea of functions.

### 4. Deep analysis of the main components

Only now do you dig. For each question from step 1, go into the block you carved out and apply the right technique. For a check algorithm or crypto, identify constants ([Lesson 16.1](/posts/re-16-1-identifying-crypto-algorithms-by-their-constants/)) and rewrite in Python or solve with Z3 ([Lesson 16.4](/posts/re-16-4-rewriting-algorithm-python-letting-z3-solve/)). For a protection layer, unpack ([Part 14](https://github.com/Haind03/Technique-Reverse/tree/main/phan-14-packer-obfuscation)) and get past anti-debug ([Part 15](https://github.com/Haind03/Technique-Reverse/tree/main/phan-15-anti-reverse)). For a data format or protocol, rebuild the spec ([Lesson 18.7](/posts/re-18-7-reversing-network-protocols-proprietary-file-formats/)). And confirm hypotheses dynamically by setting breakpoints, looking at real values, or hooking with Frida ([Lesson 17.2](/posts/re-17-2-frida-full-inspecting-modifying-program-while/)).

Keep repeating static then dynamic then notes until you've answered all the questions.

### 5. Consolidate the findings

Once you've answered everything, stop digging and start writing. Gather the scattered notes into one coherent story: what this program is, how it works, where the notable points are.

## The structure of a good RE report

The report is the part many people skip and also the part that separates people who do this as a job from people who just play with tools. A function you understand but can't write up, three months later you may as well never have understood it. The standard outline has seven sections.

It opens with an executive summary: a few short paragraphs for people who won't read the technical parts, saying what this is, the main conclusion and how much it matters. Write this part last but put it first. Next comes methodology and tools, covering what you used and what environment you ran in (mention the isolated lab if it's malware), so others can reproduce it. Then sample information, meaning file name, size, hashes (MD5/SHA-256), file type, compiler and version, which is the target's identity.

After that comes the program architecture, the overall map of the components and how they connect, where a diagram is worth a thousand words. The detailed findings are the meat. Every finding comes with concrete evidence: function address, pseudocode screenshot, the key assembly snippet, values observed at runtime. The reader has to be able to follow along. If it's malware, add IOCs: hashes, domains, IPs, mutexes, registry keys, file paths, with YARA/Sigma if you have it ([Lesson 19.2](/posts/re-19-2-ioc-yara-capa-sigma-turning-sample/)). The report ends with conclusions and recommendations, which answer the original questions again, note what's still open, and give recommendations (patch the bug, block the IOCs, or directions for further analysis).

The golden rule is that every claim needs evidence. "The program encrypts with RC4" is just an empty sentence until you point out which address the KSA function is at. Don't guess and then write it as if proven.

The full template to fill in is at [labs/20.3/bao-cao-mau.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/20.3/bao-cao-mau.md).

## Key takeaways
Pick a right-sized and legal target, not too easy and not too hard. Start with concrete questions and don't take on "reverse everything". Triage, map, and only then dig deep in the right place, repeating static and dynamic.

Write a structured report with every claim backed by evidence (address, pseudocode, runtime value). If you can write it up, only then have you really understood it.

## Closing words

You've gone from opening IDA and panicking at a sea of assembly, to unpacking, getting past anti-debug, writing keygens, extracting C2 configs and writing a complete report yourself. That's a long road and you should be proud.

RE has no finish line. There's always a new packer, a new architecture, a more sophisticated protector. From here you choose a direction to go deeper: malware analysis and threat intel, vulnerability research and exploits, or mobile and games. Each direction is its own series worth a whole year. Just keep the habit of practicing steadily on [crackmes.one and Flare-On](/posts/re-resources-study-materials-places-practice/), and most important, keep the curiosity that brought you all the way here.

And remember [Lesson 0.2](/posts/re-0-2-legal-ethics-part-everyone-wants-skip/): this skill is powerful, use it for good things. Happy reversing.

## Common pitfalls
People dig too deep into library code unrelated to their questions and waste hours for nothing. They skip notes, so when it's time to write the report they have to start over. They draw conclusions without evidence, and the report loses its value. And they pick a target that's too ambitious and then give up.
