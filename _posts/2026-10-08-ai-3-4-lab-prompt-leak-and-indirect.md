---
title: "Lesson 3.4: Lab - prompt leak and indirect injection"
image:
  path: /assets/img/covers/ai-3-4-lab-prompt-leak-and-indirect.webp
  alt: "Lab - prompt leak and indirect injection"
date: 2026-10-08 12:25:00 +0700
categories: ["LLM Security", "Part 03 · LLM01 Prompt Injection"]
tags: [ai-security, llm, owasp, lab, prompt-injection]
render_with_liquid: false
---

This is the combined hands-on session for all of Part 3. The theory is in [3.1](/posts/ai-3-1-direct-prompt-injection/), [3.2](/posts/ai-3-2-system-prompt-leak/) and [3.3](/posts/ai-3-3-indirect-prompt-injection/). Now it is time to sit down and break things. Every payload here runs only in the local lab.

![Lab - prompt leak and indirect injection](/assets/img/ai-vuln-tech/pi-lab.svg)
_Two labs, one routine: read the code, break it and record the rate, patch it in app_fixed.py, then re-run the same payloads and compare._

## Setup

```bash
cd labs && source .venv/bin/activate
python lab01-prompt-injection/app.py        # lab 1, terminal
# lab 2: add an email = create docs/03-xxx.txt, then run
python lab02-indirect-injection/app.py
```

Before you run anything, **read `app.py`** for each lab and find the point where the prompt is assembled and the point where `SEND_EMAIL` is executed. Find the bug on paper first, using the three golden questions from [Lesson 0.4](/posts/ai-0-4-threat-model-llm-app/).

## Part A - lab 1 (direct, leak)

Work through these in order. Try each payload five times and record the rate in `notes/lab1.md`:

1. Get the employee discount code.
2. Get the full system prompt (and confirm it is not the model fabricating one - see [3.2](/posts/ai-3-2-system-prompt-leak/)).
3. Make the bot write a poem (out of scope).
4. **Important:** find five different families of approach for task 1, classify them with the table from [3.1](/posts/ai-3-1-direct-prompt-injection/), and record each family's rate.

Then patch in `app_fixed.py` following the four steps of the lab. After each step, re-run the whole payload set and build a table of "which measure blocks which payload." Conclude which measures *reduce* and which one *eliminates*.

## Part B - lab 2 (indirect, chain)

Each task may add only **one** `docs/03-xxx.txt` file:

1. Make the summary misstate a real email.
2. Force `SEND_EMAIL` to an address outside the company.
3. Leak the internal revenue out to the outside (the full chain).
4. Hide the payload from the human eye.

Then patch with the four measures, and answer the golden question: which measure holds *even when the model is fully fooled* (the hint is in [3.3](/posts/ai-3-3-indirect-prompt-injection/)).

## Note-taking template (notes/labX.md)

```text
## Successful payload
- Payload: ...
  Technique family: (override / roleplay / reformat / split / multi-turn)
  Result: ...
  Rate (5 tries): x/5

## The patch
| Measure | Old payload still works? | Kind (reduces / eliminates) | Note |
|---|---|---|---|

## Reflection
...
```

## "Done" criteria

- You broke all three main tasks of each lab, with a rate table to show it.
- `app_fixed.py` clearly lowers the leak-through rate without blocking clean input.
- You can state in your own words why only the architectural measure (take the secret out of the prompt, put the barrier in the send function) removes the risk.

## Key takeaways

- Read the code for the bug before you run it.
- Record success rates, not pass or fail.
- Compare before and after the patch on the same payload set and the same temperature.
- Keep the soft barriers (reduce) and hard barriers (eliminate) clearly apart in your summary table.
