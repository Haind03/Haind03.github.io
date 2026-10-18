---
title: "Lesson 1.7: Hashing and evidence integrity"
image:
  path: /assets/img/covers/forensics-1-7-hashing-evidence-integrity.webp
  alt: "Hashing and evidence integrity"
date: 2023-06-15 09:35:00 +0700
categories: ["Forensics", "Forensics · Storage Foundations"]
tags: [forensics, disk, hex]
render_with_liquid: false
---

This whole field stands on one promise: "the image I analyze today is exactly the one I collected at the scene three months ago, not a bit off." You prove that promise with a hash. Without a hash, any investigation conclusion can be broken with one sentence: "how do you know you did not change the data?" So this lesson, though it is at the end of the foundations part, is the latch that holds the whole house. After it you understand why forensics still uses MD5 even though it is broken, and how fuzzy hashing helps when a normal hash cannot.

![Hashing and evidence integrity](/assets/img/forensics/forensics-1-7-hashing-evidence-integrity.svg)
_Hash the image at acquisition and again at verification; a single changed bit makes the digests differ, and fuzzy hashing scores near-identical files._

Level: medium, about 60 minutes. Prerequisite: Lesson 1.6. Tools: md5sum, sha256sum, hashdeep, ssdeep, Python hashlib.

## Goals

After this lesson you can explain the four properties of a hash function and why changing one bit changes the hash completely (avalanche), use a hash to prove an image was not changed and put the hash into chain of custody, answer firmly why forensics still uses MD5 despite collisions and when you absolutely must not use it, say what piecewise hashing helps with when verifying a large image with one damaged spot, and use ssdeep to find two near-identical files that MD5/SHA do not relate.

## Theory

### What a hash function is

A hash function takes an input of any length and produces a fixed-length string, called a digest or hash value. Four properties to remember:

- **Deterministic:** the same input always gives the same output. Hash a file today or next year, the result does not change if the file does not change.
- **One-way:** from the digest you cannot derive the original data. This is why a hash is not compression or encryption.
- **Avalanche:** changing even one bit of the input changes the output almost completely, there is no "roughly similar". This property is what makes a hash detect any change however small, but it is also what makes a hash useless when you want to know whether two files are "roughly alike" (see fuzzy hashing below).
- **Collision resistance:** it is very hard to find two different inputs that produce the same digest. How hard "very hard" is depends on the algorithm, and this is where MD5 is chipped.

### The algorithms you meet

| Algorithm | Digest length | Hex | Security status |
|---|---|---|---|
| MD5 | 128 bit | 32 chars | Collision broken (2004); still fine for integrity verify, forbidden where collision resistance is needed |
| SHA-1 | 160 bit | 40 chars | Collision broken (SHAttered, 2017); do not use for new security |
| SHA-256 | 256 bit | 64 chars | Secure, the current standard |
| SHA-512 | 512 bit | 128 chars | Secure, used when you want a longer digest |

SHA-256 and SHA-512 are in the SHA-2 family. There is also SHA-3 (a completely different construction, a backup if SHA-2 breaks) and BLAKE2/BLAKE3 (very fast), but in real forensics you meet MD5 and SHA-256 the most.

### What hashing is used for in an investigation

