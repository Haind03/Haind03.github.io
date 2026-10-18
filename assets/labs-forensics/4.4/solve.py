#!/usr/bin/env python3
# Lab 4.4 solver: LNK + Jump List (LnkParse3) + Shellbag (regipy/UsrClass.dat).
# Chay: python3 -I solve.py [lnk] [jumplist] [UsrClass.dat]
import sys, os, io, re, json, base64, subprocess, tempfile
import LnkParse3

HERE = os.path.dirname(os.path.abspath(__file__))
lnk_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "bang_luong.xlsx.lnk")
jl_path  = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "jumplist.customDestinations-ms")
usrclass = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "UsrClass.dat")

def parse_lnk(stream):
    return LnkParse3.lnk_file(stream).get_json()

def idlist_path(d):
    names = []
    for it in d.get("target", {}).get("items", []):
        if isinstance(it, dict):
            nm = it.get("primary_name") or it.get("volume_name") or it.get("sort_index")
            if nm:
                names.append(nm)
    return " / ".join(names)

print("=== Lab 4.4: File/folder access (LNK + Jump List + Shellbag) ===\n")

print("--- [1] LNK tu sinh: dung target IDList dung lai duong dan ---")
with open(lnk_path, "rb") as f:
    d = parse_lnk(f)
print("   file:", os.path.basename(lnk_path))
print("   target (IDList):", idlist_path(d))
print("   header ctime=%s mtime=%s" % (d["header"].get("creation_time"), d["header"].get("modified_time")))
print("   (VolumeSerial/DriveType nam trong LinkInfo cua LNK Windows that -> xem BAI TAP voi LECmd)")
print()

print("--- [2] Jump List (CustomDestinations) la container cua nhieu LNK ---")
raw = open(jl_path, "rb").read()
try:
    dec = base64.b64decode(raw, validate=True)
except Exception:
    dec = raw
hdr = bytes.fromhex("4c000000") + bytes.fromhex("0114020000000000c000000000000046")
offs = [m.start() for m in re.finditer(re.escape(hdr), dec)]
print("   so LNK nhung ben trong:", len(offs))
bounds = offs + [len(dec)]
seen = set()
for i, o in enumerate(offs):
    seg = dec[o:bounds[i + 1]]
    try:
        dd = parse_lnk(io.BytesIO(seg))
        p = (dd.get("link_info", {}) or {}).get("local_base_path") or idlist_path(dd)
        if p in seen:
            continue
        seen.add(p)
        print("   target=%s  (ctime %s)" % (p, dd["header"].get("creation_time")))
    except Exception:
        pass
print()

print("--- [3] Shellbag tu UsrClass.dat (user da DUYET thu muc nao) ---")
out = tempfile.mktemp(suffix=".json")
subprocess.run(["regipy-plugins-run", usrclass, "-o", out,
                "-p", "usrclass_shellbag_plugin", "--continue-on-error"],
               capture_output=True, text=True)
sb = json.load(open(out)).get("usrclass_shellbag_plugin") or []
os.remove(out)
print("   tong node:", len(sb) if isinstance(sb, list) else sb)
for e in (sb if isinstance(sb, list) else [])[:12]:
    if e.get("shell_type") in ("Directory", "Volume") and e.get("path"):
        print("   %-42s type=%-10s mtime=%s" % (
            e.get("path"), e.get("shell_type"), e.get("modification_time") or e.get("last_write")))
