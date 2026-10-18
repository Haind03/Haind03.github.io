---
title: "Lesson 4.5: Password reset and MFA bypass"
image:
  path: /assets/img/covers/web-4-5-password-reset-mfa-bypass.webp
  alt: "Password reset and MFA bypass"
date: 2024-06-15 12:25:00 +0700
categories: ["Web Security", "Web · Authentication and Session"]
tags: [web, mfa, password-reset]
render_with_liquid: false
---

A password reset flow lets someone change a password without the old one, so it is a prime target for account takeover. If the reset token is derived from known data like an email, an attacker computes it offline and never touches the victim's inbox. In this lesson I exploit a guessable reset token, poison the reset link through the Host header, list the channels where tokens leak, and bypass MFA three ways: a missing check at the verification step, response manipulation, and brute forcing the OTP. The lab runs on your own machine.

![Password reset and MFA bypass](/assets/img/web/web-4-5-password-reset-mfa-bypass.svg)
_A deterministic token is computed offline from the email, the Host header rewrites the reset link to the attacker, and a page that only checks "password passed" lets MFA be skipped._

Level: advanced, about 50 minutes. Prerequisites: Lesson 4.1 Authentication flaws, Lesson 4.2 Session management. Tools: curl, Python requests, Burp Suite (Repeater, Intruder).

## Goals

After this lesson you understand a secure password reset flow and its failure points. You can exploit a guessable reset token and Host header poisoning, recognize the channels where a reset token leaks, and bypass MFA three ways: a missing check at the verification step, response manipulation, and brute forcing the OTP.

## Theory

### The password reset flow

A typical reset flow: the user enters an email at `/forgot`, the server generates a reset token, binds the token to the account, and sends an email with a link `https://app/reset?token=...`. The user clicks the link, enters a new password, and the server checks the token then changes the password. Because this flow allows changing the password without the old one, it is a prime target for account takeover.

A secure reset token must be strongly random and long enough (not guessable), used once, expire quickly (a few minutes to an hour), bound tightly to the correct account, and sent only over a trusted channel.

### Weak or guessable reset token

The broken patterns:

- **Derived from known data:** the token is md5/sha1 of the email, the username, or the email plus a fixed pepper (salt). Knowing the victim's email, you compute the token offline without touching their inbox.
- **Sequential or time-based:** the token is an incrementing number, or generated from `time()`/`rand()` seeded with time. Knowing roughly when the request was made shrinks the guessing space.
- **Too short:** a 4 to 6 digit token can be brute forced when there is no rate limit.

### Host header poisoning

Many apps build the reset link by taking the host from the request's `Host` header (or `X-Forwarded-Host`). Without a check, the attacker sends `/forgot` with `Host: attacker.evil` for the victim's email. The server generates a real token but embeds it in a link pointing to `http://attacker.evil/reset?token=...`. When the victim clicks (or when a preview or anti-virus scans the link), the real token flies to the attacker's server. This leaks the token even when the token itself is strong.

### Token leak channels

Besides Host header poisoning, a reset token also leaks through: the Referer header (the reset page loads an external resource), browser history and logs if the token is in the URL, a token that does not expire so it can be reused later, and a response message that leaks the token or confirms the email exists (username enumeration, as in Lesson 4.1).

### MFA and the bypass routes

MFA (Multi-Factor Authentication) adds a factor beyond the password, commonly an OTP (One-Time Password) through an app or SMS. Correct MFA must require completing the second step before granting a full session, resist brute force (rate limit, lock after a few wrong tries), and not let the client decide the result. The bypass routes:

- **Missing check at the verification step:** after passing the password, the app issues a "half" session and only then asks for the OTP. If the later pages only check "passed the password" and not "passed the OTP", the attacker jumps straight to an internal page and skips the OTP entirely.
- **Response manipulation:** if the success decision is in a response the client relies on (for example `{"mfaPassed": false}`), the attacker edits the response to `true` to pass. Common in mobile apps and SPAs that trust the response.
- **Brute OTP:** a short OTP (4 to 6 digits) plus no rate limit lets you try the whole space. Even with a try limit, if the counter resets by requesting a new OTP, or the OTP does not change between attempts, it is still brute forceable.
- Also: logic flaws such as sending the OTP for your own account but verifying it for another account, or dropping the MFA parameter from the request.

