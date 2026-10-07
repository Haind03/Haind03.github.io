---
title: "Lesson 19.4: Extracting config and C2, pulling out the brain of the malware"
image:
  path: /assets/img/covers/re-19-4-extracting-config-c2-pulling-out-brain.webp
  alt: "Lesson 19.4: Extracting config and C2, pulling out the brain of the malware"
date: 2023-11-05 20:43:00 +0700
categories: ["Technique Reverse", "Part 19 · Malware Analysis Basics"]
tags: [reverse-engineering, malware]
render_with_liquid: false
---
Almost every piece of malware that can be controlled remotely carries a bit of config: the address of the command-and-control (C2) server, the port, the encryption key, a campaign id, a mutex name, a list of commands. Extract that config and you're holding a map of the attacker's infrastructure. It's one of the highest-value threat intel things an analyst can do, and it relies directly on the crypto skills from Part 16.

## Why it's worth the effort

A C2 domain pulled from one sample doesn't just help you block that one sample. It gives you broad detection, since writing a rule that blocks that domain/IP protects the whole organization, not just one machine. It lets you pivot, because from one C2 you can trace other samples on the same infrastructure, the same campaign, the same group. It supports takedown, since you can report the domain/IP to the registrar or provider to get it removed. And it helps classify the malware family, because the config structure is often distinctive for each family (Emotet, AgentTesla, Cobalt Strike...), and recognizing the config means recognizing the family.

In short: a hash identifies one file, a C2 identifies a whole campaign.

## Where the config lives and why you can't just read it

If malware left the C2 domain as a plain string in the binary, `strings` would pull it out, and so would every antivirus. So authors almost always hide it. The common kinds are an encrypted blob in a data section (usually XOR, RC4, AES, see Part 16) that is decrypted at runtime right before use, and compression (zlib, LZ) before encryption. Others are stack strings built one character at a time with `mov` instructions so they don't sit together as a string, and values resolved at runtime from an algorithm (DGA, domain generation algorithm) instead of being stored.

What they have in common is that on disk the config is a pile of meaningless bytes, and it only becomes a readable string in memory, in the brief moment before the malware uses it. Your job is to get it out, by the static or the dynamic route.

## Three ways to extract

### The static way: understand the algorithm and solve it yourself

This is the cleanest way and gives the deepest understanding. First you find the config blob. Signs are a data region with higher entropy than its surroundings, or one with a magic/marker, or one that an init function points to. Many families put a short marker before the blob (for example four identifying bytes).

Then you find the decryption function by tracing the xrefs to that blob. The first function that touches it is usually the decryptor. Read it to identify the algorithm: a loop with a per-byte `xor` is XOR, a 256-byte array being swapped is RC4, an S-box is AES (identified as in Lessons 16.1 to 16.3). Next you get the key, which may be a constant right in the code, or computed from a string, or sitting next to the blob. Finally you rewrite it in Python by copying the algorithm and key and decrypting, in the spirit of Lessons 16.2 and 16.4. The result is a readable config.

The upside is that you don't need to run the sample, it's completely safe, and the script is reusable for every sample in the same family. A good config extractor is a long-term asset.

### The dynamic way: let the malware decrypt it and grab it

When the algorithm is too tangled to solve statically (multiple layers, obfuscated), let the malware do the heavy lifting itself. Run the sample in an isolated lab (Lesson 0.3), under a debugger. Set a breakpoint right after the decrypt function, or at a function that takes the decrypted config (for example a network connect function that takes the domain as a parameter). When it stops, read the memory region holding the decrypted config and dump it.

It's fast, and you don't need to fully understand the algorithm. The downside is that you have to run the real sample so you need a sealed lab, and anti-debug/anti-VM (Part 15) can get in the way.

### The automatic way: sandbox and config extractors

CAPE/CAPEv2 has ready-made config extractors for lots of common malware families: feed the sample in, and it unpacks, decrypts, and prints the config itself. Always try it before doing it by hand. When you hit a family with no extractor yet, you write one (usually in Python, following the static route above) and contribute it back. This is how the community expands CAPE.

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

Once you have the config, the next step is understanding how the malware talks to the C2: data framing, encryption on the wire, commands and responses. This is protocol reversing from Lesson 18.7, applied to the malware's network stream. Understanding the protocol lets you write network detections, even impersonate the C2 to observe (sinkhole), or decrypt traffic you've captured.

## Sharing IOCs responsibly

The IOCs you extract should be shared so the community can defend together, but done properly. Post them to a threat intel platform (MISP, VirusTotal, abuse.ch) with clear context. Distinguish real C2s from legitimate domains being abused, since a lot of malware uses real cloud/CDN services as intermediaries, and blocking blindly means blocking a harmless service by mistake. And don't publish information that tips the attacker off too early if there's a coordinated takedown underway.

The spirit is the same as responsible disclosure in Lesson 0.2: share to protect, not to show off.

## Lab

This lab practices extracting a C2 config from an encrypted blob using a completely fake and harmless sample. There is no real malware and no network connection, and the domains come from the non-routable TEST-NET range. There are two files. `build_sample.py` creates `config_blob.bin`, a fake C2 config blob that is XORed with one byte and then RC4-encrypted, packed with the marker `CFG0` and a length. `extractor.py` is a reference config extractor that reverses it and prints the IOCs. You only need `python3`.

