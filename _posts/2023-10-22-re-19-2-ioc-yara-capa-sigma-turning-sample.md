---
title: "Lesson 19.2: IOC, YARA, capa and Sigma"
image:
  path: /assets/img/covers/re-19-2-ioc-yara-capa-sigma-turning-sample.webp
  alt: "Lesson 19.2: IOC, YARA, capa and Sigma"
date: 2022-09-19 22:07:00 +0700
categories: ["Reverse Engineering", "Part 19 · Malware Analysis Basics"]
tags: [reverse-engineering, malware]
render_with_liquid: false
---
Analyzing a malware sample and then leaving it there is a waste. What you want from reversing a sample is something that helps you (and the community) recognize it next time, recognize its variants, and spot it running in a system. This lesson covers four things, IOCs for sharing indicators, YARA for scanning files and memory, capa for profiling capabilities, and Sigma for catching behavior in logs. All of them are defensive tools.

![Detection layers from IOC to Sigma](/assets/img/re/re-19-2-ioc-yara-capa-sigma-turning-sample.svg)
_The four detection layers, from easy to evade (IOC) to hard to evade (Sigma)._

## IOC: indicators to share

An IOC (Indicator of Compromise) is a concrete piece of data pointing to a system that may have been compromised. When analyzing a sample, you pick out the file hashes (MD5, SHA-1, SHA-256), the network indicators, the host indicators, and for phishing the email indicators.

