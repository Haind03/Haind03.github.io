#!/usr/bin/env python3
# Lab 7.3 - phat hien C2 beacon + DNS tunnel va giai ma du lieu tuon ra.
# Dung tshark de rut truong, python de tinh interval trung binh + entropy Shannon.
# Chay: python3 -I solve.py [lab73.pcap]
import os, sys, subprocess, math, base64, statistics, collections

HERE = os.path.dirname(os.path.abspath(__file__))
PCAP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "lab73.pcap")

def tshark(args):
    return subprocess.run(["tshark", "-r", PCAP] + args, capture_output=True, text=True).stdout

def shannon(s):
    if not s:
        return 0.0
    c = collections.Counter(s); n = len(s)
    return -sum((v/n) * math.log2(v/n) for v in c.values())

print("="*62)
print("[1] BEACON DETECTION  (TCP SYN toi port 443, theo dich)")
print("="*62)
out = tshark(["-Y", "tcp.flags.syn==1 && tcp.flags.ack==0 && tcp.dstport==443",
              "-T", "fields", "-e", "frame.time_epoch", "-e", "ip.dst"])
times, dst = [], None
for line in out.strip().splitlines():
    p = line.split("\t"); times.append(float(p[0])); dst = p[1]
times.sort()
diffs = [round(times[i+1]-times[i], 2) for i in range(len(times)-1)]
print(f"C2 candidate dst   : {dst}")
print(f"so ket noi (SYN)   : {len(times)}")
print(f"cac interval (s)   : {diffs}")
print(f"interval trung binh: {statistics.mean(diffs):.2f} s")
print(f"jitter (stdev)     : {statistics.pstdev(diffs):.2f} s")
cv = statistics.pstdev(diffs) / statistics.mean(diffs)
print(f"he so bien thien   : {cv:.3f}  -> {'BEACON (bien thien thap, nhip deu)' if cv < 0.2 else 'khong deu'}")

print()
print("="*62)
print("[2] DNS TUNNEL DETECTION  (theo domain cha)")
print("="*62)
out = tshark(["-Y", "dns.flags.response==0", "-T", "fields", "-e", "dns.qry.name", "-e", "dns.qry.type"])
byparent = collections.defaultdict(list)
for line in out.strip().splitlines():
    name = line.split("\t")[0]
    labs = name.split(".")
    parent = ".".join(labs[-3:]) if len(labs) >= 3 else name
    byparent[parent].append(labs[0])
print(f"{'domain cha':30} {'queries':>7} {'avg_len':>8} {'avg_entropy':>11}")
suspicious = None
for parent, left in sorted(byparent.items(), key=lambda kv: -len(kv[1])):
    avglen = statistics.mean(len(x) for x in left)
    avgent = statistics.mean(shannon(x) for x in left)
    flag = ""
    if len(left) >= 3 and avglen > 20 and avgent > 3.5:
        flag = " <== TUNNEL"; suspicious = parent
    print(f"{parent:30} {len(left):7} {avglen:8.1f} {avgent:11.2f}{flag}")

print()
print("="*62)
print(f"[3] DECODE TUNNEL  (domain cha = {suspicious})")
print("="*62)
out = tshark(["-Y", f'dns.flags.response==0 && dns.qry.name contains "{suspicious}"',
              "-T", "fields", "-e", "dns.qry.name"])
chunks = {}
for line in out.strip().splitlines():
    left = line.split("\t")[0].split(".")[0]
    seq, data = int(left[:2]), left[2:]
    chunks[seq] = data
b32 = "".join(chunks[k] for k in sorted(chunks)).upper()
decoded = base64.b32decode(b32 + "=" * ((-len(b32)) % 8))
print("base32 ghep lai  :", b32)
print("secret giai ma   :", decoded.decode(errors="replace"))

exp = open(os.path.join(HERE, "expected_secret.txt"), "rb").read()
print("khop ground truth:", decoded == exp)
sys.exit(0 if decoded == exp else 1)
