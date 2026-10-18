---
title: "Lesson 5.2: Broken access control and privilege escalation"
image:
  path: /assets/img/covers/web-5-2-broken-access-control-privilege-escalation.webp
  alt: "Broken access control and privilege escalation"
date: 2024-06-15 13:10:00 +0700
categories: ["Web Security", "Web · Access Control"]
tags: [web, access-control, idor]
render_with_liquid: false
---

IDOR (Lesson 5.1) is a missing check at the object level: you can see another person's data. Broken access control here refers to the function level: you can reach a function that only an admin should use. OWASP puts both in the A01:2021 Broken Access Control group, which sits at the top of the risk ranking. This lesson walks through the three most common function-level flaws and escalates a normal user to admin on a real lab by three different routes.

![Broken access control and privilege escalation](/assets/img/web/web-5-2-broken-access-control-privilege-escalation.svg)
_Forced browsing, a client-supplied role flag, and verb tampering all reach the same admin function._

Level: medium, about 35 minutes. Prerequisites: Lesson 5.1 (IDOR). Tools: Burp Suite, ffuf/dirsearch, curl.

## Goals

After this lesson you understand Broken Access Control (BAC) at the function level, you recognize forced browsing, trusting a client-supplied flag, and verb/method tampering, you can escalate from a normal user to admin on a real lab, and you know the principle of a centralized, deny-by-default authorization check.

## Theory

IDOR (Lesson 5.1) is a missing check at the object level: you can view another person's data. Broken access control here means the function level: you can reach a function that only an admin should be able to use. OWASP groups both under A01:2021 Broken Access Control, the group at the top of the risk ranking.

This lesson goes through the three most common flaws.

### Forced browsing

A developer sets up an admin page or endpoint but hides it by not linking it anywhere, then forgets the authorization check entirely. The user only has to guess the right path to get in:

```text
/admin, /admin/panel, /backup/users.json, /debug, /.git/config
```

"No link" is not access control. An attacker uses a wordlist with ffuf or dirsearch to find these paths in seconds.

### Trusting a flag from the client

The app decides authorization from a value the client sends and can change:

```text
Cookie: role=user        -> change to role=admin
Hidden field: isAdmin=0  -> change to isAdmin=1
Header: X-Role: user     -> change to X-Role: admin
```

Authorization must be derived from the login session on the server side (look up in the database what role this user has), never trust a value the client declares itself.

### Verb tampering and flow tampering

The authorization check is attached to the wrong step or the wrong HTTP method, while the real action goes through a different step or method:

- Blocking GET /admin but forgetting POST, or the other way around.
- Checking authorization at the step that shows a confirmation form, but not at the step that executes the action.
- Honoring override headers such as `X-Original-URL`, `X-Rewrite-URL`, `X-HTTP-Method-Override`, which lets an attacker slip past a rule that blocks by path or method.

The principle: the authorization check must sit at the step that executes the action, and apply to every method.

## Demo

The workflow to find BAC:

1. Map the functions with two accounts: one admin, one normal user. Write down the requests only the admin can call.
2. Use ffuf to probe hidden paths:

```text
ffuf -u http://127.0.0.1:8051/FUZZ -w wordlist.txt -mc 200,302
```

3. Take an admin request and replay it with the normal user's session (or with none) in Burp Repeater. If it still works, that is BAC.
4. Try changing the authorization cookie/header, and try changing the method (GET to POST and back).

An example of trusting a client flag with curl:

```text
$ curl -s localhost:8051/admin/panel --cookie 'role=admin'
{"flag":"FLAG{5.2_tin_role_tu_client}","ok":true,"panel":"admin",
 "users":["admin","carol","dave"]}
```

Just by setting the cookie `role=admin`, a normal user walks straight into the admin page.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 5.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/5.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/5.2/app.py" download><i class="fa-solid fa-file-code"></i>app.py</a>
<a class="lab-file" href="/assets/labs-web/5.2/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
</div>
</div>

- Vulnerable app: `labs/5.2/` (runs locally, port 127.0.0.1:8051). Account `carol:pw` (a normal user).
- Task: collect all three flags, each matching one flaw.
  1. Forced browsing: `GET /backup/users.json` (no login needed).
  2. Trusting the client role: set the cookie `role=admin` to reach `/admin/panel`.
  3. Verb tampering: POST directly to `/admin/promote` to promote yourself to admin.
- Hint: look closely at `/admin/promote`, where the GET step checks authorization and the POST step does not.
- Solution: `labs/5.2/exploit.py` and `labs/5.2/transcript.txt`.

Excerpt from a real run:

```text
[*] Buoc 3: verb tampering - carol (role=user) POST promote:
    POST /admin/promote user=carol -> 200 {'flag': 'FLAG{5.2_verb_tampering_bo_qua_kiem_quyen}', ...}
[+] Flags thu duoc:
     FLAG{5.2_forced_browsing_khong_kiem_quyen}
     FLAG{5.2_tin_role_tu_client}
     FLAG{5.2_verb_tampering_bo_qua_kiem_quyen}
```

## Common pitfalls

- Hiding the admin button in the UI while the backend still serves the request.
- Blocking by exact path string (for example blocking "/admin") but missing "/Admin", "/admin/", "/admin;/...", or an API endpoint not under /admin.
- Placing the authorization check on GET while the real action lives in POST.
- The backend honoring a proxy's URL/method override headers without careful configuration.
- Authorization scattered across many places, so sooner or later one spot is missed.

## Further reading

- PortSwigger Web Security Academy: Access control vulnerabilities (labs on unprotected admin, role tampering, method-based access).
- OWASP Top 10 A01:2021 Broken Access Control.
- OWASP API Security Top 10: API5 Broken Function Level Authorization (BFLA).

## Key takeaways

- Function-level BAC: you can reach an admin function that is not yours to use.
- Always test with two accounts (admin and normal user), and replay the admin's request with the user's session.
- Probe for forced browsing with a wordlist; hiding a link is not security.
- Never trust the role or authorization sent from the client.
- Check authorization for every method and at the step that executes the action, not just the display step.
- Defense: deny by default, and gather the authorization logic in one place (middleware or a decorator).
