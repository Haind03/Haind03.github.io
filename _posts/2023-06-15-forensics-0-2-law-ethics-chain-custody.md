---
title: "Lesson 0.2: Law, Ethics and Chain of Custody"
image:
  path: /assets/img/covers/forensics-0-2-law-ethics-chain-custody.webp
  alt: "Law, Ethics and Chain of Custody"
date: 2023-06-15 08:10:00 +0700
categories: ["Forensics", "Forensics · Intro to Forensics"]
tags: [forensics, chain-of-custody, methodology]
render_with_liquid: false
---

This lesson explains why forensics is not only a technical matter. You will learn what chain of custody is and how to record it, Locard's exchange principle and the four ACPO principles, and the answer to the perennial question of why you always work on a copy.

![Law, Ethics and Chain of Custody](/assets/img/forensics/forensics-0-2-law-ethics-chain-custody.svg)
_The hash computed at collection is the anchor that proves the evidence was never altered._

Part: 0 (Intro to Forensics) | Time: about 35 minutes | Difficulty: basic

**Prerequisites:** Lesson 0.1 (what Digital Forensics is).

**Tools:** the hashing commands already present (`sha256sum`, `md5sum`) and a text editor to practice writing records.

## Goals

After this lesson you can explain what chain of custody is and the minimum information it must record. You can state Locard's exchange principle and relate it to digital traces, name the four ACPO principles and the practical meaning of each, and give three reasons why every analysis is done on a copy and never on the original. You can also tell apart the ethical and legal boundaries of what is allowed and what is not.

## 1. Theory

### Why this lesson matters more than it looks

This lesson has no clever commands and no fancy tools. But it is the one most often skipped, and the one that causes the heaviest damage when skipped. The reason is simple: a technical analysis, however brilliant, is worthless if the evidence was collected incorrectly or its integrity cannot be proven. In a legal matter it is thrown out immediately. In an internal company matter it convinces no one. The effort is wasted because of a process error in the first minute.

To put it plainly: most beginners rush to touch the data and analyze it. People who have been in the job a long time spend the early time protecting the evidence, because they have seen (or heard of) a case collapse just because someone opened the original file to take a look.

### Locard's exchange principle

Edmond Locard was a French criminologist of the early twentieth century. The principle named after him, Locard's exchange principle, states simply that every contact leaves a trace. The perpetrator carries away something of the scene and leaves at the scene something of their own.

In the physical world that is a hair, a fingerprint, a fiber. Moved to the digital world, the principle still holds and holds even more strongly, because a computer records almost everything obsessively:

- Open a file, and the access timestamp is updated.
- Run a program, and Prefetch and Amcache record it.
- Plug in a USB stick, and the registry stores the device identifier.
- Send data out, and network logs and caches keep a trace.

This is the philosophical foundation of the whole field: an attacker cannot act without leaving a trace. Your job is to find that trace. But, and this is the flip side you must burn into memory, Locard applies to you as well. Every action of the investigator also leaves a trace. Open the original file to look at it and you have just changed its access timestamp. You have just contaminated the evidence with a trace of your own. It is precisely because Locard applies to both sides that we need the principles that follow.

### The four ACPO principles

ACPO stands for the Association of Chief Police Officers, in the United Kingdom. Their guidance, the "ACPO Good Practice Guide for Digital Evidence", is condensed into four principles cited around the world. The organization has since changed its name, but the community still calls them the ACPO principles. Learn these four, because almost every hard decision in the job comes back to them.

**Principle 1: No action should change the data.** No action taken by the investigating body should change data held on the original device, if that data may later be used as evidence. This is the reason for write blockers and for working on an image. The default is: do not touch the original.

**Principle 2: If you must touch the original data, you must be competent and able to justify it.** There are unavoidable situations, the classic one being a running machine where you need to dump RAM before shutting down. Dumping RAM certainly changes a little of the machine state. Principle 2 says that is fine, but the person doing it must understand what they are doing, what the consequences are, and be ready to explain why it was necessary. It does not forbid touching the original, it forbids touching it without understanding.

