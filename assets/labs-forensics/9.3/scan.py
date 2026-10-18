#!/usr/bin/env python3
# Lab 9.3 - dung yara-python bien dich rule va quet thu muc mau.
# Chay: python3 -I scan.py
import os, sys, hashlib, yara

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "rules.yar")
SAMPLES = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "samples")

rules = yara.compile(filepath=RULES)
print("Bien dich rule tu:", os.path.basename(RULES))
print("=" * 64)
print(f"{'file':20} {'sha256(16)':18} matches")
print("-" * 64)
for fn in sorted(os.listdir(SAMPLES)):
    p = os.path.join(SAMPLES, fn)
    if not os.path.isfile(p):
        continue
    data = open(p, "rb").read()
    h = hashlib.sha256(data).hexdigest()[:16]
    names = [m.rule for m in rules.match(data=data)]
    print(f"{fn:20} {h:18} {names if names else 'clean'}")

print("=" * 64)
print("Chi tiet chuoi khop tren mau 'mã độc' (kieu yara -s):")
data = open(os.path.join(SAMPLES, "invoice_2026.exe"), "rb").read()
for m in rules.match(data=data):
    print(f"  [{m.rule}]")
    for s in m.strings:
        try:                              # yara-python >= 4.3
            ident = s.identifier
            offs = ", ".join(hex(i.offset) for i in s.instances)
        except AttributeError:            # API cu (tuple)
            ident, offs = s[1], hex(s[0])
        print(f"     {ident:8} @ {offs}")

print("=" * 64)
print("Bai hoc strong vs weak:")
print(" - invoice_2026.exe khop CA HAI rule (co marker manh + nhom API).")
print(" - it_report.txt (ghi chu IT lanh) khop rule YEU vi chi chua tu 'malware'")
print("   -> false positive. Rule MANH khong khop no (thieu magic MZ + marker).")
print(" - setup.exe co chuoi API yeu (VirtualAllocEx) nhung thieu marker manh")
print("   -> rule MANH khong khop -> tranh duoc false positive.")
