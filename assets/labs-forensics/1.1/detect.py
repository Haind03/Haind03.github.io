#!/usr/bin/env python3
# Lab 1.1 - solver: nhan dien dinh dang that tu magic byte (header, va footer khi can).
# Chay: python3 -I detect.py <file...>
import sys

MAGICS = [
    (b"\x89PNG\r\n\x1a\n", "PNG image"),
    (b"\xff\xd8\xff",      "JPEG image"),
    (b"%PDF-",            "PDF document"),
    (b"PK\x03\x04",        "ZIP container (co the la docx/xlsx/apk/jar)"),
    (b"PK\x05\x06",        "ZIP container rong"),
    (b"\x7fELF",           "ELF executable"),
    (b"MZ",                "PE/DOS executable (Windows)"),
    (b"GIF87a",            "GIF image"),
    (b"GIF89a",            "GIF image"),
    (b"\x1f\x8b",          "GZIP"),
    (b"Rar!\x1a\x07",      "RAR archive"),
    (b"BM",                "BMP image"),
]

def detect(path):
    with open(path, "rb") as f:
        head = f.read(16)
    for sig, name in MAGICS:
        if head.startswith(sig):
            return name, head[:len(sig)].hex(" ")
    return "KHONG RO (khong khop bang magic)", head[:8].hex(" ")

for p in sys.argv[1:]:
    name, ev = detect(p)
    ext = p.rsplit(".", 1)[-1] if "." in p else "(khong co)"
    noi_doi = "" if name.split()[0].lower().startswith(ext.lower()[:3]) else "  <== DUOI NOI DOI"
    print(f"{p:16s} duoi=.{ext:5s} magic={ev:24s} -> {name}{noi_doi}")
