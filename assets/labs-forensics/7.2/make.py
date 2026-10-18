#!/usr/bin/env python3
# Lab 7.2 - tao pcap THAT nhieu phien (2 host, 3 ket noi TCP, 2 lan DNS) de dung
# tshark xuat bang kieu conn.log / dns.log (thay cho Zeek - khong cai duoc o day).
# Chay: python3 -I make.py
import os
from scapy.all import Ether, IP, TCP, UDP, DNS, DNSQR, DNSRR, Raw, wrpcap

HERE = os.path.dirname(os.path.abspath(__file__))
GWMAC = "02:00:00:00:00:fe"
CMAC = "02:00:00:00:00:01"
pkts = []
t = [1768100000.0]
def tick(step=0.05):
    t[0] += step
    return t[0]

def dns(cli, qname, ip, qid):
    q = (Ether(src=CMAC, dst=GWMAC)/IP(src=cli, dst="10.0.0.53")/UDP(sport=40000+qid, dport=53)/
         DNS(id=qid, rd=1, qd=DNSQR(qname=qname)))
    q.time = tick()
    a = (Ether(src=GWMAC, dst=CMAC)/IP(src="10.0.0.53", dst=cli)/UDP(sport=53, dport=40000+qid)/
         DNS(id=qid, qr=1, rd=1, ra=1, qd=DNSQR(qname=qname),
             an=DNSRR(rrname=qname, ttl=300, rdata=ip)))
    a.time = tick()
    pkts.extend([q, a])

def http(cli, srv, cport, host, path, body, ctype="application/octet-stream"):
    req = b"GET " + path + b" HTTP/1.1\r\nHost: " + host + b"\r\nUser-Agent: Mozilla/5.0\r\nAccept: */*\r\n\r\n"
    resp = (b"HTTP/1.1 200 OK\r\nServer: lab/1.0\r\nContent-Type: " + ctype.encode() +
            b"\r\nContent-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n") + body
    cs, ss = 1000, 7000
    def C(f, p=b"", seq=0, ack=0):
        pk = Ether(src=CMAC, dst=GWMAC)/IP(src=cli, dst=srv)/TCP(sport=cport, dport=80, flags=f, seq=seq, ack=ack)
        if p: pk = pk/Raw(p)
        pk.time = tick(); return pk
    def S(f, p=b"", seq=0, ack=0):
        pk = Ether(src=GWMAC, dst=CMAC)/IP(src=srv, dst=cli)/TCP(sport=80, dport=cport, flags=f, seq=seq, ack=ack)
        if p: pk = pk/Raw(p)
        pk.time = tick(); return pk
    pkts.append(C("S", seq=cs)); cs += 1
    pkts.append(S("SA", seq=ss, ack=cs)); ss += 1
    pkts.append(C("A", seq=cs, ack=ss))
    pkts.append(C("PA", req, seq=cs, ack=ss)); cs += len(req)
    pkts.append(S("A", seq=ss, ack=cs))
    off, mss = 0, 1400
    while off < len(resp):
        ch = resp[off:off+mss]
        pkts.append(S("PA", ch, seq=ss, ack=cs)); ss += len(ch); off += mss
        pkts.append(C("A", seq=cs, ack=ss))
    pkts.append(S("FA", seq=ss, ack=cs)); ss += 1
    pkts.append(C("FA", seq=cs, ack=ss)); cs += 1
    pkts.append(S("A", seq=ss, ack=cs))

# Kich ban: workstation 10.0.0.50 phan giai 2 ten, tai 1 ZIP (CDN) va 1 EXE (host la).
dns("10.0.0.50", "cdn.lab.test", "10.0.0.80", 0x01)
dns("10.0.0.50", "files.evil.test", "10.0.0.66", 0x02)

zipbody = b"PK\x03\x04\x14\x00\x00\x00\x08\x00labzip-content-harmless" + b"\x00"*40 + b"PK\x05\x06" + b"\x00"*18
http(b"10.0.0.50", b"10.0.0.80", 49201, b"cdn.lab.test", b"/assets/pack.zip", zipbody, "application/zip")

exebody = b"MZ\x90\x00dropper-sample-harmless-LAB7.2" + b"\x00"*80 + b"PE\x00\x00" + bytes(range(256))
http(b"10.0.0.50", b"10.0.0.66", 49202, b"files.evil.test", b"/get/payload.exe", exebody, "application/octet-stream")

# Mot host khac ket noi THANG bang IP (khong qua DNS) -> co trong conn.log, vang trong dns.log.
http(b"10.0.0.51", b"10.0.0.99", 49050, b"10.0.0.99", b"/beacon", b"ok", "text/plain")

wrpcap(os.path.join(HERE, "lab72.pcap"), pkts)
with open(os.path.join(HERE, "expected_payload.exe"), "wb") as f:
    f.write(exebody)
print("Da tao lab72.pcap:", len(pkts), "goi; 3 ket noi TCP, 2 lan DNS")
