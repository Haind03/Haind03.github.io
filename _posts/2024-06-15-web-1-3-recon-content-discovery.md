---
title: "Lesson 1.3: Recon and content discovery"
image:
  path: /assets/img/covers/web-1-3-recon-content-discovery.webp
  alt: "Recon and content discovery"
date: 2024-06-15 09:15:00 +0700
categories: ["Web Security", "Web · Tools and Recon"]
tags: [web, recon, fuzzing, ffuf]
render_with_liquid: false
---

By the end of this lesson you can find the things nothing links to: hidden directories and files, admin pages, backup files, virtual hosts, and even hidden parameters. You use ffuf and gobuster with a wordlist to brute force paths, learn to filter noise by status and size, and attack a lab app yourself to pull out real hidden routes.

![Recon and content discovery](/assets/img/web/web-1-3-recon-content-discovery.svg)
_For each word in the list, ffuf sends a request, drops the 404 responses, and keeps the paths that exist._

Part 1, about 50 minutes, medium difficulty. Prerequisite: Lesson 1.2 (DevTools, curl and httpie). Tools: `ffuf`, `gobuster`, SecLists, `curl`, and a lab app (`labs/1.3/`).

## Goals

After this lesson you understand what content discovery is and why it works, use ffuf to brute force paths and filter out 404 responses, know how to pick a suitable wordlist from SecLists, grasp the ideas of vhost fuzzing and param mining, and can attack lab app 1.3 to find the hidden routes.

## Theory

### What content discovery is

Recon (reconnaissance) is the step of gathering information about a target before attacking. Content discovery is one branch of recon: finding resources that exist on the server but are not linked anywhere, so you do not see them while browsing normally. Typical examples: `/admin`, `/backup.zip`, `/.git/`, `/api/v1/internal`, `/old/`.

Why it works: developers often leave spare files behind (backups, config files, old pages), and many internal pages rely on "nobody knows the URL" for security. But URLs are guessable. By trying thousands of common path names and seeing which ones return something other than 404, we pull out these hidden resources. This is "security by obscurity", and it is not real security.

### The mechanism: brute force based on status code

The idea is simple. For each word in the wordlist, send a request to `http://target/<word>` and look at the status code. A path that does not exist usually returns `404`. A path that exists returns `200`, `301`, `302`, `401` or `403`. Filter out `404` and the rest are candidates worth a look.

In practice there is noise: many apps return `200` for everything (with a custom "not found" page), or return `302` to a login page. So beyond status, we also filter by response size, word count and line count. ffuf lets you filter out or match in on all of these criteria.

### ffuf and gobuster

Both are path-fuzzing tools written in Go and very fast:

- **ffuf** (Fuzz Faster U Fool): the most flexible. Use the keyword `FUZZ` in the URL to mark where a word is inserted. It can fuzz paths, parameters, headers and vhosts. Filter or match by status (`-mc`/`-fc`), size (`-ms`/`-fs`), words (`-mw`/`-fw`), lines, or regex.
- **gobuster:** simple, fast, with several modes (`dir` for directories, `dns` for subdomains, `vhost` for virtual hosts). The syntax is easy for beginners.

This series uses ffuf by default for its flexibility, but gobuster works just as well for basic directory brute forcing.

### Wordlists and SecLists

The quality of the results depends on the wordlist. SecLists is the standard collection of wordlists for pentesting, with lists of paths, parameters, passwords and payloads. A few lists used often for content discovery:

- `Discovery/Web-Content/common.txt`: small and fast, for a first pass.
- `Discovery/Web-Content/directory-list-2.3-medium.txt`: larger, broader coverage.
- `Discovery/Web-Content/raft-*-directories.txt` and `raft-*-files.txt`: practical, drawn from real web data.

Strategy: scan `common.txt` first for quick results, then scan the large list. If you find a directory (for example `/api/`), scan recursively or brute force inside it.

### Vhost fuzzing and param mining

- **Vhost fuzzing:** one IP can serve many sites, told apart by the `Host` header (Lesson 0.2). By keeping the IP fixed but fuzzing the `Host` header (for example `admin.target.com`, `dev.target.com`), we find virtual hosts that are not public. In ffuf, put `FUZZ` in the `Host` header.
- **Param mining:** many endpoints handle parameters that are not documented. Fuzz the parameter name (query or body) to find which one changes the response. The dedicated tool is arjun; ffuf can do it too by putting `FUZZ` in the parameter name and filtering by size. A hidden parameter often leads to forgotten vulnerabilities such as a debug mode, or a new injection channel.

## Demo

This section attacks the real lab app `labs/1.3/` (Flask, port 8011). The app only exposes `/` and `/about`; the rest are hidden routes. The output below is real, captured from a run (ffuf 2.1.0, curl 7.81).

First confirm the home page does not reveal any link to a hidden route:

```text
$ curl -s http://127.0.0.1:8011/ | grep -o 'href="[^"]*"'
href="/"
href="/about"
```

