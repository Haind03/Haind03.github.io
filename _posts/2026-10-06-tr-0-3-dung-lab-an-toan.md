---
title: "Lesson 0.3: Set up a safe lab before touching anything dangerous"
date: 2026-10-06 08:02:00 +0700
categories: ["Technique Reverse", "Part 00 · Getting Started"]
tags: [reverse-engineering, basics]
render_with_liquid: false
---
There's one rule in this field that you only break once: **never run an unknown sample on your real machine.** Some people learn it by losing an evening cleaning up their machine after "just running it to see what it does". We learn it by reading this post.

For crackmes and CTFs the risk is close to zero, and running them on a normal machine is fine. But as soon as you touch real malware or a binary of unknown origin, you need a lab. Set it up once, use it forever.

## Why you need a separate virtual machine

There are three reasons, in order of importance. The first is isolation: malware running in a VM can't touch your real machine if you configure things correctly. The second is snapshots, which are the real game changer. You capture the "clean" state of the VM, run the sample, analyze as much as you like, then press one button to go back to the exact clean state in a few seconds, with no reinstalling Windows and no cleanup at all. The third is a stable environment: install all your tools once, then clone it into as many copies as you want.

## Choosing a hypervisor

The software that creates VMs is called a hypervisor. VMware Workstation (Windows/Linux) or Fusion (macOS) is stable, has good snapshots, and is the pick of most malware people. The personal edition is free now. VirtualBox is completely free, open source, and good enough for learning, and its snapshots are a bit less smooth than VMware's. Hyper-V comes with Windows Pro and works, but fewer RE tools support it out of the box.

Beginners can just go with VirtualBox or the free VMware. Don't agonize over this for too long.

## Network configuration, the easiest place to get it wrong

By default a VM connects straight to the internet through NAT. With malware, that's the moment it calls home to its command-and-control (C2) server, and it may even spread to other machines on your home network. There are three modes to remember.

Host-only (or an internal network) means the VM only talks to the host or to other VMs, with no internet. This is the default mode when analyzing malware. NAT lets the VM reach the internet, so only turn it on when you deliberately want to observe the sample's real network traffic and you accept the risk. The third option is a simulated internet: use a second VM running INetSim or FakeNet-NG to impersonate every network service (DNS, HTTP, SMTP...). The malware thinks it got out to the internet and shows its behavior, while the packets go nowhere. This is the standard setup for a serious lab.

The classic two-VM model is one Windows VM that runs the sample (the victim machine), and one Linux VM acting as the fake network gateway and packet capture. The two are connected through a host-only network, completely separated from your home network.

## Small but important settings

Take a "clean" snapshot right after installing your tools, before running any sample, and give it a clear name like `clean-base`. Turn off shared folders and the shared clipboard when analyzing real malware, since those are two escape routes that often get forgotten (turn them back on when you're only doing crackmes). Turn off USB auto-mount too.

Consider not installing VM Guest Additions or VMware Tools when analyzing sophisticated samples, since a lot of malware checks for their presence to know it's being watched (anti-VM, covered in [Lesson 15.5](https://github.com/Haind03/Technique-Reverse/tree/main/phan-15-anti-reverse)). Keep your tools on the host or on a read-only shared drive, and don't mix them with the folder that holds samples.

## Pre-built tools: FLARE-VM and REMnux

You don't have to install hundreds of tools by hand. Two pre-built setups do all of that for you. FLARE-VM (from Mandiant) is a PowerShell script you run on a clean Windows VM, and it downloads and installs a whole forest of RE and malware analysis tools: x64dbg, IDA Free, Ghidra, PE-bear, dnSpy, Detour, and many more. Remember to snapshot right after the install. REMnux is a prebuilt Linux distro for malware analysis, with enough tools for file, network, maldoc, and memory analysis. It usually plays the Linux VM in the two-VM model.

A short workflow for beginners: install Windows into a VM, run FLARE-VM, snapshot `clean-base`. Add a REMnux VM as the network gateway. Done, you have a decent lab.

## How serious you need to get

Don't build an overly complicated lab for something that doesn't need it. A quick scale:

| What you're doing | Lab level needed |
|---|---|
| Crackme, CTF, binaries you wrote yourself | Real machine is fine, or a normal VM |
| Unknown software of unclear origin | VM with snapshot, host-only network |
| Real malware | Isolated VM + simulated network + snapshot, strictly host-only |
| Sophisticated APT sample with anti-VM | Dedicated lab, consider a separate physical machine (bare-metal) |

## Key takeaways
Don't run unknown samples on your real machine, full stop. Take a "clean" snapshot before running anything, and revert in a few seconds when you're done. For malware, use a host-only or simulated network (INetSim/FakeNet) and turn off shared folders and clipboard.

FLARE-VM (Windows) plus REMnux (Linux) give you a full lab without installing by hand. Match the lab level to how dangerous the sample is.