Hashes are the weakest IOC because changing a single byte changes the hash, but you still need them for lookups and sharing. Network indicators are the IPs, domains and URLs of the command-and-control (C2) server and the paths the payload is downloaded from. Host indicators are mutex names (malware often creates a mutex so it doesn't run twice, see Lesson 1.11 again), names of files it drops, registry keys it creates for persistence, and scheduled task names. For phishing, you note the sender address, subject and attachment file names.

IOCs are standardized for automated exchange, most commonly STIX (Structured Threat Information eXpression). But IOCs are the easiest kind of indicator to evade. Attackers change a domain or a hash in seconds. The sections below cover more durable options.

## YARA: pattern scanning

YARA is a rule language for identifying files (and process memory too) by byte patterns and strings. It lasts longer than a hash because it matches things attackers find hard to change, such as distinctive strings, code fragments, algorithm constants.

A rule has two main parts. `strings` declares the patterns to look for, and `condition` says when to count it as a match.

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

`condition` is where the logic goes, and `uint16(0) == 0x5A4D` pre-filters to PE files only, `2 of them` or `3 of ($a, $b, $c)` allow soft matching, and `$a at 0` pins a string to a specific offset. A good rule is specific enough not to false-alarm on clean files, and broad enough to catch variants. A rule that relies on 1 string is prone to false positives or easy to evade. A combination of a few distinctive signs is about right.

YARA can scan both static files and the memory of running processes, so it works well for malware that has been unpacked in RAM (see Lessons 14 and 17.5). yarGen generates rules automatically from a set of samples (it removes strings common in clean files and keeps the rare ones), which is a good starting point that you then tune by hand.

## capa: what can it do

YARA asks "is this sample X?". capa (Mandiant) asks a different question, which is "what capabilities does this binary have?". It runs a set of rules describing behavior based on APIs, strings and constants, and returns statements like "communicate over HTTP", "encrypt data using RC4", "inject code into another process", or "persist via registry run key".

capa is very useful at the triage step. Without reading any code yet, you already have a summary of what the binary does and which spots to read first. It also maps to MITRE ATT&CK so you use the same terms as the defense team. It goes well with [capa in triage from Lesson 2.1](/posts/re-2-1-five-minute-triage-die-strings-pe/).

## Sigma: behavior in logs

YARA and capa look at files. Sigma looks at logs. It's a common rule format for SIEMs and system logs (Windows Event Log, Sysmon, EDR), and it describes a suspicious behavior in a way that doesn't depend on any SIEM vendor, then converts to queries for Splunk, Elastic, Sentinel...

An example Sigma idea is that "process `winword.exe` spawns `powershell.exe`" is the typical malicious macro pattern. Or "a process writes into another process's memory and then creates a remote thread" (see the injection signs in [Lesson 17.4/17.5](/reverse-engineering/)). Sigma catches things YARA doesn't see, because it tracks runtime behavior rather than file contents.

So there are four tools at four layers, IOC (concrete data, easy to evade), YARA (file/memory contents), capa (capabilities), Sigma (behavior). The further down the list, the harder it is to evade. Attackers can change a domain easily, but changing how they behave takes real work.

## A practical workflow

After reversing a sample, I usually go through the same sequence. Compute hashes and pick out network/host IOCs (domains, mutexes, registry, dropped files). Then run capa to get a capability profile, so you know how it injects, encrypts and persists.

Next, write a YARA rule based on a combination of distinctive strings and byte patterns (preferring things that are hard to change), and test it against both the sample and a set of clean files to avoid false positives. After that, write a Sigma rule for the observed behavior (process tree, registry writes, network), so the SOC team can detect it even when the hash has changed. Finally, share the IOCs/YARA/Sigma with the community or internally.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 19.2</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/19.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/19.2/src/fakebot.yar" download><i class="fa-solid fa-download"></i>src/fakebot.yar</a>
<a class="lab-file" href="/assets/labs/19.2/src/sample_benign.bin" download><i class="fa-solid fa-download"></i>src/sample_benign.bin</a>
</div>
</div>

The goal is to write a YARA rule that recognizes a "sample" through a combination of characteristic strings, then run a scan to see which string matches at which offset. Everything in this lab is harmless. `sample_benign.bin` is not malware, it's a file containing a few marker strings for the rule to match against, so you can practice the syntax and workflow without a real malicious sample.

Install either the YARA CLI (`apt install yara` on Linux, or a Windows build from the official site) or yara-python (`pip install yara-python`). The lab has two files, `fakebot.yar`, a sample rule that recognizes a simulated FakeBot sample through its mutex, C2 URL, and the byte pattern of an RC4 key, and `sample_benign.bin`, the harmless file with the marker strings the rule matches against (it starts with a fake "MZ" so it passes the `uint16(0) == 0x5A4D` condition).

Read `fakebot.yar` and understand its `strings` section (text versus byte pattern) and its `condition` (`uint16(0)` filters for a PE, `3 of (...)` is a soft match). Run the rule against the sample file, either with the CLI (`yara fakebot.yar sample_benign.bin`) or with Python, as shown in the solution below.

Then change the condition to `5 of (...)` and run again. Does it still match? Why, given that the sample file only contains 3 of the 5 strings? Add a string of your own to both the rule and the sample file, and run again to see it match. Finally write a new rule based on only one very generic string (for example "http"), scan a few harmless files on your machine, and watch for false positives. Work out why a rule should rely on a combination of signals rather than one.

Two questions to think about. Why is a byte pattern (`{ 52 43 34 ... }`) more durable than a text string when malware changes its character encoding but keeps the same binary key? And when do you use `wide` instead of `ascii` in a rule for Windows malware? The answer and the real run output are in the collapsed section below.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The rule `fakebot.yar` matches a PE file (starting with the "MZ" bytes) that has at least 3 out of 5 signals, which are a mutex, a C2 URL, a user agent, the byte pattern of an RC4 key, and a PDB string. The sample file `sample_benign.bin` is a harmless 387-byte file that contains 3 of those 5 strings (the mutex, the C2 URL, and the RC4 key), so it matches.

The Python snippet used to scan it was run with yara-python 4.5.4 on Python 3.11.9.

```python
import yara
rules = yara.compile('fakebot.yar')
m = rules.match('sample_benign.bin')
print('MATCHES:', m)
for r in m:
    for s in r.strings:
        for inst in s.instances:
            print(f'  {s.identifier} @ offset {inst.offset}: {bytes(inst.matched_data)!r}')
```

The real result is this.

```
MATCHES: [FakeBot_Demo]
  $mutex @ offset 121: b'Global\\FakeBot_Mutex_v1'
  $c2 @ offset 145: b'http://c2.example-fakebot.test/gate.php'
  $key @ offset 185: b'RC4Key123'
```

The equivalent with the CLI is this.

```
$ yara fakebot.yar sample_benign.bin
FakeBot_Demo sample_benign.bin
```

Add `-s` to also print the matched strings and offsets like the Python output above.

Changing the condition to `5 of (...)`, the sample file only contains 3 of the 5 strings (`$ua`, the user agent, and `$pdb` are not in the file). So when you change the condition to `5 of ($mutex, $c2, $ua, $key, $pdb)`, the rule no longer matches. This is why a soft match (`3 of`) is useful because a variant can be missing a few strings and still get caught.

On the questions, a byte pattern is more durable than a text string because if malware changes how the key "RC4Key123" is displayed (for example by encoding the string and decoding it at runtime), the text string disappears from the static file. But if it still embeds the same binary key bytes somewhere, the byte pattern `{ 52 43 34 ... }` still catches it. A byte pattern can also target a piece of code, since a characteristic algorithm compiles to nearly fixed bytes, and using a wildcard `??` for a few address or relocation bytes lets a rule catch many variants that use the same algorithm.

As for wide, Windows uses UTF-16 (wide characters) for a lot of its APIs and strings (functions with a W suffix such as CreateFileW, paths, registry keys). A string like "SOFTWARE\\..." in the registry is usually stored as UTF-16 in the binary, so declare it as `wide` (or both `ascii wide`) so you don't miss it.

One safety note is not to use a real malware sample for this lab on your main machine. `sample_benign.bin` is deliberately harmless. When writing a rule for a real sample, work in an isolated VM, as covered in Lesson 0.3 on building a safe lab.

</details>

## Key takeaways

IOCs are concrete indicators (hash, domain, mutex, registry), easy to share but the easiest to evade. YARA scans files and memory with `strings` + `condition` and uses byte patterns to catch variants too. A good rule is based on a combination of indicators that are hard to change, and gets tested against clean files to avoid false positives.

capa answers "what can the binary do" and maps to ATT&CK, which is good for triage. Sigma catches behavior in logs and is harder to evade because it tracks runtime. On a durability scale it goes IOC < YARA < capa < Sigma.
