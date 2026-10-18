---
title: "Lesson 6.2: Bypassing SSRF Filters"
image:
  path: /assets/img/covers/web-6-2-bypassing-ssrf-filters.webp
  alt: "Bypassing SSRF Filters"
date: 2024-06-15 14:10:00 +0700
categories: ["Web Security", "Web · SSRF and Request-Side"]
tags: [web, ssrf]
render_with_liquid: false
---

After this lesson you understand why naive anti-SSRF filters are easy to defeat, and you know a set of techniques that range from alternate IP notations to redirects and DNS rebinding. The labs here run on your own machine or on systems you are authorized to test.

![Bypassing SSRF Filters](/assets/img/web/web-6-2-bypassing-ssrf-filters.svg)
_One IP has many spellings, so a plain string blocklist always lets some of them through._

Part: 6 | Time: about 40 minutes | Difficulty: advanced

**Prerequisites:** Lesson 6.1 (Basic SSRF).

**Tools:** Burp Suite, curl, interactsh.

## Goals

After this lesson you understand why a string blocklist is always incomplete, you know the alternate IP notations (decimal, hex, octal, IPv6), you can bypass a filter with a 302 redirect and understand the idea of DNS rebinding, and you know the other schemes (file, gopher) and how to defend correctly.

## 1. Theory

When a developer first learns about SSRF, the usual reflex is to add a filter that blocks "localhost" and "127.0.0.1". But a filter that matches strings without normalizing the address will miss a great deal, because a single IP address has many ways to be written.

### 1.1 Alternate IP notations

`127.0.0.1` can also be written as:

| Form | Value | Note |
|---|---|---|
| Decimal | `2130706433` | the 4 octets merged into one 32-bit number |
| Hex | `0x7f000001` | or `0x7f.0x0.0x0.0x1` |
| Octal | `0177.0.0.1` | `0177` = 127 |
| Shortened | `127.1` | drop the middle octets, filled with 0 |
| Host "0" | `0` | maps to 0.0.0.0, also loopback |
| IPv6 loopback | `[::1]` | different notation, same meaning |
| IPv6-mapped | `[::ffff:7f00:1]` | IPv6 mapping of the IPv4 loopback |

All of these resolve to loopback, but none contains the string `127.0.0.1`, so they get past a string blocklist.

### 1.2 The userinfo "@" trick

A URL can carry a userinfo part before the `@`: `http://user:pass@host/`. An attacker abuses this:

```text
http://expected-host.com@127.0.0.1/     the real host is 127.0.0.1, the part before @ is just a username
http://127.0.0.1#@expected-host.com/     playing with the fragment
```

Combine it with decimal notation (`http://allowed@2130706433/`) to beat both a string filter and a "must contain the allowed domain" filter.

### 1.3 302 redirect

A filter usually checks only the initial URL. If the attacker supplies a valid URL (an allowed host) and that host returns a 302 redirect to an internal target, and the server's HTTP client follows the redirect automatically, then the final destination is never checked. This is why you must re-check after EACH redirect hop, or turn off automatic redirect following.

```text
attacker.com/bounce  ->  302 Location: http://169.254.169.254/latest/meta-data/...
```

### 1.4 DNS rebinding (the idea)

A better filter resolves the hostname to an IP and then checks whether that IP is internal. DNS rebinding attacks the window between the time of check and the time of use (TOCTOU, time of check vs time of use):

1. The attacker controls a domain and sets a very short TTL.
2. The first resolution (when the filter checks) returns a valid public IP, which passes the filter.
3. The later resolution (when the server actually connects) returns 127.0.0.1.

The server checks one IP but connects to a different one. The defense is to resolve once and connect to that exact IP (pin the IP), or re-check the IP right before opening the socket.

### 1.5 Other schemes

If the HTTP client supports several schemes, an attacker uses:

