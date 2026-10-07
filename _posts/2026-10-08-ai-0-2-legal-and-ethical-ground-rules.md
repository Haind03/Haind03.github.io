---
title: "Lesson 0.2: Legal and ethical ground rules"
image:
  path: /assets/img/covers/ai-0-2-legal-and-ethical-ground-rules.webp
  alt: "Legal and ethical ground rules"
date: 2026-10-08 09:20:00 +0700
categories: ["AI Vuln Tech", "Part 00 · Getting Started"]
tags: [ai-security, llm, owasp, ethics]
render_with_liquid: false
---

This is the least exciting part of the series, but skipping it can cost you a banned account, money, or legal trouble. Read it once and keep it in mind.

![Legal and ethical ground rules](/assets/img/ai-vuln-tech/where-to-practice.svg)
_Systems you may practice on, and systems you may not._

## The boundary in one sentence
**You may only attack systems you own, or systems whose owner has given you written permission, within the scope that document states.** There is no exception for "just trying it for fun".

## Why LLMs make it easy to cross the line

Public chatbots are everywhere, and "attacking" one takes a few typed sentences, so it feels harmless. It is not:

- Sending an exploit payload to a company's chatbot is **unauthorized access** under the laws of many countries (in Vietnam, the cybercrime articles of the Criminal Code; in the US, the CFAA, and so on).
- Using **unbounded consumption** techniques (Lesson 8) against a real service is a denial-of-service attack and causes real financial damage to the owner.
- Extracting other users' data through a vulnerability is a personal data violation (in Vietnam, Decree 13/2023 on personal data protection).

## Where you are allowed to practice

1. **Your own labs.** The whole series uses these. The app runs locally, the model runs locally, and nobody else is affected.
2. **Your organization's systems**, when you have written red team authorization that states the scope and the time window.
3. **Bug bounty programs with AI/LLM terms.** Read the scope carefully. Many programs exclude "model safety/jailbreak" and accept only application vulnerabilities (for example, output handling that leads to a real XSS).
4. **CTFs and wargames** built for this purpose.

## Responsible red teaming

If you red team an LLM system legally:

- **Stay in scope.** Touch only the accounts, data, and endpoints listed in the scope.
- **Minimize real data.** When you prove a data leak, take one sample that is enough to show the problem, then stop. Do not collect everything.
- **Do not break the service.** Test unbounded consumption on staging, or at an agreed rate, and never hammer production.
- **Report responsibly (coordinated disclosure).** Send the report privately to the vendor and give them time to patch before publishing. Do not post a 0-day payload together with the victim's name.

## Ethics of publishing payloads

This series describes payloads. When you write your own blog posts or training material:

- Demonstrate on your own lab and remove details that identify a real system.
- Describe the **vulnerability class and the fix**, not only a payload string for others to copy and misuse.
- Consider the harm. A jailbreak that makes a model swear is very different from a technique that makes an agent delete customer data.

## Key takeaways
- Attack only your own systems, or systems you have written permission for, within the stated scope.
- A public chatbot is still someone else's system, so it is not a place to practice.
- A local lab is a safe place to try any payload.
- Red team rules: stay in scope, minimize real data, do not disrupt the service, and disclose responsibly.