Only `/` and `/about`. Now brute force with ffuf, filtering out the `404` responses:

```text
$ ffuf -w wordlist.txt -u http://127.0.0.1:8011/FUZZ -fc 404 -c
about                   [Status: 200, Size: 292, Words: 23, Lines: 5, Duration: 4ms]
admin                   [Status: 200, Size: 300, Words: 23, Lines: 5, Duration: 10ms]
.git/config             [Status: 200, Size: 103, Words: 6, Lines: 5, Duration: 14ms]
old                     [Status: 200, Size: 300, Words: 25, Lines: 5, Duration: 17ms]
backup                  [Status: 200, Size: 124, Words: 6, Lines: 6, Duration: 18ms]
```

With just a small wordlist, ffuf pulls out `admin`, `.git/config`, `old` and `backup`, all with no link pointing to them. The flags: `-w` loads the wordlist, `-u` sets the URL with the `FUZZ` keyword as the insertion point for each word, `-fc 404` filters out (filter code) every 404 response, and `-c` colourises.

Confirm each route with curl. The backup file leaks the whole config:

```text
$ curl -s http://127.0.0.1:8011/backup
# config.bak - lo ra ngoai
DB_HOST=127.0.0.1
DB_USER=acme
DB_PASS=sup3r-s3cr3t-pw
FLAG=WEB{content_discovery_tim_ra_backup}

$ curl -s http://127.0.0.1:8011/.git/config
[core]
	repositoryformatversion = 0
[remote "origin"]
	url = https://github.com/acme/internal-site.git
```

The `/backup` file exposes the database password, and `/.git/config` exposes the whole `.git` directory (from which the entire source can be downloaded, a classic misconfiguration). This is the real impact of content discovery.

ffuf does not return `/api/v1/users` because the wordlist does not contain that multi-level path. This shows the limit of brute forcing: the result is only as good as the wordlist. When you see `/api`, guess the next level from common structure:

```text
$ curl -s -o /dev/null -w "%{http_code}  /api\n"          http://127.0.0.1:8011/api
404  /api
$ curl -s -o /dev/null -w "%{http_code}  /api/v1/users\n" http://127.0.0.1:8011/api/v1/users
200  /api/v1/users
$ curl -s http://127.0.0.1:8011/api/v1/users
[{"id":1,"role":"superuser","user":"admin"},{"id":2,"role":"staff","user":"alice"}]
```

`/api` returns 404 but `/api/v1/users` exists and exposes a user list with roles. The lesson: a wordlist brute force finds the lead, then you use your head (and recursive scanning and API-specific wordlists) to dig deeper.

The same task with gobuster (reference syntax):

```text
gobuster dir -u http://127.0.0.1:8011 -w wordlist.txt -s 200,301,302,401,403 -b ''
```

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 1.3</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/1.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/1.3/app.py" download><i class="fa-solid fa-file-code"></i>app.py</a>
</div>
</div>

- **Vulnerable app:** `labs/1.3/` is a Flask app with several hidden routes. Set it up per `labs/1.3/README.md`, running locally on port 8011.
- **Quick run:**

```text
cd labs/1.3
python3 app.py        # 127.0.0.1:8011
ffuf -w wordlist.txt -u http://127.0.0.1:8011/FUZZ -fc 404
```

- **Tasks:**
  1. Brute force with ffuf to find all the hidden routes (hint: there are 5 that the bundled wordlist finds).
  2. Fetch the content of `/backup` and extract the `FLAG`.
  3. Explain why `/api/v1/users` did not show up in the first brute force, then find a way to get it.
  4. Try again with gobuster and compare the results.
  5. Advanced: download SecLists, try `common.txt` against the same app and see what differs.
- **Hint:** if the app returns `200` for non-existent paths too, filter by size instead of status (`-fs <size>`).
- **Answer:** the real script and output are in `labs/1.3/transcript.txt`.

## Common pitfalls

- Filtering by status only while forgetting the app has a custom 404 page returning 200, which gives all-junk results.
- Using a huge wordlist from the start, which is slow and noisy; scan small first.
- Forgetting to scan recursively after finding a directory, missing resources deeper inside.
- Brute forcing too fast and overloading the lab app (or a real in-scope target); tune the thread count `-t` sensibly.
- Confusing "does not exist" (404) with "access denied" (403): 403 means it exists and is well worth digging into.

## Further reading

- ffuf wiki: https://github.com/ffuf/ffuf/wiki
- gobuster: https://github.com/OJ/gobuster
- SecLists: https://github.com/danielmiessler/SecLists
- arjun (param mining): https://github.com/s0md3v/Arjun

## Key takeaways

- Content discovery finds resources that exist but are not linked, based on URLs being guessable.
- Path brute force: try a wordlist, filter out 404, inspect the rest.
- When the app returns 200 for everything, also filter by size, words and lines.
- The result is only as good as the wordlist; SecLists is the standard, so scan small first then large.
- Vhost fuzzing (fuzz the Host header) and param mining (fuzz the parameter name) widen the attack surface.
