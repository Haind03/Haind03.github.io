---
title: "Lesson 5.1: IDOR and unchecked object references"
image:
  path: /assets/img/covers/web-5-1-idor-unchecked-object-references.webp
  alt: "IDOR and unchecked object references"
date: 2024-06-15 13:05:00 +0700
categories: ["Web Security", "Web · Access Control"]
tags: [web, idor, access-control]
render_with_liquid: false
---

IDOR, short for Insecure Direct Object Reference, happens when an application uses a client-supplied value such as an id, a file name, or an order number to point straight at a backend object, but forgets to check whether the person making the request is allowed to touch that object. A valid account can then read or change another user's data just by changing one id in the request. This lesson shows how to recognize that pattern, how to exploit both read and write variants on a real lab, and how to fix it at the right layer.

![IDOR and unchecked object references](/assets/img/web/web-5-1-idor-unchecked-object-references.svg)
_Authentication confirms who you are; the missing authorization check is what lets you read another user's object._

Level: basic, about 30 minutes. Prerequisites: sessions and cookies (Part 4). Tools: Burp Suite, curl, a browser.

## Goals

After this lesson you understand what IDOR (Insecure Direct Object Reference) is and why it belongs to the Broken Access Control group, you can tell authentication apart from authorization, you can exploit both read-IDOR and write-IDOR on a real lab, and you know where to place the fix.

## Theory

### What IDOR is

IDOR, short for Insecure Direct Object Reference, happens when an application uses a value supplied by the client (an id, a file name, an order number) to point straight at a backend object, but then forgets to check whether the requester has any right to that object.

A classic example:

```text
GET /api/order/1003      -> my order, shown normally
GET /api/order/1001      -> change the number, you get someone else's order
```

If the server returns order 1001 without checking "does this order belong to you", that is IDOR.

### Two ideas that get mixed up

- Authentication: who you are. After you log in, the server knows you are mallory.
- Authorization: what you are allowed to do. Mallory may view mallory's orders, not alice's.

IDOR is a flaw at the authorization layer. The app checks "are you logged in" (yes), then skips the step "do you have a right to this resource" (not checked). That is why a legitimate account is enough to exploit it, with no need to break the login.

### Where the direct object reference sits

The reference shows up everywhere, not only in the path:

```text
Path:    /api/order/1001 , /files/1001/download
Query:   /invoice?id=1001
Body:    {"account_id": 1001}
Cookie:  cart=1001
Header:  X-User-Id: 1001
```

Anywhere the client sends up a pointer to data is a point to be suspicious of.

### Which id types are easy, which are hard

- Sequential numbers (1001, 1002, 1003): the easiest, just add or subtract to reach another valid id.
- Guessable UUIDs: many people think a UUID is safe, but UUIDv1 is generated from time and MAC address, so it can be guessed or enumerated; a base64 code of a sequential id is still just a sequential id in disguise. A hard-to-guess id only slows an attacker down, it does NOT replace the authorization check.
- Random UUIDv4: hard to enumerate, but if the id leaks elsewhere (logs, a shared URL, the Referer header) it can be reused. This is security by obscurity, not real access control.

## Demo

The general idea when hunting IDOR with Burp Suite:

1. Log in with your own account and act normally (view your own orders).
2. Capture a request that contains an id in Burp Proxy.
3. Send it to Repeater, change the id to a different value, and send it again.
4. If the response returns someone else's data (status 200, unfamiliar content) instead of 403, that is IDOR.
5. Automate with Intruder: sweep a range of ids to collect data.

An illustrative request and response (changing the id from 1003 to 1001):

```text
GET /api/order/1001 HTTP/1.1
Host: 127.0.0.1:8050
Cookie: auth=mallory

HTTP/1.1 200 OK
Content-Type: application/json

{"owner":"alice","total":"12.000.000 VND","card_last4":"4291",
 "address":"12 Tran Hung Dao, Ha Noi","note":"..."}
```

Mallory logs in with her own account but reads alice's order, including the card number and address. That is the real impact of IDOR: mass leakage of personal data.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 5.1</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/5.1.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/5.1/app.py" download><i class="fa-solid fa-file-code"></i>app.py</a>
<a class="lab-file" href="/assets/labs-web/5.1/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
</div>
</div>

- Vulnerable app: `labs/5.1/` (build instructions in the lab README, runs locally, port 127.0.0.1:8050).
- Tasks:
  1. Log in as `mallory:pw` and view your own order (1003).
  2. Change the id to 1001..1005, read the other users' data, and find the flag in the `note` of order 1001.
  3. Try write-IDOR: `POST /api/order/1004/address` to change the shipping address of alice's order.
- Hint: the flaw is that `get_order()` and `set_address()` do not compare `order["owner"]` with the logged-in user.
- Solution: the exploit script `labs/5.1/exploit.py` and `labs/5.1/transcript.txt`.

Excerpt from a real run:

```text
[*] Buoc 2: IDOR doc - doi id tu 1001 den 1005:
    order 1001 owner=alice    total=12.000.000 VND   note=FLAG{...} <= KHONG PHAI CUA MINH
    order 1002 owner=bob      total=350.000 VND      note=giao gio hanh chinh <= KHONG PHAI CUA MINH
    order 1003 owner=mallory  total=99.000 VND       note=don cua chinh mallory
...
[+] Lay duoc du lieu nhay cam cua nguoi khac. FLAG = FLAG{5.1_idor_doc_don_nguoi_khac}
```

## Common pitfalls

- Checking authorization only on the list page while forgetting the detail page or the API endpoint.
- Checking authorization on GET but dropping it on POST/PUT/DELETE of the same resource.
- Trusting an id hidden in a hidden field or a cookie, assuming the user cannot change it.
- Using a UUID and then relaxing the authorization check. Once a UUID leaks, it gets reused.
- Hiding a button on the frontend while the backend still accepts the direct request.

## Further reading

- PortSwigger Web Security Academy: Access control vulnerabilities (the IDOR part).
- OWASP WSTG: Testing for Insecure Direct Object References.
- OWASP API Security Top 10: API1 Broken Object Level Authorization (BOLA), which is IDOR on an API.

## Key takeaways

- IDOR is an authorization flaw: the app checks "logged in" but forgets "has a right to this resource".
- Every id, file name, or code the client sends is a point to suspect, including those in headers and cookies.
- Test both read-IDOR (viewing) and write-IDOR (modify/delete); the two are often protected separately.
- A hard-to-guess id only slows an attacker; it is not access control.
- Defense: check ownership at every endpoint, and ideally filter at the query layer (only SELECT the current user's resources).
