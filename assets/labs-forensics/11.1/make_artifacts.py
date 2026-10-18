#!/usr/bin/env python3
# Lab 11.1 - dong mot mini challenge forensics tu chua:
#   capture.pcap chua mot phien HTTP tai ve secret.zip (co mat khau)
#   va mot truy van DNS TXT mang mat khau da base64 (kenh exfil kinh dien).
# Tai tao dung ky thuat demo trong bai 11.1. Khong dung du lieu that.
#
# Dung: python3 -I make_artifacts.py [thu_muc_dich]   (mac dinh ./chal)

import os
import sys
import base64
import subprocess

PASSWORD = "Z1pK3y_DNS_2026"
FLAG = "flag{dns_txt_carried_the_zip_key}"

def build_zip(outdir):
    flag_txt = os.path.join(outdir, "flag.txt")
    with open(flag_txt, "w", newline="\n") as f:
        f.write(FLAG + "\n")
    zip_path = os.path.join(outdir, "secret.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    # dung zip CLI de tao archive co mat khau (ZipCrypto), unzip -P mo duoc
    subprocess.run(["zip", "-j", "-P", PASSWORD, zip_path, flag_txt],
                   check=True, stdout=subprocess.DEVNULL)
    os.remove(flag_txt)  # chi de flag trong zip, buoc nguoi choi phai giai
    return open(zip_path, "rb").read()

def build_pcap(outdir, zip_bytes):
    from scapy.all import Ether, IP, TCP, UDP, DNS, DNSQR, DNSRR, Raw, wrpcap, conf
    conf.verb = 0
    cmac, smac = "02:00:00:00:00:01", "02:00:00:00:00:02"
    cip, sip = "192.168.56.101", "192.168.56.10"

    http_resp = (b"HTTP/1.1 200 OK\r\n"
                 b"Server: nginx\r\n"
                 b"Content-Type: application/zip\r\n"
                 b'Content-Disposition: attachment; filename="secret.zip"\r\n'
                 b"Content-Length: " + str(len(zip_bytes)).encode() + b"\r\n"
                 b"Connection: close\r\n\r\n" + zip_bytes)
    req = (b"GET /download/secret.zip HTTP/1.1\r\nHost: files.example.ctf\r\n"
           b"User-Agent: curl/8.0\r\nAccept: */*\r\n\r\n")

    def e(src, dst):
        return Ether(src=src, dst=dst)

    pkts = []
    cseq, sseq = 1000, 5000
    pkts += [e(cmac, smac)/IP(src=cip, dst=sip)/TCP(sport=44001, dport=80, flags="S", seq=cseq)]
    pkts += [e(smac, cmac)/IP(src=sip, dst=cip)/TCP(sport=80, dport=44001, flags="SA", seq=sseq, ack=cseq+1)]
    pkts += [e(cmac, smac)/IP(src=cip, dst=sip)/TCP(sport=44001, dport=80, flags="A", seq=cseq+1, ack=sseq+1)]
    cseq += 1
    pkts += [e(cmac, smac)/IP(src=cip, dst=sip)/TCP(sport=44001, dport=80, flags="PA", seq=cseq, ack=sseq+1)/Raw(load=req)]
    cseq += len(req)
    pkts += [e(smac, cmac)/IP(src=sip, dst=cip)/TCP(sport=80, dport=44001, flags="A", seq=sseq+1, ack=cseq)]
    pkts += [e(smac, cmac)/IP(src=sip, dst=cip)/TCP(sport=80, dport=44001, flags="PA", seq=sseq+1, ack=cseq)/Raw(load=http_resp)]
    sseq += 1 + len(http_resp)
    pkts += [e(cmac, smac)/IP(src=cip, dst=sip)/TCP(sport=44001, dport=80, flags="A", seq=cseq, ack=sseq)]
    pkts += [e(smac, cmac)/IP(src=sip, dst=cip)/TCP(sport=80, dport=44001, flags="FA", seq=sseq, ack=cseq)]
    pkts += [e(cmac, smac)/IP(src=cip, dst=sip)/TCP(sport=44001, dport=80, flags="FA", seq=cseq, ack=sseq+1)]

    label = base64.b64encode(("pass:" + PASSWORD).encode()).decode().rstrip("=")
    qname = label + ".files.example.ctf"
    pkts += [e(cmac, smac)/IP(src=cip, dst=sip)/UDP(sport=51000, dport=53)/DNS(id=1, rd=1, qd=DNSQR(qname=qname, qtype="TXT"))]
    pkts += [e(smac, cmac)/IP(src=sip, dst=cip)/UDP(sport=53, dport=51000)/DNS(
        id=1, qr=1, rd=1, ra=1, qd=DNSQR(qname=qname, qtype="TXT"),
        an=DNSRR(rrname=qname, type="TXT", ttl=60, rdata="zippw=" + PASSWORD))]

    pcap = os.path.join(outdir, "capture.pcap")
    wrpcap(pcap, pkts)
    return pcap, label

def main():
    outdir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "chal")
    os.makedirs(outdir, exist_ok=True)
    zb = build_zip(outdir)
    pcap, label = build_pcap(outdir, zb)
    print(f"[+] secret.zip ({len(zb)} bytes) nhung trong HTTP response")
    print(f"[+] DNS TXT mang mat khau da base64 (label: {label})")
    print(f"[+] Da tao challenge: {pcap}")
    print("[+] De bai: 'Nhan vien tai nham mot file. Lay lai noi dung bi mat.' Flag dang flag{...}")
    print("[+] Chay tiep:  bash solve.sh " + (sys.argv[1] if len(sys.argv) > 1 else "chal"))

if __name__ == "__main__":
    main()
