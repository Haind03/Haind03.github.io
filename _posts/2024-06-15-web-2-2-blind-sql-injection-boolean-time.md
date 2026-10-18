---
title: "Lesson 2.2: Blind SQL Injection with Boolean and Time"
image:
  path: /assets/img/covers/web-2-2-blind-sql-injection-boolean-time.webp
  alt: "Blind SQL Injection with Boolean and Time"
date: 2024-06-15 10:10:00 +0700
categories: ["Web Security", "Web · Injection"]
tags: [web, sqli, blind-sqli]
render_with_liquid: false
---

By the end of this lesson you can extract data even when the application does not print the query result, relying only on a true/false difference or a difference in response time.

![Blind SQL Injection with Boolean and Time](/assets/img/web/web-2-2-blind-sql-injection-boolean-time.svg)
_Each injected condition returns one bit, and binary search over SUBSTR recovers the secret character by character._

Part 2, about 60 minutes, medium difficulty. Prerequisite: Lesson 2.1. Tools: curl, Python.

## Goals

After this lesson you understand when you are forced to use blind SQLi, you build a boolean oracle from a difference in the true/false response, you extract data character by character with `SUBSTR` and binary search, and you use response time (time-based) when there is not even a content difference.

## Theory

### When it is "blind"

In Lesson 2.1 the application printed the query result on screen, so we used UNION to pull data out. But many SQLi points display nothing. An API that only returns "yes/no", a form that only says "login succeeded/failed", an endpoint that always returns the same content. In those cases we cannot read the data directly and have to infer it bit by bit. That is blind SQLi.

There are two kinds of inference channel (called an oracle, a source that tells you true or false):

- Boolean-based: inject a condition and watch whether the response changes depending on whether the condition is true or false.
- Time-based: inject a condition so that when it is true the query runs noticeably slower, then measure the response time.

### Boolean-based

The idea: we cannot ask "what is the password", but we can ask "is the first character of the password greater than M". Each question gives only one bit of information (true or false), but many questions combined recover the whole string.

Common functions:

- `SUBSTR(string, i, 1)`: take the `i`-th character.
- `unicode(c)` (sqlite) or `ASCII(c)` (MySQL): turn a character into its numeric code for comparison.
- `LENGTH(string)`: the length, so you know when to stop extracting.

Instead of a linear scan of 95 printable characters, we use binary search: each character needs only about 7 questions (`log2(95)`), which is much faster.

### Time-based

When the response is identical whether the condition is true or false (no content oracle), we create an oracle from time: if the condition is true, make the DBMS do something slow.

- MySQL: `SLEEP(5)`, usually wrapped in `IF(cond, SLEEP(5), 0)`.
- PostgreSQL: `pg_sleep(5)`.
- MSSQL: `WAITFOR DELAY '0:0:5'`.
- sqlite: has no `SLEEP`. The common trick (also what sqlmap does) is to force heavy computation: `LIKE('A', HEX(RANDOMBLOB(N)))` with a large `N`. `RANDOMBLOB(N)` makes a random block of `N` bytes, `HEX(...)` turns it into a hex string twice as long, which is very slow when `N` is in the tens of millions.

Wrap it in `CASE WHEN (cond) THEN <slow work> ELSE 0 END`: the condition true means slow, false means fast. Measuring the delay tells you true or false.

## Demo

The lab `labs/2.2/` has two endpoints, both injecting into `SELECT id FROM users WHERE username='<user>'`:

- `/api/check?user=`: returns `FOUND` when there is a row, `NOTFOUND` when there is not. This is the boolean oracle.
- `/api/log?user=`: always returns `ok` regardless of the result. No content oracle, so time-based is required.

The goal: extract the password of `admin`, which is the flag.

### Building a boolean oracle

The base payload is `admin' AND (<condition>)-- -`. When the condition is true and admin exists, the query returns a row and the server replies `FOUND`:

```text
admin' AND 1=1-- -   ->  FOUND
admin' AND 1=2-- -   ->  NOTFOUND
```

### Find the length, then extract each character

The condition compares the code of the `i`-th character of the admin password:

```sql
admin' AND unicode(substr((SELECT password FROM users WHERE username='admin'),I,1)) > MID-- -
```

Use binary search over `MID` to find the exact code of each character. The script `exploit.py` automates the whole thing and prints:

```text
  admin' AND 1=1 -> FOUND
  admin' AND 1=2 -> NOTFOUND
  Do dai mat khau admin = 27
  Trich: WEB{bl1nd_b00l3an_and_t1me}
  => Mat khau admin (FLAG): WEB{bl1nd_b00l3an_and_t1me}
```

### Time-based on an endpoint that leaks nothing

`/api/log` always returns `ok`, so boolean is useless. We use a payload that creates a delay:

```sql
admin' AND CASE WHEN (<cond>) THEN LIKE('A', HEX(RANDOMBLOB(90000000))) ELSE 0 END-- -
```

Measure the time: the condition true means a slow response, false means fast.

```text
  CASE WHEN 1=1 -> tre 1.43s (TRUE)
  CASE WHEN 1=2 -> tre 0.22s (FALSE)
  ky tu 1 = 'W'   ky tu 2 = 'E'   ky tu 3 = 'B'   ky tu 4 = '{'
  => 4 ky tu dau trich bang TIME-BASED: WEB{
```

The first four characters extracted with time-based match the boolean result. The full real output is in `labs/2.2/transcript.txt`.

Note: the `RANDOMBLOB` number depends on machine speed. On a fast machine increase it, on a slow machine decrease it, as long as the difference between true and false is clear enough (the lab sets a threshold of 0.5s).

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 2.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/2.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/2.2/app.py" download><i class="fa-solid fa-file-code"></i>app.py</a>
<a class="lab-file" href="/assets/labs-web/2.2/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
</div>
</div>

- **App:** `labs/2.2/` (Flask + sqlite). Build it per the README in the lab, run it locally on port 8022.
- **Task:** extract the password of `admin` (the flag) using only the `FOUND`/`NOTFOUND` response, then try extracting the first few characters with time-based on `/api/log`.
- **Hints:** find the length first with `LENGTH(...)`, then binary search each character code with `unicode(substr(...))`. Use `>` rather than a linear scan for speed.
- **Answer:** `exploit.py` and `transcript.txt` in `labs/2.2/`.

## Common pitfalls

- A linear scan across the whole ASCII table is very slow: always prefer binary search.
- Time-based is sensitive to network jitter and machine load: repeat, take a safe threshold, and avoid an `N` that is too small.
- Forgetting the base part has to be correct (`admin'` must match an existing row) or the `AND` condition is meaningless.
- sqlite has no `SLEEP`: do not copy a MySQL payload, use the `RANDOMBLOB` trick.

## Further reading

- PortSwigger, Blind SQL injection: https://portswigger.net/web-security/sql-injection/blind
- HackTricks, SQL Injection (blind, time-based): https://book.hacktricks.xyz/pentesting-web/sql-injection
- The payload cheatsheet in this series.

## Key takeaways

- No visible data does not mean no exploitation: find the oracle.
- A boolean oracle is any difference that follows the condition: content, status code, response length, error or no error.
- Extract character by character with `SUBSTR` plus a code comparison; use binary search for speed.
- When there is no content oracle, use time-based; each DBMS has its own delay function.
- Find `LENGTH` first so you know where to stop.
