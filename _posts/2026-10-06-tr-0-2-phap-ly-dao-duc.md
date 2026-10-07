---
title: "Lesson 0.2: Legal and ethics, the part everyone wants to skip"
date: 2026-10-06 08:01:00 +0700
categories: ["Technique Reverse", "Part 00 · Getting Started"]
tags: [reverse-engineering, basics]
render_with_liquid: false
---
I know you want to jump straight into IDA. But this lesson decides whether you last in this field or get into trouble early, so read it once and be done.

RE techniques are neutral. The same unpack, hook or patch is a good thing when you use it to analyze malware and protect a company, and breaks the law when you use it to crack software that's sold commercially. The difference is in the purpose and permission, not in the tool.

## The general boundary

There's no single legal code for the whole world, every country is different, so this is a guiding principle and not legal advice.

What's usually accepted is reversing your own software, or software where the owner gave you written permission. Analyzing malware for defense, research and incident response is fine too, as is playing CTF, solving crackmes and using binaries made for learning. Research for interoperability is conditionally exempted by law in many places. And if you find vulnerabilities, you can report them responsibly (coordinated disclosure) through a bug bounty program or by contacting the vendor.

What's easy to get into trouble with is cracking, patching licenses or sharing cracks of commercial software, and bypassing DRM and then distributing the content. Reversing someone else's system without permission is risky even "just to look". The same goes for breaking terms of use (EULA/ToS), especially in online games and cloud services, and for publishing a 0-day with a working exploit before the vendor has a chance to patch.

"I'm just learning" is not a legal shield. Distributing tools or patches is where the line gets crossed, not when you sit reading code alone.

## A few legal frameworks worth knowing by name

You don't need to memorize them, just know the names so you know where to look when needed. DMCA section 1201 in the US prohibits circumventing technical protection measures, but has exceptions for security research, interoperability and education, and those exceptions are reviewed periodically. The CFAA in the US covers unauthorized access to computer systems. The EU Software Directive allows decompilation for interoperability under certain conditions.

Vietnam and many other countries have their own intellectual property and cybersecurity laws. Nobody will arrest you for reversing to learn, but distributing a crack is clearly copyright infringement.

The message isn't "the law is complicated so don't bother learning", it's "know where you're standing".

## Professional ethics, what the law doesn't write down

The law sets the floor. People who do this job decently set a higher bar. Get permission before touching someone else's system, since a saved permission email is your best friend. Keep the infection chain clean when analyzing malware, with an isolated lab and never letting the sample escape onto the real network. Lesson [0.3](/posts/tr-0-3-dung-lab-an-toan/) covers this in detail.

If you find a vulnerability, report it. Don't sell it on the black market and don't post it to show off with an exploit. Give the vendor time to patch (usually 90 days) and only then publish the details. And don't teach others to do what you wouldn't sign your name to.

## Where this series stands

All the hands-on lessons in this series use one of three things, with no exceptions: crackmes and CTF binaries made by me or the community for learning, small programs we write ourselves and then reverse ourselves, or public malware samples used in an isolated lab for defensive purposes.

No lesson teaches how to crack a specific commercial product. If you plan to use the skills you learn here to crack software that's sold commercially, the rest of the series isn't for you, and I can't help you when something goes wrong.

## Key takeaways
Techniques are neutral, and purpose and permission decide right from wrong. Reversing your own stuff, CTF and defensive malware work are safe, while distributing cracks or bypassing DRM to distribute are illegal.

If you find a vulnerability, report it responsibly and don't rush to publish an exploit. When in doubt, get written permission first.
