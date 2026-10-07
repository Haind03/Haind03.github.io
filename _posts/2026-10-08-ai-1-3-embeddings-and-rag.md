---
title: "Lesson 1.3: Embeddings and RAG"
image:
  path: /assets/img/covers/ai-1-3-embeddings-and-rag.webp
  alt: "Embeddings and RAG"
date: 2026-10-08 11:00:00 +0700
categories: ["AI Vuln Tech", "Part 01 · LLM Foundations"]
tags: [ai-security, llm, owasp, rag, embeddings]
render_with_liquid: false
---

A model only knows what is in its training data and in its context window. To make it answer from your own documents, such as an internal handbook or a knowledge base, people use **RAG (Retrieval-Augmented Generation)**. RAG is the most common LLM architecture today, and it introduces two OWASP entries of its own (LLM04 data poisoning and LLM08 vector and embedding weaknesses). Understanding RAG is required.

![Embeddings and RAG](/assets/img/ai-vuln-tech/rag-lifecycle.svg)
_RAG has an ingest phase and a query phase. The retrieved chunks go into the prompt as untrusted input._

## Embeddings: turning text into vectors

An **embedding** is a vector of numbers (for example 768 or 1536 dimensions) that represents the meaning of a piece of text. Sentences with similar meaning produce vectors that are close to each other. "a cat" and "a kitten" are close. "a cat" and "bank interest rate" are far apart.

Distance is usually measured with **cosine similarity**. Semantic search is this and nothing more: embed the question as a vector, then find the vectors closest to it in the store.

## The life cycle of a RAG system

```
Ingest phase:
  Documents -> split into chunks -> embed each chunk -> store in a vector DB

Query phase:
  Question -> embed -> find the top-k nearest chunks -> insert into the prompt -> LLM answers
```

The final prompt usually looks like this:

```text
Use the following context to answer. If the answer is not in the context, say you do not know.
Context:
{top_k_chunks}
Question: {user_question}
```

## Why RAG is attractive to attackers

Look again at the three golden questions (Lesson 0.4). RAG touches all three.

1. **Data in:** `{top_k_chunks}` is decided by what is in the document store. If an attacker can **write to the store** (a public web page the system crawls, a document a user uploads, a comment), they can put malicious instructions into the prompt. This is **RAG poisoning / indirect injection** (Lessons 6.1 and 3.3).
2. **Trust:** a retrieved chunk is usually treated by the model, and by the user, as an authoritative document. A poisoned chunk therefore carries a lot of weight.
3. **Store separation (namespaces):** if the data of several customers or several sensitivity levels sits in one index, a carefully chosen query can pull back chunks the asker is not allowed to see. This is **cross-tenant leakage** (LLM08, Lesson 6.2).

## Weaknesses specific to embeddings (LLM08)

- **Namespace mix-ups:** mixing data from several tenants or permission levels in one vector store makes queries return the wrong data.
- **Embedding inversion:** a vector can be partly reversed to recover the original content. If vectors are exposed, the data behind them may be exposed too.
- **Poisoning through similarity:** an attacker inserts a chunk packed with many popular keywords so that it lands in the top-k for almost every question, then places malicious instructions in it.
- **No access control at the retrieval layer:** the retriever selects by semantic closeness, not by what the asker may view.

## Defense

The basics are covered here. Part 06 goes deeper.

- Split the vector store by tenant or permission level. Attach permission metadata to each chunk and filter by the asker *before* chunks enter the prompt.
- Treat every chunk as untrusted data. Do not let the model treat chunk content as instructions.
- Control what gets ingested: decide who may write to the store and review content at ingest time.

## Key takeaways

- An embedding is a vector that represents meaning. Semantic search finds nearby vectors (cosine similarity).
- RAG puts the top-k chunks into the prompt. Those chunks are untrusted data coming in.
- Being able to write to the store means being able to place malicious instructions in the prompt (RAG poisoning / indirect injection).
- Mixed namespaces cause cross-tenant leakage. The retriever does not know about permissions on its own.
