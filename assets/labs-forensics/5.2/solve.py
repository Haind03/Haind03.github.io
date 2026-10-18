#!/usr/bin/env python3
# Lab 5.2 - script giai: doc plist + quarantine + WhereFroms + knowledgeC + TCC
# de truy mot app la tu khoi dong. MO PHONG tren Linux:
#   plutil  -> plistlib        (doc binary plist)
#   xattr   -> os.getxattr     (doc com.apple.quarantine, kMDItemWhereFroms)
#   mdls    -> doc WhereFroms tu xattr metadata
#   sqlite3 -> sqlite3 module  (knowledgeC.db, TCC.db)
#
# Dung: python3 -I solve.py [thu_muc_mac]   (mac dinh ./mac)

import os
import sys
import glob
import plistlib
import sqlite3
import datetime

MAC_EPOCH_OFFSET = 978307200

def get_xattr(path, name):
    try:
        return os.getxattr(path, name.encode())
    except OSError:
        side = os.path.join(os.path.dirname(path), ".xattr",
                            os.path.basename(path) + "." + name.replace("/", "_"))
        if os.path.exists(side):
            return open(side, "rb").read()
        return None

def h(t): print("\n==== " + t + " ====")

def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "mac")
    if not os.path.isdir(root):
        print("Khong thay thu muc:", root, "(chay make_artifacts.py truoc)"); return 1

    h("1. LaunchAgents: doc binary plist tim autostart dang ngo")
    suspect_bin = None
    for p in glob.glob(os.path.join(root, "Users/*/Library/LaunchAgents/*.plist")) + \
             glob.glob(os.path.join(root, "Library/Launch*/*.plist")):
        with open(p, "rb") as f:
            d = plistlib.load(f)
        label = d.get("Label", "")
        args = d.get("ProgramArguments", [])
        prog = args[0] if args else ""
        flags = [k for k in ("RunAtLoad", "KeepAlive") if d.get(k)]
        susp = ("/Users/Shared" in prog) or ("/tmp" in prog) or (prog.startswith("/Users") and "." in prog)
        tag = "  <== DANG NGO" if susp else ""
        print(f"  {os.path.relpath(p, root)}")
        print(f"    Label={label}  Program={prog}  {'+'.join(flags)}{tag}")
        if susp:
            suspect_bin = os.path.join(root, prog.lstrip("/"))

    if not suspect_bin or not os.path.exists(suspect_bin):
        print("Khong xac dinh duoc binary dang ngo."); return 1

    h("2. Nguon tai: quarantine + kMDItemWhereFroms")
    q = get_xattr(suspect_bin, "user.com.apple.quarantine")
    if q:
        parts = q.decode().split(";")
        flags, ts_hex, agent = parts[0], parts[1], parts[2]
        when = datetime.datetime.fromtimestamp(int(ts_hex, 16), datetime.timezone.utc)
        print(f"  com.apple.quarantine = {q.decode()}")
        print(f"    -> tai bang: {agent}")
        print(f"    -> luc:      {when:%Y-%m-%d %H:%M:%S} UTC (tu timestamp hex {ts_hex})")
    wf = get_xattr(suspect_bin, "user.com.apple.metadata:kMDItemWhereFroms")
    if wf:
        urls = plistlib.loads(wf)
        print(f"  kMDItemWhereFroms = {urls}")
        print(f"    -> URL tai: {urls[0]}")

    h("3. knowledgeC.db: app foreground luc nao (Mac absolute time + 978307200)")
    kdb = glob.glob(os.path.join(root, "Users/*/Library/Application Support/Knowledge/knowledgeC.db"))
    if kdb:
        con = sqlite3.connect(kdb[0])
        cur = con.execute(
            "SELECT ZVALUESTRING,"
            " datetime(ZSTARTDATE+?, 'unixepoch'),"
            " datetime(ZENDDATE+?, 'unixepoch')"
            " FROM ZOBJECT WHERE ZSTREAMNAME='/app/inFocus' ORDER BY ZSTARTDATE",
            (MAC_EPOCH_OFFSET, MAC_EPOCH_OFFSET))
        n_susp = 0
        for app, st, en in cur:
            mark = ""
            if ".updater" in app:
                mark = "  <== app la"; n_susp += 1
            print(f"  {st} -> {en}  {app}{mark}")
        con.close()
        print(f"  => app la foreground {n_susp} lan (dung khung sau moi lan login)")

    h("4. TCC.db: quyen nhay cam da cap (auth_value 2 = cho phep)")
    tdb = glob.glob(os.path.join(root, "Library/Application Support/com.apple.TCC/TCC.db"))
    if tdb:
        con = sqlite3.connect(tdb[0])
        cur = con.execute(
            "SELECT client, service, auth_value,"
            " datetime(last_modified,'unixepoch') FROM access ORDER BY last_modified")
        for client, service, auth, when in cur:
            flag = "  <== CO RED FLAG" if (".updater" in client and auth == 2 and
                    service in ("kTCCServiceAccessibility", "kTCCServiceSystemPolicyAllFiles")) else ""
            print(f"  {when}  {service}  auth={auth}  {client}{flag}")
        con.close()

    h("KET LUAN")
    print("""  Vao may    : tai http://cdn-update.example.bad/su.zip bang Google Chrome (quarantine + WhereFroms)
  Autostart  : LaunchAgent com.apple.softwareupdated (gia danh Apple), RunAtLoad + KeepAlive,
               Program /Users/Shared/.updater/softwareupdated (Apple khong bao gio de binary o /Users/Shared)
  Da chay    : knowledgeC cho thay app foreground sau moi lan login
  Quyen      : TCC cap kTCCServiceAccessibility + AllFiles (auth=2) -> du suc keylog -> nghi stalkerware
  Ghi chu    : day la MO PHONG cau truc tren Linux (plistlib/os.getxattr/sqlite3 thay plutil/xattr/mdls)""")
    return 0

if __name__ == "__main__":
    sys.exit(main())
