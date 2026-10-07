---
title: "Lesson 18.8: AI-assisted reverse engineering, twice as fast when used in the right place"
date: 2023-10-14 15:46:00 +0700
categories: ["Technique Reverse", "Part 18 · Advanced Topics"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
Reversing is a lot of reading: reading pseudocode, guessing what a function does, renaming a pile of `sub_401000` and `v7`. Most of that is repetitive and eats time. This is exactly where an LLM can step in: it reads a function, guesses the purpose, suggests variable names, explains a confusing chunk. It doesn't reverse for you, but it clears the road so you can go faster. This lesson covers two ways to use AI in RE, and more importantly, when not to trust it.

## Two kinds of AI integration

There are two ways AI gets into your workflow, differing in depth.

The first kind is a plugin that calls an LLM from inside the decompiler. You're in IDA or Ghidra, select a function, press a key, and the plugin sends the pseudocode to an LLM and pastes the answer back. One direction: the tool asks, the AI answers. Simple, and enough for "what does this function do".

The second kind is an MCP server so the AI drives the decompiler itself. This is the leap. Instead of you copying each function to the AI, an LLM agent (Cursor, Cline) talks directly to the decompiler through an MCP server: it gets the function list itself, reads the pseudocode itself, renames, adds comments, follows xrefs. You give commands in plain language ("find the license check function and explain the algorithm"), and the agent feels its way through.

## Type 1: LLM plugins in the decompiler

Common plugins, by decompiler:

| Decompiler | Plugin | What it does |
|---|---|---|
| IDA | **Gepetto** | Select a function, ask the LLM to explain it and suggest batch variable renames right in the pseudocode |
| Binary Ninja | **aiDAPal / Sidekick** | Built-in AI assistant, explains and suggests names |
| Ghidra | **GhidrAssist / G-3PO** | Calls an LLM to explain functions in Ghidra's decompiler |

Typical use with Gepetto: open a tangled function `sub_14000C0A0`, press the hotkey, and Gepetto returns "this function reads a config file, decrypts it with RC4 using a hardcoded key, then parses it into key-value pairs", along with suggestions to rename `v3` to `decrypted_config` and `v7` to `rc4_key`. You skim it, accept it if it looks right, drop it if it's wrong.

The strength is speed. A function that takes you five minutes to read, the LLM summarizes in five seconds. The weakness is in the word "suggest": it guesses, and guesses are sometimes wrong.

## Type 2: MCP servers for RE

MCP (Model Context Protocol) is a standard protocol for LLM agents to call external tools. For RE, people write MCP servers that bridge the agent and the decompiler/debugger:

| MCP server | Connects to | What the agent can do |
|---|---|---|
| **ida-pro-mcp** (mrexodia) | IDA Pro | Get decompilation, xrefs, rename, comment, read/write through Hex-Rays |
| **GhidraMCP** (LaurieWired) | Ghidra | List functions, decompile, rename, set data types |
| **Binary Ninja MCP** | Binary Ninja | Work with HLIL/MLIL through conversation |
| **r2mcp** | radare2/rizin | Run r2 commands, analyze through conversation |
| **frida-mcp** | Frida | The agent writes and loads Frida scripts itself, reads the hook results |

A fuller list is in the [tools repository, section 23b](/posts/re-resources-reverse-engineering-tool-repository-roundup/).

### Basic configuration

The MCP server is declared in the client's config file (Cline, Cursor). A common template looks like:

```json
{
  "mcpServers": {
    "ida": {
      "command": "python",
      "args": ["-m", "ida_pro_mcp.server"]
    }
  }
}
```

The details differ per server (some run as a plugin inside an already open IDA and expose a port that the client connects to, others are a separate process). Read the README of the exact server you install. Once connected, you ask the agent in natural language and it calls the MCP functions itself (list functions, decompile, rename...) to answer.

The real experience: open an unfamiliar binary, tell the agent "survey and rename the main functions so they're easier to read", and a few minutes later the whole `sub_*` function tree has suggested names. You review it, fix the wrong parts, and save yourself a whole session of naming by hand.

## The limit: AI guesses, and guesses can be wrong

This is the most important part of the lesson, read it carefully.

An LLM doesn't run code and doesn't prove anything. It guesses based on patterns it has seen, and the consequences are real. It can hallucinate: it may confidently say "this is AES" when it's actually an XOR loop, or make up a function name that sounds reasonable but is completely wrong. Wrong names also spread. If you accept a wrong name without checking, the functions that call it will be read by the AI through that wrong name, and errors stack on errors. And it can't replace the analyst, because AI is good at summarizing and naming but bad at multi-step reasoning, subtle logic, and anything that depends on runtime values it can't see.

The survival rule: **treat the AI's output as a hypothesis, not a fact.** It says "this function decrypts RC4"? Good, now you confirm by finding the KSA/PRGA in the code (lesson [16.2](/posts/re-16-2-xor-rc4-custom-base64-three-youll/)), or by running it dynamically to see the input and output. If the hypothesis is right keep it, if wrong drop it, but always check.

## Safety when analyzing malware

MCP gives the agent permission to run tools on your machine. When the target is malware, this is dangerous. Run the client and the MCP server in an isolated VM (see lesson [0.3](/posts/re-0-3-set-up-safe-lab-before-touching/)), the same lab you already use for malware. Don't let the agent execute the sample on its own: a "proactive" agent might decide to run the binary to see what it does, and with malware that's an infection. Limit the agent's permissions to reading and static analysis, or supervise closely if you let it run dynamically in a sandbox. Also be careful with data sent to the cloud. For a malware sample, or an internal company binary, sending pseudocode to a cloud LLM means handing data out, so for sensitive samples consider a locally running LLM.

## When AI is worth using, when not

Worth using: batch renaming, quickly summarizing an unfamiliar function, explaining an unfamiliar API, generating boilerplate scripts (IDAPython, Frida), suggesting directions when you're stuck. It's a speed springboard.

Don't rely on it for: the final conclusion about a crypto algorithm, security logic that has to be exactly right, or any claim you'll put in a report without checking it yourself. Those are still your job.

AI makes reversing faster, not easier. You still need to understand everything in the earlier parts of the series to know when the AI is talking nonsense.

## Key takeaways
There are two kinds of AI integration: one-way LLM plugins (Gepetto, GhidrAssist) and MCP servers so an agent drives the decompiler itself (ida-pro-mcp, GhidraMCP, r2mcp, frida-mcp). MCP is declared in the client config, and then you give commands in natural language. AI output is a hypothesis, so always verify by hand or by running dynamically before trusting it. Hallucination and spreading wrong names are the biggest risks.

For malware analysis, keep the client and MCP in an isolated VM, don't let the agent run the sample on its own, and be careful with data sent to the cloud. AI speeds you up, it doesn't replace foundational knowledge.
