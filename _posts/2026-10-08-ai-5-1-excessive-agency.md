---
title: "Lesson 5.1: Excessive agency"
image:
  path: /assets/img/covers/ai-5-1-excessive-agency.webp
  alt: "Excessive agency"
date: 2026-10-08 13:05:00 +0700
categories: ["LLM Security", "Part 05 · LLM06 Excessive Agency"]
tags: [ai-security, llm, owasp, excessive-agency, agents, llm06]
render_with_liquid: false
---

When an LLM only produces text, the worst it can do is say something wrong. When it is given tools to act ([Lesson 1.4](/posts/ai-1-4-tool-calling-agents-mcp/)), it can do something wrong. Excessive agency is the vulnerability of **granting the model more power than it needs**, so that when it is talked into misusing that power, by injection or by one well-phrased sentence, the damage is real.

![The app executes what the model proposes, and the control belongs in the tool](/assets/img/ai-vuln-tech/excessive-agency.svg)
_The model only proposes a tool call; the app decides whether to run it, and the authorization check has to live inside each tool, keyed to the session identity._

## The three axes of excessive agency

OWASP separates three axes, and it is worth memorizing them because they are how you diagnose a design:

- **Too much functionality.** The tool can do more than the task needs. A tool that "runs arbitrary SQL" when reading one table would do; a `delete_user` tool that an ordinary user can still reach.
- **Too much permission.** The tool runs with more privilege than it needs. `get_balance` can read anyone's balance instead of only the balance of the signed-in user.
- **Too much autonomy.** A dangerous action runs with no human in the loop. `refund` executes on its own, with no confirmation and no threshold.

## Looking at the excessive-agency lab

The internal assistant has three mock tools: `refund`, `get_balance`, and `delete_user`. You are signed in as **bob**, an ordinary user. The app **executes every tool the model calls, with no re-check of its own**. The tasks hit all three axes in turn:

1. Read **alice**'s balance while signed in as bob. That is both a permissions problem and a textbook **IDOR**.
2. Refund a large amount with no real order behind it. That is excess autonomy.
3. Call `delete_user`, functionality an ordinary user should never be able to touch.
4. Watch how many turns it takes to get the model to call a dangerous tool, and which phrasings tend to work.

The fourth task shows the probabilistic side. Sometimes you have to "persuade" the model over several turns. But the key point stands no matter how easy or hard it is to persuade. **The vulnerability is that if the model does call the tool, the app actually runs it.** The vulnerable executor is as naive as this:

```python
# The app runs whatever tool the model names, with no check of its own
def handle(tool_name, args):
    return TOOLS[tool_name](**args)   # bob can trigger delete_user this way
```

## The defense goes in the app layer, not the prompt

The lab states the key sentence plainly: *the defense goes in the app layer, not in the prompt.* Why is writing "only serve the signed-in user" in the system prompt not enough? Because that is a soft, probabilistic boundary ([Lesson 1.5](/posts/ai-1-5-instructions-vs-data/)), and a clever sentence can still flip it. Four fixes, mapped onto the three axes:

| Fix | Axis | Type |
|---|---|---|
| bob does not see `delete_user` at all | functionality | removes the class |
| `get_balance` serves only the signed-in user | permissions | removes the class |
| `refund` asks for confirmation and caps the amount | autonomy | removes the class |
| Authorization check **inside each tool function** | all three | removes the class |

The overarching principle is **least privilege for the agent**. The permission check has to live inside the function that executes the tool, and it must take the identity from the application's own session, **not** from anything the model says. The model proposes; the app decides whether to act.

Concretely, the authorization lives in the tool itself and reads the identity from the session, never from the arguments the model supplied:

```python
def get_balance(args, *, session_user):
    target = args["user"]
    if target != session_user:          # identity from the session, not the model
        raise PermissionError("not allowed")
    return balances[target]
```

A refund is irreversible, so it gets a confirmation step and a hard ceiling, both enforced in the function rather than requested in a prompt:

```python
def refund(args, *, session_user, confirmed):
    amount = args["amount"]
    if amount > REFUND_LIMIT:
        raise PermissionError("over the per-refund limit")
    if not confirmed:
        return {"status": "needs_human_confirmation", "amount": amount}
    return do_refund(session_user, amount)
```

And `delete_user` is simply not in the tool set that bob's role is allowed to call. If the function is never exposed to that role, no amount of persuasion reaches it.

## How bad it gets when you combine it with indirect injection

The final reflection connects back to the injection lessons. If an outsider plants an indirect injection (Lesson 3.3) in data the agent reads, and the agent holds high-privilege tools, then the attacker controls those tools **with the victim's privileges**. This is how a harmless-looking chatbot becomes a channel for deleting data or moving money. Excessive agency is the damage amplifier for every injection. A prompt that cannot do anything is an annoyance; a prompt that can call `delete_user` is an incident.

This is also why the fix for injection and the fix for agency are the same shape. You do not try to make the model refuse. You make sure that even a fully hijacked model can only call tools that are scoped, authorized against the real session, and gated by a human for anything it cannot undo.

## Key takeaways
- The three axes are too much functionality, too much permission, and too much autonomy.
- The model only proposes a tool call; the app executes it. Put the control in the tool function and take the identity from the session, not from what the model says.
- Least privilege for the agent: fewer tools, a tight scope per tool, and human confirmation for anything irreversible.
- Excessive agency amplifies every injection. A prompt-level instruction is a soft boundary and is not enough on its own.

## Further reading
- [OWASP LLM06:2025 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/)
