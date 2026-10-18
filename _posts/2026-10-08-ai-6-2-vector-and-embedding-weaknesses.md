---
title: "Lesson 6.2: Vector and embedding weaknesses"
image:
  path: /assets/img/covers/ai-6-2-vector-and-embedding-weaknesses.webp
  alt: "Vector and embedding weaknesses"
date: 2026-10-08 13:40:00 +0700
categories: ["LLM Security", "Part 06 · LLM04 & LLM08 RAG"]
tags: [ai-security, llm, owasp, embeddings, rag, llm08]
render_with_liquid: false
---

LLM08 is a **new** entry in the 2025 list, added because RAG is now everywhere. Where LLM04 (Lesson 6.1) is about poisoning the *content* of the store, LLM08 is about weaknesses in the **vector and embedding machinery itself**, the retrieval layer that almost nobody inspects. The content can be perfectly honest and you can still leak data or get the wrong chunk selected, simply because of how the store is built and queried.

![Vector and embedding weaknesses](/assets/img/ai-vuln-tech/embedding-weakness.svg)
_The retriever ranks chunks by similarity, so a shared index can hand one user another user's private data or an attacker's magnet chunk._

## Four weaknesses to look for

**1. Mixed namespaces that leak across tenants.** The most dangerous and the most common. Many applications pour every tenant, or every sensitivity level, into one shared vector store. The retriever selects by semantic distance, it has no idea who is **allowed** to see what. A query from user A can pull back a private chunk that belongs to user B, and that chunk lands in A's prompt and A's answer.

**2. Retrieval manipulation through similarity.** An attacker writes a "magnet" chunk, stuffed with keywords that make it close to almost any question, so it always lands in the top-k. Hidden inside it is wrong content or an instruction. This is exactly task 3 from the Lesson 5 lab, getting one planted document retrieved for many different queries.

**3. Embedding inversion and leakage through vectors.** An embedding is not a safe one-way hash. A large part of the original text can be reconstructed from its vector. If you expose the vector store, or an API that returns raw vectors, you may be handing out the sensitive text that was embedded into it.

**4. No access control at the retrieval layer.** Authorization is usually enforced in the application, while the retriever happily searches the whole store for whoever asks. Permissions have to travel **with the chunk** as metadata and be used to filter results **before** anything is placed in the prompt.

## How LLM04 and LLM08 differ, and why they travel together

The two risks sit at different points in the same system.

- **LLM04, poisoning.** The problem is in the *content* of a chunk. Someone planted a false or malicious document. Tasks 1, 2 and 4 of the lab are mostly this.
- **LLM08, vector weakness.** The problem is in the *mechanism*. How does a bad chunk get **selected** (similarity manipulation, task 3), or how does data **leak** through the way vectors are stored and queried (mixed namespaces, inversion)?

In practice they chain. An attacker poisons the content under LLM04, then abuses the retrieval mechanism under LLM08 to guarantee the poisoned chunk is actually the one that gets used. Content without selection is harmless, and selection without content has nothing to serve, so a real attack needs both.

## The defense

- **Separate the vector store per tenant and per permission level.** Attach permission metadata to each chunk and filter by the person asking **before** the chunks reach the prompt. This is the hard control against cross-tenant leakage, and it is the one worth building first.
- **Set a distance threshold** and drop chunks that match too weakly. This shrinks the opening for a magnet document that is only loosely related to the question.
- **Do not expose the vector store or raw vectors.** Treat embeddings as sensitive data, because inversion can turn them back into text.
- **Control the ingest source** (from Lesson 6.1) so fewer poisoned chunks exist in the first place.
- **Display provenance** so a user notices when a strange source has slipped into an answer.

The pattern is the same as every other lesson in this series. Filtering by identity in the application layer removes the cross-tenant class outright, while thresholds and provenance only reduce the odds of a bad chunk being used.

## Key takeaways

- LLM08 is new in 2025 and is about the vector and retrieval mechanism, not the content of the documents.
- The four weaknesses are mixed namespaces (cross-tenant leakage), similarity manipulation, embedding inversion, and missing access control at the retriever.
- LLM04 is dirty content, LLM08 is the storage and selection mechanism that lets dirty content be used or lets data leak, and real attacks combine the two.
- The hard control is per-tenant namespaces plus permission filtering on each chunk before it enters the prompt.
