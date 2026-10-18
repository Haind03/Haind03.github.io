---
title: "Lesson 11.1: CTF practice and resources"
image:
  path: /assets/img/covers/ai-11-1-ctf-and-resources.webp
  alt: "CTF practice and resources"
date: 2026-10-08 16:10:00 +0700
categories: ["LLM Security", "Part 11 · Hands-on"]
tags: [ai-security, llm, owasp, ctf, resources]
render_with_liquid: false
---

By now you have worked through all ten OWASP entries and the newer techniques layered on top of them. The next step is to take that skill somewhere real, which means somewhere you are actually allowed to attack. The LLM security community has built plenty of legal arenas for exactly this, and the one hard rule is the same as it was in [Lesson 0.2](/posts/ai-0-2-legal-and-ethical-ground-rules/). Practice on systems you own, or on systems where you have written permission inside a stated scope.

This lesson maps the legal places to practice, explains how AI bug bounty scope actually works (it is narrower than most people expect), and shows how to write an LLM vulnerability report that someone will take seriously.

![From practice arena to a report that counts](/assets/img/ai-vuln-tech/practice-to-report.svg)
_Skills built in your own labs go out to legal arenas; a bug bounty scope filter keeps only application-layer impact, and that becomes a report that counts._

## Legal places to practice

These arenas were built to be attacked, so you can send your worst payloads without harming anyone.

- **Gandalf by Lakera.** A classic web game for prompt injection and leaking. You coax a secret password out of the model one level at a time, and each level adds a new defense. It is a good way to feel the families of technique from direct prompt injection (Lesson 3.1).
- **HackAPrompt and prompt-injection challenges.** Organized competitions and challenge sets that let you work through injection techniques systematically rather than ad hoc.
- **CTFs with an AI/LLM category.** More and more CTFs add LLM tasks such as jailbreaks, system prompt leaks and RAG poisoning. Watch the calendar on [CTFtime](https://ctftime.org/) and look for the AI or LLM tags.
- **DEF CON AI Village and similar villages.** Controlled, organized red-team-the-model events where getting the model to misbehave is the point.
- **Your own labs.** The scaffold that ships with this roadmap is always the safest arena. You can change the model, the temperature and the system prompt freely, and nothing leaves your machine.

The common thread is that all of these exist in order to be attacked. That is exactly what separates them from somebody's production chatbot. A public chatbot is still someone else's system, even when it looks like a harmless toy, and attacking it is the same as attacking any other production service. Do not confuse the two (Lesson 0.2).

## AI/LLM bug bounty: read the scope first

Many programs now advertise an AI category, but the scope varies a lot, and it is usually narrower than newcomers expect.

- **Usually out of scope.** Pure "model safety" or jailbreaking, meaning you got the model to say something offensive or against its own policy. Most programs treat this as a content-safety matter, not a security vulnerability, and it does not earn a reward.
- **Usually accepted.** Application-layer bugs with real impact. Improper output handling that leads to actual XSS or SSRF (Lesson 4.1), excessive agency that leads to an unauthorized action or access (Lesson 5.1), or a leak of another user's data.
- **Always read the "out of scope" section and stay inside it.** Test only what is in scope, stop the moment you have proven the issue, and never vacuum up real user data to make a point (Lesson 0.2).

The dividing line is the same one from the threat model in [Lesson 0.4](/posts/ai-0-4-threat-model-llm-app/). The question a triager is really asking is not "did the model misbehave" but "did that misbehavior cross an application boundary and cause real damage". A rude sentence stays inside the model. An `onerror` handler that runs in another user's authenticated session does not.

## Writing a good LLM vulnerability report

Because LLM behavior is probabilistic (Lesson 1.1), an LLM report cannot read like an ordinary bug report. "It always works" is not true, and a triager knows it is not true, so a report that claims it loses credibility immediately. A good report has five parts.

- **Success rate.** State it as a measurement, for example "this payload succeeded 4 out of 5 times", not "it always works".
- **Configuration.** Model and version, temperature, and the seed if one is available. Without this the number is meaningless, because the same payload behaves differently at a different temperature.
- **Minimal repro.** The shortest sequence of steps or the shortest payload that reproduces the issue, with logs or screenshots.
- **Application-layer impact.** Spell out exactly which output or action turned into real damage. Do not stop at "the model said something bad".
- **A fix worth the name.** Recommend a hard control in the application layer (Lesson 2.4), such as escaping the output or authorizing the tool call, not just "tweak the system prompt".

A concrete report skeleton makes the shape obvious:

```text
Title:  Stored XSS via unescaped LLM output in document summary
Model:  qwen2.5:3b (Ollama), temperature 0.7, seed 42
Rate:   4/5 attempts

Steps:
  1. Upload a document containing:
     <img src=x onerror=alert(document.domain)>
  2. Ask the assistant to summarize the document.
  3. The summary is rendered as raw HTML in the chat pane,
     so the onerror handler runs.

Impact: script executes in the victim's authenticated session (XSS),
        session theft and actions on their behalf are possible.

Fix:    escape model output before rendering; never use innerHTML.
        Prompt wording alone does not remove this (soft control).
```

Notice how little of that is about the model. The jailbreak or injection is only the delivery mechanism. The thing that makes it a reportable vulnerability is where the output lands.

| Weak report | Report that counts |
|---|---|
| "The jailbreak always works" | "Succeeds 4/5 at temperature 0.7, seed 42" |
| No model or settings given | Model, version, temperature, seed listed |
| "The model said something harmful" | Output rendered as XSS in the victim's session |
| "Improve the system prompt" | Escape output or authorize the tool in the app layer |

## The capstone: an LLM01-LLM10 summary

Finish the roadmap with the summary exercise in the misinformation lab (`labs/lab08`). Write a `notes/summary.md` in which, for each of LLM01 through LLM10, you record two or three sentences: what the vulnerability is, how you exploited it, and the single most effective defense and why.

For almost every entry, that most effective defense will be a **hard control in the application layer**, one that removes the class of bug, rather than a **soft control in the prompt**, which only reduces the odds (Lesson 0.4). Writing this down for all ten is the step that turns "I read the blog" into "I understand it", and it doubles as the skeleton for your own writeup or conference talk. The [OWASP GenAI Security Project](https://genai.owasp.org/) keeps the canonical list current, so check it against your notes when you are done.

## Key takeaways

- Practice only in arenas built to be attacked, such as Gandalf, HackAPrompt, CTFs with an LLM category and AI Village, and in your own labs. A public chatbot is someone else's production system.
- In bug bounty, a pure jailbreak is usually out of scope. What pays is application-layer impact such as XSS, SSRF, an unauthorized action, or a leak of another user's data. Read the scope before you touch anything.
- An LLM report needs a success rate and the full configuration (model, version, temperature, seed), because the behavior is probabilistic.
- Recommend a hard control in the application layer, not a prompt tweak, and show the real impact instead of just a bad sentence.
- Close the roadmap with an LLM01-LLM10 summary. It turns reading into understanding and seeds your first writeup or talk.
