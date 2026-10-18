#!/usr/bin/env python3
# Lab 5.2 - tao artifact macOS gia lap, MO PHONG tren Linux.
# Khong co may Mac van tap duoc: ta tai tao DUNG CAU TRUC cac artifact
#   - LaunchAgent plist (binary plist, doc bang plistlib thay cho plutil)
#   - co quarantine com.apple.quarantine (xattr user.* thay cho xattr macOS)
#   - kMDItemWhereFroms (binary plist nhung trong xattr metadata)
#   - knowledgeC.db va TCC.db (SQLite y het macOS)
# Khong dung du lieu rieng tu that.
#
# Dung: python3 -I make_artifacts.py [thu_muc_dich]   (mac dinh ./mac)

import os
import sys
import plistlib
import sqlite3
import datetime

MAC_EPOCH_OFFSET = 978307200  # giay giua 1970-01-01 va 2001-01-01

def utc(y, mo, d, h, mi, s):
    return int(datetime.datetime(y, mo, d, h, mi, s,
               tzinfo=datetime.timezone.utc).timestamp())

def set_xattr(path, name, value):
    """Set xattr user.*; neu fs khong ho tro thi ghi file sidecar .xattr/."""
    try:
        os.setxattr(path, name.encode(), value)
        return True
    except OSError:
        side = os.path.join(os.path.dirname(path), ".xattr")
        os.makedirs(side, exist_ok=True)
        with open(os.path.join(side, os.path.basename(path) + "." +
                  name.replace("/", "_")), "wb") as f:
            f.write(value)
        return False

def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "mac")
    if os.path.exists(root):
        import shutil
        shutil.rmtree(root)
    os.makedirs(root)

    user = "an"
    dl_time = utc(2026, 1, 7, 9, 15, 2)   # luc tai binary ve

    # 1. binary gia (chi la script vo hai ghi log)
    bindir = os.path.join(root, "Users/Shared/.updater")
    os.makedirs(bindir)
    binpath = os.path.join(bindir, "softwareupdated")
    with open(binpath, "w", newline="\n") as f:
        f.write("#!/bin/sh\n# gia lap payload: chi ghi 1 dong log\n"
                "echo \"$(date) softwareupdated ran\" >> /tmp/.su.log\n")
    os.chmod(binpath, 0o755)

    # 1b. quarantine xattr: flags;timestamp_hex;agent;event_UUID
    q = f"0081;{dl_time:x};Google Chrome;F1B2C3D4-0000-4000-8000-ABCDEF012345"
    q_ok = set_xattr(binpath, "user.com.apple.quarantine", q.encode())

    # 1c. kMDItemWhereFroms = binary plist mang [url, referrer]
    wf = plistlib.dumps(["http://cdn-update.example.bad/su.zip",
                         "http://cdn-update.example.bad/download"],
                        fmt=plistlib.FMT_BINARY)
    wf_ok = set_xattr(binpath, "user.com.apple.metadata:kMDItemWhereFroms", wf)

    # 2. LaunchAgent plist (BINARY plist - phai doc bang plutil/plistlib)
    la_dir = os.path.join(root, f"Users/{user}/Library/LaunchAgents")
    os.makedirs(la_dir)
    plist = {
        "Label": "com.apple.softwareupdated",
        "ProgramArguments": ["/Users/Shared/.updater/softwareupdated"],
        "RunAtLoad": True,
        "KeepAlive": True,
    }
    with open(os.path.join(la_dir, "com.apple.softwareupdated.plist"), "wb") as f:
        plistlib.dump(plist, f, fmt=plistlib.FMT_BINARY)
    # mot LaunchAgent hop le de doi chung
    good = {"Label": "com.google.keystone.agent",
            "ProgramArguments": ["/Library/Google/GoogleSoftwareUpdate/Agent"],
            "StartInterval": 3600}
    with open(os.path.join(la_dir, "com.google.keystone.agent.plist"), "wb") as f:
        plistlib.dump(good, f, fmt=plistlib.FMT_BINARY)

    # 3. knowledgeC.db - app inFocus theo Mac absolute time
    kdir = os.path.join(root, f"Users/{user}/Library/Application Support/Knowledge")
    os.makedirs(kdir)
    kdb = os.path.join(kdir, "knowledgeC.db")
    con = sqlite3.connect(kdb)
    con.executescript("""
    CREATE TABLE ZOBJECT(
      Z_PK INTEGER PRIMARY KEY, ZSTREAMNAME TEXT, ZVALUESTRING TEXT,
      ZSTARTDATE REAL, ZENDDATE REAL);
    """)
    # app la foreground sau moi lan login (3 lan), kem mot app binh thuong
    sessions = [
        ("/Users/Shared/.updater/softwareupdated", (2026,1,7, 9,16,0), (2026,1,7, 9,16,8)),
        ("com.apple.Safari",                        (2026,1,7, 9,20,0), (2026,1,7, 9,35,0)),
        ("/Users/Shared/.updater/softwareupdated", (2026,1,8, 8,2,0),  (2026,1,8, 8,2,9)),
        ("/Users/Shared/.updater/softwareupdated", (2026,1,9, 7,51,0), (2026,1,9, 7,51,7)),
    ]
    for i, (app, st, en) in enumerate(sessions, 1):
        con.execute("INSERT INTO ZOBJECT VALUES(?,?,?,?,?)",
                    (i, "/app/inFocus", app,
                     utc(*st) - MAC_EPOCH_OFFSET,
                     utc(*en) - MAC_EPOCH_OFFSET))
    con.commit(); con.close()

    # 4. TCC.db - quyen rieng tu (last_modified = Unix epoch)
    tdir = os.path.join(root, "Library/Application Support/com.apple.TCC")
    os.makedirs(tdir)
    tdb = os.path.join(tdir, "TCC.db")
    con = sqlite3.connect(tdb)
    con.executescript("""
    CREATE TABLE access(
      service TEXT, client TEXT, client_type INTEGER,
      auth_value INTEGER, last_modified INTEGER);
    """)
    rows = [
        ("kTCCServiceAccessibility", "/Users/Shared/.updater/softwareupdated", 1, 2,
         utc(2026,1,7, 9,17,10)),
        ("kTCCServiceSystemPolicyAllFiles", "/Users/Shared/.updater/softwareupdated", 1, 2,
         utc(2026,1,7, 9,17,15)),
        ("kTCCServiceCamera", "com.apple.Safari", 0, 2, utc(2026,1,5, 12,0,0)),
    ]
    con.executemany("INSERT INTO access VALUES(?,?,?,?,?)", rows)
    con.commit(); con.close()

    print(f"[+] Da tao artifact macOS gia lap tai: {root}")
    print(f"[+] quarantine xattr: {'OK (fs ho tro user.*)' if q_ok else 'ghi sidecar .xattr/'}")
    print(f"[+] WhereFroms xattr: {'OK' if wf_ok else 'ghi sidecar .xattr/'}")
    print("[+] Chay tiep:  python3 -I solve.py " + (sys.argv[1] if len(sys.argv) > 1 else "mac"))

if __name__ == "__main__":
    main()
