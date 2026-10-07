---
title: "Lesson 20.3: Final project, reverse a program and write the report"
image:
  path: /assets/img/covers/re-20-3-final-project-fully-reverse-program-write.webp
  alt: "Lesson 20.3: Final project, reverse a program and write the report"
date: 2023-11-20 22:22:00 +0700
categories: ["Technique Reverse", "Part 20 · Real-World Practice"]
tags: [reverse-engineering, ctf]
render_with_liquid: false
---
This is the last lesson of the series. Everything from Part 0 until now, reading assembly, rebuilding structs, unpacking, getting past anti-debug, writing keygens, extracting configs, comes together in one job: take a program you've never seen the inside of, and explain to other people how it works. It's not a ten-minute crackme. It's a target big enough that you have to plan, keep notes over several days, and then write it up as a report others can follow.

Solving crackmes is a sprint. This project is a long run. They're different skills, and the real RE job is the long run.

## Pick the right target

If you pick the wrong target the project falls apart, either too easy so you learn nothing, or too hard so you give up halfway. A few reasonable and legal choices. You can use a program of your own: build it, throw away the source, and reverse it yourself. It sounds a bit fake, but you have the answer key to grade yourself, which is good for a first time. You can take a multi-layer crackme from crackmes.one at level 4 or above, the kind that has both a serial algorithm and a layer of protection. A large CTF rev challenge also works, for example a late-season Flare-On challenge (challenges 7 to 10 are often a whole real program). Or you can pick an open-source program, reverse it and then compare with the source to check whether you read it correctly.

A reminder of the boundary in [Lesson 0.2](/posts/re-0-2-legal-ethics-part-everyone-wants-skip/): don't pick a commercial product and crack it, and don't touch someone else's system without permission. This project is to prove your skills, not to cause trouble.

A right-sized target is one where you finish triage in one evening and you're still curious, not discouraged.

## The project workflow

This is the [four-step process](/posts/re-0-4-reverse-engineering-workflow-not-get-lost/) from Part 0, stretched out for a large target.

### 1. Define the scope and questions

Don't say "I'll reverse this whole program". A real program has thousands of functions, most of them libraries and boilerplate, and you don't need to read them all. Write down a few concrete questions instead. What algorithm does the program use to check the license? Where does it store data, and in what format? Which server does it talk to, and with what protocol? Are there any anti-analysis mechanisms?

With clear questions you know when you're done. Without questions, you'll read assembly until morning for nothing.

### 2. Triage

Apply [Lesson 2.1](/posts/re-2-1-five-minute-triage-die-strings-pe/): file type, language, compiler, packed or not, 32 or 64 bit, notable strings, imports. The triage result decides which toolset you use (dnSpy for .NET, JADX for Android, IDA/Ghidra for native, GoReSym for Go...). Record the file hash right away for later cross-checking.

### 3. Map the functionality

Before digging deep, draw the overall map. Find the real `main` ([Lesson 3.1](/posts/re-3-1-hello-world-under-microscope-finding-real/)), and work from important strings and imports to carve out the big functional blocks (initialization, UI, data handling, network, protection). Rename and annotate in IDA/Ghidra as you understand things. The goal of this step isn't to understand every line, but to know where the interesting part is so the next step digs in the right place.

A simple block diagram drawn by hand or in a notes file, one line per block, helps a lot when you feel lost in a sea of functions.

### 4. Deep analysis of the main components

Now you dig. For each question from step 1, go into the block you carved out and apply the right technique. For a check algorithm or crypto, identify constants ([Lesson 16.1](/posts/re-16-1-identifying-crypto-algorithms-by-their-constants/)) and rewrite in Python or solve with Z3 ([Lesson 16.4](/posts/re-16-4-rewriting-algorithm-python-letting-z3-solve/)). For a protection layer, unpack ([Part 14](/technique-reverse/)) and get past anti-debug ([Part 15](/technique-reverse/)). For a data format or protocol, rebuild the spec ([Lesson 18.7](/posts/re-18-7-reversing-network-protocols-proprietary-file-formats/)). And confirm hypotheses dynamically by setting breakpoints, looking at real values, or hooking with Frida ([Lesson 17.2](/posts/re-17-2-frida-full-inspecting-modifying-program-while/)).

