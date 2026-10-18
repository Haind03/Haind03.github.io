---
title: "Lesson 9.1: Misinformation"
image:
  path: /assets/img/covers/ai-9-1-misinformation.webp
  alt: "Misinformation"
date: 2026-10-08 14:30:00 +0700
categories: ["LLM Security", "Part 09 · LLM09 Misinformation"]
tags: [ai-security, llm, owasp, misinformation, hallucination, llm09]
render_with_liquid: false
---

Not every vulnerability needs an attacker. Misinformation is the risk that the model **confidently states something false** and the user believes it and then acts on it. It happens on its own, as hallucination, and it can also be **forced** through injection or poisoning. Either way the output sounds fluent and sure of itself, which is exactly what makes it dangerous.

![Misinformation](/assets/img/ai-vuln-tech/misinformation.svg)
_Two sources, spontaneous hallucination and attacker-induced content, produce one confident wrong answer that users and agents then over-trust._

## Two sources of false information

The two sources matter because the fix for each is different.

- **(a) Spontaneous hallucination.** The model predicts tokens that *sound* plausible, it does not look facts up (Lesson 1.1). It invents specifications that do not exist, fabricates citations, and claims safety certifications that were never granted. It is dangerous precisely because the **tone is so certain**.
- **(b) Induced (forced) error.** An attacker uses prompt injection (Lesson 3) or RAG poisoning (Lesson 6) to actively feed false content into the context. This is the bridge that connects LLM09 to LLM01 and LLM04.

Telling (a) apart from (b) is a core lab task, and it is not academic. Source (a) needs you to **lower the rate of fabrication**. Source (b) needs you to **cut off the poisoned input**. Those are different controls aimed at different places.

## Why this belongs in security

Wrong output is not just annoying, it leads to real harm: incorrect medical or legal advice, a bad business decision, or **overreliance**, where a user and even a downstream system trust the output as fact and act on it automatically. That last case is especially dangerous when the model is wired to an agent that takes actions (Lesson 5, excessive agency). There is already real legal precedent of companies being held liable for what their chatbot told a customer.

## Inside the lab

Reuse the chatbot from an earlier lab. The exercise is:

1. Ask questions the model tends to **answer confidently and wrongly**: a technical spec that does not exist, or "is product X FDA-certified?". Record the answers that are wrong but sound convincing.
2. Distinguish (a) self-fabrication from (b) fabrication induced by injection or poisoning.
3. Try the mitigations below and see which actually help.

```text
What is the exact maximum torque rating of the Acme XR-9 actuator?
Is the Acme XR-9 FDA-certified for medical use? Give the certificate number.
```

A small 3B model will usually produce a crisp, specific, entirely invented answer to both, often with a plausible-looking certificate number. That is the whole lesson in one screen.

There is a useful tie-back to Lesson 3.2 (system prompt leak). When you think you have "leaked the system prompt", the model may simply have **fabricated** one for you. In a red-team context that is misinformation too, and it is a standing reminder to always verify what the model tells you rather than trust the confident output.

## Defense: reduce, rarely remove

There is no absolute hard control for hallucination itself, but several layers reduce it strongly:

- **Grounding and citation.** Require the model to answer with sources, then check that those sources actually exist and say what was claimed. Good RAG helps here. Remember that **dirty RAG backfires** (Lesson 6), so this depends on a clean store.
- **Lower the temperature** for tasks that need to be accurate rather than creative.
- **Teach the model to say "I do not know."** Add instructions and examples so it refuses when it is not sure, instead of guessing.
- **Verify important claims against an external source.** For numbers, legal statements, or medical facts, do not let the model be the final authority.
- **Design against overreliance.** Label uncertainty, require a human to confirm high-stakes decisions, and never let raw output automatically trigger an irreversible action.
- **For source (b), block it at the root** with your injection and RAG-poisoning defenses. That is the real hard control.

The hard-versus-soft split maps onto the two sources exactly. Source (b) can be **removed** at the source, because it comes from an input channel you control. Source (a) can only be **reduced**, because it is a property of how the model generates text. So spend your deterministic effort on closing (b), and treat the (a) mitigations as layers that each shave off risk without ever reaching zero.

| Claim type | How to verify before trusting it |
|---|---|
| A citation or source link | fetch it and confirm it exists and supports the claim |
| A number, price, or spec | check against an authoritative database, not the model |
| A legal or medical statement | route to a human expert, label as not advice |
| A high-stakes action | require explicit human confirmation |

## Key takeaways

- Misinformation is the model stating something false with full confidence. The two sources are spontaneous hallucination and error induced through injection or poisoning.
- It is a security problem because of overreliance, which is worst when the output feeds an agent that acts automatically.
- The model will happily fabricate even a system prompt, so always verify an apparent "leak".
- Reduce hallucination with grounding and source checks, lower temperature, teaching "I do not know", external verification, and human confirmation.
- Source (b) can be removed at the root, source (a) can only be reduced. Spend the deterministic effort on blocking the poisoned input.
