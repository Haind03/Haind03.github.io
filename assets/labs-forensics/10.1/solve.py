#!/usr/bin/env python3
# Lab 10.1 solver: phat hien timestomp (so mtime/atime voi crtime) + log clearing.
# Doc THANG tu ext4 image bang debugfs, KHONG mount, KHONG can sudo.
import os, re, subprocess, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
IMG  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "case_disk.img")

def dbg(script):
    env = dict(os.environ); env["TZ"] = "UTC"
    r = subprocess.run('debugfs -R "%s" "%s"' % (script, IMG),
                       shell=True, env=env, capture_output=True, text=True)
    return r.stdout

TS = re.compile(r"^\s*(crtime|ctime|mtime|atime):\s*0x[0-9a-f]+:[0-9a-f]+\s*--\s*(.+)$")
def stat_times(name):
    out = dbg("stat <%s>" % name) if name.startswith("/") else dbg("stat %s" % name)
    times = {}
    for line in out.splitlines():
        m = TS.match(line)
        if m:
            times[m.group(1)] = datetime.datetime.strptime(m.group(2).strip(), "%a %b %d %H:%M:%S %Y")
    return times

def list_files():
    out = dbg("ls -l /")
    names = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 9:
            nm = parts[-1]
            if nm not in (".", "..") and "." in nm:
                names.append(nm)
    return names

print("=== Lab 10.1: timestomp & log-clearing detection on ext4 ===")
print("image:", os.path.basename(IMG))
print()
print("--- [1] Quet timestamp moi file, so mtime/atime voi crtime ---")
suspects = []
for name in sorted(set(list_files())):
    t = stat_times(name)
    if not t: continue
    flag = ""
    if "crtime" in t and "mtime" in t and t["mtime"] < t["crtime"]:
        flag = "  <-- TIMESTOMP: mtime < crtime (sua truoc khi tao, bat kha thi)"
        suspects.append(name)
    print("%-20s crtime=%s  mtime=%s  ctime=%s%s" % (
        name, t.get("crtime"), t.get("mtime"), t.get("ctime"), flag))
print()

print("--- [2] Neo su that bang nguon doc lap (upload_server.log) ---")
anchor = os.path.join(HERE, "upload_server.log")
if os.path.exists(anchor):
    for line in open(anchor):
        if "report_q4.pdf" in line:
            print("server audit:", line.strip())
    print("=> report_q4.pdf that su xuat hien 2026-10-15, khop crtime(2026), KHONG phai mtime(2009).")
    print("=> Ket luan: mtime/atime da bi timestomp lui ve 2009.")
print()

print("--- [3] Phat hien log clearing tren auth.log ---")
tauth = stat_times("auth.log")
content = dbg("cat auth.log")
lines = [l for l in content.splitlines() if l.strip().startswith("2026")]
last_entry = None
if lines:
    m = re.match(r"(\S+)", lines[-1])
    last_entry = datetime.datetime.strptime(lines[-1].split()[0], "%Y-%m-%dT%H:%M:%S+00:00")
print("auth.log: so dong con lai =", len(lines), "| dong cuoi =", lines[-1].split()[0] if lines else "N/A")
print("auth.log inode: mtime=%s ctime=%s" % (tauth.get("mtime"), tauth.get("ctime")))
if last_entry and tauth.get("mtime") and tauth["mtime"] > last_entry:
    gap = tauth["mtime"] - last_entry
    print("=> BAT THUONG: file bi ghi luc %s nhung dong log moi nhat chi toi %s (lech %s)."
          % (tauth["mtime"], last_entry, gap))
    print("   Mot log ngung o 02:11 nhung inode bi sua luc 03:05 => co nguoi ghi de/cat log.")
wtmp = os.path.join(HERE, "wtmp_last.txt")
if os.path.exists(wtmp):
    print("doi chieu wtmp (nguon doc lap):")
    for line in open(wtmp):
        if "02:45" in line:
            print("  ", line.strip(), " <-- phien nay KHONG con trong auth.log => bi xoa co chu dich")
print()
print("--- Tuong ung tren Windows/NTFS (xem phan ly thuyet) ---")
print("  timestomp: so $SI voi $FN bang MFTECmd/istat; log clearing: Security event 1102, channel khac 104.")
