---
title: "Lesson 3.2: File carving when metadata is gone"
image:
  path: /assets/img/covers/forensics-3-2-file-carving-metadata-gone.webp
  alt: "File carving when metadata is gone"
date: 2023-06-15 11:10:00 +0700
categories: ["Forensics", "Forensics · Disk Forensics"]
tags: [forensics, carving, recovery]
render_with_liquid: false
---

After this lesson you can recover files when the file system no longer knows anything about them: no name, no inode, no entry. You will carve by header/footer with foremost and scalpel, recover more intelligently with PhotoRec, and scan for content with bulk_extractor.

![File carving when metadata is gone](/assets/img/forensics/forensics-3-2-file-carving-metadata-gone.svg)
_A carver scans the raw block for a header, cuts to the matching footer, and the output has content only, no name or timestamp._

## Theory

### When the metadata is dead

Lesson 3.1 recovered a deleted file by following the leftover metadata: `fls` saw the inode, `icat` followed the cluster pointers. But what if the metadata is gone too? That happens when:

- The file was deleted long ago and its $MFT entry (or inode) has been reused for another file.
- The file system was formatted, corrupted, or the partition table was lost.
- You only have a raw block of data: a RAM dump, unallocated space, part of a drive, a pagefile.

Now nobody tells you where a file starts, how long it is, or what it is named. You have to recognize the file from its own content. That is file carving.

### Carving by header and footer

Many file formats have a fixed signature at the start (the header, also called the magic bytes), and many also have an end marker (the footer):

```text
Format      Header (hex)             Footer (hex)
JPEG        FF D8 FF                 FF D9
PNG         89 50 4E 47 0D 0A 1A 0A  49 45 4E 44 AE 42 60 82  (IEND...)
GIF         47 49 46 38 (GIF8)       00 3B
PDF         25 50 44 46 (%PDF)       25 25 45 4F 46 (%%EOF)
ZIP/docx    50 4B 03 04 (PK..)       50 4B 05 06 ...
PKZIP/Office is also PK
```

The basic carving algorithm scans the data block sequentially, marks a start when it meets a header, keeps scanning to the matching footer, and cuts that out as a file. For a format with no clear footer, the carver cuts at a preconfigured maximum size.

### Why carving is not perfect

Carving is strong but has built-in limits:

- **Fragmentation:** a real file may not sit contiguously on the drive. A JPEG split into 3 scattered fragments will trip up a header/footer carver, which cuts from header to footer continuously and grabs another file's junk in between. The result is a broken file. A smarter, file-structure-based carver tries to understand the structure and reassemble, which is better but still hard.
- **No name and no timestamp:** a carved file has no original name and no MAC times, because the metadata is gone. You only have the content.
- **False positive:** a byte sequence that matches a header appears by chance inside other data, and the carver thinks it is a file.
- **Overrun:** a format with no footer tends to be carved longer than the real file and drags in junk after it.

Keep these limits in mind so you are not surprised when you carve 500 JPEGs and half of them fail to open.

### Four tools, four roles

- **foremost:** the classic header/footer carver, configured in `foremost.conf`. Simple, fast, easy to understand.
- **scalpel:** originally a fork of foremost, optimized for performance, also driven by a file database in `scalpel.conf`. You enable the file types you need to carve.
- **PhotoRec:** a smarter carver that understands the structure of more than 480 formats, handles fragmentation much better, and produces less junk. It ships with TestDisk. The first choice when the goal is to recover as many usable files as possible.
- **bulk_extractor:** not exactly a file carver but a content scanner. It plows through a whole image (or dump) looking for email addresses, URLs, credit card numbers, phone numbers, domains, and even embedded PCAP, without needing to understand the file system. A good fit for quickly triaging "what is interesting in this blob of data".

## Demo

### Create an image to carve

We put a few files in, then delete and format so no metadata is left.

```bash
cd /tmp/claude-work
dd if=/dev/zero of=carve.img bs=1M count=60
mkfs.vfat carve.img
mkdir mnt && sudo mount -o loop carve.img mnt
# drop in a few real images and PDFs
sudo cp /usr/share/pixmaps/*.png mnt/ 2>/dev/null
sudo cp some_photo.jpg some_doc.pdf mnt/ 2>/dev/null
sudo umount mnt
# Now reformat to "wipe the metadata", the data still sits in the clusters
mkfs.vfat carve.img
```

### foremost

```bash
foremost -t jpg,png,pdf,gif -i carve.img -o out_foremost
# -t: file types to carve; -i: input; -o: output directory (must not exist)
# Output is split by type: out_foremost/jpg/, out_foremost/pdf/...
# The file audit.txt records the offset and size of each carved file.
cat out_foremost/audit.txt
ls -la out_foremost/jpg/
```

