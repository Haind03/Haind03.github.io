#!/usr/bin/env python3
# capture.py - lab 6.3: chup maps + carve rieng cac vung RWX bat thuong (malfind analog).
#
# Luong:
#   1. Phong victim.py (co vung anonymous RWX chua "shellcode" gia).
#   2. Luu /proc/<pid>/maps.
#   3. Quet maps tim vung co quyen 'rwx' + private + khong backing file,
#      carve tung vung do tu /proc/<pid>/mem ra file rieng (nho, vai KB).
#   4. Ket thuc victim.
import glob
import os
import sys
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DUMPDIR = os.environ.get("DUMPDIR", "/tmp/mem6_3")
os.makedirs(DUMPDIR, exist_ok=True)
MAPS = os.path.join(DUMPDIR, "victim.maps")

# Xoa carve cu de lan chay moi sach, tranh lan file RWX cua lan truoc.
for old in glob.glob(os.path.join(DUMPDIR, "rwx_*.bin")):
    os.remove(old)


def main():
    victim = subprocess.Popen([sys.executable, "-I", os.path.join(HERE, "victim.py")],
                              stdout=subprocess.PIPE, text=True)
    pid = victim.pid
    victim.stdout.readline()           # pid
    info = victim.stdout.readline().strip()  # RWX region at ...
    victim.stdout.readline()           # READY
    print(f"[*] victim PID = {pid} ({info})")
    time.sleep(0.3)

    with open(f"/proc/{pid}/maps") as m:
        maps = m.read()
    with open(MAPS, "w") as out:
        out.write(maps)

    carved = []
    with open(f"/proc/{pid}/mem", "rb", 0) as mem:
        for line in maps.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            addr, perms = parts[0], parts[1]
            # malfind analog: vung vua Write vua Execute, private ('p'), khong backing file.
            is_anon = len(parts) < 6
            if perms[:3] == "rwx" and perms[3:4] == "p" and is_anon:
                lo, hi = (int(x, 16) for x in addr.split("-"))
                size = hi - lo
                if size > 16 * 1024 * 1024:
                    continue
                try:
                    mem.seek(lo)
                    data = mem.read(size)
                except OSError:
                    continue
                out_path = os.path.join(DUMPDIR, f"rwx_{lo:#x}.bin")
                with open(out_path, "wb") as f:
                    f.write(data)
                carved.append((addr, perms, out_path, size))

    print(f"[*] maps -> {MAPS}")
    if carved:
        for addr, perms, p, size in carved:
            print(f"[*] vung RWX: {addr} {perms} ({size} byte) -> {p}")
    else:
        print("[!] khong thay vung RWX nao (kernel co the chan PROT_EXEC tren anon)")

    victim.terminate()
    try:
        victim.wait(timeout=5)
    except subprocess.TimeoutExpired:
        victim.kill()


if __name__ == "__main__":
    main()