Keep repeating static, then dynamic, then notes, until you've answered all the questions.

### 5. Consolidate the findings

Once you've answered everything, stop digging and start writing. Gather the scattered notes into one coherent story: what this program is, how it works, where the notable points are.

## The structure of a good RE report

Many people skip the report, and it's what separates people who do this as a job from people who just play with tools. If you understand a function but can't write it up, three months later it's as if you never understood it. The standard outline has seven sections.

It opens with an executive summary: a few short paragraphs for people who won't read the technical parts, saying what this is, the main conclusion and how much it matters. Write this part last but put it first. Next comes methodology and tools, covering what you used and what environment you ran in (mention the isolated lab if it's malware), so others can reproduce it. Then sample information: file name, size, hashes (MD5/SHA-256), file type, compiler and version, which is the target's identity.

After that comes the program architecture, the overall map of the components and how they connect. A diagram helps a lot here. The detailed findings are the main part. Every finding comes with concrete evidence: function address, pseudocode screenshot, the key assembly snippet, values observed at runtime. The reader has to be able to follow along. If it's malware, add IOCs: hashes, domains, IPs, mutexes, registry keys, file paths, with YARA/Sigma if you have it ([Lesson 19.2](/posts/re-19-2-ioc-yara-capa-sigma-turning-sample/)). The report ends with conclusions and recommendations, which answer the original questions again, note what's still open, and give recommendations (patch the bug, block the IOCs, or directions for further analysis).

Every claim needs evidence. "The program encrypts with RC4" is an empty sentence until you point out which address the KSA function is at. Don't guess and then write it as if proven.

The full template to fill in is in the "Show sample report" block at the end.

## Lab

This is the final test of the series. You reverse a program end to end and write a complete report. There's no ready answer, because everyone picks a different target and the value is in the process. Choose a legal target (see the target-picking part above), reverse it to answer questions you set yourself, and then write the report following the sample report below.

For a suggested target by level, an easy one is a C/C++ program you write yourself (a few hundred lines, with a license check and file saving), built in release mode and then reversed, comparing against the source to grade yourself. A medium one is a crackme from crackmes.one at level 4 or higher, or an offline Unity Mono game of your own. A hard one is a challenge from an older Flare-On season (challenge 7 onward), or a public malware sample in an isolated lab, but only if you're solid on Part 19 and have set up the lab properly following Lesson 0.3.

What you hand in is the report following the template, with all seven sections, plus your raw notes file (or the IDA/Ghidra database with renames and comments) to prove the process. Add any scripts you wrote (a keygen, config extractor, solve script and so on), and if the target is malware, the IOCs and a YARA rule. To grade yourself, check these points. The scope should have a concrete question and not try to take on everything. Triage should identify the file type, language and protection correctly. For depth, you should be able to answer the questions you set, with specific pseudocode and addresses. On evidence, every claim should come with reproducible proof, and on reproducibility, someone else reading the report should be able to redo it. The report should read coherently with an executive summary that is easy to understand, and on ethics the target must be legal and you must not distribute cracks or samples.

A few tips. Spend the first session only on triage and mapping, and don't dig deep too early. Keep notes continuously and name functions as soon as you understand them. When you're stuck on a function, switch to dynamic analysis to see real values instead of reading statically forever. Write the executive summary last, once you understand the whole picture.

<details class="lab-solution" markdown="1">
<summary>Show sample report</summary>

This is a pre-filled template for the final project. Delete the bracketed lines and replace them with your own content, and keep every claim paired with evidence.

### Reverse Engineering Report: [Target name]

Analyst: [name]. Date: [YYYY-MM-DD]. Report version: 1.0.

---

#### 1. Executive summary

