---
title: "Lesson 0.2: Legal and ethics"
image:
  path: /assets/img/covers/re-0-2-legal-ethics-part-everyone-wants-skip.webp
  alt: "Lesson 0.2: Legal and ethics"
date: 2022-01-19 14:56:00 +0700
categories: ["Technique Reverse", "Part 00 · Getting Started"]
tags: [reverse-engineering, basics]
render_with_liquid: false
---
I know you want to jump straight into IDA. But this lesson decides whether you last in this field or get into trouble early, so read it once and be done.

RE techniques are neutral. The same unpack, hook or patch is fine when you use it to analyze malware and protect a company, and illegal when you use it to crack commercial software. The difference is the purpose and the permission, not the tool.

## The general boundary

There's no single legal code for the whole world and every country is different, so take this as a rule of thumb and not legal advice.

What's usually accepted is reversing your own software, or software where the owner gave you written permission. Analyzing malware for defense, research and incident response is fine too, and so is playing CTF, solving crackmes and using binaries made for learning. Research for interoperability is conditionally exempted by law in many places. If you find a vulnerability, you can report it responsibly (coordinated disclosure) through a bug bounty program or by contacting the vendor.

What gets people in trouble is cracking, patching licenses or sharing cracks of commercial software, and bypassing DRM and then distributing the content. Reversing someone else's system without permission is risky even "just to look". Breaking terms of use (EULA/ToS) is a problem too, especially in online games and cloud services. So is publishing a 0-day with a working exploit before the vendor has a chance to patch.

"I'm just learning" does not protect you legally. The line gets crossed when you distribute tools or patches, not when you sit reading code alone.

## A few legal frameworks worth knowing by name

You don't need to memorize them. Just know the names so you know where to look later. DMCA section 1201 in the US prohibits circumventing technical protection measures, but has exceptions for security research, interoperability and education, and those exceptions are reviewed periodically. The CFAA in the US covers unauthorized access to computer systems. The EU Software Directive allows decompilation for interoperability under certain conditions.

Vietnam and many other countries have their own intellectual property and cybersecurity laws. Nobody will arrest you for reversing to learn, but distributing a crack is clearly copyright infringement.

I'm not saying the law is too complicated to bother with. I'm saying you should know where you're standing.

## Professional ethics

The law sets the floor. People who do this job decently set a higher bar. Get permission before touching someone else's system, and keep the permission email somewhere safe. Keep your malware analysis contained, with an isolated lab, and never let a sample get onto the real network. Lesson [0.3](/posts/re-0-3-set-up-safe-lab-before-touching/) covers this in detail.

If you find a vulnerability, report it. Don't sell it on the black market and don't post it with an exploit to show off. Give the vendor time to patch (usually 90 days) and only then publish the details. And don't teach others to do what you wouldn't sign your name to.

## Where this series stands

All the hands-on lessons in this series use one of three things, no exceptions, which are crackmes and CTF binaries made by me or the community for learning, small programs we write ourselves and then reverse, or public malware samples used in an isolated lab for defensive purposes.

No lesson teaches how to crack a specific commercial product. If you plan to use these skills to crack commercial software, the rest of the series isn't for you, and I can't help you when something goes wrong.

## Key takeaways
Techniques are neutral, and purpose and permission decide what's right. Reversing your own stuff, CTF and defensive malware work are safe. Distributing cracks, or bypassing DRM to distribute content, is illegal.

If you find a vulnerability, report it responsibly and don't rush to publish an exploit. When in doubt, get written permission first.
