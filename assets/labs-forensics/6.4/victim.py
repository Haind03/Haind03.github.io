#!/usr/bin/env python3
# victim.py - lab 6.4: tien trinh giu credential + payload -enc trong RAM (tat ca gia, vo hai).
#
# Minh hoa vi sao secret nam trong RAM: mot chuong trinh thuong phai giu password/token
# o dang ro trong bo nho de dung, du tren dia chung co the da ma hoa. Ta se dump roi
# moi lai bang strings/grep (giong hashdump/lsadump tren anh Windows), va giai mot
# chuoi -enc (base64 UTF-16LE) giong PowerShell fileless.
import base64
import os
import time

# Credential gia - KHONG phai cua he thong that.
PASSWORD = "password=Pa$$w0rd_LAB64"
API_TOKEN = "api_token=tok_live_LAB64_deadbeefcafe0001"
# NTLM hash gia (32 hex) chi de minh hoa dinh dang hashdump.
NTLM_LINE = "ntlm=LAB64user:1001:aad3b435b51404eeaad3b435b51404ee:0123456789abcdef0123456789abcdef"

# Chuoi -enc kieu PowerShell: base64 cua UTF-16LE mot lenh VO HAI (khong chay).
PSENC_B64 = (
    "VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGwAYQBiADYANAAgAGYAaQBsAGUAbABlAHMA"
    "cwAgAGQAZQBtAG8AOgAgAHcAbwB1AGwAZAAgAEQAbwB3AG4AbABvAGEAZABTAHQAcgBpAG4A"
    "ZwAgAGgAdAB0AHAAOgAvAC8AMQA5ADgALgA1ADEALgAxADAAMAAuADcANwAvAGEALgBwAHMA"
    "MQAnAA=="
)
PSENC = "PSENC=" + PSENC_B64

# (tu kiem) chung minh day la UTF-16LE vo hai, khong thuc thi gi:
_decoded = base64.b64decode(PSENC_B64).decode("utf-16-le")

# Giu nhieu ban trong vung writable.
KEEP = [PASSWORD, API_TOKEN, NTLM_LINE, PSENC] * 24

print(os.getpid(), flush=True)
print("READY", flush=True)

deadline = time.time() + 120
while time.time() < deadline:
    time.sleep(0.2)
_ = KEEP[0][:1]
