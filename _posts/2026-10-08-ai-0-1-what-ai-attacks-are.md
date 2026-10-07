---
title: "Lesson 0.1: What AI attacks are and how they differ"
image:
  path: /assets/img/covers/ai-0-1-what-ai-attacks-are.webp
  alt: "What AI attacks are and how they differ"
date: 2026-10-08 09:00:00 +0700
categories: ["LLM Security", "Part 00 · Getting Started"]
tags: [ai-security, llm, owasp, fundamentals]
render_with_liquid: false
---

When you first look at a chatbot application, it is easy to assume that attacking it means finding an SQL injection, a buffer overflow, or a bug in the web framework. Those issues still exist. The newest and most dangerous one sits somewhere less expected: **the plain human language you type into the chat box.** In an LLM application, natural language is an attack surface.

In short, **LLM application security studies what happens when untrusted data is fed into a model that does not doubt it, and the model's output is then trusted where it should not be.**

![What AI attacks are and how they differ](/assets/img/ai-vuln-tech/attack-surfaces.svg)
_The OWASP Top 10 for LLM sorted into three zones on the data flow._

## How it differs from traditional software security

Classic software vulnerabilities are usually **deterministic**. The same payload `' OR 1=1--` gives the same result every time. LLM vulnerabilities are **probabilistic**. With the same exploit prompt, the model is sometimes affected and sometimes not, depending on temperature, model version, and the random number generator. You get used to this early: we report "3 successes out of 5 attempts", not "vulnerable / not vulnerable".

The second difference is the one that matters most: **an LLM mixes instructions and data in a single stream of tokens.** A CPU knows which memory region is code and which is data (imperfectly, as buffer overflows show). An LLM has no such boundary. The developer's system prompt, the user's message, and the content of a web page the model just read all flow into the same token stream, and the model tries to follow all of them in the same way. This whole series follows from that fact (see [Lesson 1.5](/posts/ai-1-5-instructions-vs-data/)).

## The three attack-surface zones

However complex the application is, the attack surface always falls into three zones:

- **Input.** What the user types and, more importantly, whether any outside data reaches the prompt (RAG documents, a web page the agent just browsed, an email it just read). This is where direct and indirect prompt injection live.
- **The model and its data.** Where was the model downloaded from? Does it contain a backdoor (supply chain)? Has the training data or the RAG store been poisoned?
- **Output and actions.** Where does the model's output go? Is it printed straight into HTML (XSS), concatenated into an SQL query, or used to call a real tool (send mail, delete files)? How much authority does the model have?

The whole OWASP Top 10 for LLM is a detailed list of these three zones.

## OWASP Top 10 for LLM 2025: the map we will follow

The 2025 version (published at the end of 2024) contains:

| ID | Name | Zone |
|---|---|---|
| LLM01 | Prompt Injection | Input |
| LLM02 | Sensitive Information Disclosure | Input/Output |
| LLM03 | Supply Chain | Model |
| LLM04 | Data and Model Poisoning | Model |
| LLM05 | Improper Output Handling | Output |
| LLM06 | Excessive Agency | Output/actions |
| LLM07 | System Prompt Leakage | Input/Output |
| LLM08 | Vector and Embedding Weaknesses | Model (RAG) |
| LLM09 | Misinformation | Output |
| LLM10 | Unbounded Consumption | Resources |

Two entries are new compared with the 2023 version: **LLM07 System Prompt Leakage** and **LLM08 Vector and Embedding Weaknesses**. They reflect that RAG and agents are now the dominant architectures.

## Attacker, red team, or blue team?

This series does not teach you to break other people's chatbots. It teaches how to think in all three roles:

- **Attacker**, to understand how a payload works.
- **Red team**, to test your own organization's systems in an authorized and systematic way.
- **Blue team**, to know where to place defenses (hint: most of them belong in the application layer, not in the prompt).

The best practitioners can read all three. After breaking a lab, you have to patch it and break it again. That is why the labs follow a "build it, break it, fix it" loop.

## What the learning curve is really like

Some days you will type twenty variations of a payload and the model still refuses, and then the 21st, almost identical one, gets through. That is normal. Because the behavior is probabilistic, the skill here is **thinking about data flow and trust**, not memorizing a list of payloads. A payload gets patched once a new model is released. The question "is this data trustworthy at the place where it is used?" stays valid.

## Key takeaways
- LLM security = untrusted data going in + over-trusted output coming out.
- LLM vulnerabilities are probabilistic and measured by success rate.
- An LLM cannot separate instructions from data, which is the root of prompt injection.
- Three attack-surface zones: input, model, output/actions. The OWASP Top 10 is a detailed version of those three zones.

## Further reading
- [OWASP Top 10 for LLM 2025](https://genai.owasp.org/llm-top-10/)
- [MITRE ATLAS](https://atlas.mitre.org/)
