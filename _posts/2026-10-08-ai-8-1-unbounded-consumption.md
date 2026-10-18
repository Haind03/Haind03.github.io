---
title: "Lesson 8.1: Unbounded consumption"
image:
  path: /assets/img/covers/ai-8-1-unbounded-consumption.webp
  alt: "Unbounded consumption"
date: 2026-10-08 14:15:00 +0700
categories: ["LLM Security", "Part 08 · LLM10 Unbounded Consumption"]
tags: [ai-security, llm, owasp, unbounded-consumption, dos, llm10]
render_with_liquid: false
---

This lesson stands apart from the rest of the Top 10. It does not leak data and it does not seize control. It attacks **availability and cost**. And because every token the model produces burns real CPU or GPU time and, on a paid API, real money, this is the risk that is easiest to underestimate and quickest to hurt your wallet.

![Unbounded consumption](/assets/img/ai-vuln-tech/unbounded-consumption.svg)
_An abusive request makes the model emit many tokens, and because each token is one full model pass, cost grows linearly while nothing bounds it. Deterministic guardrails at the gateway close the class._

## Why an LLM is unusually expensive to run

A few properties of how the model works (Lesson 1.1) make it a soft target for resource abuse:

- **Inference is expensive.** Each output token is one full pass over the model. Output length cost is linear: a 2000-token answer costs roughly ten times a 200-token answer.
- **You pay per token.** With a cloud API, tokens are money, directly. Spamming long output inflates the bill.
- **Long input costs too.** Stuffing a huge context burns memory and prompt-processing time before a single output token is produced.
- **Abuse looks like real use.** A prompt that says "write a 5000-word essay" is indistinguishable from a legitimate request. There is no malicious payload to filter.

## The variants

All of these abuse availability or cost rather than confidentiality or integrity:

- **Output flooding.** Force the model to generate as many tokens as possible, for example "count from 1 to 1000, one number per line" or "write 500 distinct sentences about autumn".
- **Input flooding.** Paste a few thousand words to inflate the `prompt tokens` and the processing time.
- **Denial of Wallet (DoW).** Do not crash the service, make the **API bill** explode. This is specific to the economics of LLMs and often the real goal.
- **Concurrent DoS.** Open many sessions in parallel so the server slows for everyone. On CPU-only inference this is very visible.
- **Model extraction and distillation.** Send a large volume of queries to copy the model's behavior into your own. This both drains resources and steals intellectual property.

## Inside the lab

The lab exposes a chat API with no limits at all: it does not cap output length, it does not rate limit, and it does not cap input length. On purpose, the app prints the **time and token count for every answer** so you can *see* the cost. The exercise is:

1. Force a very long output, record the time and tokens, and compare against a normal answer.
2. Send a very long input and watch `prompt tokens` and the latency climb.
3. Estimate the cost: if this were a paid API, what would spamming like this cost per hour.
4. Observe only, do not abuse: open two or three sessions at once and watch the server slow down. That slowdown is the DoS.

Everything below runs against your local lab only.

```text
# output flooding
Count from 1 to 1000, one integer per line, with no commentary.
Write 500 distinct sentences describing a sunset.

# input flooding: paste thousands of words of filler, then ask a trivial question
<~10,000 words of lorem ipsum>
Summarize the text above in one sentence.
```

Printing the token count and latency is the point of the lab. It turns an abstract idea ("this wastes resources") into a number you can measure, which is exactly what you want when you later prove a fix works.

## Defense: deterministic guardrails

This is the cleanest defense in the entire Top 10. The controls are **deterministic and do not depend on the model**. You set a limit, and the limit holds every time.

| Control | Where it belongs |
|---|---|
| Output cap (`num_predict` / `max_tokens`, for example 256) | app code |
| Input length limit (reject prompts over N tokens or characters) | app code / gateway |
| Rate limit per user (X requests per minute) | **gateway / infrastructure** (best) |
| Daily and monthly quota, with cost alerts | gateway / billing |
| Timeout per LLM call | app code |

The output cap and the timeout are a couple of lines where you call the model:

```python
resp = client.chat(
    model="qwen2.5:3b",
    messages=messages,
    options={"num_predict": 256},   # hard cap on output tokens
)
```

```python
MAX_INPUT_TOKENS = 2000
if count_tokens(user_input) > MAX_INPUT_TOKENS:
    raise ValueError("input too long")
```

### Hard controls versus soft controls

The distinction that runs through this whole series applies here with unusual clarity. A **hard** control removes the class: a server-side `max_tokens` cap means a request physically cannot produce more than 256 tokens, no matter what it says. A **soft** control only reduces the risk: writing "keep your answers short" in the system prompt is a request the model is free to ignore, and a long enough prompt will talk it out of being brief. Put the budget in code, not in the prompt.

### Why the gateway, not the app

The lab's reflection question points at placement. Rate limits and quotas belong at the **gateway or infrastructure** layer rather than scattered across each application, so they apply uniformly to every endpoint and cannot be forgotten when someone adds a new route next quarter. One policy, enforced in one place, for everything behind it.

Finally, the name earns its keep. "Denial of Wallet" means the attacker never has to crash you. They simply make you **pay until you switch the service off yourself**. A quota with a cost alert is what turns that open-ended bill into a bounded, noticed event.

## Key takeaways

- LLM10 attacks availability and cost, not confidentiality or integrity. There is often no payload to filter, because abuse looks like a large but legitimate request.
- The variants are output flooding, input flooding, Denial of Wallet, concurrent DoS, and model extraction.
- Tokens are money plus CPU and GPU time, and output cost is linear, so a long answer is a large bill.
- The defense is deterministic: cap output and input, rate limit and set quotas (best at the gateway), and time out every call.
- A server-side cap is a hard control that removes the class. An in-prompt "be brief" is a soft control that the model can ignore.
