---
title: "Study materials and places to practice"
date: 2026-10-06 14:03:00 +0700
categories: ["Technique Reverse", "Resources"]
tags: [reverse-engineering, resources]
render_with_liquid: false
---
> A place to keep learning on your own and, more importantly, a place to practice by hand. You don't get good at RE by reading, you have to sit down and take apart real binaries. The last section is the practice grounds, and those should be the priority.

## Books worth reading

You don't need to read them all, pick by your direction.

| Book | For | Notes |
|---|---|---|
| **Practical Malware Analysis** (Sikorski & Honig) | People going into malware | A classic, lots of hands-on, with very good labs included |
| **Practical Reverse Engineering** (Dang, Gazet, Bachaalany) | Intermediate | x86/x64, kernel, anti-RE, VM |
| **The IDA Pro Book** (Chris Eagle) | IDA users | Still the most complete IDA reference |
| **Reversing: Secrets of Reverse Engineering** (Eldad Eilam) | Foundational intro | Old but the fundamentals are still right |
| **The Ghidra Book** (Eagle & Nance) | Ghidra users | The counterpart to the IDA Pro Book |
| **Practical Binary Analysis** (Dennis Andriesse) | Those who like automation, Linux | ELF, DBI, taint, symbolic |
| **Windows Internals** (Russinovich et al.) | Windows specialists | A reference for when you need to understand the OS deeply |
| **Rootkits and Bootkits** | Advanced, kernel/firmware | Once the basics are solid |
| **Android Security Internals** / **OWASP MASTG** | The mobile side | MASTG comes with UnCrackable practice apps |

## Free courses and materials

- **OpenSecurityTraining2** (ost2.fyi). Free structured courses on x86/x64, PE, debugging, genuinely high quality.
- **Malware Unicorn RE101 / RE102**. A very well-loved intro malware workshop.
- **Nightmare** (guyinatuxedo). A CTF pwn/RE course through examples, open on github.
- **TryHackMe** Reverse Engineering track, **HackTheBox Academy**. With step-by-step guidance.
- **pwn.college**. A module-based learning platform, from basic to advanced, free.
- **Official documentation**: Ghidra docs, the Frida handbook (learnfrida.info), angr docs, the x64dbg wiki.

## YouTube channels and blogs

Channels:
- **stacksmashing**, **LiveOverflow**, **OALabs**, **MalwareTech**, **John Hammond**, **GuidedHacking** (games), **HackerSploit**.

Blogs and sites:
- **OALabs**, **Hex-Rays blog**, **Binary Ninja blog**, **0x00sec**, **tuts4you** (a long-running RE forum, with lots of unpacking tutorials).
- Flare-On writeups from past years (fireeye/mandiant publishes official solutions after each season, extremely good for learning).

## Places to practice, the most important part

Reading ten posts isn't worth taking apart one binary yourself. Ordered by increasing difficulty:

**Intro, gentle crackmes:**
- **crackmes.one**. A huge crackme collection, filtered by difficulty 1 to 6 and by language/platform. Start from level 1, this is the best practice ground for beginners.
- **Reversing.kr**. A classic set of RE challenges, getting harder as you go.
- **crackmes.de** (archive). An old collection but still has lots of good ones.

**CTFs and wargames:**
- **picoCTF**. Education-oriented, with a Reverse Engineering section that suits beginners well.
- **pwnable.kr / pwnable.tw**. Leaning toward pwn but with many RE challenges.
- **Root-Me** Cracking section. Clearly categorized.
- **HackTheBox** Reversing section. Harder, for people who are already solid.

**Real competitions:**
- **Flare-On**. Mandiant's annual RE competition, lasting a few weeks each year, from easy to very hard. Redoing past seasons is a complete free RE curriculum.
- CTFs on **CTFtime** with a rev category.

**Malware samples (only use in an isolated lab, see [Lesson 0.3](/posts/tr-0-3-dung-lab-an-toan/)):**
- **MalwareBazaar** (abuse.ch), **vx-underground**, **theZoo**, **Malshare**. Download real samples to practice analysis. Be extremely careful, this is live malware.

**Mobile:**
- **OWASP UnCrackable Apps** (Android and iOS). Three levels, included in the MASTG.
- **DIVA / InsecureBankv2**. Android apps that are deliberately vulnerable.

## Communities to ask

- Discord/subreddits **r/ReverseEngineering**, **r/malware**.
- Forums **tuts4you**, **0x00sec**.
- The hashtags and communities **#malware**, **#RE** on technical social networks.

## How to use this page

Don't try to take in everything. A suggested self-study path alongside the series:
1. Start taking apart **crackmes.one level 1** as soon as you finish Part 2.
2. After finishing each language part, find a crackme in that language and do it.
3. When you feel confident enough, jump into **picoCTF** and then **past Flare-On seasons**.
4. Whichever direction you follow, dig deeper into the books and practice grounds for that direction.
