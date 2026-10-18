#!/usr/bin/env python3
# Lab 3.2 - shim chay binwalk 2.x tren may co capstone moi (5.x/6.x) da doi ten CS_ARCH_ARM64.
# Moi truong binh thuong chi can chay thang: binwalk carve.img
# O may nay binwalk 2.x import module disasm bi loi, nen ta va lai hang so truoc khi import.
# Chay: /usr/bin/python3 binwalk_shim.py <args cua binwalk...>
import capstone
if not hasattr(capstone, "CS_ARCH_ARM64"):
    capstone.CS_ARCH_ARM64 = getattr(capstone, "CS_ARCH_AARCH64", 0)
for m in ("CS_MODE_ARM", "CS_MODE_THUMB"):
    if not hasattr(capstone, m):
        setattr(capstone, m, 0)
from binwalk.__main__ import main
main()