## Demo

Lab 4.5 at `127.0.0.1:8046` has a deterministic reset token (derived from the email), a reset link built from the Host header, and a broken MFA flow.

### Guessable reset token

The token is `md5(email + fixed pepper)[:12]`. Knowing the victim's email, compute the token offline then change the password:

```text
token computed offline = 35fda2afc20b
/reset -> {'email': 'ceo@corp.local', 'flag': 'FLAG{4.5_reset_token_predictable}', 'message': 'password changed', 'ok': True}
```

The account `ceo@corp.local` is taken over without ever knowing the old password.

### Host header poisoning

Send `/forgot` with `Host: attacker.evil`:

```text
$ curl -s -X POST localhost:8046/forgot -H 'Host: attacker.evil' -d email=ceo@corp.local
{"email":"ceo@corp.local","ok":true,"reset_link":"http://attacker.evil/reset?token=35fda2afc20b"}
```

The reset link carries the real token but points at the attacker's domain, so the token leaks when the victim clicks.

### Bypassing MFA with a missing check

Pass the password step to receive `mfa_token`, then go straight to the account page without entering an OTP:

```text
passed password step, received mfa_token=22077d836d (stage=mfa_required)
/mfa/account (no OTP entered) -> {'flag': 'FLAG{4.5_mfa_bypassed}', 'note': 'accessible without entering an OTP', 'ok': True, 'user': 'bob@corp.local'}
```

The `/mfa/account` page only checks that the password was passed, not that the OTP was passed.

### Brute OTP

A 4-digit OTP, no rate limit, try `0000` to `9999`:

```text
[+] correct OTP = 2912 after 2913 tries (not blocked)
```

The OTP is random on each run so the number of tries varies, but it is never blocked.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 4.5</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/4.5.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/4.5/app.py" download><i class="fa-solid fa-file-code"></i>app.py</a>
<a class="lab-file" href="/assets/labs-web/4.5/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
</div>
</div>

- Vulnerable app: `labs/4.5/` (README in the lab, runs locally on port 8046).
- Task: (1) guess the reset token of `ceo@corp.local`, change the password, take over the account; (2) make the reset link point at the attacker's domain through Host header poisoning; (3) bypass MFA with a missing check; (4) brute the OTP.
- Hints: the token is deterministic, so compute it offline if you know how it is generated; try changing the `Host` header; inspect whether an internal page checks "passed MFA" or only "passed the password"; the OTP is short and not locked.
- Solution: `exploit.py` and `transcript.txt` in `labs/4.5/`. The transcript shows `ceo` taken over through reset and bob's MFA bypassed, flags `FLAG{4.5_reset_token_predictable}` and `FLAG{4.5_mfa_bypassed}`.

## Common pitfalls

- Assuming a long token is safe; a long token that is deterministic from known data is still guessable.
- Forgetting Host header poisoning because "there is already HTTPS"; the problem is in the content of the link, not the transport channel.
- Testing only the OTP verify step and skipping the pages after it; many bypasses sit on internal pages that do not check MFA.
- Believing MFA is untouchable; MFA is only strong when every step checks and there is brute force protection.

## Further reading

- PortSwigger Web Security Academy, the Authentication topic (labs on password reset broken logic, password reset poisoning via middleware, 2FA bypass, 2FA broken logic, 2FA brute-force).
- OWASP WSTG, Testing for Weak Password Change or Reset Functionalities and Testing Multi-Factor Authentication.
- OWASP Forgot Password Cheat Sheet.
- Related: Lesson 4.1 Authentication flaws, Lesson 6.3 Open redirect.

## Key takeaways

- A reset token must be strongly random, used once, expire quickly, and bound to the correct account.
- Try changing `Host` and `X-Forwarded-Host` to see whether the reset link gets poisoned.
- Check whether a token in the URL leaks through Referer, logs, or history, and whether it expires.
- MFA: check whether every page after the password actually demands "passed the OTP" (missing check).
- Try editing the response at the verify step (response manipulation) and brute the OTP when there is no rate limit.
