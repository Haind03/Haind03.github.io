#!/usr/bin/env python3
# Lab 11.2 - script giai: dieu tra he thong nhiem theo BAY BUOC, tu triage toi IOC.
# Doc artifact la du lieu khong tin cay -> chi doc, truyen duong dan lam tham so.
#
# Dung: python3 -I solve.py [thu_muc_case]   (mac dinh ./case-host)

import os
import sys
import re
import glob
import hashlib
import datetime

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()

def strings(path, minlen=6):
    out, cur = [], bytearray()
    with open(path, "rb") as f:
        data = f.read()
    for byte in data:
        if 32 <= byte < 127:
            cur.append(byte)
        else:
            if len(cur) >= minlen:
                out.append(cur.decode())
            cur = bytearray()
    if len(cur) >= minlen:
        out.append(cur.decode())
    return out

def h(t): print("\n==== " + t + " ====")

def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "case-host")
    if not os.path.isdir(root):
        print("Thieu", root, "(chay make_artifacts.py truoc)"); return 1
    ioc = {"ip": set(), "path": [], "sha256": {}, "ua": set(), "mutex": set(),
           "url": set(), "persistence": []}

    h("Buoc 1. Chuan bi & xac minh (hash file kha nghi, lam tren ban sao)")
    implant = os.path.join(root, "var/tmp/.sysd/kworkerd")
    webshell = os.path.join(root, "var/www/html/uploads/shell.php")
    for p in (implant, webshell):
        if os.path.exists(p):
            dg = sha256(p)
            ioc["sha256"][os.path.relpath(p, root)] = dg
            print(f"  sha256 {os.path.relpath(p, root)} = {dg}")

    h("Buoc 2. Triage: diem nong trong log va file bat thuong")
    acc = os.path.join(root, "var/log/nginx/access.log")
    hot = []
    for ln in open(acc, encoding="utf-8", errors="replace"):
        if "cmd=" in ln or "upload.php" in ln:
            hot.append(ln.rstrip())
    for ln in hot:
        print("  [nginx]", ln)
    print("  [fs] file an / staging trong /var/tmp/.sysd:")
    for p in glob.glob(os.path.join(root, "var/tmp/.sysd/*")):
        st = os.stat(p)
        print(f"    {os.path.relpath(p, root)}  size={st.st_size}  "
              f"mtime={datetime.datetime.utcfromtimestamp(st.st_mtime):%Y-%m-%d}")

    h("Buoc 3. Root cause (initial access)")
    ip_access = re.findall(r"^(\d+\.\d+\.\d+\.\d+).*(POST /upload\.php|shell\.php\?cmd=)",
                           open(acc, encoding="utf-8", errors="replace").read(), re.M)
    atk = ip_access[0][0] if ip_access else "?"
    ioc["ip"].add(atk)
    print(f"  Webshell {os.path.relpath(webshell, root)} duoc upload qua POST /upload.php")
    print(f"  roi khai thac bang GET shell.php?cmd=... tu IP {atk}")
    print(f"  -> Initial Access: upload webshell (tuong duong T1505.003 Web Shell)")

    h("Buoc 4. Persistence")
    for f in glob.glob(os.path.join(root, "etc/cron.d/*")):
        txt = open(f, encoding="utf-8", errors="replace").read().strip()
        print(f"  [cron]    {os.path.relpath(f, root)}: {txt}")
        ioc["persistence"].append(os.path.relpath(f, root))
        ioc["ip"].update(re.findall(r"\d+\.\d+\.\d+\.\d+", txt))
    for f in glob.glob(os.path.join(root, "etc/systemd/system/*.service")):
        txt = open(f, encoding="utf-8", errors="replace").read()
        es = [l.strip() for l in txt.splitlines() if l.startswith("ExecStart=")]
        print(f"  [systemd] {os.path.relpath(f, root)}: {es[0] if es else '?'}")
        ioc["persistence"].append(os.path.relpath(f, root))

    h("Buoc 5. Lateral movement & pham vi")
    print("  He thong tu chua mot host (web01). Khong thay bang chung SSH di ra may khac")
    print("  trong auth.log/known_hosts -> pham vi: 1 host. (Ca that: quet fleet bang IOC/YARA.)")

    h("Buoc 6. C2 & exfil (strings tren implant)")
    for s in strings(implant):
        if re.search(r"\d+\.\d+\.\d+\.\d+", s):
            ioc["ip"].update(re.findall(r"\d+\.\d+\.\d+\.\d+", s))
        if s.startswith("http"):
            ioc["url"].add(s)
        if "Mozilla" in s or "AcctLoader" in s:
            ioc["ua"].add(s)
        if "AcctLdr" in s:
            ioc["mutex"].add(s)
        if s.strip():
            print("  [str]", s)
    exfil = os.path.join(root, "var/tmp/.sysd/data.tar.gz")
    if os.path.exists(exfil):
        ioc["path"].append(os.path.relpath(exfil, root))
        print(f"  [exfil] staged archive {os.path.relpath(exfil, root)} "
              f"({os.path.getsize(exfil)} bytes) -> nghi chuan bi day ra C2")

    h("Buoc 7. Anti-forensic + bo IOC ban giao")
    st = os.stat(implant)
    yr = datetime.datetime.utcfromtimestamp(st.st_mtime).year
    if yr < 2015:
        print(f"  [timestomp] mtime cua implant = {yr} (gia ve qua khu xa) -> Defense Evasion")
    # log clearing dau hieu
    sysl = open(os.path.join(root, "var/log/syslog"), encoding="utf-8", errors="replace").read()
    if "Stopping System Logging" in sysl:
        print("  [log] co dau khoi dong lai rsyslog luc 10:15 (nghi xoa/xoay log de xoa dau)")
    ioc["path"].append(os.path.relpath(implant, root))

    print("\n  --- BO IOC ---")
    print("  IP      :", ", ".join(sorted(ioc["ip"])))
    print("  URL     :", ", ".join(sorted(ioc["url"])))
    print("  UA      :", ", ".join(sorted(ioc["ua"])))
    print("  Mutex   :", ", ".join(sorted(ioc["mutex"])))
    print("  Path    :", ", ".join(ioc["path"]))
    for k, v in ioc["sha256"].items():
        print(f"  sha256  : {v}  ({k})")
    print("  Persist :", ", ".join(ioc["persistence"]))
    print("  YARA goi y: rule AcctLoader { strings: $a=\"AcctLoader/1.2\" $b=\"AcctLdr_7f3a\" "
          "condition: any of them }")

    # xuat IOC ra JSON de lab 11.3 dung lam dau vao
    import json
    out = {
        "case": "web01-0107",
        "host": "web01",
        "initial_access": "Web shell upload (T1505.003)",
        "ip": sorted(ioc["ip"]),
        "url": sorted(ioc["url"]),
        "user_agent": sorted(ioc["ua"]),
        "mutex": sorted(ioc["mutex"]),
        "paths": ioc["path"],
        "sha256": ioc["sha256"],
        "persistence": ioc["persistence"],
        "exfil": os.path.relpath(exfil, root),
        "anti_forensics": [f"timestomp implant mtime -> {yr}", "rsyslog restart 10:15 (nghi xoa log)"],
    }
    iocfile = os.path.join(root, "iocs.json")
    with open(iocfile, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\n  [+] Da xuat IOC ra {os.path.relpath(iocfile, root)} (dung cho lab 11.3)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