- **Image integrity verify:** this is the number one use. As soon as you create the image (Lesson 2.2), you hash it. Later, at any time, you hash it again and compare: a match means the image has not changed by a single bit. Many imaging tools (dc3dd, FTK Imager, ewfacquire) hash while reading the disk, then hash the written image to prove the copy process did not distort anything.
- **Chain of custody:** the hash is written into the seizure record, signed, timestamped. It is the technical evidence of integrity across the whole life of the case.
- **Known-file filtering:** use a known hash set like NSRL RDS (NIST's Reference Data Set) to drop millions of operating system and common software files (known to be harmless), so the investigator does not have to look at each one. The reverse direction: a set of known malware hashes to scan for bad files.
- **Dedup:** group duplicate files to avoid analyzing them twice.
- **File identification and IOC:** share the hash of a malware sample so others can look it up (VirusTotal, threat intel).

### Why MD5 is STILL used even though it is "broken"

This is the most misunderstood point. "MD5 is broken" is true, but you have to understand broken in what way:

- **Collision attack:** the attacker actively creates TWO different files with the same MD5. This is now cheap and fast. But note: the attacker controls BOTH files from the start.
- **Second-preimage attack:** given ONE specific file (the image you already collected), create a DIFFERENT file with the same MD5 as it. This is what threatens evidence integrity, and for MD5 it is still not feasible in practice to date.

See the difference? When you verify an already-collected image, the dangerous scenario is that someone changes the image yet keeps it matching the old hash, which is second-preimage, and MD5 still resists that. A collision is only dangerous when the fraudster is free to build both copies from the start (for example signing a document), not the situation of verifying an existing image. On top of that: MD5 is fast, short, and a deeply embedded standard across countless old tools and legal procedures. So MD5 lives on fine for integrity verification.

The best practice today: compute BOTH MD5 and SHA-256 (dual hash). For an image to match on both hashes, the chance of a match by accident or by building a simultaneous collision is nearly zero, and you keep compatibility with old tools while gaining the weight of SHA-256.

A firm warning: DO NOT use MD5 (or SHA-1) anywhere an attacker controls the content and only needs two colliding files, for example digital signatures, certificates, or hash-based malware identification. There cheap collisions will bite you. The line is: verifying a thing already fixed is fine with MD5; resisting someone building the thing from scratch is not.

### Piecewise (block) hashing

Hashing a whole 2TB image into one number has a weakness: just one bad sector changes the total hash, and you do not know where the error is. Piecewise hashing solves this by hashing fixed-size blocks (for example every 1MB or 64KB) in addition to the total hash. On verify, if one block is wrong, you know exactly which block is bad and the rest is still trustworthy. `hashdeep`, `dc3dd`, and the E01 format (EnCase Evidence File, hashing each 32KB chunk with a CRC) all work this way. It is very useful when reading a dying drive, keeping whatever you copy for sure.

### Fuzzy hashing: when you need "roughly alike"

Avalanche makes a normal hash useless for the question "are these two files related". Change one byte in a file and MD5 is completely different, so looking at two digests you cannot tell whether two files differ by one comma or are entirely different. Fuzzy hashing (also called similarity hashing) exists to answer exactly that question.

`ssdeep` is the classic tool, using CTPH (Context Triggered Piecewise Hashing, hashing pieces at content-dependent break points). Instead of hashing the whole file into one number, it splits the file at "anchor points" based on local content then hashes each piece, so when you insert/delete a few bytes at the start of the file, most of the later pieces keep their anchor points and still match. The comparison result is a score from 0 to 100 (100 is almost identical, 0 is unrelated). Applications:

- Group variants of the same malware family (differing a little to dodge signatures).
- Find a document slightly edited from an original.
- Detect near-duplicate files in a large data set.

Relatives of ssdeep include sdhash (based on statistical features) and TLSH (Trend Micro Locality Sensitive Hash, more robust on large files). ssdeep has limits: it is sensitive to size differences (two files far apart in size are hard to match even if their content is related) and a fraudster can deliberately dodge it. Use it as a lead to narrow down, do not treat the score as a final conclusion.

## Demo

Always work on a copy. Illustrate avalanche, integrity verify, piecewise, then fuzzy hashing.

```bash
# 1) Basic hash. Note MD5 is 32 hex, SHA-256 is 64 hex
echo -n "bang chung" > a.txt
md5sum a.txt
# 7f1f0...c9  a.txt   (32 chars)
sha256sum a.txt
# 2c26b...e1  a.txt   (64 chars)

# 2) Avalanche: change exactly one character then hash again, COMPLETELY different
echo -n "Bang chung" > b.txt      # only capitalize the B
sha256sum a.txt b.txt
# 2c26b46b68ffc68ff99b453c1d304...  a.txt
# 9f4390f8d30c2d0d1c3...           b.txt   <-- nothing like a.txt
```

Verify the integrity of an image: hash first, save it, then prove it later:

```bash
# At "collection": create the hash and store it in a record file
sha256sum disk.img | tee disk.img.sha256
# 3b8e...  disk.img

# At any time later: check it again
sha256sum -c disk.img.sha256
# disk.img: OK          <-- matches, the image has not changed by a bit

# Simulate someone changing 1 byte in the image then re-check
printf '\x00' | dd of=disk.img bs=1 seek=1000 count=1 conv=notrunc status=none
sha256sum -c disk.img.sha256
# disk.img: FAILED      <-- exposed at once, even for 1 changed byte
# sha256sum: WARNING: 1 computed checksum did NOT match
```

Piecewise hashing a whole directory tree with hashdeep (both MD5 and SHA-256), useful to verify piece by piece:

```bash
hashdeep -r -c md5,sha256 ./evidence_dir > manifest.txt
# the first line is a header, each file one line: size,md5,sha256,path
# To audit later: compare against the manifest, know which file changed/was lost/was added
hashdeep -r -c md5,sha256 -a -k manifest.txt ./evidence_dir   # -a audit mode
```

Fuzzy hashing: create two files that differ only slightly, then let ssdeep compare:

```bash
# Two "variants": v2 adds just one line versus v1
seq 1 1000 > v1.txt
cp v1.txt v2.txt
echo "them mot dong moi" >> v2.txt

# MD5 shows no relation (completely different)
md5sum v1.txt v2.txt
# 9a1f...  v1.txt
# e07c...  v2.txt      <-- looking at these you cannot guess they are nearly alike

# ssdeep: generate signatures then compare, a high similarity score
ssdeep -b v1.txt > sigs.txt
ssdeep -b -m sigs.txt v2.txt
# v2.txt matches v1.txt (99)      <-- 99/100: almost identical
```

For a large file or image, hash by streaming so you do not load it all into RAM (Python hashlib, reading chunk by chunk):

```python
# save as hash_stream.py, run: python3 -I hash_stream.py disk.img
import hashlib, sys

def hash_file(path, chunk=1024 * 1024):   # read 1MB at a time
    md5 = hashlib.md5()
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            md5.update(block)
            sha.update(block)
    return md5.hexdigest(), sha.hexdigest()

m, s = hash_file(sys.argv[1])
print("MD5   :", m)
print("SHA256:", s)
```

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 1.7</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-forensics/1.7.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-forensics/1.7/fuzzyhash.py" download><i class="fa-solid fa-file-code"></i>fuzzyhash.py</a>
<a class="lab-file" href="/assets/labs-forensics/1.7/make.sh" download><i class="fa-solid fa-file-code"></i>make.sh</a>
<a class="lab-file" href="/assets/labs-forensics/1.7/solve.sh" download><i class="fa-solid fa-file-code"></i>solve.sh</a>
</div>
</div>

A runnable lab (Linux, no root needed). Run `bash make.sh` then `bash solve.sh`.

Tasks:
- SHA-256 hash `disk.img` into a manifest, change exactly one byte with `dd ... conv=notrunc`, use `sha256sum -c` to prove it is detected; explain the avalanche property.
- Two variants `v1.txt`/`v2.txt` differing by a few lines: show that MD5/SHA-256 are completely different, then use a fuzzy hash to show they are near-identical and read the score. This machine has no ssdeep so the lab illustrates with `fuzzyhash.py` (Jaccard over shingles); the real tool is `ssdeep`.
- Answer in words (see `solution.md`): why MD5 is broken but still usable to detect change, and the dual hash best practice.
- Advanced (exercise): download a public MD5-colliding block pair, show that `md5sum` matches while `sha256sum` differs.

## Common pitfalls

- Forgetting to hash BEFORE operating. Without an initial mark you can prove nothing later; the first hash must be computed right at collection.
- Confusing the hash scope: hashing a whole device (`/dev/sdb`) is different from hashing a partition or a file. Record what you hashed.
- Using MD5 where collision resistance is needed (digital signatures, malware dedup where the attacker controls the input) and thinking it is safe.
- Assuming one changed byte changes the hash only a little; in fact it changes completely, which is why fuzzy hashing is needed for the "roughly alike" question.
- Using SHA-1 for a newly built security system; it has a collision break (SHAttered 2017).
- Treating an ssdeep score as solid proof. It is sensitive to size differences and can be dodged, so use it only to narrow down.
- Verifying a compressed/split image (split E01) while forgetting that the hash of each piece differs from the hash of the logical image; use the format's own tool to verify.

## Further reading

- NIST NSRL (Reference Data Set): the known-file hash set for filtering, nsrl.nist.gov.
- Marc Stevens and the SHAttered team: the papers on MD5 and SHA-1 collisions (shattered.io).
- RFC 1321 (MD5), FIPS 180-4 (the SHA-2 family).
- Jesse Kornblum, "Identifying almost identical files using context triggered piecewise hashing" (the original ssdeep/CTPH paper).
- man `md5sum`, `sha256sum`, `hashdeep`, `ssdeep`; the libewf documentation of the E01 format.

## Key takeaways

- [ ] Hash: deterministic, one-way, avalanche (change 1 bit, change the whole digest), collision resistant.
- [ ] Integrity verify is the number one use: hash at collection, hash again to prove the image is unchanged.
- [ ] MD5 is still usable for verify because it resists second-preimage; it only breaks on collisions when a fraudster builds both files.
- [ ] Dual hash (MD5 + SHA-256) is best practice; do not use MD5/SHA-1 where collision resistance is needed (signatures, malware identification).
- [ ] Piecewise hashing locates the damaged block in a large image.
- [ ] ssdeep (CTPH) finds near-identical files, scored 0-100, used for malware variants and lightly edited documents; treat it as a lead, not a verdict.
