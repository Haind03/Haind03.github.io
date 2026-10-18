#!/usr/bin/env python3
# Lab 4.3 solver: program execution tu Amcache (SHA1) + Shimcache (SYSTEM) + UserAssist (NTUSER).
# Chay: python3 -I solve.py [thu_muc_chua_hive]
import json, subprocess, os, sys, tempfile

HIVES = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))

def run(hive, plugins):
    out = tempfile.mktemp(suffix=".json")
    subprocess.run(["regipy-plugins-run", os.path.join(HIVES, hive), "-o", out,
                    "-p", ",".join(plugins), "--include-unvalidated", "--continue-on-error"],
                   capture_output=True, text=True)
    d = json.load(open(out)); os.remove(out); return d

print("=== Lab 4.3: Program execution (Amcache + Shimcache + UserAssist) ===\n")

am = run("amcache.hve", ["amcache"]).get("amcache") or []
print("--- [1] Amcache: SHA1 cua binary (chung minh HIEN DIEN + cho hash de tra IOC) ---")
print("Tong entry co SHA1:", sum(1 for e in am if isinstance(e, dict) and e.get("sha1")))
shown = 0
for e in am:
    if isinstance(e, dict) and e.get("sha1") and "temp" in (e.get("full_path") or "").lower():
        print("   %s" % e.get("full_path"))
        print("      sha1=%s  ts=%s" % (e.get("sha1"), e.get("timestamp")))
        shown += 1
        if shown >= 4: break
print()

sysd = run("SYSTEM", ["shimcache", "background_activity_moderator"])
sc = sysd.get("shimcache") or []
print("--- [2] Shimcache: path + last_mod_date (LA mtime, KHONG phai gio chay) ---")
print("Tong entry:", len(sc), " (thu tu: moi nhat o dau)")
for e in sc[:5]:
    print("   mtime=%s  exec_flag=%s  %s" % (e.get("last_mod_date"), e.get("exec_flag"), e.get("path")))
bam = sysd.get("background_activity_moderator") or []
print("BAM/DAM entries:", len(bam), "(hive Win7 nay khong co BAM -> xem BAI TAP tren Win10 1709+)")
print()

ua = [x for x in (run("NTUSER.DAT", ["user_assist"]).get("user_assist") or []) if isinstance(x, dict)]
print("--- [3] UserAssist: chuong trinh chay QUA Explorer, co run_counter + last run ---")
seen = set(); cnt = 0
for e in sorted(ua, key=lambda x: x.get("run_counter") or 0, reverse=True):
    if e.get("name") in seen: continue
    seen.add(e.get("name"))
    print("   run=%s  last=%s  %s" % (e.get("run_counter"), e.get("timestamp"), e.get("name")))
    cnt += 1
    if cnt >= 6: break
print()
print("--- Nguyen tac: Amcache/Shimcache = HIEN DIEN; UserAssist/Prefetch/BAM = DA CHAY ---")