### scalpel

```bash
# Open /etc/scalpel/scalpel.conf, uncomment the format lines you need (jpg, png, pdf)
sudo sed -i 's/^#\(\s*jpg\)/\1/' /etc/scalpel/scalpel.conf    # example: enable jpg
scalpel carve.img -o out_scalpel
ls -la out_scalpel/
cat out_scalpel/audit.txt
```

### PhotoRec (smart, handles fragmentation well)

```bash
photorec carve.img
# PhotoRec runs interactively (ncurses interface):
#   choose the media (carve.img) > Proceed
#   choose partition / Whole disk > File Opt (pick the file types to find)
#   choose Search > choose the file system type (Other for FAT/NTFS) >
#   Free (free space only) or Whole > choose the destination directory > carve
# Output goes to recup_dir.1/, recup_dir.2/...

# Run non-interactively (batch):
photorec /log /d out_photorec/recup carve.img
```

### bulk_extractor (content scan)

```bash
bulk_extractor -o out_bulk carve.img
ls out_bulk/
# Produces feature files:
#   email.txt      emails found, with offset
#   url.txt        URLs
#   ccn.txt        credit card numbers (Luhn-checked)
#   telephone.txt  phone numbers
#   domain.txt     domains
#   packets.pcap   network packets if embedded PCAP is detected
cat out_bulk/email_histogram.txt   # sorted by frequency, the common ones surface
```

bulk_extractor does not care about the file system or partitions, it plows straight through the bytes, so it works on unallocated space, pagefiles, RAM dumps, and corrupted images.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 3.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-forensics/3.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-forensics/3.2/binwalk_shim.py" download><i class="fa-solid fa-file-code"></i>binwalk_shim.py</a>
<a class="lab-file" href="/assets/labs-forensics/3.2/carve.py" download><i class="fa-solid fa-file-code"></i>carve.py</a>
<a class="lab-file" href="/assets/labs-forensics/3.2/make.sh" download><i class="fa-solid fa-file-code"></i>make.sh</a>
<a class="lab-file" href="/assets/labs-forensics/3.2/solve.sh" download><i class="fa-solid fa-file-code"></i>solve.sh</a>
</div>
</div>

A real, runnable lab (Linux, no root needed): `labs/3.2/`. It uses an image pre-loaded with a JPG + PNG + ZIP + PDF (bytes concatenated, with junk in between). Run `bash make.sh` then `bash solve.sh`.

Tasks:

- Carve with `binwalk`, record the offset of each signature. Carve again with `carve.py` (a hand-written header/footer carver), and check whether the offsets match binwalk. (On this machine binwalk 2.x is stuck with the newer capstone, so it runs through `binwalk_shim.py`; a normal environment runs `binwalk` directly.)
- Open the carved files (`file`, `unzip -t`), count how many open correctly, and compare bytes against the originals with `cmp`/`md5sum`.
- Find a JPEG header yourself with `xxd carve.img | grep -i ffd8ff`, and compare the offset against binwalk.

Task as an exercise (foremost/PhotoRec/bulk_extractor are not installed on this machine): compare foremost with PhotoRec on a fragmented file; run bulk_extractor to find emails/URLs embedded in the ZIP.

Answers are in `labs/3.2/solution.md`, real output in `labs/3.2/transcript.txt`.

## Common pitfalls

- Expecting every carved file to open: fragmentation and false positives break some of them.
- Assuming a carved file keeps its original name and date: no, the metadata is gone.
- Carving on a live system drive by mistake instead of on a read-only image.
- Leaving too many file types enabled in foremost/scalpel on a large drive: tens of thousands of false positives, and the destination fills up.
- Skipping bulk_extractor because you think it does not "carve files": it is actually the fastest way to find IOCs in a large blob of data.
- Forgetting that carving is only one approach: if the metadata survives, metadata-based recovery (Lesson 3.3) gives a cleaner result with timestamps.

## Further reading

- foremost and scalpel man pages, and the `.conf` configuration files.
- PhotoRec step-by-step (cgsecurity.org), and the list of supported formats.
- bulk_extractor (Simson Garfinkel) and the paper "Digital media triage with bulk data analysis".
- The DFRWS File Carving Challenge, to see the limits of carving with fragmented files.

## Key takeaways

- Carving means recognizing a file from its content (header/footer), with no metadata needed.
- A carved file has no original name and no timestamp.
- foremost/scalpel are simple header/footer carvers; PhotoRec is smart and handles fragmentation well.
- bulk_extractor scans for emails/URLs/cards/PCAP and runs on unallocated space and dumps.
- Fragmented files are the enemy of carving, and the results can be broken.
