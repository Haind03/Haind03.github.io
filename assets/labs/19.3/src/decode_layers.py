#!/usr/bin/env python3
"""
Decodes two HARMLESS loader samples for Lesson 19.3.
Golden rule: only DECODE and PRINT, never EXECUTE.
Run: python3 decode_layers.py
"""
import base64
import gzip

# Stage 1: PowerShell -EncodedCommand using UTF-16LE
stage1 = ("VwByAGkAdABlAC0ASABvAHMAdAAgACcASABlAGwAbABvACAAZgByAG8AbQAg"
          "AGEAIABiAGUAbgBpAGcAbgAgAGQAZQBjAG8AZABlAGQAIABwAGEAeQBsAG8A"
          "YQBkACcA")

# Stage 2: base64 wrapped around gzip
stage2 = "H4sIACi+xGoC/wsvyixJ1fXILy5RUA8uSUxPVTBSKEpNTM5ITdFRKC7JzMlRSErNy0zPUwcAecI0BioAAAA="


def decode_ps_encodedcommand(b64: str) -> str:
    # PowerShell -enc: base64 then decode UTF-16LE (NOT UTF-8)
    return base64.b64decode(b64).decode("utf-16-le")


def decode_b64_gzip(b64: str) -> str:
    return gzip.decompress(base64.b64decode(b64)).decode()


if __name__ == "__main__":
    print("[Stage 1: base64 UTF-16LE]")
    print("  ->", decode_ps_encodedcommand(stage1))
    print()
    print("[Stage 2: base64 + gzip]")
    print("  ->", decode_b64_gzip(stage2))
    print()
    print("Both are harmless commands that only print text.")
