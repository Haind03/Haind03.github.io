---
title: "Lesson 9.2: GraphQL Introspection and Query Abuse"
image:
  path: /assets/img/covers/web-9-2-graphql-introspection-query-abuse.webp
  alt: "GraphQL Introspection and Query Abuse"
date: 2024-06-15 17:10:00 +0700
categories: ["Web Security", "Web · API and Modern Web"]
tags: [web, graphql, api]
render_with_liquid: false
---

By the end of this lesson you can read the entire schema of a GraphQL API through introspection, pull sensitive fields that were meant to stay hidden, call a mutation that lacks an authorization check, and understand why nested queries and batching can turn into a denial of service. GraphQL has a single endpoint that describes itself, which is both its convenience and its security surface.

![GraphQL Introspection and Query Abuse](/assets/img/web/web-9-2-graphql-introspection-query-abuse.svg)
_Introspection returns the full schema, and without field-level authorization the hidden apiKey and ssn fields resolve for anyone who asks._

Part: 9 (API and Modern Web) | Time: about 45 minutes | Difficulty: medium

**Prerequisites:** Lesson 9.1 (REST API security), and familiarity with JSON and HTTP POST.

**Tools:** curl, Python requests, GraphiQL/Altair/InQL (Burp extension), clairvoyance.

## Goals

After this lesson you understand the GraphQL model (one endpoint, query and mutation, types and fields). You can use introspection to retrieve the whole schema, query sensitive fields that are hidden from the UI, and recognize a mutation without authorization and the DoS risk from nested queries and batching.

## 1. Theory

GraphQL is an API query language created by Facebook. It differs from REST in that, instead of many endpoints (`/users`, `/orders`, `/posts`), GraphQL has only **one** endpoint (usually `/graphql`) that accepts queries describing exactly the data the client needs. The client picks the fields, and the server returns exactly those fields.

There are two main kinds of operation:

- **query**: read data (like `GET`).
- **mutation**: change data (like `POST`/`PUT`/`DELETE`).

Every GraphQL API has a **schema**: a description of the **types** (for example `User`, `Post`), where each type has **fields** (`username`, `email`, `apiKey`). And here is the GraphQL-specific security concern:

**Introspection (self-description)**: GraphQL itself has a mechanism for the client to ask "what does your schema contain" through the special queries `__schema` and `__type`. It exists so that tools like GraphiQL can auto-suggest. But if it is enabled in production, an attacker downloads the **entire** map of the API: every type, every field, every mutation, including things the UI never uses.

From that, several classes of bug follow:

- **Exposed sensitive fields**: the developer thinks "the `apiKey` field is only called by the admin page, so it is fine". But the field is still in the schema and still resolves for anyone who asks, unless there is **field-level authorization** (a permission check per field). Introspection gives you the names, and a query gives you the values.
- **Mutation without an authorization check**: a `mutation { promoteUser(id: 2) }` that the server does not check for admin role can be called by anyone.
- **DoS through nested queries**: if types reference each other in a cycle (for example `User.posts -> Post.author -> User.posts ...`), a query nested a few dozen levels deep forces the server to generate data exponentially.
- **DoS through batching/alias**: GraphQL lets you set an alias to call the same field many times in one request (`a1: user(id:1) a2: user(id:1) ...`). With no limit, a single request multiplies the cost thousands of times. Some servers even accept an array of several queries in one HTTP request (query batching), which amplifies further.

## 2. Demo

The lab in `labs/9.2/` builds a GraphQL API with `graphql-core` (the Python version of GraphQL), with introspection enabled.

Step 1, run introspection to get the schema. This is a shortened version; in practice tools like InQL or clairvoyance do it automatically:

```text
POST /graphql
{"query":"query{ __schema{ types{ name fields{ name } } mutationType{ name } } }"}

-> fields of type User: ["id","username","email","isAdmin","apiKey","ssn","posts"]
   mutation found: ["promoteUser"]
```

Notice the two fields `apiKey` and `ssn`: the ordinary UI does not show them, but introspection just pointed them out. Step 2, query them directly for the admin account:

```text
POST /graphql
{"query":"query{ user(id:\"1\"){ username isAdmin apiKey ssn } }"}

-> {"username":"admin","isAdmin":true,
    "apiKey":"FLAG{9.2_graphql_introspection_hidden_field}",
    "ssn":"999-99-9999"}
```

There is no field-level authorization, so the server returns it without complaint. Step 3, call the privilege-escalation mutation as an ordinary client:

```text
POST /graphql
{"query":"mutation{ promoteUser(id:\"2\"){ ok message flag } }"}

-> {"ok":true,"message":"user 2 da duoc nang quyen (KHONG kiem tra authorization)",
    "flag":"FLAG{9.2_graphql_mutation_no_authz}"}
```

Step 4, show the DoS risk. A query nested 5 levels through the cycle `posts -> author -> posts ...` runs fine because there is no depth limit. And alias batching fetches one expensive field 12 times in a single request:

```text
query{ a0:user(id:"1"){apiKey} a1:user(id:"1"){apiKey} ... a11:user(id:"1"){apiKey} }
-> 1 request executes the expensive field 12 times
```

Multiply that 12 by thousands, add deep nesting, and it is enough to clog the server.

## 3. Lab

- Vulnerable app: `labs/9.2/` (Flask + graphql-core, binds `127.0.0.1:8072`, run locally per the lab README).
- Task:
  1. Run introspection, list the types and fields, and find a field that does not appear in the UI.
  2. Query the admin's sensitive field to get the flag.
  3. Call the `promoteUser` mutation as an ordinary client.
  4. Try a deeply nested query and alias batching, and observe that the server still returns data without a limit.
- Hint: if introspection is disabled on a real API, you can still guess field names with a tool like clairvoyance (it probes the schema through suggestive error messages).
- Solution: `exploit.py` and `transcript.txt` in `labs/9.2/`.

## 4. Common pitfalls

- Disabling introspection but leaving error-message field suggestions on, which means nothing is really hidden.
- Placing authorization at the HTTP/gateway layer, while GraphQL has one endpoint so every query and mutation goes through the same door, so you must check permission in each resolver.
- Rate limiting only by the number of HTTP requests and forgetting the intrinsic cost of each query (one request can be a thousand times heavier than another).
- Thinking "a field hidden from the UI is hidden from the API", a classic misunderstanding.

## 5. Further reading

- The official GraphQL documentation on introspection and schema.
- PortSwigger Web Security Academy: the GraphQL API vulnerabilities topic.
- Tools: InQL (Burp), Altair, clairvoyance, graphql-cop.

## 6. Key takeaways

- Always try introspection first: `{ __schema { types { name fields { name } } } }`.
- A field that is in the schema can be queried, unless the server checks permission per field.
- A mutation is more dangerous than a query because it changes state, so always try calling it with a low-privilege account.
- Count the depth and the number of aliases a query allows: no limit means a DoS risk.
- GraphQL error messages are very eager to suggest the correct field name, which helps the attacker.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 9.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/9.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/9.2/app.py" download><i class="fa-solid fa-file-code"></i>app.py</a>
<a class="lab-file" href="/assets/labs-web/9.2/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
</div>
</div>
