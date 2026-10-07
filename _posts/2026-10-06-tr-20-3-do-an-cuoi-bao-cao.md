---
title: "Lesson 20.3: Final project, fully reverse a program and write the report"
date: 2026-10-06 10:01:00 +0700
categories: ["Technique Reverse", "Part 20 · Real-World Practice"]
tags: [reverse-engineering, ctf]
render_with_liquid: false
---
This is the last lesson of the whole series. Everything you learned from Part 0 until now, reading assembly, rebuilding structs, unpacking, getting past anti-debug, writing keygens, extracting configs, now comes together into one single job: take a program you've never seen the inside of, and tell other people how it works. Not a ten-minute crackme, but a target big enough that you have to plan, keep notes over several days, and then write it up as a report that others can read and understand.

Solving crackmes is a sprint. This project is a long run. They're different skills, and the real RE job lives in the long run.

## Pick the right target

Pick the wrong target and the whole project falls apart, either too easy so you learn nothing, or too hard so you give up halfway. A few reasonable and legal choices:

- **A program of your own**, build it, throw away the source, and reverse it yourself. Sounds a bit fake, but you have the answer key to grade yourself, which is great for a first time.
- **A multi-layer crackme** from crackmes.one at level 4 or above, the kind that has both a serial algorithm and a layer of protection.
- **A large CTF rev challenge**, for example a late-season Flare-On challenge (challenges 7 to 10 are often a whole real program).
- **An open-source program**, reverse it and then compare with the source to check whether you read it correctly.

A reminder of the boundary in [Lesson 0.2](/posts/tr-0-2-phap-ly-dao-duc/): don't pick a commercial product and crack it, don't touch someone else's system without permission. This project is to prove your skills, not to cause trouble.

One sign of a right-sized target: you finish triage in one evening and you're still curious, not discouraged.

## The project workflow

This is the [four-step process](/posts/tr-0-4-quy-trinh-reverse/) from Part 0, but stretched out for a large target.

### 1. Define the scope and questions

Don't say "I'll reverse this whole program". A real program has thousands of functions, most of them libraries and boilerplate, and you don't need to read them all. Instead write down a few concrete questions, for example:

- What algorithm does the program use to check the license?
- Where does it store data, and in what format?
- Which server does it talk to, and with what protocol?
- Are there any anti-analysis mechanisms?

With clear questions you know when you're done. Without questions, you'll read assembly until morning for nothing.

### 2. Triage

Apply [Lesson 2.1](/posts/tr-2-1-triage-die-strings-pebear/): file type, language, compiler, packed or not, 32 or 64 bit, notable strings, imports. The triage result decides which toolset you use (dnSpy for .NET, JADX for Android, IDA/Ghidra for native, GoReSym for Go...). Record the file hash right away for later cross-checking.

### 3. Map the functionality

Before digging deep, draw the overall map. Find the real `main` ([Lesson 3.1](/posts/tr-3-1-hello-world-tim-main-that/)), and work from important strings and imports to carve out the big functional blocks (initialization, UI, data handling, network, protection). Rename and annotate right in IDA/Ghidra as you understand things. The goal of this step isn't to understand every line, but to know "where the interesting part is" so the next step digs in the right place.

Tip: a simple block diagram drawn by hand or in a notes file, one line per block, pulls you out of the feeling of being lost in a sea of functions.

### 4. Deep analysis of the main components

Only now do you dig. For each question from step 1, go into the block you carved out and apply the right technique:

- Check algorithm or crypto: identify constants ([Lesson 16.1](/posts/tr-16-1-nhan-dien-hang-so-crypto/)), rewrite in Python or solve with Z3 ([Lesson 16.4](/posts/tr-16-4-viet-lai-python-z3/)).
- Protection layer: unpack ([Part 14](https://github.com/Haind03/Technique-Reverse/tree/main/phan-14-packer-obfuscation)), get past anti-debug ([Part 15](https://github.com/Haind03/Technique-Reverse/tree/main/phan-15-anti-reverse)).
- Data format or protocol: rebuild the spec ([Lesson 18.7](/posts/tr-18-7-reverse-giao-thuc-dinh-dang-file/)).
- Confirm hypotheses dynamically: set breakpoints, look at real values, or hook with Frida ([Lesson 17.2](/posts/tr-17-2-frida-toan-tap/)).

Keep repeating static then dynamic then notes until you've answered all the questions.

### 5. Consolidate the findings

Once you've answered everything, stop digging and start writing. Gather the scattered notes into one coherent story: what this program is, how it works, where the notable points are.

## The structure of a good RE report

The report is the part many people skip and also the part that separates people who do this as a job from people who just play with tools. A function you understand but can't write up, three months later you may as well never have understood it. The standard outline:

1. **Executive summary.** A few short paragraphs for people who won't read the technical parts: what this is, the main conclusion, how much it matters. Write this part last but put it first.
2. **Methodology and tools.** What you used, what environment you ran in (mention the isolated lab if it's malware), so others can reproduce it.
3. **Sample information.** File name, size, hashes (MD5/SHA-256), file type, compiler, version. This is the target's identity.
4. **Program architecture.** The overall map of the components and how they connect. A diagram here is worth a thousand words.
5. **Detailed findings.** The meat. Every finding comes with concrete evidence: function address, pseudocode screenshot, the key assembly snippet, values observed at runtime. The reader has to be able to follow along.
6. **IOCs (if it's malware).** Hashes, domains, IPs, mutexes, registry keys, file paths, with YARA/Sigma if you have it ([Lesson 19.2](/posts/tr-19-2-ioc-yara-capa-sigma/)).
7. **Conclusions and recommendations.** Answer the original questions again, note what's still open, and give recommendations (patch the bug, block the IOCs, or directions for further analysis).

Golden rule: **every claim needs evidence.** "The program encrypts with RC4" is just an empty sentence until you point out which address the KSA function is at. Don't guess and then write it as if proven.

The full template to fill in is at [labs/20.3/bao-cao-mau.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/20.3/bao-cao-mau.md).

## Key takeaways
- Pick a right-sized and legal target, not too easy and not too hard.
- Start with concrete questions, don't take on "reverse everything".
- Triage, map, and only then dig deep in the right place, repeating static and dynamic.
- Write a structured report, every claim with evidence (address, pseudocode, runtime value).
- If you can write it up, only then have you really understood it.

## Closing words

You've gone from opening IDA and panicking at a sea of assembly, to unpacking, getting past anti-debug, writing keygens, extracting C2 configs and writing a complete report yourself. That's a long road and you should be proud.

RE has no finish line. There's always a new packer, a new architecture, a more sophisticated protector. From here you choose a direction to go deeper: malware analysis and threat intel, vulnerability research and exploits, or mobile and games. Each direction is its own series worth a whole year. Just keep the habit of practicing steadily on [crackmes.one and Flare-On](/posts/tr-tai-nguyen-tai-lieu-hoc/), and most important, keep the curiosity that brought you all the way here.

And remember [Lesson 0.2](/posts/tr-0-2-phap-ly-dao-duc/): this skill is powerful, use it for good things. Happy reversing.

## Common pitfalls
- Digging too deep into library code unrelated to your questions, wasting hours for nothing.
- Not taking notes, so when it's time to write the report you have to start over.
- Conclusions without evidence, the report loses its value.
- Picking a target that's too ambitious and then giving up.
