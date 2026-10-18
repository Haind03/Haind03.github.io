#!/usr/bin/env python3
# victim.py - tien trinh "nhiem" gia lap cho lab 6.2 (vo hai).
# Giu mot cau hinh C2 (IOC) trong RAM va mo mot ket noi THAT toi stub loopback,
# de ta vua tim duoc chuoi C2 trong dump, vua thay ket noi song trong bang socket.
#
# IP trong cau hinh dung dai TEST-NET (RFC 5737, 198.51.100.0/24, 203.0.113.0/24):
# chi de minh hoa IOC, khong tro toi may that. Ket noi THAT la 127.0.0.1 (stub noi bo).
import socket
import sys
import time

port = int(sys.argv[1])

# Cau hinh C2 nhung trong bo nho - day la IOC ta se grep lai tu dump.
C2_CONFIG = (
    "C2CONFIG|campaign=LAB62|"
    "c2_host=198.51.100.77|c2_port=4444|"
    "beacon_url=http://198.51.100.77/beacon|"
    "fallback=203.0.113.9:8443|"
    "key=lab62-not-a-real-secret"
)
# Giu nhieu ban cho chac vung writable.
KEEP = [C2_CONFIG] * 32

# Ket noi that toi stub loopback de co mot entry ESTABLISHED.
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", port))

print(socket.gethostname() if False else "", end="")  # no-op giu import gon
print(KEEP[0][:0], end="")                             # giu tham chieu
print("victim connected", flush=True)
print("READY", flush=True)

deadline = time.time() + 120
while time.time() < deadline:
    time.sleep(0.2)
s.close()
