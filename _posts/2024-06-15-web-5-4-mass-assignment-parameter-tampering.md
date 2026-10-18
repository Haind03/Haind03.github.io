---
title: "Lesson 5.4: Mass assignment and parameter tampering"
image:
  path: /assets/img/covers/web-5-4-mass-assignment-parameter-tampering.webp
  alt: "Mass assignment and parameter tampering"
date: 2024-06-15 13:20:00 +0700
categories: ["Web Security", "Web · Access Control"]
tags: [web, mass-assignment, access-control]
render_with_liquid: false
---

Many frameworks let you create or update an object by binding the whole client payload straight onto it. That is convenient, but if the client also sends fields that only the server should set, such as isAdmin or role, those get written too. This lesson shows why binding a raw JSON body onto an object lets a user make themselves an admin, and how to block it with a whitelist.

![Mass assignment and parameter tampering](/assets/img/web/web-5-4-mass-assignment-parameter-tampering.svg)
_The form shows only email and bio, but the request carries isAdmin, and a blind bind writes it onto the model._

Level: medium, about 25 minutes. Prerequisites: Lesson 5.2 (Broken access control). Tools: Burp Suite, curl.

## Goals

After this lesson you understand mass assignment and parameter tampering, you recognize the code patterns prone to the flaw, you can escalate privileges by inserting a privileged field into a request, and you know how to defend with a whitelist and a DTO.

## Theory

### What mass assignment is

Many frameworks let you create or update an object by binding the whole client payload directly:

```text
user.update(request.json)          # Python
Object.assign(user, req.body)       # Node.js
User(**request.json)                # build a model from JSON
@ModelAttribute User user           # Spring, automatic binding
```

Convenient for the developer, but if the client sends along fields that only the server should set (isAdmin, role, balance, verified, is_active), those get overwritten too. That is mass assignment, also called autobinding or object injection.

### Parameter tampering

Broader than mass assignment: the attacker changes any client-controlled parameter to bypass logic. For example changing `price` in the cart, setting `quantity` to a negative number, adding `discount=100`, or changing `user_id` to someone else (which touches IDOR). Mass assignment is one specific kind of parameter tampering: adding a field the interface never shows.

### Why it is dangerous

The web interface only lets the user edit email and bio, so the developer thinks "the user will only send email and bio". But the request is entirely attacker-controlled, so they add `"isAdmin": true` to the JSON. If the backend binds everything, a normal account becomes an admin immediately.

## Demo

The workflow:

1. Perform the normal profile update, capturing the request in Burp.
2. Observe which fields appear in the GET profile response (often isAdmin, role, balance are exposed).
3. Add those fields to the update request body, with privileged values.
4. Send it again, then check the new privileges.

An example with curl:

```text
$ curl -s -X POST localhost:8053/api/profile \
    -H 'Content-Type: application/json' \
    -d '{"isAdmin":true}' -b cookie.txt
{"balance":0,"bio":"...","email":"...","isAdmin":true,"role":"user",
 "ok":true,"updated":["isAdmin"]}
```

The `isAdmin` field was never on the form, yet the server accepts it and writes it as true.

Tip for finding hidden fields: read the GET profile response, read the API docs, and try common names (admin, is_admin, isAdmin, role, roles, group, balance, credit, verified, status). Burp Intruder helps try many field names at once.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 5.4</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/5.4.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/5.4/app.py" download><i class="fa-solid fa-file-code"></i>app.py</a>
<a class="lab-file" href="/assets/labs-web/5.4/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
</div>
</div>

- Vulnerable app: `labs/5.4/` (runs locally, port 127.0.0.1:8053). Account `eve:pw`.
- Tasks:
  1. Log in as eve, view the profile (isAdmin=false), and try `/admin`, which returns 403.
  2. POST `/api/profile` with JSON that adds `isAdmin:true` (and try `balance`, `role` as well).
  3. Access `/admin` to collect the flag.
- Hint: the update endpoint uses the loop `for k, v in data.items(): user[k] = v`, binding everything, with no whitelist.
- Solution: `labs/5.4/exploit.py` and `labs/5.4/transcript.txt`.

Excerpt from a real run:

```text
    profile truoc: {'balance': 0, 'isAdmin': False, 'role': 'user', ...}
    gui: {'email': ..., 'isAdmin': True, 'balance': 1000000, 'role': 'admin'}
    profile sau: {'balance': 1000000, 'isAdmin': True, 'role': 'admin', ...}
[+] Nang quyen thanh cong qua mass assignment. FLAG = FLAG{5.4_mass_assignment_isAdmin_true}
```

## Common pitfalls

- Using a blacklist (block a few fields) instead of a whitelist (allow only a few); a blacklist always misses one.
- Thinking "the interface has no such field, so the user cannot send it"; the request is client-controlled.
- Using the same model for both input and output, so it exposes fields and accepts extra ones.
- Blocking only on the frontend while the backend still binds the raw body.

## Further reading

- OWASP API Security Top 10: API6 (Mass Assignment, named differently across versions).
- OWASP Mass Assignment Cheat Sheet.
- PortSwigger: Finding and exploiting mass assignment (within the API testing topic).

## Key takeaways

- Mass assignment: binding the request body straight onto the model also accepts privileged fields.
- Every field exposed in the GET response is a candidate to try inserting into the update request.
- Try the names: isAdmin, role, balance, verified, is_active, group.
- Defense: whitelist the writable fields; use a separate DTO/schema for input; mark sensitive fields read-only.
