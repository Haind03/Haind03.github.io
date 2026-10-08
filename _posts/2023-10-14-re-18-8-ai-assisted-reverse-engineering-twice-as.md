---
title: "Lesson 18.8: AI-assisted reverse engineering"
image:
  path: /assets/img/covers/re-18-8-ai-assisted-reverse-engineering-twice-as.webp
  alt: "Lesson 18.8: AI-assisted reverse engineering"
date: 2023-10-14 15:46:00 +0700
categories: ["Reverse Engineering", "Part 18 · Advanced Topics"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
Reversing is a lot of reading, such as reading pseudocode, guessing what a function does, renaming many `sub_401000` and `v7`. Most of it is repetitive and eats time. An LLM can help here, since it reads a function, guesses the purpose, suggests variable names, explains a confusing chunk. It doesn't reverse for you, but it speeds up the boring parts. This lesson covers two ways to use AI in RE, and when not to trust it.

## Two kinds of AI integration

There are two ways AI gets into your workflow, differing in depth.

The first kind is a plugin that calls an LLM from inside the decompiler. You're in IDA or Ghidra, select a function, press a key, and the plugin sends the pseudocode to an LLM and pastes the answer back. It goes one way. The tool asks, the AI answers. It's simple, and enough for "what does this function do".

The second kind is an MCP server so the AI drives the decompiler itself. Instead of you copying each function to the AI, an LLM agent (Cursor, Cline) talks directly to the decompiler through an MCP server, and it gets the function list itself, reads the pseudocode itself, renames, adds comments, follows xrefs. You give commands in plain language ("find the license check function and explain the algorithm"), and the agent works its way through.

## Type 1: LLM plugins in the decompiler

Common plugins, by decompiler:

| Decompiler | Plugin | What it does |
|---|---|---|
| IDA | Gepetto | Select a function, ask the LLM to explain it and suggest batch variable renames right in the pseudocode |
| Binary Ninja | aiDAPal / Sidekick | Built-in AI assistant, explains and suggests names |
| Ghidra | GhidrAssist / G-3PO | Calls an LLM to explain functions in Ghidra's decompiler |

Typical use with Gepetto is to open a tangled function `sub_14000C0A0`, press the hotkey, and Gepetto returns "this function reads a config file, decrypts it with RC4 using a hardcoded key, then parses it into key-value pairs", along with suggestions to rename `v3` to `decrypted_config` and `v7` to `rc4_key`. You skim it, accept it if it looks right, drop it if it's wrong.

It's fast. A function that takes you five minutes to read, the LLM summarizes in five seconds. But it only suggests, and its guesses are sometimes wrong.

## Type 2: MCP servers for RE

MCP (Model Context Protocol) is a standard protocol for LLM agents to call external tools. For RE, people write MCP servers that bridge the agent and the decompiler/debugger:

| MCP server | Connects to | What the agent can do |
|---|---|---|
| ida-pro-mcp (mrexodia) | IDA Pro | Get decompilation, xrefs, rename, comment, read/write through Hex-Rays |
| GhidraMCP (LaurieWired) | Ghidra | List functions, decompile, rename, set data types |
| Binary Ninja MCP | Binary Ninja | Work with HLIL/MLIL through conversation |
| r2mcp | radare2/rizin | Run r2 commands, analyze through conversation |
| frida-mcp | Frida | The agent writes and loads Frida scripts itself, reads the hook results |

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

The details differ per server (some run as a plugin inside an already open IDA and expose a port that the client connects to, others are a separate process). Read the README of the server you install. Once connected, you ask the agent in natural language and it calls the MCP functions itself (list functions, decompile, rename...) to answer.

In practice, you open an unfamiliar binary, tell the agent "survey and rename the main functions so they're easier to read", and a few minutes later the whole `sub_*` function tree has suggested names. You review it, fix the wrong parts, and save a whole session of naming by hand.

## The limit: AI guesses, and guesses can be wrong

Read this part carefully.

An LLM doesn't run code and doesn't prove anything. It guesses based on patterns it has seen. It can hallucinate, so it may confidently say "this is AES" when it's actually an XOR loop, or make up a function name that sounds reasonable but is wrong. Wrong names also spread. If you accept a wrong name without checking, the functions that call it will be read by the AI through that wrong name, and errors stack on errors. And it can't replace the analyst, because AI is good at summarizing and naming but bad at multi-step reasoning, subtle logic, and anything that depends on runtime values it can't see.

I treat the AI's output as a hypothesis, not a fact. It says "this function decrypts RC4"? Then I confirm by finding the KSA/PRGA in the code (lesson [16.2](/posts/re-16-2-xor-rc4-custom-base64-three-youll/)), or by running it dynamically to see the input and output. If the hypothesis is right keep it, if wrong drop it, but always check.

## Safety when analyzing malware

MCP gives the agent permission to run tools on your machine. When the target is malware, this is dangerous. Run the client and the MCP server in an isolated VM (see lesson [0.3](/posts/re-0-3-set-up-safe-lab-before-touching/)), the same lab you already use for malware. Don't let the agent execute the sample on its own, because a "proactive" agent might decide to run the binary to see what it does, and with malware that's an infection. Limit the agent's permissions to reading and static analysis, or supervise closely if you let it run dynamically in a sandbox. Also be careful with data sent to the cloud. For a malware sample, or an internal company binary, sending pseudocode to a cloud LLM means handing data out, so for sensitive samples consider a locally running LLM.

## When AI is worth using

It's worth using for batch renaming, quickly summarizing an unfamiliar function, explaining an unfamiliar API, generating boilerplate scripts (IDAPython, Frida), and suggesting directions when you're stuck.

Don't rely on it for the final conclusion about a crypto algorithm, security logic that has to be exactly right, or any claim you'll put in a report without checking it yourself. Those are still your job.

AI makes reversing faster, not easier. You still need everything from the earlier parts of the series to know when the AI is talking nonsense.

## Lab

The task is to set up an MCP server for IDA or Ghidra, connect it to an LLM client, ask it to explain a function, and then check the result yourself. The point is not to trust the AI but to get into the habit of verifying its output. You need IDA Pro (with Hex-Rays) or Ghidra, an LLM client that supports MCP (a desktop chat client, Cline in VS Code, or Cursor), and a matching MCP server, namely `ida-pro-mcp` (by mrexodia) for IDA, or `GhidraMCP` (by LaurieWired) for Ghidra. You also need a binary to try it on. Reuse any crackme from the earlier labs, for example the three-layer C crackme from Lesson 3.5 or the TEA one from Lesson 16.3. On safety, if you try it on a real malware sample, do everything in an isolated VM (see Lesson 0.3) and don't let the agent run the sample.

Start by installing the MCP server by following the README of the server you chose. It usually means installing a plugin into IDA or Ghidra (which opens an endpoint) and then declaring the server in the client's MCP configuration file. Confirm the connection by asking the agent a simple question such as "list the functions in the open binary". If it returns a real list of functions, the connection works. Then open the password-checking function of the crackme and tell the agent to "explain what this function does and suggest names for the variables", and write down the answer.

Now verify by hand. Read that same function yourself and ask whether the AI is right and whether the algorithm it describes matches the code. If it says "string comparison" when the code is actually "XOR then compare against a constant array", it was wrong. Next have the agent rename the main `sub_*` functions in bulk, then go back over every name, keeping the right ones and fixing the wrong ones, and count what percentage of its suggestions were usable. Finally try to break it. Give the agent a function with a plain XOR loop but ask the loaded question "is this AES?" and see whether it goes along with you (a hallucination) or pushes back. The lesson is not to steer the AI with a biased question.

Some questions to think about. With the crackme you tried, how much time did the AI save and where was it wrong? Why shouldn't AI output go straight into the final report? And when analyzing malware, which permissions of the agent must you block? Compare with the solution after you have done it yourself.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This lab has no single fixed numeric answer, because the result depends on the server and the LLM you use. Below are what to observe and the conclusions to draw.

### Installing and connecting

A sample MCP configuration in a client (a JSON config file of the desktop chat client, for example):

```json
{
  "mcpServers": {
    "ghidra": {
      "command": "python",
      "args": ["/path/to/GhidraMCP/bridge_mcp_ghidra.py"]
    }
  }
}
```

With ida-pro-mcp you usually run the plugin inside IDA (it opens a port), and the client connects through the matching configuration. Read the README of the exact server, since the way to start it differs between projects. If the connection works, asking "list the functions" returns the real function list of the open binary, not a generic answer.

### Explaining and verifying

With the three-layer crackme from Lesson 3.5 (length 10, XOR 0x5A compared against a constant array, a checksum), a good agent will describe it roughly right, for example "the function checks the length, transforms each character and compares it with a hard-coded array, and checks a sum". That is a correct hypothesis. But it can be wrong in the details, such as misstating the XOR constant, missing the checksum layer, or calling the XOR "encryption" too grandly. To check, look at the opcodes themselves. `xor ... 5Ah` in the loop confirms the XOR and the key value, and an accumulating add followed by a `cmp` against a constant confirms the checksum. The AI's hypothesis only has value after you cross-check it like this.

### Bulk renaming, then reviewing

The typical result is that most suggested names are usable for functions with clear logic (for example `check_length`, `transform_input`), while wrapper functions or library functions get skewed names. The usable rate is usually high but never 100%. Accepting the whole batch and reviewing each name is faster than naming from scratch, but you must not accept it blindly.

### Breaking it with a biased question

If you ask "is this AES?" about an XOR loop, a weak LLM will go along and invent reasons, because the question already hints at the answer. A good LLM will push back with "no, this is just a single-byte XOR, AES has an S-box and multiple rounds". So don't ask leading questions, and stay skeptical whenever the AI agrees too easily with your assumption.

### Answers to the questions

AI is best at naming and the initial summary (a clear saving) and wrong most often on algorithm details and specific values, which are exactly the things that must be precise. AI output shouldn't go straight into the report because it is an unchecked hypothesis that may contain hallucinations, and an RE report has to rest on evidence from the code, not on a model's guess. When analyzing malware, block the agent from executing the sample, from writing outside the VM, and from reaching the real network. Keep the agent at reading and static analysis, or monitor it closely when running dynamically in an isolated sandbox.

</details>

## Key takeaways
There are two kinds of AI integration, one-way LLM plugins (Gepetto, GhidrAssist) and MCP servers so an agent drives the decompiler itself (ida-pro-mcp, GhidraMCP, r2mcp, frida-mcp). MCP is declared in the client config, and then you give commands in natural language. AI output is a hypothesis, so always verify by hand or by running dynamically before trusting it. Hallucination and spreading wrong names are the biggest risks.

For malware analysis, keep the client and MCP in an isolated VM, don't let the agent run the sample on its own, and be careful with data sent to the cloud. AI speeds you up, it doesn't replace foundational knowledge.
