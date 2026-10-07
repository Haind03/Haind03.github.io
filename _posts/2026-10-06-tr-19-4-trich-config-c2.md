---
title: "Lesson 19.4: Extracting config and C2, pulling out the brain of the malware"
date: 2026-10-06 09:58:00 +0700
categories: ["Technique Reverse", "Part 19 · Malware Analysis Basics"]
tags: [reverse-engineering, malware]
render_with_liquid: false
---
Almost every piece of malware that can be controlled remotely carries a bit of config: the address of the command-and-control (C2) server, the port, the encryption key, a campaign id, a mutex name, a list of commands. Extract that config and you're holding a map of the attacker's infrastructure. It's one of the highest-value threat intel things an analyst can do, and it relies directly on the crypto skills from Part 16.

## Why it's worth the effort

A C2 domain pulled from one sample doesn't just help you block that one sample. It opens up:

- **Broad detection.** Writing a rule that blocks that domain/IP protects the whole organization, not just one machine.
- **Pivoting.** From one C2 you can trace other samples on the same infrastructure, the same campaign, the same group.
- **Takedown.** Report the domain/IP to the registrar or provider to get it removed.
- **Classifying the malware family.** The config structure is often distinctive for each family (Emotet, AgentTesla, Cobalt Strike...), and recognizing the config means recognizing the family.

In short: a hash identifies one file, a C2 identifies a whole campaign.

## Where the config lives and why you can't just read it

If malware left the C2 domain as a plain string in the binary, `strings` would pull it out, and so would every antivirus. So authors almost always hide it. Common kinds:

- **An encrypted blob** in a data section (usually XOR, RC4, AES, see Part 16), decrypted at runtime right before use.
- **Compression** (zlib, LZ) before encryption.
- **Stack strings** built one character at a time with `mov` instructions so they don't sit together as a string.
- **Resolved at runtime** from an algorithm (DGA, domain generation algorithm) instead of being stored.

What they have in common: on disk the config is a pile of meaningless bytes, and it only becomes a readable string in memory, in the brief moment before the malware uses it. Your job is to get it out, by the static or the dynamic route.

## Three ways to extract

### The static way: understand the algorithm and solve it yourself

This is the cleanest way and gives the deepest understanding. The steps:

1. **Find the config blob.** Signs: a data region with higher entropy than its surroundings, or one with a magic/marker, or one that an init function points to. Many families put a short marker before the blob (for example four identifying bytes).
2. **Find the decryption function.** Trace the xrefs to that blob. The first function that touches it is usually the decryptor. Read it to identify the algorithm: a loop with a per-byte `xor` is XOR, a 256-byte array being swapped is RC4, an S-box is AES (identified as in Lessons 16.1 to 16.3).
3. **Get the key.** The key may be a constant right in the code, or computed from a string, or sitting next to the blob.
4. **Rewrite it in Python.** Copy the algorithm and key into Python and decrypt, in the spirit of Lessons 16.2 and 16.4. The result is a readable config.

Pros: you don't need to run the sample, it's completely safe, and the script is reusable for every sample in the same family. A good config extractor is a long-term asset.

### The dynamic way: let the malware decrypt it and grab it

When the algorithm is too tangled to solve statically (multiple layers, obfuscated), let the malware do the heavy lifting itself:

1. Run the sample in an isolated lab (Lesson 0.3), under a debugger.
2. Set a breakpoint right **after** the decrypt function, or at a function that takes the decrypted config (for example a network connect function that takes the domain as a parameter).
3. When it stops, read the memory region holding the decrypted config and dump it.

Fast, and you don't need to fully understand the algorithm. The downside: you have to run the real sample so you need a sealed lab, and anti-debug/anti-VM (Part 15) can get in the way.

### The automatic way: sandbox and config extractors

- **CAPE/CAPEv2** has ready-made config extractors for lots of common malware families: feed the sample in, and it unpacks, decrypts, and prints the config itself. Always try it before doing it by hand.
- When you hit a family with no extractor yet, you **write one** (usually in Python, following the static route above) and contribute it back. This is how the community expands CAPE.

## Example workflow on an XOR then RC4 blob

Suppose you've reversed it and see that the decryptor works in two layers: RC4 with a string key, then a per-byte XOR with one byte. To decrypt, you undo the layers in the reverse of the author's encryption order. In the accompanying lab, the 157-byte blob starts with the marker `CFG0`, then a 4-byte little-endian length, then the encrypted data. The Python extractor, actually run, gives:

```
[+] Extracted C2 config:
{
  "c2": ["cdn.example-fake.test", "203.0.113.45"],
  "port": 8443,
  "campaign": "DEMO-2024-01",
  "mutex": "Global\\FakeMwDemoMutex",
  "sleep": 60
}
```

From a pile of bytes `43 46 47 30 95 00 00 00 f3 56 96 16 ...` to a complete set of IOCs. That's the entire value of this lesson. (The config in the lab is completely made up and harmless, with domains from the non-routable TEST-NET range.)

## Understand the C2 protocol too

Once you have the config, the next step is understanding how the malware **talks** to the C2: data framing, encryption on the wire, commands and responses. This is protocol reversing from Lesson 18.7, applied to the malware's network stream. Understanding the protocol lets you write network detections, even impersonate the C2 to observe (sinkhole), or decrypt traffic you've captured.

## Sharing IOCs responsibly

The IOCs you extract should be shared so the community can defend together, but done properly:

- Post them to a threat intel platform (MISP, VirusTotal, abuse.ch) with clear context.
- Distinguish real C2s from legitimate domains being abused (a lot of malware uses real cloud/CDN services as intermediaries, and blocking blindly means blocking a harmless service by mistake).
- Don't publish information that tips the attacker off too early if there's a coordinated takedown underway.

The spirit is the same as responsible disclosure in Lesson 0.2: share to protect, not to show off.

## Lab

In `labs/19.4/` there's `build_sample.py`, which builds a fake (harmless) C2 config blob that's XORed then RC4'd, and `extractor.py`, which reverses it into the config plus a list of IOCs. Task: run the build, then rewrite the extractor from scratch by reading the algorithm, without copying the existing one. Details in `labs/19.4/README.md`.

## Key takeaways
- Config (C2, key, mutex, campaign) is the most valuable threat intel target, one C2 identifies a whole campaign.
- Config is usually encrypted/compressed in the binary and only readable in memory at runtime.
- Three ways: static (understand the algorithm and solve it in Python, clean and reusable), dynamic (dump after the malware decrypts it itself), automatic (CAPE or write your own extractor).
- Identify the decryption algorithm following Part 16, get the key, rewrite it in Python.
- Understand the C2 protocol per Lesson 18.7 to write network detections.
- Share IOCs responsibly, and distinguish real C2s from legitimate services being abused.
