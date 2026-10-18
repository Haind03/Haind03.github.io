#!/usr/bin/env python3
# capture.py - chup bo nho tien trinh (process memory dump) cho lab 6.1
#
# Cach lam (process memory forensics tai lap duoc tren Linux):
#   1. Phong holder.py nhu tien trinh con  -> no la descendant cua ta.
#   2. Cho no bao READY (da nap secret vao RAM).
#   3. Doc /proc/<pid>/maps, duyet tung vung, seek + read /proc/<pid>/mem,
#      ghi cac vung writable/anon/heap/stack ra mot file dump raw.
#   4. Ket thuc tien trinh con.
#
# Vi sao khong dung gcore o day:
#   gcore goi gdb -> ptrace ATTACH. Voi kernel.yama.ptrace_scope=1, mot tien trinh
#   chi ptrace duoc con chau cua no; gcon chay nhu tien trinh rieng nen bi tu choi.
#   Doc /proc/<pid>/mem tu CHINH tien trinh cha (ancestor) thi duoc phep. Day la
#   cach on dinh, khong can root. Neu ban la root hoac dat
#   kernel.yama.ptrace_scope=0 thi `gcore -o out <pid>` cung chup duoc tuong tu.
#
# Dump nang -> ghi ra thu muc tam (DUMPDIR), KHONG de trong labs/.
import os
import sys
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DUMPDIR = os.environ.get("DUMPDIR", "/tmp/mem6_1")
os.makedirs(DUMPDIR, exist_ok=True)
DUMP = os.path.join(DUMPDIR, "holder.dump")

# Chi dump vung <= 64MB/vung va tong <= 256MB cho an toan dung luong.
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
                # Uu tien vung writable/anon/heap/stack (noi secret runtime hay nam).
                is_anon = len(parts) < 6
                path = parts[5] if len(parts) >= 6 else ""
                interesting = ("w" in perms) or is_anon or path in ("[heap]", "[stack]")
                if not interesting:
                    continue
                lo_s, hi_s = addr.split("-")
                lo, hi = int(lo_s, 16), int(hi_s, 16)
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
    holder = os.path.join(HERE, "holder.py")
    child = subprocess.Popen(
        [sys.executable, "-I", holder],
        stdout=subprocess.PIPE, text=True,
    )
    pid_line = child.stdout.readline().strip()
    ready = child.stdout.readline().strip()
    pid = int(pid_line)
    print(f"[*] holder PID = {pid} ({ready})")
    time.sleep(0.3)
    regions, total = dump_process(pid, DUMP)
    child.terminate()
    try:
        child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        child.kill()
    mb = total / (1024 * 1024)
    print(f"[*] da chup {regions} vung, {total} byte (~{mb:.1f} MB)")
    print(f"[*] dump: {DUMP}")


if __name__ == "__main__":
    main()