**Principle 3: There must be a full record of every action, enough for a third party to repeat it and reach the same result.** This is exactly chain of custody and the investigation journal. If an independent expert reads your record and repeats it identically, they must reach the same result. Reproducibility is the standard you aim for. Whatever is not recorded is treated as not having happened, or worse, it looks like you are hiding something.

**Principle 4: The person in charge of the case is responsible overall for compliance with the law and these principles.** Responsibility does not vanish because work is divided among several people. There is one person who carries the can.

Notice how the four principles fit together: principle 1 sets the ideal (do not touch the original), principle 2 handles the exception (when you must), principle 3 forces you to record everything (for reproducibility), and principle 4 assigns responsibility. It is not a dry set of rules, it is a logical system for keeping evidence trustworthy.

### Chain of custody: the evidence passport

Chain of custody is the continuous record that answers the question: from collection until now, where has this evidence been, in whose hands, and has anything touched it. Think of it as a passport stamped at every stage of a piece of evidence. Every time it changes hands or changes location, there must be a line recording it.

A minimum chain of custody record must have:

- Evidence identification: the number, a physical description (for example "Seagate 1TB hard drive, serial ABC123"), which case it belongs to.
- Time of collection: date and time, with the time zone stated. This is the place most often gotten wrong, discussed in the pitfalls section.
- Who collected it, where, and under what circumstances.
- The hash of the evidence at the moment of collection: this is the mathematical anchor. SHA-256 (and often MD5 alongside for compatibility with older tools). This hash later proves no one changed the data.
- Every transfer: from whom to whom, when, with a signature.
- Where it is stored: a safe, a locked cabinet, an evidence store, with access control.

The vital rule: chain of custody must be continuous, with no break. If there is a stretch of time where no one can account for where the evidence was, the opposing side will argue that during that gap it could have been tampered with. One hole is enough to sink a whole case. Better the nuisance of recording too much than recording too little.

### Why you always work on a copy

This question is answered by what you just learned. Three reasons, from strongest to softest:

**Reason 1, integrity (mandatory).** The original is the evidence. Every read, open or run risks changing it, remember Locard. Work on an image (a bit-for-bit copy) and the original is sealed, kept in its original state. If you damage the copy by accident, you make another copy from the original. The original is irreplaceable and must be protected that way.

**Reason 2, provability (legal).** You compute the hash when you create the image. At any time you can recompute the hash of the original and of the copy, compare them, and prove they are identical and untouched. This is how you answer the question "how do I trust you did not change anything". Without working on a copy there is no such anchor.

**Reason 3, operational safety (practical).** Analysis often goes wrong, often has to be redone, often uses tools with bugs. Work on a copy and you can experiment freely, make another if it breaks. Work on the original and one slip of a command is lost forever. The copy gives you the right to be wrong.

There is one exception you should know in advance: you cannot always make a copy before touching anything. On a running machine the RAM will be lost at power off, so you are forced to collect from the live system (live acquisition). That is when ACPO principle 2 speaks up: it is allowed, but you must be competent, use tools with minimal impact, and record exactly what you did. This does not contradict "work on a copy", it is the case where collecting the copy is itself that unavoidable action. Part 2 goes deeper.

### The ethical and legal boundaries

This part is short, but do not treat it lightly. Forensic skills give you the ability to read other people's private data. That ability comes with responsibility.

- Authorization is what you must have before touching anything. You investigate only systems you own, or that the owner permits in writing, or that the law permits (a court order, an official duty). Without one of those three, stop.
- Scope limits what you may look at. Being allowed to investigate a malware incident does not mean being allowed to rummage through an employee's personal email for fun. Going out of scope is both unethical and possibly illegal.
- Data confidentiality: evidence contains sensitive information. You keep it private, share it only with those who have the right, and dispose of it correctly when the work is done.
- Honesty: you report the traces that argue against your theory, not only those that support it. An investigator is not a prosecution lawyer. Bending the facts to suit someone is a betrayal of the core of the job.

In Vietnam, unauthorized access to another party's information systems and data can constitute an offense under the Penal Code. The legal detail is outside the scope of this series, but the principle is universal: no permission, no touching. All the content in this series is for learning, CTF, investigation on your own systems, and authorized defensive research.

## 2. Hands-on (demo)

