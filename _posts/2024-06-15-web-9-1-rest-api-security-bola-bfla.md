---
title: "Lesson 9.1: REST API Security, BOLA and BFLA"
image:
  path: /assets/img/covers/web-9-1-rest-api-security-bola-bfla.webp
  alt: "REST API Security, BOLA and BFLA"
date: 2024-06-15 17:05:00 +0700
categories: ["Web Security", "Web · API and Modern Web"]
tags: [web, api, access-control]
render_with_liquid: false
---

By the end of this lesson you understand why APIs are more prone to access control bugs than traditional web apps, and you can exploit both BOLA (reading another user's data) and BFLA (calling an admin function) on a real Flask REST API. The cause is that an API exposes its objects directly through URLs, which puts the weight on authorization.

![REST API Security, BOLA and BFLA](/assets/img/web/web-9-1-rest-api-security-bola-bfla.svg)
_The server checks that the token is valid but not that the caller owns the object (BOLA) or holds the admin role (BFLA)._

Part: 9 (API and Modern Web) | Time: about 45 minutes | Difficulty: medium

**Prerequisites:** Lesson 5.1 (IDOR) and Lesson 5.2 (Broken access control), and some comfort reading requests in Burp or curl.

**Tools:** curl, Python requests, Burp Suite, Postman.

## Goals

After this lesson you understand what makes a REST API different from a server-rendered web app: state, token authentication, and many objects exposed directly through URLs. You can tell BOLA (Broken Object Level Authorization) from BFLA (Broken Function Level Authorization), recognize common bugs such as missing rate limit, verb tampering, and excessive data exposure, and exploit BOLA and BFLA on a REST Flask lab.

## 1. Theory

A REST API (Representational State Transfer, an API design style that uses HTTP as the protocol, with one URL per resource) is the backbone of almost every modern application: SPA web apps (single page applications, web apps that run in JavaScript), mobile apps, and services that call each other. Unlike a web app rendered on the server, a REST API usually returns plain JSON, authenticates with a token (Bearer token, API key, JWT) rather than a pre-rendered cookie session, and most importantly, it exposes objects directly through URLs such as `/api/users/42` and `/api/orders/1007`.

That direct exposure is exactly what makes access control the number one weak point. The OWASP API Security Top 10 puts two access control bugs at the top of the list:

- **API1 BOLA (Broken Object Level Authorization)**: the server checks whether you are logged in (authentication) but forgets to check whether the object you ask for is yours (object-level authorization). This is IDOR applied to an API. Change the `id` in the URL and you read another user's data.
- **API5 BFLA (Broken Function Level Authorization)**: the server forgets to check your role when you call a sensitive function. An ordinary user can call an endpoint like `/api/admin/...` just because they guessed the path.

The two bugs sound alike but differ in nature:

| | BOLA | BFLA |
|---|---|---|
| Breaks | Permission over one specific **object** | Permission to call a **function/endpoint** |
| Example | Reading `/api/users/2` while you are user 1 | Calling `/api/admin/promote` while you are an ordinary user |
| Root cause | Missing "owner == caller" check | Missing "role == required_role" check |

Beyond those two, a REST API also commonly suffers from:

- **Excessive data exposure**: the server returns the whole database record (including `ssn`, `card`, `password_hash`) and lets the client "filter the display". An attacker reads the raw JSON and sees everything.
- **Missing rate limit**: no limit on request frequency, which opens the door to brute force, enumeration, and scraping.
- **Verb tampering (playing with the HTTP method)**: authorization is applied only to `GET` but forgets `PUT`/`DELETE`, or the framework treats `HEAD` like `GET` but skips the check. Changing the method sometimes bypasses the control.
- **Mass assignment**: the client adds an extra `"role":"admin"` field to a profile update body, and the server assigns all of it to the object (see Lesson 5.4).

## 2. Demo

The REST Flask lab in `labs/9.1/` builds a small shop API where each user has their own Bearer token. We play `alice`, an ordinary user.

Step 1, log in with our own account to get a valid token:

```text
POST /api/login
{"username":"alice","password":"alice123"}

-> {"ok":true,"token":"tok-alice-111","user_id":1,"role":"user"}
```

Step 2, use alice's token to request bob's object (`id=2`). The server only checks that the token is valid, not that the token belongs to id 2:

```text
GET /api/users/2
Authorization: Bearer tok-alice-111

-> HTTP 200
{"id":2,"username":"bob","email":"bob@shop.local",
 "ssn":"002-22-2222","card":"5500-0000-0000-0004",
 "secret_note":"FLAG{9.1_bola_read_other_users_object}"}
```

That is BOLA, plus excessive data exposure (ssn, card, and secret_note should not be returned). Step 3, try to call an admin function with an ordinary user's token:

```text
POST /api/admin/promote
Authorization: Bearer tok-alice-111
{"user_id":1}

-> HTTP 200
{"ok":true,"message":"user 1 da thanh admin","promoted_by":"alice",
 "flag":"FLAG{9.1_bfla_function_level_bypass}"}
```

That is BFLA: the endpoint only asks "is there a token" and not "is this an admin".

## 3. Lab

- Vulnerable app: `labs/9.1/` (Flask, binds `127.0.0.1:8071`, run locally per the lab README).
- Task:
  1. Log in with the `alice` account and get a token.
  2. Use that token to read bob's object and orders, and find the `secret_note`.
  3. Promote yourself through `/api/admin/promote`.
- Hint: you only need to change the `id` number in the URL; for BFLA, just send a request to the admin endpoint with an ordinary token and see whether the server blocks it.
- Solution: the exploit script `exploit.py` and `transcript.txt` in `labs/9.1/`.

## 4. Common pitfalls

- Thinking "a token means it is safe". A token only proves identity, it does not automatically limit which objects you can reach.
- Thinking that hiding the admin endpoint from the UI is enough. An attacker reads the JS files, the API documentation (Swagger/OpenAPI), or guesses the path.
- Testing only with your own `id` and never seeing the bug. You always need at least two accounts to cross-check.
- Placing authorization at the gateway or UI rather than in each service, which is easy to bypass by calling the API directly.

## 5. Further reading

- OWASP API Security Top 10 (2023): API1 BOLA, API3 Broken Object Property Level Authorization, API5 BFLA.
- PortSwigger Web Security Academy: the Access control vulnerabilities and API testing topics.
- Lesson 5.1 (IDOR) and Lesson 5.4 (Mass assignment) in this series to connect the access control thread.

## 6. Key takeaways

- Authentication (who you are) is not authorization (what you are allowed to do). APIs often do the first and forget the second.
- BOLA: try changing every `id` to another user's object. BFLA: try calling every sensitive endpoint with a low-privilege account.
- Read the returned JSON carefully: is there any field that should not be exposed (excessive data exposure).
- No rate limit means brute force and enumeration run freely.
- Try playing with the HTTP method (`GET` vs `POST` vs `PUT` vs `DELETE` vs `PATCH`) at endpoints that have authorization.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 9.1</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/9.1.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/9.1/app.py" download><i class="fa-solid fa-file-code"></i>app.py</a>
<a class="lab-file" href="/assets/labs-web/9.1/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
</div>
</div>