[Two to four paragraphs for a non-technical reader. What this is, the most important thing you found, and its severity or meaning. Write this section last.]

Key findings: [finding 1], [finding 2], [finding 3].

---

#### 2. Methodology and tools

The analysis goal is [the question you set]. The environment is [VM/host, OS, whether the network was isolated]. The tools used are [DIE, IDA/Ghidra, x64dbg, dnSpy, Frida, Python/Z3...]. The scope covers [which parts were analyzed, which were skipped and why].

---

#### 3. Sample information

| Attribute | Value |
|---|---|
| File name | [...] |
| Size | [... bytes] |
| MD5 | [...] |
| SHA-256 | [...] |
| File type | [PE/ELF/Mach-O/APK/.NET/...] |
| Architecture | [x86 / x64 / ARM64 / ...] |
| Compiler/Language | [MSVC / GCC / Go / Rust / .NET / ...] |
| Packer/Protector | [none / UPX / VMProtect / ...] |

---

#### 4. Program architecture

[Describe the overall components and how they connect. A block diagram helps.]

```
[Block diagram: main flow, modules, entry point, where network/crypto/protection calls happen]
```

| Component | Address/Module | Role |
|---|---|---|
| [Entry/main] | [0x...] | [...] |
| [License check] | [0x...] | [...] |
| [Data handling] | [0x...] | [...] |
| [Network/C2] | [0x...] | [...] |

---

#### 5. Detailed findings

Each finding gets its own subsection. Always attach evidence: addresses, pseudocode, assembly, or runtime values.

##### 5.1 [Finding name, for example: the serial check algorithm]

Description: [...]

Evidence: the function at `[0x...]`, and [a screenshot of the pseudocode or a code excerpt].

```c
// pseudocode taken from the decompiler
```

Analysis: [explain the logic and the conclusion drawn]

Reproduction (if you have a script):

```python
# keygen / solver / decoder
```

##### 5.2 [Next finding]

[...]

---

#### 6. IOCs (only for malware)

| Type | Value |
|---|---|
| SHA-256 | [...] |
| C2 domain | [...] |
| C2 IP | [...] |
| Mutex | [...] |
| Registry key | [...] |
| File dropped | [...] |

YARA rule:

```
rule [Rule_Name] {
    meta:
        description = "[...]"
        author = "[...]"
    strings:
        $a = "[...]"
    condition:
        $a
}
```

---

#### 7. Conclusion and recommendations

Answers to the original questions: [question 1 -> answer], [question 2 -> answer]. Open points: [parts not fully analyzed]. Recommendations: [patching, blocking the IOCs, directions for further analysis, or lessons learned].

---

#### Appendix

[List of function addresses you named] and [links to scripts, the IDA/Ghidra database, and raw notes].

</details>

## Key takeaways
Pick a right-sized and legal target, not too easy and not too hard. Start with concrete questions and don't take on "reverse everything". Triage, map, and only then dig deep in the right place, repeating static and dynamic.

Write a structured report with every claim backed by evidence (address, pseudocode, runtime value). If you can write it up, then you've really understood it.

## Closing words

You started by opening IDA and panicking at a sea of assembly, and now you can unpack, get past anti-debug, write keygens, extract C2 configs and write a complete report yourself. That's a long road and you should be proud.

RE has no finish line. There's always a new packer, a new architecture, a more sophisticated protector. From here you choose a direction to go deeper: malware analysis and threat intel, vulnerability research and exploits, or mobile and games. Each direction is its own series worth a whole year. Keep practicing steadily on [crackmes.one and Flare-On](/posts/re-resources-study-materials-places-practice/), and keep the curiosity that brought you here.

And remember [Lesson 0.2](/posts/re-0-2-legal-ethics-part-everyone-wants-skip/): use this skill for good things. Happy reversing.

## Common pitfalls
People dig too deep into library code unrelated to their questions and waste hours for nothing. They skip notes, so when it's time to write the report they have to start over. They draw conclusions without evidence, and the report loses its value. And they pick a target that's too ambitious and then give up.
