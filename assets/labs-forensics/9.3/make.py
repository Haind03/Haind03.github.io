#!/usr/bin/env python3
# Lab 9.3 - tao thu muc mau cho YARA: 1 file "mã độc" gia (vo hai) co marker + chuoi cau hinh,
# vai file sach, va mot file lanh CO chua tu "malware" de minh hoa false positive cua rule yeu.
# Chay: python3 -I make.py
import os
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "samples")
os.makedirs(D, exist_ok=True)

# 1) Mau "mã độc" gia (KHONG phai ma doc that): PE gia + marker + cau hinh C2 + API injection
mal = bytearray(b"MZ\x90\x00")
mal += b"\x00" * 56
mal += b"PE\x00\x00"
mal += b"this program contains the word malware for the lab\n"
mal += b"C2=http://evil-tunnel.test/gate.php\n"
mal += b"MUTEX=Global\\LAB_BADGER_7f3a\n"
mal += b"CreateRemoteThread\x00VirtualAllocEx\x00WriteProcessMemory\x00"
mal += b"\x00" * 200
with open(os.path.join(D, "invoice_2026.exe"), "wb") as f:
    f.write(mal)

# 2) File sach
with open(os.path.join(D, "readme.txt"), "wb") as f:
    f.write(b"This is a normal readme. Nothing to see. Uses CreateFile and ReadFile.\n")
with open(os.path.join(D, "photo.jpg"), "wb") as f:
    f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 300 + b"\xff\xd9")

# 3) PE sach chia SE mot chuoi API yeu (VirtualAllocEx) nhung KHONG co marker manh
clean_pe = bytearray(b"MZ\x90\x00" + b"\x00" * 56 + b"PE\x00\x00")
clean_pe += b"legit installer. imports VirtualAllocEx only.\n" + b"\x00" * 100
with open(os.path.join(D, "setup.exe"), "wb") as f:
    f.write(clean_pe)

# 4) File lanh CO tu "malware" (bao cao IT) -> se khien rule YEU false positive
with open(os.path.join(D, "it_report.txt"), "wb") as f:
    f.write(b"Weekly IT note: our malware scanner found nothing unusual this week.\n")

print("Da tao samples/:", ", ".join(sorted(os.listdir(D))))
