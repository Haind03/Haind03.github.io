---
title: "Reading list: the books behind these notes"
image:
  path: /assets/img/covers/re-resources-reading-list-windows-internals-books.webp
  alt: "Reading list: the books behind these notes"
date: 2023-07-29 10:20:00 +0700
categories: ["Technique Reverse", "Resources"]
tags: [reverse-engineering, resources, windows-internals]
render_with_liquid: false
---

A lot of the Technique Reverse series came from a small stack of books I kept going back to. None of them are light reading, but if you only pick up a few RE books, these are the ones I'd point you at. I've linked the publisher or author pages so you can get a proper copy.

## Windows Internals (6th edition, Part 1 and Part 2)

Mark Russinovich, David Solomon and Alex Ionescu, Microsoft Press. This is the book for understanding what Windows is doing underneath your debugger. Part 1 covers the system architecture, processes and threads, security and the I/O system, and Part 2 goes into memory management, storage, networking and boot. You don't read it cover to cover. I kept it open next to WinDbg and looked things up whenever a structure like the PEB or an object handle showed up in a sample and I didn't know what I was looking at. Newer editions exist and are worth getting if you're starting fresh. The book's home is on the [Sysinternals site](https://learn.microsoft.com/en-us/sysinternals/resources/windows-internals).

## Windows via C/C++ (5th edition)

Jeffrey Richter and Christophe Nasarre, Microsoft Press. Windows Internals explains the kernel side, this one is about the Win32 API from the programmer's side: processes, threads, synchronization, memory, DLLs and DLL injection. It's old, but when you reverse a Windows binary you're mostly reading calls into these APIs, and knowing how they're meant to be used makes the disassembly easier to follow.

## Practical Malware Analysis

Michael Sikorski and Andrew Honig, [No Starch Press](https://nostarch.com/malware). Still the best starting point for malware analysis, in my opinion. It covers static and dynamic analysis, IDA, OllyDbg, and then the tricks malware uses against you: anti-disassembly, anti-debugging, anti-VM and packers. The labs at the end of each chapter are what make it worth it, so do them. The anti-reverse part of my series (Part 15) leans on these chapters a lot.

## Practical Reverse Engineering

Bruce Dang, Alexandre Gazet and Elias Bachaalany, [Wiley](https://www.wiley.com/en-us/Practical+Reverse+Engineering-p-9781118787250). Denser than Practical Malware Analysis. It covers x86, x64 and ARM, then spends a big chunk on the Windows kernel and rootkits, and finishes with obfuscation. The exercises use real system binaries instead of toy samples. That's painful at first, but you learn to read code nobody wrote for you to read.

## Assembly Language for x86 Processors (7th edition)

Kip Irvine, Pearson ([author's site](https://asmirvine.com/)). A textbook rather than an RE book, but it's how I got comfortable with x86. If assembly still looks like noise to you, work through the first half of this and write small programs yourself. Part 1 of the series gets much easier after that.

## Other material

I also went through a set of Windows internals slides by EaZyq that cover processes and threads, memory management, DLLs, persistence techniques and payloads. It's a short overview you can read before opening the big books, though it isn't mine to share here.
