---
title: "Lesson 5.3: CSRF, tokens and SameSite cookies"
image:
  path: /assets/img/covers/web-5-3-csrf-tokens-samesite-cookies.webp
  alt: "CSRF, tokens and SameSite cookies"
date: 2024-06-15 13:15:00 +0700
categories: ["Web Security", "Web · Access Control"]
tags: [web, csrf, access-control]
render_with_liquid: false
---

CSRF, short for Cross-Site Request Forgery, exploits one fact about browsers: when a request goes to a site, the browser automatically attaches that site's cookies, even when the request was started from a different page. This lesson shows why a hostile page can force a victim's browser to perform an action on another site, and how to block it with a CSRF token and a SameSite cookie.

![CSRF, tokens and SameSite cookies](/assets/img/web/web-5-3-csrf-tokens-samesite-cookies.svg)
_The attacker's page auto-submits a form; the browser attaches the victim's session cookie to the cross-site request._

Level: medium, about 35 minutes. Prerequisites: Lesson 5.1 (IDOR), and an understanding of cookies and the same-origin policy. Tools: Burp Suite, a browser, curl.

## Goals

After this lesson you understand CSRF (Cross-Site Request Forgery) and the conditions for it to occur, you can build an attacker page that auto-submits to force an action on the victim site, you understand the defenses (a synchronizer CSRF token and the SameSite cookie), and you know when CSRF is not exploitable.

## Theory

### What CSRF is

CSRF, short for Cross-Site Request Forgery, exploits one fact about browsers: when sending a request to a site, the browser AUTOMATICALLY attaches that site's cookies, even when the request was started from a different page.

The scenario: the victim is logged in to bank.local (the browser holds the session cookie). The victim opens an attacker's page (through a link, an ad, or an email). That page silently sends a POST request to bank.local. The browser attaches the victim's session cookie, the server believes the victim acted, and it carries out the action (transfer money, change email, change password).

```text
Victim (logged in to shop.local)
   |
   |  opens the attacker page (evil.example)
   v
evil.example  --- auto-submitting form --->  shop.local/change-email
                  (the browser attaches shop.local's session cookie)
                                            |
                                            v
                                    email changed to the attacker's
```

### Conditions for CSRF to be exploitable

1. There is a valuable action (change email, change password, transfer money).
2. The app relies only on the cookie to identify the session, with no other secret value accompanying the request.
3. The request contains no parameter the attacker cannot guess.

If any one of the three is missing, CSRF is hard or impossible to exploit.

### Defenses

- CSRF token: the server generates a random secret string bound to the session and embeds it in a legitimate form. Every state-changing request must carry the correct token. An attacker page on a different origin CANNOT read this token (because the same-origin policy blocks reading cross-origin content), so it cannot forge the request.
- SameSite cookie: a cookie attribute that controls whether the browser sends the cookie on a cross-site request.
  - `SameSite=Strict`: do not send the cookie on any cross-site request.
  - `SameSite=Lax` (the default in modern browsers): send the cookie only for top-level navigation by GET, not for a cross-site POST form. Lax alone already blocks most form-POST CSRF.
  - `SameSite=None`: send the cookie on every cross-site request (must be paired with `Secure`). This is the configuration most exposed to CSRF.
- Check `Origin`/`Referer` for sensitive actions, and require re-confirmation (password or OTP).

## Demo

A typical attacker page: a hidden form that auto-submits as soon as it loads, with nothing for the victim to click.

```html
<form id="csrf" action="http://127.0.0.1:8052/change-email" method="POST">
  <input type="hidden" name="email" value="attacker@evil.example">
</form>
<script>document.getElementById('csrf').submit();</script>
```

When the victim (while logged in) opens this page, the browser sends a POST to `/change-email` with the session cookie, and the email is changed. In the lab, we imitate the browser behavior with a Python client that carries the victim's cookie, reads the form on the attacker page, and sends it, to prove the action really happens.

Burp Suite includes Engagement tools, Generate CSRF PoC, which quickly builds an attacker page from a captured request.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 5.3</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/5.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/5.3/app.py" download><i class="fa-solid fa-file-code"></i>app.py</a>
<a class="lab-file" href="/assets/labs-web/5.3/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
</div>
</div>

- Vulnerable app: `labs/5.3/` (runs locally, port 127.0.0.1:8052). Account `victim:pw`.
- Components: `app.py` (with the vulnerable endpoint `/change-email` and the patched endpoint `/change-email-safe`), `attacker.html` (the auto-submitting form), `exploit.py` (simulates the victim's browser).
- Tasks:
  1. Log in as the victim and view the current email.
  2. Run the exploit that simulates the victim opening `attacker.html`, and confirm the email was changed.
  3. Try the attack again against `/change-email-safe` (which has a CSRF token) and observe it blocked with 403.
- Hint: the vulnerable endpoint checks no token; the patched endpoint requires a `csrf_token` matching the token in the session, which the attacker page cannot read.
- Solution: `labs/5.3/exploit.py` and `labs/5.3/transcript.txt`.

Excerpt from a real run:

```text
    email hien tai: victim@shop.local
...
    email SAU tan cong: attacker@evil.example
    => CSRF thanh cong!
[*] Buoc 3: thu CSRF len endpoint co token /change-email-safe
    POST /change-email-safe (token bua) -> 403 {'error': 'CSRF token sai/thieu', 'ok': False}
```

## Common pitfalls

- Setting a CSRF token but the server not actually checking it, or accepting an empty token.
- Using the same token for every user, or a token not bound to the session.
- Letting a sensitive endpoint accept GET (GET should not change state).
- Thinking a Referer check alone is enough; the Referer can be absent in some legitimate cases and needs careful handling.
- An API that uses a token in the `Authorization` header (not a cookie) is less prone to classic CSRF, but if the app still accepts a cookie as the session, it remains exposed.

## Further reading

- PortSwigger Web Security Academy: Cross-site request forgery (CSRF), with labs on missing token, unchecked token, and SameSite bypass.
- OWASP CSRF Prevention Cheat Sheet.
- MDN: SameSite cookies.

## Key takeaways

- CSRF exploits the browser automatically attaching the cookie on a cross-site request.
- Conditions: a valuable action, reliance only on the cookie, and no hard-to-guess parameter.
- Defend with a synchronizer CSRF token on every state-changing action.
- Set the session cookie to `SameSite=Lax` or `Strict`.
- Check Origin/Referer and re-confirm for important actions.
