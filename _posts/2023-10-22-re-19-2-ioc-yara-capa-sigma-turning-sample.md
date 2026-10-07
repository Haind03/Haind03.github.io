---
title: "Lesson 19.2: IOC, YARA, capa and Sigma, turning a sample into something detectable"
date: 2023-10-22 10:09:00 +0700
categories: ["Technique Reverse", "Part 19 · Malware Analysis Basics"]
tags: [reverse-engineering, malware]
render_with_liquid: false
---
Analyzing a malware sample and then leaving it there is a waste. The real value of reversing a sample is pulling out something that helps you (and the community) recognize it next time, recognize its variants, and recognize it running in a system. This lesson covers four things: IOCs for sharing indicators, YARA for scanning files and memory, capa for profiling capabilities, and Sigma for catching behavior in logs. All of them are defensive tools.

## IOC: indicators to share

An IOC (Indicator of Compromise) is a concrete piece of data pointing to a system that may have been compromised. When analyzing a sample, you pick out the file hashes (MD5, SHA-1, SHA-256), the network indicators, the host indicators, and for phishing the email indicators.

Hashes are the weakest IOC because changing a single byte changes the hash, but you still need them for lookups and sharing. Network indicators are the IPs, domains, and URLs of the command-and-control (C2) server and the paths the payload is downloaded from. Host indicators are mutex names (malware often creates a mutex so it doesn't run twice, see Lesson 1.11 again), names of files it drops, registry keys it creates for persistence, and scheduled task names. For phishing, you note the sender address, subject, and attachment file names.

IOCs are standardized for automated exchange, most commonly STIX (Structured Threat Information eXpression). But remember: IOCs are the easiest kind of indicator to evade. Attackers change a domain or a hash in seconds. The more durable stuff is below.

## YARA: pattern scanning

YARA is a rule language for identifying files (and process memory too) by byte patterns and strings. It's more durable than a hash because it latches onto things attackers find hard to change: distinctive strings, code fragments, algorithm constants.

A rule has two main parts: `strings` declares the patterns to look for, and `condition` says when to count it as a match.

```yara
rule FakeBot_Demo
{
    meta:
        description = "Detects the simulated FakeBot sample"
        author = "blog"

    strings:
        $mutex = "Global\\FakeBot_Mutex_v1" ascii
        $c2    = "http://c2.example-fakebot.test/gate.php" ascii
        $key   = { 52 43 34 4B 65 79 31 32 33 }   // byte pattern "RC4Key123"

    condition:
        uint16(0) == 0x5A4D and          // 0x5A4D = "MZ", only scan PE files
        2 of them                        // match at least 2 of the strings above
}
```

Strings can be text (`ascii`, `wide` for UTF-16, `nocase` for case-insensitive) or a byte pattern in curly braces, usable for code fragments or constants. Byte patterns allow the wildcard `??` (any single byte), so they can catch code even when a few bytes change.

`condition` is where the logic goes: `uint16(0) == 0x5A4D` pre-filters to PE files only, `2 of them` or `3 of ($a, $b, $c)` allow soft matching, and `$a at 0` pins a string to a specific offset. A good rule is specific enough not to false-alarm on clean files, and broad enough to catch variants. Relying on 1 string is prone to false positives or easy to evade, while relying on a combination of a few distinctive signs is about right.

YARA can scan both static files and the memory of running processes, so it's great for catching malware that has been unpacked in RAM (tying back to Lessons 14 and 17.5). yarGen generates rules automatically from a set of samples (it removes strings common in clean files and keeps the rare ones), which is a good starting point that you then tune by hand.

## capa: ask "what can it do"

While YARA asks "is this sample X?", capa (Mandiant) asks a different question: "what capabilities does this binary have?". It runs a set of rules describing behavior based on APIs, strings, constants, and returns statements like "communicate over HTTP", "encrypt data using RC4", "inject code into another process", or "persist via registry run key".

capa is extremely useful at the triage step: without reading any code yet, you already have a summary of what the binary does and know which spots are worth reading first. It also maps to MITRE ATT&CK so you speak the same language as the defense team. It pairs nicely with [capa in triage from Lesson 2.1](/posts/re-2-1-five-minute-triage-die-strings-pe/).

## Sigma: catching behavior in logs

YARA and capa look at files. Sigma looks at logs. It's a common rule format for SIEMs and system logs (Windows Event Log, Sysmon, EDR): it describes a suspicious behavior in a way that doesn't depend on any SIEM vendor, then converts to queries for Splunk, Elastic, Sentinel...

An example Sigma idea: "process `winword.exe` spawns `powershell.exe`" is the typical malicious macro pattern. Or "a process writes into another process's memory and then creates a remote thread" (tying back to the injection signs in [Lesson 17.4/17.5](/technique-reverse/)). Sigma catches things YARA doesn't see, because it tracks runtime behavior rather than file contents.

Four tools, four layers: IOC (concrete data, easy to evade), YARA (file/memory contents), capa (capabilities), Sigma (behavior). The further down you go, the harder it is to evade, because attackers can change a domain easily, but changing how they behave takes real work.

## A practical workflow

After reversing a sample, you usually go through the same sequence. You compute hashes and pick out network/host IOCs (domains, mutexes, registry, dropped files). Then you run capa to get a capability profile, so you know how it injects, encrypts, and persists.

Next you write a YARA rule based on a combination of distinctive strings and byte patterns (preferring things that are hard to change), and test it against both the sample and a set of clean files to avoid false positives. After that you write a Sigma rule for the observed behavior (process tree, registry writes, network), so the SOC team can detect it even when the hash has changed. Finally you share the IOCs/YARA/Sigma with the community or internally.

## Lab

Go to `labs/19.2/`. You'll write a YARA rule, create a harmless sample file containing marker strings, then run `yara` (or `yara-python`) to see exactly which string the rule matches at which offset. The sample rule and the real run output are in `solution.md`.

## Key takeaways

IOCs are concrete indicators (hash, domain, mutex, registry), easy to share but the easiest to evade. YARA scans files and memory with `strings` + `condition` and uses byte patterns to catch variants too. A good rule is based on a combination of indicators that are hard to change, and gets tested against clean files to avoid false positives.

capa answers "what can the binary do" and maps to ATT&CK, which is great for triage. Sigma catches behavior in logs and is harder to evade because it tracks runtime. On a durability scale it goes IOC < YARA < capa < Sigma.
