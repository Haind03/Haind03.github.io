---
title: "Lesson 0.3: Setting up a safe lab"
image:
  path: /assets/img/covers/re-0-3-set-up-safe-lab-before-touching.webp
  alt: "Lesson 0.3: Setting up a safe lab"
date: 2022-01-29 21:43:00 +0700
categories: ["Reverse Engineering", "Part 00 · Getting Started"]
tags: [reverse-engineering, basics]
render_with_liquid: false
---
Never run an unknown sample on your real machine. Some people learn this by losing an evening cleaning up after "just running it to see what it does". Read this post and skip that part.

For crackmes and CTFs the risk is close to zero, and running them on a normal machine is fine. Once you touch real malware or a binary of unknown origin, you need a lab. Set it up once and reuse it.

## Why you need a separate virtual machine

There are three reasons. First is isolation, because malware running in a VM can't touch your real machine if you configure things correctly. Second is snapshots. You save the clean state of the VM, run the sample, analyze as much as you like, then revert to the exact clean state in a few seconds. No reinstalling Windows, no cleanup. Third, you install your tools once and clone the VM as many times as you want.

## Choosing a hypervisor

The software that creates VMs is called a hypervisor. VMware Workstation (Windows/Linux) or Fusion (macOS) is stable, has good snapshots, and most malware people use it. The personal edition is free now. VirtualBox is free and open source, and good enough for learning, but its snapshots are a bit less smooth than VMware's. Hyper-V comes with Windows Pro and works, but fewer RE tools support it out of the box.

If you're a beginner, just take VirtualBox or the free VMware. Don't spend too long on this choice.

## Network configuration

By default a VM connects to the internet through NAT. With malware, that's when it calls home to its command-and-control (C2) server, and it may even spread to other machines on your home network. There are three modes to remember.

Host-only (or an internal network) means the VM only talks to the host or to other VMs, with no internet. This is the default when analyzing malware. NAT lets the VM reach the internet, so only turn it on when you deliberately want to watch the sample's real network traffic and accept the risk. The third option is a simulated internet, where a second VM running INetSim or FakeNet-NG pretends to be every network service (DNS, HTTP, SMTP...). The malware thinks it got out and shows its behavior, while the packets go nowhere. This is the standard setup for a serious lab.

The classic two-VM model is one Windows VM that runs the sample (the victim machine), and one Linux VM acting as the fake network gateway and packet capture. They're connected through a host-only network, completely separate from your home network.

## Small settings that matter

Take a clean snapshot right after installing your tools, before running any sample, and give it a clear name like `clean-base`. Turn off shared folders and the shared clipboard when analyzing real malware. They're two escape routes that people often forget (turn them back on for crackmes). Turn off USB auto-mount too.

For sophisticated samples, consider not installing VM Guest Additions or VMware Tools, since a lot of malware checks for them to see if it's being watched (anti-VM, covered in [Lesson 15.5](/reverse-engineering/)). Keep your tools on the host or on a read-only shared drive, away from the folder that holds samples.

## Pre-built tools: FLARE-VM and REMnux

You don't have to install hundreds of tools by hand. FLARE-VM (from Mandiant) is a PowerShell script you run on a clean Windows VM. It downloads and installs lots of RE and malware analysis tools, such as x64dbg, IDA Free, Ghidra, PE-bear, dnSpy, Detour, and many more. Snapshot right after the install. REMnux is a prebuilt Linux distro for malware analysis, with tools for file, network, maldoc, and memory analysis. It usually plays the Linux VM in the two-VM model.

A short workflow for beginners is to install Windows into a VM, run FLARE-VM, snapshot `clean-base`. Add a REMnux VM as the network gateway. That's a decent lab.

## How serious you need to get

Don't build a complicated lab for something that doesn't need one. A quick scale:

| What you're doing | Lab level needed |
|---|---|
| Crackme, CTF, binaries you wrote yourself | Real machine is fine, or a normal VM |
| Unknown software of unclear origin | VM with snapshot, host-only network |
| Real malware | Isolated VM + simulated network + snapshot, strictly host-only |
| Sophisticated APT sample with anti-VM | Dedicated lab, consider a separate physical machine (bare-metal) |

## Key takeaways
Don't run unknown samples on your real machine. Take a clean snapshot before running anything, and revert when you're done. For malware, use a host-only or simulated network (INetSim/FakeNet) and turn off shared folders and clipboard.

FLARE-VM (Windows) plus REMnux (Linux) give you a full lab without installing by hand. Match the lab level to how dangerous the sample is.