This demo uses no investigation tool, it drills the two core skills of the lesson: anchoring evidence with a hash, and writing a proper chain of custody line. This is a motion you will repeat thousands of times in the job, so make it a reflex from now.

```text
# 1. Simulate the "original evidence" (in practice this is a disk or its image)
$ dd if=/dev/urandom of=goc.img bs=1M count=10 status=none
$ ls -l goc.img
-rw-r--r-- 1 user user 10485760 Oct  8 09:40 goc.img

# 2. Anchor integrity: compute the hash RIGHT at collection, save it to a file
$ sha256sum goc.img | tee goc.img.sha256
3f8a...c1  goc.img
$ md5sum goc.img | tee goc.img.md5
9ab0...7e  goc.img

# 3. Make a copy to work on. From now on touch only this copy.
$ cp goc.img lamviec.img

# 4. Prove the copy is identical to the original
$ sha256sum lamviec.img
3f8a...c1  lamviec.img        # matches the hash from step 2 -> copy is intact

# 5. Re-check the original at any time, it must match the saved hash
$ sha256sum -c goc.img.sha256
goc.img: OK
```

Step 5 is the small trick of the trade: the `-c` option reads the saved hash and compares it with the current state. OK means the evidence has not been touched. If anyone changed even a byte, it reports FAILED at once. This is mathematical proof of integrity, something that mere words cannot replace.

Now practice writing one chain of custody line. No software needed, a disciplined text file is enough to start:

```text
=== CHAIN OF CUSTODY RECORD ===
Case:          VV-2026-014 (suspected malware on the accounting machine)
Evidence:      BC-01, image file goc.img (simulated 10MB USB)
Source:        USB Kingston SN:FAKE123, collected in the accounting office
Collected at:  2026-10-08 09:40:00 +07:00 (Vietnam time, UTC+7)
Collected by:  Nguyen Van A
SHA-256:       3f8a...c1
MD5:           9ab0...7e
Stored at:     Locked evidence cabinet, IT room, key held by A

--- Transfer log ---
2026-10-08 10:15 +07:00  A hands the copy lamviec.img to B for analysis
                         (the original goc.img is sealed and does not travel)
```

Notice the valuable details: the time zone is stated clearly (+07:00), both hashes are present, and crucially, only the copy is taken away for analysis while the original sits untouched in the locked cabinet. That is the lesson wrapped up in one small record.

## 3. Lab

- Data: create one as in the demo, or use any file on your machine as "evidence".
- Task 1: create a fake image file, compute and save both SHA-256 and MD5, make a copy, then prove the copy matches the original with `sha256sum -c`. Then deliberately change one byte of the copy (with a hex editor or `printf`) and run the check again, observing it report FAILED.
- Task 2: write a complete chain of custody record for a situation you invent (for example: seizing a laptop in a suspected data leak). It must include all of: identification, source, time with time zone, who collected it, both hashes, storage location, and at least one transfer line.
- Task 3: for each ACPO principle, write one sentence describing a real situation where that principle is violated, and the consequence.
- Hint: Task 3 is a thinking exercise. For example, principle 3 is violated when you run a series of analysis commands without recording them, and later, asked "how did you get this result", you cannot reconstruct it.
- Answer: self-check by these criteria. Task 1 is correct when you see exactly one OK and one FAILED. Task 2 is correct when the record is missing none of the fields from the "minimum" list in the theory section.

## 4. Key takeaways

- [ ] Locard: every contact leaves a trace. It applies to the attacker (so there is always a trace to find) and to you (so do not touch the original).
- [ ] ACPO 1: do not change the original. ACPO 2: if you must, be competent and able to justify it. ACPO 3: record everything so a third party can reproduce it. ACPO 4: one person is responsible overall.
- [ ] Chain of custody must be continuous, with no gap. Minimum: identification, time with time zone, person, hash, transfers, storage location.
- [ ] Work on a copy for three reasons: integrity (the original is unique), provability (hashes compared), safety (the right to be wrong).
- [ ] The hash computed at collection is the mathematical anchor for integrity. Use `sha256sum -c` to re-check at any time.
- [ ] No authorization, no touching. Stay within the permitted scope. Report honestly, including the unfavorable traces.