```text
file:///etc/passwd           read a local file
gopher://127.0.0.1:6379/_... send raw commands to Redis/SMTP (gopher can build an arbitrary request)
dict://127.0.0.1:11211/      talk to memcached
```

Python's `requests` library does not support gopher/file, but `curl` and some other clients do, so always try.

## 2. Demo

The strategy is: when you hit a filter, try the IP notations in turn, then "@", then redirect, then (if possible) other schemes. Use interactsh to confirm the server makes the call.

An example with curl, bypassing the filter with a decimal IP:

```text
$ curl -s 'localhost:8057/fetch?url=http://2130706433:8058/admin/secret'
{"body":"{\"flag\":\"FLAG{6.2_vuot_filter_ssrf_toi_noi_bo}\", ...}","ok":true, ...}
```

The filter blocks the string `127.0.0.1`, but `2130706433` does not contain that string while still resolving to loopback.

## 3. Lab

- Vulnerable app: `labs/6.2/` (runs locally). Main app on 127.0.0.1:8057 (with a naive filter), internal service on 127.0.0.1:8058.
- Components: `app.py` (string blocklist filter plus a `/bounce` redirector), `internal_service.py`, `exploit.py`.
- Task: reach `127.0.0.1:8058/admin/secret` even though the filter blocks the internal strings. Try all of them: decimal, hex, octal, shortened, host "0", "@" plus decimal, IPv6-mapped, and a 302 redirect through `/bounce`.
- Hint: the filter only does `if "127.0.0.1" in url ...`, with no normalization and no re-check after a redirect.
- Solution: `labs/6.2/exploit.py` and `labs/6.2/transcript.txt`.

An excerpt from a real run (every method gets through):

```text
[*] Buoc 0: thu URL noi bo that tha (phai bi filter chan):
    [403] {'blocked': True, ...}
[*] Vuot filter bang cac bieu dien host khac nhau:
    thap phan (decimal)      [200] FLAG=FLAG{6.2_vuot_filter_ssrf_toi_noi_bo}
    hex                      [200] FLAG=...
    octal                    [200] FLAG=...
    rut gon 127.1            [200] FLAG=...
    host '0' (=0.0.0.0)      [200] FLAG=...
    userinfo @ + decimal     [200] FLAG=...
    IPv6-mapped hex          [200] FLAG=...
[*] Vuot bang redirect 302 ...
    redirect qua /bounce  [200] FLAG=...
```

## 4. Common pitfalls

- Blocking only the string `127.0.0.1`/`localhost` and then feeling safe.
- Resolving and checking the IP but still letting the client follow redirects on its own (redirect bypass).
- Checking the IP once and then reconnecting (a second resolution), which is vulnerable to DNS rebinding.
- Forgetting the link-local range 169.254.0.0/16 and internal IPv6.
- Allowing only http but forgetting to forbid file/gopher at the client layer.

## 5. Further reading

- PortSwigger Web Security Academy: SSRF with blacklist/whitelist filter bypass, SSRF via redirect.
- HackTricks: SSRF bypass, URL format tricks, DNS rebinding.
- PayloadsAllTheThings: Server Side Request Forgery.
- Tools: Burp Suite, interactsh.

## 6. Key takeaways

- A string blocklist always misses, because one IP has many spellings.
- Try: decimal, hex, octal, shortened, "0", IPv6-mapped, "@", and a 302 redirect.
- DNS rebinding attacks the gap between the time of check and the time of connect.
- gopher/file/dict open deeper exploitation if the client supports them.
- The correct defense: resolve, then check the destination IP against an allowlist, pin the IP, re-check after redirects, and allow only http/https.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 6.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/6.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/6.2/app.py" download><i class="fa-solid fa-file-code"></i>app.py</a>
<a class="lab-file" href="/assets/labs-web/6.2/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
<a class="lab-file" href="/assets/labs-web/6.2/internal_service.py" download><i class="fa-solid fa-file-code"></i>internal_service.py</a>
</div>
</div>
