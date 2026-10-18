---
title: "Lesson 4.3: Attacking JWT with alg none and weak secrets"
image:
  path: /assets/img/covers/web-4-3-attacking-jwt-alg-none-weak-secrets.webp
  alt: "Attacking JWT with alg none and weak secrets"
date: 2024-06-15 12:15:00 +0700
categories: ["Web Security", "Web · Authentication and Session"]
tags: [web, jwt, auth]
render_with_liquid: false
---

A JWT is a token made of three parts joined by dots, and the payload is only encoded, not encrypted, so anyone can read it. The signature is the only thing standing between a user token and an admin token, so when a server verifies the signature loosely the whole scheme falls apart. In this lesson I read the structure of a JWT, forge a token through `alg=none`, crack a weak HS256 secret and re-sign, and work through kid injection, the jwk header, and HS/RS algorithm confusion. The lab runs on your own machine.

![Attacking JWT with alg none and weak secrets](/assets/img/web/web-4-3-attacking-jwt-alg-none-weak-secrets.svg)
_Each attack ends with a valid role=admin token: alg=none drops the signature, a cracked secret re-signs, and kid=/dev/null signs with an empty key._

Level: advanced, about 60 minutes. Prerequisites: Lesson 4.2 Session management, plus base64 and HMAC basics. Tools: jwt_tool, hashcat or John, Python (PyJWT or hand-rolled), Burp JWT Editor.

## Goals

After this lesson you can read and hand-build a JWT from its three parts header, payload, and signature. You can forge a token with `alg=none`, crack a weak HS256 secret with a wordlist and then re-sign the token, and understand and recognize kid injection, jwk/jku/x5u header injection, and HS/RS confusion.

## Theory

### What a JWT is

A JWT (JSON Web Token) is a string of three parts joined by dots: `header.payload.signature`. Each part is base64url encoded (a URL-safe variant of base64).

- **Header:** JSON describing the signing algorithm, for example `{"alg":"HS256","typ":"JWT"}`.
- **Payload:** JSON holding the claims (statements), for example `{"user":"wiener","role":"user"}`. The payload is NOT encrypted, only encoded, so anyone can read it.
- **Signature:** a signature over `base64url(header).base64url(payload)`, used to prevent tampering.

Two common algorithm families:

- **HS256 (HMAC-SHA256):** symmetric, one secret both signs and verifies. Anyone who knows the secret can sign any token.
- **RS256 (RSA-SHA256):** asymmetric, a private key signs and a public key verifies. The public key is public and cannot sign tokens.

A JWT is often used as a stateless authentication token: the server stores no session and only verifies the signature on each request. The core weakness is that if the verification is wrong or the secret is weak, an attacker makes their own valid token with `role=admin`.

### alg=none

The JWT spec has an algorithm `none` meaning "no signature", originally intended for cases where the token is protected at another layer. If the server verifies loosely and accepts `alg=none`, the attacker sets the header to `{"alg":"none"}`, writes any payload they want, and leaves the signature part empty. The token `header.payload.` (empty signature) is accepted. This is the most classic forging flaw.

### HS256 weak secret

With HS256 the signature is `HMAC_SHA256(secret, signing_input)`. If the secret is weak (dictionary, short, a default like `secret`, `changeme`, `your-256-bit-secret`), the attacker cracks it offline: for each candidate secret, recompute the HMAC over the real token and compare to the real signature. A match reveals the secret. With the secret in hand, they sign any `role=admin` token. Tools: `hashcat -m 16500`, John the Ripper, or jwt_tool with a wordlist. This lesson builds the crack loop in Python to make the mechanism clear.

### HS256 mistaken for RS256 (algorithm confusion)

This bug happens when the server uses RS256 (verify with the public key) but the verification code trusts the `alg` in the token header. The attacker takes the public key (usually public, or leaked through `/jwks.json`), changes the header to `HS256`, then signs the token with HMAC using the content of that public key as the key. The server thinks it is HS256, so it uses the public key as the HMAC secret to verify, and the signature matches. Because the public key is available to everyone, the attacker signs a valid token. The defense is to fix the list of allowed algorithms on the server and not read `alg` from the token.

### kid injection

`kid` (key id) is an optional field in the header that tells the server which key to verify with. If the server uses `kid` in a dangerous way, a vulnerability appears:

- **Path traversal:** the server treats `kid` as the path to a file holding the key, then reads that file. The attacker points `kid` at a file whose content is known in advance, for example `/dev/null` (empty), then signs the token with the empty key. Or they point at a public static file whose content is already known.
- **SQL injection:** if `kid` is placed into a query that looks up the key, an attacker injects to return a value they control.

### jwk, jku, x5u header injection

