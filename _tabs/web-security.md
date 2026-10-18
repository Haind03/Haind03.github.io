---
title: Web Security
icon: fas fa-globe
order: 4
render_with_liquid: false
---

My notes on web security and web exploitation, from HTTP and the tooling through the classic vulnerability classes (injection, XSS, authentication, access control, SSRF, file and path, template and deserialization, API), then chaining bugs together and real practice. Each lesson pairs the theory with a tool demo and a self-contained lab you can run.

Everything here is for learning, CTFs, authorized testing and bug bounty within scope. The labs are deliberately vulnerable apps that run on your own machine. Do not attack systems you do not have permission to test.
{: .prompt-warning }

## Web · Intro to Web Hacking

| # | Lesson |
|---|---|
| 0.1 | [What Web Hacking Is, Attack Surface and Ethics](/posts/web-0-1-web-hacking-attack-surface-ethics/) |
| 0.2 | [HTTP and HTTPS Methods, Headers, Status Codes and Cookies](/posts/web-0-2-http-https-methods-headers-cookies/) |
| 0.3 | [Web Architecture, Same-Origin Policy and Cookie Attributes](/posts/web-0-3-web-architecture-same-origin-policy-cookies/) |
| 0.4 | [Building a Web Lab with Burp Suite and Docker](/posts/web-0-4-building-web-lab-burp-docker/) |

## Web · Tools and Recon

| # | Lesson |
|---|---|
| 1.1 | [Burp Suite core modules](/posts/web-1-1-burp-suite-core-modules/) |
| 1.2 | [DevTools, curl and httpie](/posts/web-1-2-devtools-curl-httpie/) |
| 1.3 | [Recon and content discovery](/posts/web-1-3-recon-content-discovery/) |
| 1.4 | [Fingerprinting web technologies](/posts/web-1-4-fingerprinting-web-technologies/) |

## Web · Injection

| # | Lesson |
|---|---|
| 2.1 | [Basic SQL Injection with UNION and Error-Based](/posts/web-2-1-basic-sql-injection-union-error/) |
| 2.2 | [Blind SQL Injection with Boolean and Time](/posts/web-2-2-blind-sql-injection-boolean-time/) |
| 2.3 | [sqlmap and WAF Bypass with Tamper Scripts](/posts/web-2-3-sqlmap-waf-bypass-tamper-scripts/) |
| 2.4 | [NoSQL Injection and Auth Bypass in MongoDB](/posts/web-2-4-nosql-injection-auth-bypass-mongodb/) |
| 2.5 | [Command Injection, In-Band and Blind](/posts/web-2-5-command-injection-in-band-blind/) |

## Web · Cross-Site Scripting

| # | Lesson |
|---|---|
| 3.1 | [Reflected XSS and Choosing Payloads by Context](/posts/web-3-1-reflected-xss-choosing-payloads-context/) |
| 3.2 | [Stored XSS and Its Lasting Impact](/posts/web-3-2-stored-xss-lasting-impact/) |
| 3.3 | [DOM-based XSS from Source to Sink](/posts/web-3-3-dom-based-xss-source-sink/) |
| 3.4 | [Bypassing Filters and CSP](/posts/web-3-4-bypassing-filters-csp/) |
| 3.5 | [Exploiting XSS from Cookie Theft to Account Takeover](/posts/web-3-5-exploiting-xss-cookie-theft-account-takeover/) |

## Web · Authentication and Session

| # | Lesson |
|---|---|
| 4.1 | [Authentication flaws, brute force, and default credentials](/posts/web-4-1-authentication-flaws-brute-force-default-credentials/) |
| 4.2 | [Session management, fixation, and guessable tokens](/posts/web-4-2-session-management-fixation-guessable-tokens/) |
| 4.3 | [Attacking JWT with alg none and weak secrets](/posts/web-4-3-attacking-jwt-alg-none-weak-secrets/) |
| 4.4 | [OAuth2 and SSO, redirect_uri and state attacks](/posts/web-4-4-oauth2-sso-redirect-uri-state-attacks/) |
| 4.5 | [Password reset and MFA bypass](/posts/web-4-5-password-reset-mfa-bypass/) |

## Web · Access Control

| # | Lesson |
|---|---|
| 5.1 | [IDOR and unchecked object references](/posts/web-5-1-idor-unchecked-object-references/) |
| 5.2 | [Broken access control and privilege escalation](/posts/web-5-2-broken-access-control-privilege-escalation/) |
| 5.3 | [CSRF, tokens and SameSite cookies](/posts/web-5-3-csrf-tokens-samesite-cookies/) |
| 5.4 | [Mass assignment and parameter tampering](/posts/web-5-4-mass-assignment-parameter-tampering/) |

## Web · SSRF and Request-Side

| # | Lesson |
|---|---|
| 6.1 | [Basic SSRF and Reaching Internal Services](/posts/web-6-1-basic-ssrf-reaching-internal-services/) |
| 6.2 | [Bypassing SSRF Filters](/posts/web-6-2-bypassing-ssrf-filters/) |
| 6.3 | [Open Redirect and Its Abuse](/posts/web-6-3-open-redirect-abuse/) |
| 6.4 | [HTTP Request Smuggling with CL.TE and TE.CL](/posts/web-6-4-http-request-smuggling/) |

## Web · File and Path

| # | Lesson |
|---|---|
| 7.1 | [Path Traversal and LFI](/posts/web-7-1-path-traversal-lfi/) |
| 7.2 | [File Upload to RCE](/posts/web-7-2-file-upload-to-rce/) |
| 7.3 | [Escalating LFI to RCE](/posts/web-7-3-escalating-lfi-rce/) |

## Web · Template and Deserialization

| # | Lesson |
|---|---|
| 8.1 | [Server-Side Template Injection](/posts/web-8-1-server-side-template-injection/) |
| 8.2 | [Insecure Deserialization](/posts/web-8-2-insecure-deserialization/) |
| 8.3 | [XML External Entity Injection](/posts/web-8-3-xml-external-entity-injection/) |

## Web · API and Modern Web

| # | Lesson |
|---|---|
| 9.1 | [REST API Security, BOLA and BFLA](/posts/web-9-1-rest-api-security-bola-bfla/) |
| 9.2 | [GraphQL Introspection and Query Abuse](/posts/web-9-2-graphql-introspection-query-abuse/) |
| 9.3 | [CORS Misconfiguration and Its Consequences](/posts/web-9-3-cors-misconfiguration-consequences/) |
| 9.4 | [Prototype Pollution in Node.js](/posts/web-9-4-prototype-pollution-nodejs/) |

## Web · Chaining

| # | Lesson |
|---|---|
| 10.1 | [Chaining recon to RCE](/posts/web-10-1-chaining-recon-rce/) |
| 10.2 | [Client-side chaining from XSS to account takeover](/posts/web-10-2-client-side-chain-xss-account-takeover/) |

## Web · Hands-on

| # | Lesson |
|---|---|
| 11.1 | [Solving PortSwigger Web Security Academy Labs by Topic](/posts/web-11-1-solving-portswigger-web-security-academy-labs/) |
| 11.2 | [Writing a Web CTF Writeup](/posts/web-11-2-writing-web-ctf-writeup/) |
| 11.3 | [Auditing a Web App and Writing the Report](/posts/web-11-3-auditing-web-app-writing-report/) |
