#!/usr/bin/env python3
# capture.py - lab 6.4: chup bo nho tien trinh giu credential/payload (parent /proc/mem).
import os
import sys
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DUMPDIR = os.environ.get("DUMPDIR", "/tmp/mem6_4")
os.makedirs(DUMPDIR, exist_ok=True)
DUMP = os.path.join(DUMPDIR, "victim.dump")

MAX_REGION = 64 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024


def dump_process(pid, out_path):
    total = regions = 0
    with open(f"/proc/{pid}/maps") as maps, open(out_path, "wb") as out:
        with open(f"/proc/{pid}/mem", "rb", 0) as mem:
            for line in maps:
                parts = line.split()
                if len(parts) < 2 or "r" not in parts[1]:
                    continue
                perms = parts[1]
                is_anon = len(parts) < 6
                path = parts[5] if len(parts) >= 6 else ""
                if not (("w" in perms) or is_anon or path in ("[heap]", "[stack]")):
                    continue
                lo, hi = (int(x, 16) for x in parts[0].split("-"))
                size = hi - lo
                if size <= 0 or size > MAX_REGION:
                    continue
                if total + size > MAX_TOTAL:
                    break
                try:
                    mem.seek(lo)
                    data = mem.read(size)
                except OSError:
                    continue
                out.write(data)
                total += len(data)
                regions += 1
    return regions, total


def main():
    victim = subprocess.Popen([sys.executable, "-I", os.path.join(HERE, "victim.py")],
                              stdout=subprocess.PIPE, text=True)
    pid = victim.pid
    victim.stdout.readline()  # pid
    victim.stdout.readline()  # READY
    print(f"[*] victim PID = {pid}")
    time.sleep(0.3)
    regions, total = dump_process(pid, DUMP)
    print(f"[*] da chup {regions} vung, {total} byte (~{total/1048576:.1f} MB) -> {DUMP}")
    victim.terminate()
    try:
        victim.wait(timeout=5)
    except subprocess.TimeoutExpired:
        victim.kill()


if __name__ == "__main__":
    main()