Run `python3 -I build_sample.py` to create `config_blob.bin`. Open it in a hex editor and recognize the `CFG0` marker and the 4-byte little-endian length field right after it. Pretend you don't know the algorithm yet. The blob has high entropy and no readable strings, which is the real situation when you meet malware. Then read `build_sample.py` as if it were what you just reversed out of the sample's decryptor: two layers, RC4 with a string key and then a one-byte XOR, plus the two keys.

Now rewrite the extractor from scratch (don't copy `extractor.py`). Read the file, find `CFG0`, take the length, cut out the blob, undo the RC4 and then remove the XOR, parse the JSON and print the C2, port, mutex and campaign. Finally, compare your result with `extractor.py`.

Some questions to think about. Why must you do the RC4 first and only then remove the XOR, and not the other way around? If you can't find the RC4 key in the code (for example the key is computed from another string at runtime), which route do you switch to? And why can a config extractor written once be used for many different samples of the same family?

<div class="lab-box">
<div class="lab-head"><b>LAB 19.4</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/19.4/src/build_sample.py" download><i class="fa-solid fa-file-code"></i>src/build_sample.py</a>
<a class="lab-file" href="/assets/labs/19.4/src/extractor.py" download><i class="fa-solid fa-file-code"></i>src/extractor.py</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This is a real run:

```
$ python3 -I build_sample.py
Created config_blob.bin, size: 157 bytes
Original plaintext (printed for comparison only, a real binary does NOT have this line):
  {"c2":["cdn.example-fake.test","203.0.113.45"],"port":8443,"campaign":"DEMO-2024-01","mutex":"Global\\FakeMwDemoMutex","sleep":60,"rc4_marker":"cfg"}
XOR key 1 byte: 0x6b
RC4 key: s3cr3t_campaign_key

$ python3 -I extractor.py config_blob.bin
[+] Extracted C2 config:
{
  "c2": [
    "cdn.example-fake.test",
    "203.0.113.45"
  ],
  "port": 8443,
  "campaign": "DEMO-2024-01",
  "mutex": "Global\\FakeMwDemoMutex",
  "sleep": 60,
  "rc4_marker": "cfg"
}

[+] IOCs extracted:
   C2: cdn.example-fake.test
   C2: 203.0.113.45
   Port: 8443
   Mutex: Global\FakeMwDemoMutex
   Campaign: DEMO-2024-01
```

The hexdump of the start of the blob (the marker `CFG0` = `43 46 47 30`, then the length `95 00 00 00` = 149 bytes of data):

```
00000000: 4346 4730 9500 0000 f356 9616 4a5d 73b5  CFG0.....V..J]s.
00000010: 4336 e770 031d 82c6 3b66 28c9 ad03 ff7e  C6.p....;f(....~
```

To locate the blob, the marker `CFG0` is what you find with `strings` or by searching for the bytes in a hex editor. Right after it come 4 little-endian bytes giving the length of the encrypted part (`95 00 00 00` = 0x95 = 149). Cut exactly 149 bytes from offset marker+8.

On the order of decryption, the author encrypted in the order plaintext, then 1-byte XOR, then RC4. To recover it you must do the reverse: RC4 first (RC4 is symmetric, so running it again with the same key decrypts), and only then remove the outer XOR layer. The wrong order gives garbage. That is the answer to the first question: whichever layer was wrapped last gets peeled first.

For the keys, in the lab the XOR key `0x6B` and the RC4 key `s3cr3t_campaign_key` are constants in the decryptor. With a real sample you read them from the code or from data next to the blob.

For parsing, once decrypted to JSON you just read the fields. With a real family the config may be a binary struct and not JSON, in which case you parse by offsets (using the skills from Lesson 18.7).

On the questions. You do RC4 first because it is the innermost layer from the encryption side (it was applied last), so it has to be peeled off first. Always unwrap in the reverse order of the wrapping. If the key is computed at runtime, switch to the dynamic route: set a breakpoint after the decryption function in an isolated lab and dump the decrypted config from memory, without needing to rebuild the key generation algorithm. And a config extractor written once works for many samples because samples of the same family use the same algorithm and the same config structure, differing only in the data and sometimes the keys. An extractor written once, with the keys as parameters, handles a whole batch of samples. That is why CAPE has per-family extractors.

The whole config is made up and harmless, the domains belong to the documentation and TEST-NET ranges, and there is no network behavior at all.

</details>

## Key takeaways
Config (C2, key, mutex, campaign) is the most valuable threat intel target, and one C2 identifies a whole campaign. It's usually encrypted or compressed in the binary and only readable in memory at runtime.

There are three ways to get it: static (understand the algorithm and solve it in Python, clean and reusable), dynamic (dump after the malware decrypts it itself), and automatic (CAPE or write your own extractor). Identify the decryption algorithm following Part 16, get the key, and rewrite it in Python. Understand the C2 protocol per Lesson 18.7 to write network detections, and share IOCs responsibly, distinguishing real C2s from legitimate services being abused.
