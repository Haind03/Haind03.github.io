---
title: "Lesson 1.1: How an LLM works"
image:
  path: /assets/img/covers/ai-1-1-how-an-llm-works.webp
  alt: "How an LLM works"
date: 2026-10-08 10:20:00 +0700
categories: ["AI Vuln Tech", "Part 01 · LLM Foundations"]
tags: [ai-security, llm, owasp, tokens, temperature]
render_with_liquid: false
---

To attack or defend an LLM, you do not need the math of the transformer. You do need to understand three things, because every vulnerability in this series comes from them. The model only **predicts the next token**, it does so **by probability**, and it has **no memory** beyond the text it is given.

![How an LLM works](/assets/img/ai-vuln-tech/next-token.svg)
_Text becomes tokens, the model produces a probability distribution, one token is sampled and appended, and the loop repeats._

## Tokens: the unit the model actually sees

The model does not read letters or words the way a person does. Text is split into **tokens**, small pieces that range from a few characters to a whole word. For example "prompt injection" might be split into three tokens, where the leading space is part of a token:

```text
"prompt"  +  " inj"  +  "ection"
```

Spaces, punctuation and even emoji are tokens too.

This matters to an attacker for two reasons:
- Content filters usually match **strings or words**. If you insert odd whitespace, a look-alike Unicode character, or split a blocked word into two tokens, the token sequence changes and the filter may miss it, while the model still understands the text. This is the basis of **token manipulation / TokenBreak** (Lesson 10.3).
- The number of tokens sets **cost and limits**. Sending a very large number of tokens is one way to cause **unbounded consumption** (Lesson 8).

## It only predicts the next token

An LLM takes a sequence of tokens and answers one question: *which token is most likely to come next?* It appends that token to the sequence and asks again. All of its output is this step repeated thousands of times.

This has a direct consequence for security. **The model does not know rules, it continues patterns.** If your context looks like a conversation where the assistant happily does something forbidden, the most likely next tokens continue doing the forbidden thing. This is why roleplay, many-shot and Crescendo (Stage 3) work. They build a context in which obeying the bad request is the most natural continuation.

## Temperature and probability

The model outputs a **probability distribution** over the next token and then samples one token from it. The **temperature** parameter controls how random that sampling is:
- Low temperature (close to 0): almost always picks the most likely token. Output is stable and repeatable.
- High temperature: picks a wider range of tokens. Output is more varied but less predictable.

This is the technical reason the same payload works on one attempt and fails on the next. When you test in the lab and want a fair comparison before and after a fix, fix the temperature (and the seed if the model supports one). When you want to show that a jailbreak is real, run it many times at the default temperature and report the success rate.

## Context window: all the model knows

The model remembers nothing between calls. The only thing it knows is the **context window**, the full sequence of tokens sent in this call: system prompt, conversation history, RAG documents and the new message. The application assembles all of this and sends it.

Two consequences follow:
- "Conversation memory" is the application **resending the whole history** on every turn. Anyone who can insert text into that history can influence the model.
- The context window has a **length limit**. Newer models have very long windows, hundreds of thousands of tokens. That is convenient, but it enables the **many-shot jailbreak** (Lesson 10.2), where hundreds of bad examples are placed in a long window to push the model to follow the pattern.

## Model properties as attack surface

| Model property | Vulnerability it opens |
|---|---|
| Works on tokens, not words | Token manipulation, filter bypass |
| Continues patterns, does not know rules | Roleplay, Crescendo, many-shot jailbreak |
| Probabilistic (temperature) | Non-deterministic attacks, measured as a rate |
| Only knows the context window | Prompt injection, system prompt leak, context stuffing |

## Key takeaways
- The model sees tokens, not words. This is the basis of token manipulation.
- An LLM predicts the next token by probability. It continues patterns and does not understand rules.
- Temperature makes results non-deterministic, so measure an attack by its success rate.
- All of the model's memory is the context window, which the application assembles. Whoever can insert text into it can influence the model.
