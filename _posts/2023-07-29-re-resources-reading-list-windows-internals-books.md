---
title: "Reading list: the books behind these notes"
date: 2023-07-29 10:20:00 +0700
categories: ["Technique Reverse", "Resources"]
tags: [reverse-engineering, resources, windows-internals]
render_with_liquid: false
---

A lot of what ended up in the Technique Reverse series came from a small stack of books I kept going back to. None of them are light reading, but if you only ever pick up a few RE books, these are the ones I'd point you at. I've linked the publisher or author pages so you can get a proper copy.

## Windows Internals (6th edition, Part 1 and Part 2)

Mark Russinovich, David Solomon and Alex Ionescu, Microsoft Press. This is the book for understanding what Windows is actually doing underneath your debugger. Part 1 covers the system architecture, processes and threads, security and the I/O system, and Part 2 goes into memory management, storage, networking and boot. You don't read it cover to cover. I kept it open next to WinDbg and looked things up whenever a structure like the PEB or an object handle showed up in a sample and I didn't know what I was looking at. Newer editions exist and are worth getting if you're starting fresh. The book's home is on the [Sysinternals site](https://learn.microsoft.com/en-us/sysinternals/resources/windows-internals).

## Windows via C/C++ (5th edition)

Jeffrey Richter and Christophe Nasarre, Microsoft Press. Where Windows Internals explains the kernel side, this one is about the Win32 API from the programmer's seat: processes, threads, synchronization, memory, DLLs and DLL injection. It's old, but when you're reversing a Windows binary you're mostly reading calls into exactly these APIs, and seeing how they're meant to be used makes the disassembly a lot easier to follow.

## Practical Malware Analysis

Michael Sikorski and Andrew Honig, [No Starch Press](https://nostarch.com/malware). Still the best starting point for malware analysis in my opinion. It walks through static and dynamic analysis, IDA, OllyDbg, and then the tricks malware uses against you: anti-disassembly, anti-debugging, anti-VM and packers. The labs at the end of each chapter are what make it worth it, so actually do them. The anti-reverse part of my series (Part 15) leans on these chapters a lot.

## Practical Reverse Engineering

Bruce Dang, Alexandre Gazet and Elias Bachaalany, [Wiley](https://www.wiley.com/en-us/Practical+Reverse+Engineering-p-9781118787250). Denser than Practical Malware Analysis. It covers x86, x64 and ARM, then spends a big chunk on the Windows kernel and rootkits, and finishes with obfuscation. The exercises use real system binaries instead of toy samples, which is painful at first but teaches you to read code you didn't write for you.

## Assembly Language for x86 Processors (7th edition)

Kip Irvine, Pearson ([author's site](http://asmirvine.com/)). A textbook rather than an RE book, but it's how I got comfortable with x86 in the first place. If assembly still feels like noise, working through the first half of this, writing small programs yourself, makes Part 1 of the series much easier.

## Other material

I also went through a set of Windows internals slides by EaZyq that cover processes and threads, memory management, DLLs, persistence techniques and payloads. It's a nice short overview before opening the big books, though it isn't mine to share here.
