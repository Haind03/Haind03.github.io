---
title: LLM Security
icon: fas fa-robot
order: 2
render_with_liquid: false
---

My notes on attacking and defending LLM applications, following the OWASP Top 10 for LLM Applications 2025. It starts with how an LLM actually works, then the threat model, then each vulnerability class with a local lab you can break and patch.

Everything here is for learning, CTFs, authorized red teaming, and defending your own systems. Payloads are only meant for the local labs or systems you have written permission to test.
{: .prompt-warning }

## Chapter 1: Foundations

### Part 00 · Intro to LLM Security

| # | Lesson |
|---|---|
| 0.1 | [What AI attacks are and how they differ](/posts/ai-0-1-what-ai-attacks-are/) |
| 0.2 | [Legal and ethical ground rules](/posts/ai-0-2-legal-and-ethical-ground-rules/) |
| 0.3 | [Building a safe lab with Ollama](/posts/ai-0-3-building-a-safe-lab/) |
| 0.4 | [Threat model of an LLM app](/posts/ai-0-4-threat-model-llm-app/) |

### Part 01 · LLM Foundations

| # | Lesson |
|---|---|
| 1.1 | [How an LLM works](/posts/ai-1-1-how-an-llm-works/) |
| 1.2 | [Anatomy of a prompt](/posts/ai-1-2-anatomy-of-a-prompt/) |
| 1.3 | [Embeddings and RAG](/posts/ai-1-3-embeddings-and-rag/) |
| 1.4 | [Tool calling, agents and MCP](/posts/ai-1-4-tool-calling-agents-mcp/) |
| 1.5 | [Why LLMs cannot separate instructions from data](/posts/ai-1-5-instructions-vs-data/) |

### Part 02 · The Toolkit

| # | Lesson |
|---|---|
| 2.1 | [The Ollama lab environment](/posts/ai-2-1-ollama-lab-environment/) |
| 2.2 | [A proxy to observe prompts](/posts/ai-2-2-proxy-to-observe-prompts/) |
| 2.3 | [Automated red teaming](/posts/ai-2-3-automated-red-teaming/) |
| 2.4 | [Guardrails for defense](/posts/ai-2-4-guardrails-for-defense/) |

## Chapter 2: OWASP Top 10 for LLM

### Part 03 · LLM01 Prompt Injection

| # | Lesson |
|---|---|
| 3.1 | [Direct prompt injection](/posts/ai-3-1-direct-prompt-injection/) |
| 3.2 | [System prompt leak](/posts/ai-3-2-system-prompt-leak/) |
| 3.3 | [Indirect prompt injection](/posts/ai-3-3-indirect-prompt-injection/) |
| 3.4 | [Lab: prompt leak and indirect injection](/posts/ai-3-4-lab-prompt-leak-and-indirect/) |

### Part 04 · LLM05 Improper Output Handling

| # | Lesson |
|---|---|
| 4.1 | [Improper output handling](/posts/ai-4-1-improper-output-handling/) |

### Part 05 · LLM06 Excessive Agency

| # | Lesson |
|---|---|
| 5.1 | [Excessive agency](/posts/ai-5-1-excessive-agency/) |

### Part 06 · LLM04 & LLM08 RAG

| # | Lesson |
|---|---|
| 6.1 | [Data and model poisoning](/posts/ai-6-1-data-and-model-poisoning/) |
| 6.2 | [Vector and embedding weaknesses](/posts/ai-6-2-vector-and-embedding-weaknesses/) |

### Part 07 · LLM03 Supply Chain

| # | Lesson |
|---|---|
| 7.1 | [Supply chain](/posts/ai-7-1-supply-chain/) |

### Part 08 · LLM10 Unbounded Consumption

| # | Lesson |
|---|---|
| 8.1 | [Unbounded consumption](/posts/ai-8-1-unbounded-consumption/) |

### Part 09 · LLM09 Misinformation

| # | Lesson |
|---|---|
| 9.1 | [Misinformation](/posts/ai-9-1-misinformation/) |

## Chapter 3: New techniques and practice

### Part 10 · New Techniques

| # | Lesson |
|---|---|
| 10.1 | [A map of jailbreaks](/posts/ai-10-1-map-of-jailbreaks/) |
| 10.2 | [Many-shot jailbreak](/posts/ai-10-2-many-shot-jailbreak/) |
| 10.3 | [Encoding and token manipulation](/posts/ai-10-3-encoding-and-token-manipulation/) |
| 10.4 | [Multimodal attacks](/posts/ai-10-4-multimodal-attacks/) |
| 10.5 | [Agent and MCP attacks](/posts/ai-10-5-agent-and-mcp-attacks/) |

### Part 11 · Hands-on

| # | Lesson |
|---|---|
| 11.1 | [CTF practice and resources](/posts/ai-11-1-ctf-and-resources/) |
