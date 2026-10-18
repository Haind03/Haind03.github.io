---
title: Forensics
icon: fas fa-magnifying-glass
order: 6
render_with_liquid: false
---

My notes on digital forensics and incident response, from how a disk stores data through evidence acquisition, disk and file-system analysis, Windows, Linux and macOS artifacts, memory, network, timelines and reporting. Each lesson pairs the theory with a tool demo and a lab you can run yourself.

Everything here is for learning, CTFs and investigations on systems you are authorized to examine. Work on images and copies, and keep the chain of custody.
{: .prompt-warning }

## Forensics · Intro to Forensics

| # | Lesson |
|---|---|
| 0.1 | [What Digital Forensics Is](/posts/forensics-0-1-digital-forensics/) |
| 0.2 | [Law, Ethics and Chain of Custody](/posts/forensics-0-2-law-ethics-chain-custody/) |
| 0.3 | [Building a Forensics Lab](/posts/forensics-0-3-building-forensics-lab/) |
| 0.4 | [The Standard Investigation Process](/posts/forensics-0-4-standard-investigation-process/) |

## Forensics · Storage Foundations

| # | Lesson |
|---|---|
| 1.1 | [Hex, endianness and magic bytes](/posts/forensics-1-1-hex-endianness-magic-bytes/) |
| 1.2 | [Sectors, clusters, LBA and slack space](/posts/forensics-1-2-sectors-clusters-lba-slack-space/) |
| 1.3 | [MBR and GPT partition tables](/posts/forensics-1-3-mbr-gpt-partition-tables/) |
| 1.4 | [FAT and exFAT file systems](/posts/forensics-1-4-fat-exfat-file-systems/) |
| 1.5 | [NTFS and the MFT](/posts/forensics-1-5-ntfs-mft/) |
| 1.6 | [ext4, APFS and HFS+ for forensics](/posts/forensics-1-6-ext4-apfs-hfs-forensics/) |
| 1.7 | [Hashing and evidence integrity](/posts/forensics-1-7-hashing-evidence-integrity/) |

## Forensics · Evidence Acquisition

| # | Lesson |
|---|---|
| 2.1 | [Order of volatility, live and dead acquisition](/posts/forensics-2-1-order-volatility-live-dead-acquisition/) |
| 2.2 | [Creating a forensic disk image](/posts/forensics-2-2-creating-forensic-disk-image/) |
| 2.3 | [Acquiring RAM on Windows and Linux](/posts/forensics-2-3-acquiring-ram-windows-linux/) |
| 2.4 | [Fast triage at the scene](/posts/forensics-2-4-fast-triage-scene/) |

## Forensics · Disk Forensics

| # | Lesson |
|---|---|
| 3.1 | [The Sleuth Kit and Autopsy](/posts/forensics-3-1-sleuth-kit-autopsy/) |
| 3.2 | [File carving when metadata is gone](/posts/forensics-3-2-file-carving-metadata-gone/) |
| 3.3 | [Recovering deleted files on NTFS and FAT](/posts/forensics-3-3-recovering-deleted-files-ntfs-fat/) |
| 3.4 | [Analyzing hidden data](/posts/forensics-3-4-analyzing-hidden-data/) |

## Forensics · Windows Forensics

| # | Lesson |
|---|---|
| 4.1 | [Registry Forensics and the Windows Hives](/posts/forensics-4-1-registry-forensics-windows-hives/) |
| 4.2 | [Event Log Forensics with evtx Files](/posts/forensics-4-2-event-log-forensics-evtx/) |
| 4.3 | [Program Execution and Proving a Program Ran](/posts/forensics-4-3-program-execution-proving-program-ran/) |
| 4.4 | [File and Folder Access Artifacts](/posts/forensics-4-4-file-folder-access-artifacts/) |
| 4.5 | [Windows Persistence and Where Malware Hides](/posts/forensics-4-5-windows-persistence-malware-hides/) |
| 4.6 | [Volume Shadow Copy and Recovering Old Files](/posts/forensics-4-6-volume-shadow-copy-recovering-old-files/) |

## Forensics · Linux and macOS

| # | Lesson |
|---|---|
| 5.1 | [Linux artifacts after an SSH brute force](/posts/forensics-5-1-linux-artifacts-ssh-brute-force/) |
| 5.2 | [macOS artifacts behind a suspicious auto-start app](/posts/forensics-5-2-macos-artifacts-suspicious-auto-start-app/) |

## Forensics · Memory Forensics

| # | Lesson |
|---|---|
| 6.1 | [Memory forensics and Volatility 3 from scratch](/posts/forensics-6-1-memory-forensics-volatility-3/) |
| 6.2 | [Processes, DLLs, network, and hidden processes](/posts/forensics-6-2-processes-dlls-network-hidden-processes/) |
| 6.3 | [Detecting code injection, process hollowing, and rootkits in RAM](/posts/forensics-6-3-code-injection-process-hollowing-rootkits/) |
| 6.4 | [Extracting credentials and fileless PowerShell payloads from RAM](/posts/forensics-6-4-credentials-fileless-powershell-ram/) |

## Forensics · Network Forensics

| # | Lesson |
|---|---|
| 7.1 | [Reading pcap with Wireshark, filters, and object export](/posts/forensics-7-1-reading-pcap-wireshark-filters-object-export/) |
| 7.2 | [Traffic analysis with Zeek and NetworkMiner](/posts/forensics-7-2-traffic-analysis-zeek-networkminer/) |
| 7.3 | [Detecting C2, DNS tunneling, and exfiltration](/posts/forensics-7-3-detecting-c2-dns-tunneling-exfiltration/) |

## Forensics · Browser, Email, Mobile

| # | Lesson |
|---|---|
| 8.1 | [Browser forensics and reconstructing web activity](/posts/forensics-8-1-browser-forensics-reconstructing-web-activity/) |
| 8.2 | [Email forensics and tracing the sender](/posts/forensics-8-2-email-forensics-tracing-sender/) |
| 8.3 | [Mobile forensics with Android and iOS backups](/posts/forensics-8-3-mobile-forensics-android-ios-backup/) |

## Forensics · Timeline and IR

| # | Lesson |
|---|---|
| 9.1 | [Super Timelines with plaso and Timesketch](/posts/forensics-9-1-super-timelines-plaso-timesketch/) |
| 9.2 | [Reconstructing the Attack Chain with MITRE ATT&CK](/posts/forensics-9-2-reconstructing-attack-chain-mitre-attack/) |
| 9.3 | [IOCs and YARA for Bulk Artifact Scanning](/posts/forensics-9-3-iocs-yara-bulk-artifact-scanning/) |

## Forensics · Anti-Forensics

| # | Lesson |
|---|---|
| 10.1 | [Timestomp, Wiping and Log Clearing Detection](/posts/forensics-10-1-timestomp-wiping-log-clearing-detection/) |
| 10.2 | [Full Disk Encryption and Investigation Strategy](/posts/forensics-10-2-full-disk-encryption-investigation-strategy/) |

## Forensics · Hands-on

| # | Lesson |
|---|---|
| 11.1 | [Solving CTF forensics challenges](/posts/forensics-11-1-solving-ctf-forensics-challenges/) |
| 11.2 | [Investigating a malware infected image end to end](/posts/forensics-11-2-investigating-malware-infected-image/) |
| 11.3 | [Writing a standard forensics report](/posts/forensics-11-3-writing-standard-forensics-report/) |
