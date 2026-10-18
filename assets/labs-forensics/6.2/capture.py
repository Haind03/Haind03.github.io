#!/usr/bin/env python3
# capture.py - lab 6.2: chup bo nho tien trinh "victim" + chup bang ket noi mang song.
#
# Day la ban local, chay that, cua y tuong trong Bai 6.2:
#   - netscan: lay ket noi mang con song luc chup  -> o day doc tu `ss -tnp` (live)
#   - tim IOC C2 nhung trong RAM                    -> dump victim roi grep
#   - dlllist: module nap vao tien trinh            -> doc /proc/<pid>/maps (cac .so)
#
# Luong:
#   1. Phong c2_stub.py (loopback), lay cong.
#   2. Phong victim.py <cong> -> no ket noi toi stub, giu C2 config trong RAM.
#   3. Chup bang socket (`ss -tnp`) cua victim: ket noi ESTABLISHED that.
#   4. Dump bo nho victim + luu /proc/<pid>/maps.
#   5. Ket thuc ca hai tien trinh con.
import os
import sys
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DUMPDIR = os.environ.get("DUMPDIR", "/tmp/mem6_2")
os.makedirs(DUMPDIR, exist_ok=True)
DUMP = os.path.join(DUMPDIR, "victim.dump")
MAPS = os.path.join(DUMPDIR, "victim.maps")
CONNS = os.path.join(DUMPDIR, "connections.txt")

MAX_REGION = 64 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024


def dump_process(pid, out_path):
    total = 0
    regions = 0
    with open(f"/proc/{pid}/maps") as maps, open(out_path, "wb") as out:
        with open(f"/proc/{pid}/mem", "rb", 0) as mem:
            for line in maps:
                parts = line.split()
                if len(parts) < 2:
                    continue
                addr, perms = parts[0], parts[1]
                if "r" not in perms:
                    continue
                is_anon = len(parts) < 6
                path = parts[5] if len(parts) >= 6 else ""
                if not (("w" in perms) or is_anon or path in ("[heap]", "[stack]")):
                    continue
                lo, hi = (int(x, 16) for x in addr.split("-"))
                size = hi - lo
                if size <= 0 or size > MAX_REGION or total + size > MAX_TOTAL:
                    if total + size > MAX_TOTAL:
                        break
                    continue
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
    stub = subprocess.Popen([sys.executable, "-I", os.path.join(HERE, "c2_stub.py")],
                            stdout=subprocess.PIPE, text=True)
    port = int(stub.stdout.readline().strip())
    stub.stdout.readline()  # READY
    print(f"[*] stub C2 (loopback) tren cong {port}")

    victim = subprocess.Popen([sys.executable, "-I", os.path.join(HERE, "victim.py"), str(port)],
                              stdout=subprocess.PIPE, text=True)
    vpid = victim.pid
    victim.stdout.readline()  # victim connected
    victim.stdout.readline()  # READY
    print(f"[*] victim PID = {vpid} da ket noi toi 127.0.0.1:{port}")
    time.sleep(0.3)

    # 3. Chup bang ket noi song (netscan analog). Loc theo PID victim.
    try:
        ss = subprocess.run(["ss", "-tnp"], capture_output=True, text=True)
        lines = [ss.stdout.splitlines()[0]] if ss.stdout else []
        for ln in ss.stdout.splitlines()[1:]:
            if f"pid={vpid}," in ln or f":{port} " in ln or f":{port}\t" in ln:
                lines.append(ln)
        with open(CONNS, "w") as f:
            f.write("\n".join(lines) + "\n")
        print(f"[*] bang ket noi -> {CONNS}")
    except FileNotFoundError:
        with open(CONNS, "w") as f:
            f.write("(khong co lenh ss)\n")

    # 4. Luu maps (dlllist analog) + dump bo nho
    with open(f"/proc/{vpid}/maps") as m, open(MAPS, "w") as out:
        out.write(m.read())
    regions, total = dump_process(vpid, DUMP)
    print(f"[*] da chup {regions} vung, {total} byte (~{total/1048576:.1f} MB) -> {DUMP}")
    print(f"[*] maps -> {MAPS}")

    victim.terminate(); stub.terminate()
    for p in (victim, stub):
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()


if __name__ == "__main__":
    main()
