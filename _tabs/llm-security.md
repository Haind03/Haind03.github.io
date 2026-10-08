---
title: LLM Security
icon: fas fa-robot
order: 4
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

More parts (the OWASP Top 10 one by one, plus newer attack techniques) are on the way.
