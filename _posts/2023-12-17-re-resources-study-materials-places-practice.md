---
title: "Study materials and places to practice"
image:
  path: /assets/img/covers/re-resources-study-materials-places-practice.webp
  alt: "Study materials and places to practice"
date: 2023-12-17 11:51:00 +0700
categories: ["Technique Reverse", "Resources"]
tags: [reverse-engineering, resources]
render_with_liquid: false
---
> Books, courses and places to keep learning on your own. You don't get good at RE by reading, you have to sit down and take apart real binaries, so the last section on practice grounds matters most.

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

OpenSecurityTraining2 (ost2.fyi) has free structured courses on x86/x64, PE, and debugging, and they're good quality. Malware Unicorn's RE101 and RE102 are a well-loved intro malware workshop. Nightmare (guyinatuxedo) is a CTF pwn/RE course through examples, open on github.

TryHackMe's Reverse Engineering track and HackTheBox Academy come with step-by-step guidance. pwn.college is a module-based learning platform, from basic to advanced, and free. For official documentation, look at the Ghidra docs, the Frida handbook (learnfrida.info), the angr docs, and the x64dbg wiki.

## YouTube channels and blogs

Channels include stacksmashing, LiveOverflow, OALabs, MalwareTech, John Hammond, GuidedHacking (games), and HackerSploit.

Blogs and sites include OALabs, the Hex-Rays blog, the Binary Ninja blog, 0x00sec, and tuts4you (a long-running RE forum with lots of unpacking tutorials). Flare-On writeups from past years are very good for learning, since fireeye/mandiant publishes official solutions after each season.

## Places to practice

Reading ten posts isn't worth as much as taking apart one binary yourself. These are ordered by increasing difficulty.

For gentle crackmes, crackmes.one is a huge crackme collection, filtered by difficulty 1 to 6 and by language/platform. Start from level 1. Reversing.kr is a classic set of RE challenges that gets harder as you go, and crackmes.de (an archive) is an old collection that still has lots of good ones.

For CTFs and wargames, picoCTF is education-oriented, with a Reverse Engineering section that suits beginners. pwnable.kr and pwnable.tw lean toward pwn but have many RE challenges. Root-Me has a clearly categorized Cracking section, and HackTheBox has a harder Reversing section for people who are already solid.

For real competitions, Flare-On is Mandiant's annual RE competition, lasting a few weeks each year, from easy to very hard. Redoing past seasons is a complete free RE curriculum. CTFs listed on CTFtime with a rev category are also worth doing.

For malware samples (only use them in an isolated lab, see [Lesson 0.3](/posts/re-0-3-set-up-safe-lab-before-touching/)), there are MalwareBazaar (abuse.ch), vx-underground, theZoo, and Malshare. You download real samples to practice analysis. Be very careful, because this is live malware.

For mobile, there are the OWASP UnCrackable Apps (Android and iOS), which have three levels and are included in the MASTG. DIVA and InsecureBankv2 are Android apps that are deliberately vulnerable.

## Communities to ask

There are Discord servers, the subreddits r/ReverseEngineering and r/malware, the forums tuts4you and 0x00sec, and the #malware and #RE communities on technical social networks.

## How to use this page

Don't try to take in everything. Here's a self-study path to go along with the series. Start taking apart crackmes.one level 1 as soon as you finish Part 2. After finishing each language part, find a crackme in that language and do it. When you feel confident enough, move on to picoCTF and then past Flare-On seasons. Whichever direction you follow, go deeper into the books and practice grounds for that direction.
