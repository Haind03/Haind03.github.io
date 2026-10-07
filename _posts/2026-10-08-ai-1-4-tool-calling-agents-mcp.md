---
title: "Lesson 1.4: Tool calling, agents and MCP"
image:
  path: /assets/img/covers/ai-1-4-tool-calling-agents-mcp.webp
  alt: "Tool calling, agents and MCP"
date: 2026-10-08 11:20:00 +0700
categories: ["AI Vuln Tech", "Part 01 · LLM Foundations"]
tags: [ai-security, llm, owasp, agents, mcp]
render_with_liquid: false
---

A chatbot that only produces text can only cause harm through text. The current trend is the **agent**: an LLM that is given tools so it can *act*. It can query a database, send email, run commands, call APIs and browse the web. At that point the model output is no longer harmless text. It is a **command that gets executed**. This is where LLM vulnerabilities move from saying the wrong thing to doing the wrong thing (LLM06 Excessive Agency).

![Tool calling, agents and MCP](/assets/img/ai-vuln-tech/agent-loop.svg)
_The model proposes a tool call, the app executes it, and the result returns to the model as new input._

## How tool calling works

The application gives the model a list of tools. Each tool has a name, a description and a parameter schema:

```json
{
  "name": "send_email",
  "description": "Send an email to a customer",
  "parameters": {"to": "string", "subject": "string", "body": "string"}
}
```

When the model decides to use a tool, it does not run anything itself. It returns a structured **call intent**: `send_email(to=..., subject=..., body=...)`. The **application** is the part that actually executes the call, and then passes the result back to the model as a new message. The loop "model proposes, app executes, result returns, model proposes again" is what an **agent** is.

The key security point is that **the model only proposes, and the application holds the permission.** So the right place for controls is the application's execution layer, not an instruction telling the model not to misbehave.

## The agent loop

```
user/data -> LLM proposes a tool call -> app executes the tool -> result returns to the LLM
     ^-----------------------------------------------------------------|
```

The loop is useful but risky, for these reasons:

- **A tool result is new input** to the model. If a tool returns content controlled by an attacker (a web page, an email), indirect injection happens inside the loop (Lessons 3.3 and 10.5).
- **Errors propagate.** An injection at an early step can cause the model to make wrong calls for all the later steps.
- **Permissions add up.** The more tools an agent has, the larger the attack surface.

## The three axes of Excessive Agency

When you review an agent, separate these three axes (they are used again in Lesson 5.1):

- **Too much functionality:** a tool can do more than it needs to, for example a tool that "runs arbitrary SQL" when only one table needs to be read.
- **Too many permissions:** a tool runs with more privilege than needed, for example an admin token for a read-only task.
- **Too much autonomy:** a dangerous action is executed without a human confirming it.

## MCP, the Model Context Protocol

**MCP** is an open standard for connecting a model to "servers" that provide tools and data in a plug-in way. It makes the agent ecosystem easier to extend, and it also adds new attack surface:

- A **malicious (or compromised) MCP server** can return tool descriptions and content that contain injection, and so steer your agent.
- **Tool shadowing and name confusion:** several servers offer tools with the same name, and the model calls the malicious one.
- Permissions and trust between the MCP client and server are often configured loosely.

Agent and MCP attacks are covered in Lesson 10.5. In the lab for Lesson 4, the tools are **simulated**, so you can see the mechanism without causing real harm.

## Defense principles

Part 05 goes deeper.

- Give each tool **least privilege**. Separate read tools from write tools.
- Put controls (argument validation, scope limits, allowlists) in the **app's execution layer**. Do not rely on the model to restrain itself.
- Require **human confirmation** for actions that cannot be undone (transfers, deletes, sending data out).
- Treat every tool result as untrusted data when it is passed back to the model.

## Key takeaways

- An agent is a loop: the model proposes a tool call, the app executes it, and the result returns to the model.
- The model only proposes and the app holds the permission, so controls belong in the execution layer.
- A tool result is new input, which opens the loop to indirect injection.
- Excessive agency has three axes: functionality, permissions and autonomy. MCP adds attack surface through tools and malicious servers.
