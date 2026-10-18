#!/usr/bin/env python3
# holder.py - chuong trinh "nan nhan" cho lab 6.1
# Giu mot secret va chuoi marker dac trung trong RAM (heap), roi cho.
# Khong lam gi doc hai: chi giu chuoi trong bo nho de ta dump lai.
import os
import sys
import time

# Secret gia, vo hai. Marker de de grep lai trong dump.
SECRET = "SECRET{proc_memory_forensics_lab_6_1}"
MARKER = "FORENSICS_MARKER_" + SECRET + "_ENDMARKER"

# Giu nhieu ban de chac chan secret nam trong vung writable/anon.
BLOB = (MARKER + "\n") * 64


def main():
    # In PID va bao da san sang de dumper biet luc nao chup.
    print(os.getpid(), flush=True)
    print("READY", flush=True)
    # Giu tham chieu song de secret khong bi GC.
    keep = BLOB
    # Cho bi dumper ket thuc (hoac tu thoat sau timeout an toan).
    deadline = time.time() + 120
    while time.time() < deadline:
        time.sleep(0.2)
    # Dung keep de trinh bien dich khong toi uu mat bien.
    sys.stdout.write(keep[:1])


if __name__ == "__main__":
    main()