Some headers let a token carry its own key or point to where the key is fetched:

- **jwk:** embeds a public key directly into the header. If the server trusts `jwk` to verify, the attacker embeds their own key and signs with the matching private key.
- **jku / x5u:** a URL to a key set (JWKS) or certificate. If the server loads the key from the URL in the token without checking, the attacker points it at their own server.

The general rule is: do not let a token declare which key verifies it.

## Demo

Lab 4.3 at `127.0.0.1:8043` issues HS256 JWTs with the weak secret `secret`, has a hand-written verifier that accepts `alg=none`, and uses `kid` as a file path.

### Reading the user token

Logging in as `wiener:peter` returns a `role=user` token. Decoding the base64url payload shows `{"user":"wiener","role":"user"}`. Calling `/admin` is refused:

```text
/admin with user token -> {'error': 'not admin', 'ok': False, 'you': {'role': 'user', 'user': 'wiener'}}
```

### Forging with alg=none

Set the header `{"alg":"none","typ":"JWT"}`, the payload `{"user":"admin","role":"admin"}`, and an empty signature:

```text
forged: eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4ifQ.
/admin -> {'flag': 'FLAG{4.3_jwt_forged_admin}', 'ok': True, 'user': 'admin'}
```

A quick test with curl and basenc:

```text
H=$(printf '{"alg":"none","typ":"JWT"}' | basenc --base64url | tr -d '=')
P=$(printf '{"user":"admin","role":"admin"}' | basenc --base64url | tr -d '=')
curl -s localhost:8043/admin -H "Authorization: Bearer $H.$P."
```

### Cracking the HS256 secret and re-signing

Use the signature of a real token as the oracle and run through a small wordlist:

```text
secret cracked = 'secret'
/admin -> {'flag': 'FLAG{4.3_jwt_forged_admin}', 'ok': True, 'user': 'admin'}
```

In the real world this step runs hashcat `-m 16500` with rockyou and hits in a few seconds if the secret is weak.

### kid injection pointing at /dev/null

Set `kid=/dev/null` so the server reads the key from an empty file (the key becomes an empty string), then sign the token with that empty key:

```text
forged kid=/dev/null: eyJ...ImtpZCI6Ii9kZXYvbnVsbCJ9.eyJ1c2VyIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4ifQ.gorX...
/admin -> {'flag': 'FLAG{4.3_jwt_forged_admin}', 'ok': True, 'user': 'admin'}
```

All three methods produce a valid `role=admin` token.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 4.3</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/4.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/4.3/app.py" download><i class="fa-solid fa-file-code"></i>app.py</a>
<a class="lab-file" href="/assets/labs-web/4.3/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
</div>
</div>

- Vulnerable app: `labs/4.3/` (README in the lab, runs locally on port 8043).
- Task: forge a `role=admin` token that `/admin` accepts, by any of the three methods above. The app only gives you a plain user token (`wiener:peter`).
- Hints: the payload is just base64url of JSON, edit it freely; for alg=none leave the signature empty; for the crack use a wordlist of common secrets; for kid try files with known content.
- Solution: `exploit.py` and `transcript.txt` in `labs/4.3/`. The transcript shows all three methods forging successfully, flag `FLAG{4.3_jwt_forged_admin}`.

## Common pitfalls

- A good JWT library rejects `alg=none` by default and requires the algorithm to be specified; the flaw usually sits in hand-written verification code or misconfiguration, not in the library.
- Forgetting to strip the `=` padding when base64url encoding by hand, producing a malformed token.
- Cracking the wrong part: you must crack over the correct `signing_input` (the header.payload base64url verbatim, not decoded).
- Thinking a JWT is always safe because it "is signed"; the signature is only as strong as the key and as tight as the verification step.

## Further reading

- PortSwigger Web Security Academy, the JWT attacks topic (all the labs on alg none, weak secret, jwk/jku/kid injection, algorithm confusion).
- The jwt_tool (ticarpi) tool and its documentation; hashcat mode 16500.
- RFC 7519 (JWT), RFC 7515 (JWS); OWASP JWT Cheat Sheet.
- Related: Lesson 9.1 REST API security.

## Key takeaways

- Always decode the base64url header and payload first; the payload is not encrypted.
- Try `alg=none` (and the variants `None`, `NONE`, `nOnE`) first.
- HS256 with a weak secret can be cracked offline; collect real tokens then run hashcat or John.
- RS256 needs checking: does the server fix the algorithm, and is there a risk of HS/RS confusion.
- Inspect odd headers: `kid`, `jwk`, `jku`, `x5u`; they are the door to injecting a key or a path.
- Exposed tokens usually sit in the Authorization header, a cookie, or localStorage.
