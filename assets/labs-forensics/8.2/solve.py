#!/usr/bin/env python3
# Lab 8.2 - script giai: parse header email bang module email, lan chuoi Received
# tu duoi len ra IP gui goc, va chi ra cac diem venh (dau hieu gia mao).
#
# Dung: python3 -I solve.py <file.eml>   (vi du: solve.py mail/phish.eml)

import sys
import re
import email
from email import policy

IP_RE = re.compile(r"\[(\d{1,3}(?:\.\d{1,3}){3})\]")
ADDR_RE = re.compile(r"[\w.+-]+@([\w.-]+)")

def domain_of(value):
    if not value:
        return None
    m = ADDR_RE.search(value)
    return m.group(1).lower() if m else None

def h(t): print("\n==== " + t + " ====")

def analyze(path):
    with open(path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    print("FILE:", path)

    h("1. Cac header chinh")
    for k in ("From", "Return-Path", "Reply-To", "To", "Subject", "Date", "Message-ID"):
        print(f"  {k}: {msg.get(k, '(khong co)')}")

    h("2. Chuoi Received doc tu DUOI len (chang dau = gan nguoi gui nhat)")
    recv = msg.get_all("Received", [])
    # email tra ve tren-cung truoc; chang cuoi la phan tu cuoi danh sach
    origin_ip = None
    for i, r in enumerate(reversed(recv), 1):
        one = " ".join(str(r).split())
        ips = IP_RE.findall(str(r))
        tag = ""
        if i == 1 and ips:
            origin_ip = ips[-1]
            tag = "   <== CHANG DAU, IP gui goc"
        print(f"  [{i}] {one}{tag}")
    if origin_ip:
        print(f"\n  -> IP gui goc: {origin_ip}")

    h("3. Authentication-Results (SPF / DKIM / DMARC)")
    ar = msg.get("Authentication-Results")
    if ar:
        for part in re.split(r";\s*", " ".join(str(ar).split())):
            part = part.strip()
            if part.startswith(("spf=", "dkim=", "dmarc=")):
                verdict = part.split("=", 1)[1].split()[0]
                flag = "  <== FAIL" if verdict in ("fail", "softfail") else ""
                flag = "  <== khong co" if verdict == "none" else flag
                print(f"  {part}{flag}")
    else:
        print("  (khong co Authentication-Results; tu tra SPF bang dig/whois)")

    h("4. Soi diem venh giua cac truong dia chi")
    d_from = domain_of(msg.get("From"))
    d_rp = domain_of(msg.get("Return-Path"))
    d_reply = domain_of(msg.get("Reply-To"))
    d_mid = domain_of(msg.get("Message-ID"))
    print(f"  From domain        : {d_from}")
    print(f"  Return-Path domain : {d_rp}   {'(VENH voi From)' if d_rp and d_rp != d_from else ''}")
    print(f"  Reply-To domain    : {d_reply}   {'(VENH voi From)' if d_reply and d_reply != d_from else ''}")
    print(f"  Message-ID domain  : {d_mid}   {'(khong phai ha tang cua From)' if d_mid and d_from not in (d_mid or '') else ''}")

    h("5. Link trong body (KHONG bam, chi trich de doi chieu)")
    body = ""
    if msg.is_multipart():
        for p in msg.walk():
            if p.get_content_type() in ("text/html", "text/plain"):
                body += p.get_content()
    else:
        body = msg.get_content()
    hrefs = re.findall(r'href="([^"]+)"', body)
    for u in hrefs:
        ld = domain_of("x@" + re.sub(r"^https?://", "", u).split("/")[0]) or re.sub(r"^https?://", "", u).split("/")[0]
        flag = "  <== domain la" if d_from and d_from not in u else ""
        print(f"  {u}{flag}")
    if not hrefs:
        print("  (khong co link href)")

    # danh gia tong
    spf_fail = ar and "spf=fail" in " ".join(str(ar).split())
    mism = (d_rp and d_rp != d_from) or (d_reply and d_reply != d_from)
    h("KET LUAN")
    if spf_fail or mism:
        print(f"  Email NGHI GIA MAO. Khai From={d_from} nhung:")
        print(f"    - IP gui goc {origin_ip} (chang Received duoi cung)")
        if spf_fail:
            print(f"    - SPF/DMARC fail trong Authentication-Results")
        if d_rp and d_rp != d_from:
            print(f"    - Return-Path ve {d_rp} (khac From)")
        if d_reply and d_reply != d_from:
            print(f"    - Reply-To ve {d_reply} (khac From)")
        if d_mid and d_from not in (d_mid or ""):
            print(f"    - Message-ID sinh tu {d_mid} (khong phai ha tang cua From)")
    else:
        print(f"  Email NHIEU KHA NANG THAT: From={d_from}, SPF/DKIM/DMARC pass,")
        print(f"  Return-Path/Reply-To cung domain, Message-ID tu ha tang hop le.")

def main():
    if len(sys.argv) < 2:
        print("Dung: python3 -I solve.py <file.eml>"); return 1
    for p in sys.argv[1:]:
        analyze(p)
        print("\n" + "-" * 70)
    return 0

if __name__ == "__main__":
    sys.exit(main())
