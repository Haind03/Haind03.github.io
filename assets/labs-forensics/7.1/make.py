#!/usr/bin/env python3
# Lab 7.1 - tao pcap THAT bang scapy: mot phien HTTP tai file co magic MZ.
# Bat buoc: scapy. Khong can mang (tu tao goi va ghi thang ra pcap).
# Chay:  python3 -I make.py
import os
from scapy.all import Ether, IP, TCP, UDP, DNS, DNSQR, DNSRR, Raw, wrpcap

HERE = os.path.dirname(os.path.abspath(__file__))

# --- File se duoc "tai" trong phien HTTP: PE gia, vo hai, co magic MZ + chuoi PE ---
body = bytearray()
body += b"MZ\x90\x00\x03\x00"
body += b"Harmless lab sample, not a real executable. Marker: LAB-FILE-7.1\n"
body += b"\x00" * 64
body += b"PE\x00\x00"
body += bytes(range(256)) * 2
body = bytes(body)

filename = "update.exe"
resp = (
    b"HTTP/1.1 200 OK\r\n"
    b"Server: lab-httpd/1.0\r\n"
    b"Content-Type: application/octet-stream\r\n"
    b'Content-Disposition: attachment; filename="%s"\r\n' % filename.encode()
    + b"Content-Length: %d\r\n" % len(body)
    + b"Connection: close\r\n\r\n"
) + body

req = (
    b"GET /download/update.exe HTTP/1.1\r\n"
    b"Host: files.lab.test\r\n"
    b"User-Agent: curl/7.81.0\r\n"
    b"Accept: */*\r\n\r\n"
)

cli, srv, dns_srv = "10.0.0.50", "10.0.0.80", "10.0.0.53"
cport, sport = 49152, 80
cmac, smac = "02:00:00:00:00:01", "02:00:00:00:00:02"
pkts = []

# DNS phan giai ten truoc khi ket noi
pkts.append(Ether(src=cmac, dst=smac)/IP(src=cli, dst=dns_srv)/UDP(sport=53000, dport=53)/
            DNS(id=0x1234, rd=1, qd=DNSQR(qname="files.lab.test", qtype="A")))
pkts.append(Ether(src=smac, dst=cmac)/IP(src=dns_srv, dst=cli)/UDP(sport=53, dport=53000)/
            DNS(id=0x1234, qr=1, aa=1, rd=1, ra=1, qd=DNSQR(qname="files.lab.test", qtype="A"),
                an=DNSRR(rrname="files.lab.test", type="A", ttl=300, rdata=srv)))

cseq, sseq = 1000, 5000
def C(flags, payload=b"", seq=0, ack=0):
    p = Ether(src=cmac, dst=smac)/IP(src=cli, dst=srv)/TCP(sport=cport, dport=sport, flags=flags, seq=seq, ack=ack)
    return p/Raw(payload) if payload else p
def S(flags, payload=b"", seq=0, ack=0):
    p = Ether(src=smac, dst=cmac)/IP(src=srv, dst=cli)/TCP(sport=sport, dport=cport, flags=flags, seq=seq, ack=ack)
    return p/Raw(payload) if payload else p

# 3-way handshake
pkts.append(C("S", seq=cseq));            cseq += 1
pkts.append(S("SA", seq=sseq, ack=cseq)); sseq += 1
pkts.append(C("A", seq=cseq, ack=sseq))
# request
pkts.append(C("PA", req, seq=cseq, ack=sseq)); cseq += len(req)
pkts.append(S("A", seq=sseq, ack=cseq))
# response, chia thanh cac segment ~MSS
mss = 1400
off = 0
while off < len(resp):
    chunk = resp[off:off+mss]
    pkts.append(S("PA", chunk, seq=sseq, ack=cseq)); sseq += len(chunk)
    pkts.append(C("A", seq=cseq, ack=sseq))
    off += mss
# teardown
pkts.append(S("FA", seq=sseq, ack=cseq)); sseq += 1
pkts.append(C("FA", seq=cseq, ack=sseq)); cseq += 1
pkts.append(S("A", seq=sseq, ack=cseq))

base = 1768000000.0
for i, p in enumerate(pkts):
    p.time = base + i * 0.01

wrpcap(os.path.join(HERE, "lab71.pcap"), pkts)
with open(os.path.join(HERE, "expected_update.exe"), "wb") as f:
    f.write(body)
print("Da tao lab71.pcap:", len(pkts), "goi; file goc", len(body), "bytes (expected_update.exe)")
