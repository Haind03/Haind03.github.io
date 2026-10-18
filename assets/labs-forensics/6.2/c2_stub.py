#!/usr/bin/env python3
# c2_stub.py - may chu gia lap "C2" chay tren LOOPBACK (127.0.0.1), hoan toan vo hai.
# Chi mo mot cong local, chap nhan mot ket noi va giu no de ta co mot ket noi
# ESTABLISHED that ma quan sat (giong buoc netscan tren anh RAM Windows).
import socket
import sys

srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("127.0.0.1", 0))  # cong ephemeral
srv.listen(1)
port = srv.getsockname()[1]
print(port, flush=True)       # bao cong cho capture.py
print("READY", flush=True)
conn, addr = srv.accept()
# Giu ket noi mo; khong gui/nhan gi doc hai.
try:
    conn.recv(16)
except Exception:
    pass
import time
time.sleep(120)
