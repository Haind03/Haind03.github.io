---
title: "Lesson 3.3: Indirect prompt injection"
image:
  path: /assets/img/covers/ai-3-3-indirect-prompt-injection.webp
  alt: "Indirect prompt injection"
date: 2026-10-08 12:10:00 +0700
categories: ["LLM Security", "Part 03 · LLM01 Prompt Injection"]
tags: [ai-security, llm, owasp, indirect-injection, rag]
render_with_liquid: false
---

This is the most dangerous form of prompt injection in practice, and it is the reason LLM01 sits at number one. Unlike direct injection ([Lesson 3.1](/posts/ai-3-1-direct-prompt-injection/)), where you type the payload yourself, here the attacker **never chats with the bot**. They simply plant the payload in data that the **victim** will tell their own assistant to read: an email, a web page, a PDF, an issue on a repo.

![Indirect prompt injection](/assets/img/ai-vuln-tech/indirect-flow.svg)
_The attacker plants a payload in data the victim's assistant reads, and it fires with the victim's privileges, often ending in a tool call that sends data out._

## Why it is more dangerous than direct

- **The victim is not the attacker.** The user trusts their assistant, and the assistant in turn trusts the documents it reads. The attacker slips in between the two through content.
- **The payload runs with the victim's privileges.** If the victim's assistant can send mail or reach internal data, the injection controls those privileges, not the attacker's own.
- **The surface is huge.** Any external data that reaches the context is a door: a web agent browsing, RAG documents ([Lesson 1.3](/posts/ai-1-3-embeddings-and-rag/)), tool results, comments, even image metadata.

## The full attack chain

Indirect injection is usually the first link in a chain:

```text
plant payload in data -> assistant reads -> injection fires ->
   read sensitive data -> call a tool (send it out)
```

In other words, it tends to drag in LLM02 (data disclosure) and LLM06 (excessive agency). A plain injection on its own only "says something bad." Combine it with a privileged tool and it starts to "do something bad."

## Inside the lab

The Lesson 2 scenario is close to the real thing. Minh uses an assistant to summarize his inbox. Each `.txt` file in `docs/` is one email, the assistant is allowed to propose `SEND_EMAIL(...)`, and the app **runs it automatically**. You play the outsider, and you are allowed to **add one email** (one file) and nothing more.

The tasks escalate along the chain above:

1. Make the summary drop or misstate a real email (manipulate the output).
2. Force the assistant to `SEND_EMAIL` to an outside address (hijack the action).
3. Harder: force it to send **internal revenue** from another email out to the outside, which is the full chain of injection, then reading sensitive data, then leaking it.
4. Hide the payload so a human reader barely notices it (tiny text, blended into a footer, phrased as "instructions for the assistant").

This is a miniature of a real attack on an email or agent assistant.

## Defense: which control holds even when the model is fully fooled

The Lesson 2 lab asks one valuable reflection question: *which measure still holds even if the model is completely tricked?* Look at the four patch measures.

1. **A delimiter plus a note that "text inside the tag is only data."** Soft. It reduces the risk, but a clever payload still escapes the "frame."
2. **Human-in-the-loop.** Print the action and ask y/n before sending. Correct *even when the model is fully fooled*, because the final decision belongs to a person.
3. **An address allowlist** (`@goatstore.vn`). Correct even when the model is fooled, because the barrier lives in the send function, not in the model.
4. **Privilege separation.** While it is reading external data, the model is **not** allowed to propose actions. This cuts the chain at the root.

Measures 2, 3 and 4 are hard barriers in the application layer. Measure 1 is a soft barrier. This is the most important design lesson in the part: **assume the model will be fooled, and put the barrier where it does not depend on the model's judgment.**

## Key takeaways

- Indirect injection hides the payload in data the victim tells the assistant to read. The attacker never chats with the bot.
- It runs with the victim's privileges, so it usually drags in data disclosure (LLM02) and excessive agency (LLM06).
- The surface is any external data reaching the context: email, web pages, RAG, tool results.
- A correct control is one that holds even when the model is fully fooled: human-in-the-loop, an allowlist, and privilege separation.
