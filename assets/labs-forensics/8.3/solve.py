#!/usr/bin/env python3
# Lab 8.3 - script giai: trich tin nhan tu Android SMS, WhatsApp va iOS backup,
# doi dung don vi thoi gian moi nen, va minh hoa cai bay WAL.
# Mo moi SQLite o che do READ-ONLY (khong lam hong bang chung, giu nguyen -wal).
#
# Dung: python3 -I solve.py [thu_muc_backup]   (mac dinh ./backup)

import os
import sys
import shutil
import sqlite3
import tempfile

MAC_EPOCH_OFFSET = 978307200

def ro(path):
    return sqlite3.connect("file:%s?mode=ro" % path, uri=True)

def h(t): print("\n==== " + t + " ====")

def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "backup")
    adir = os.path.join(root, "android")
    sms = os.path.join(adir, "mmssms.db")
    wa = os.path.join(adir, "msgstore.db")
    if not os.path.exists(sms):
        print("Thieu", sms, "(chay make_artifacts.py truoc)"); return 1

    h("1. Android SMS (mmssms.db): date la epoch MILIgiay -> /1000")
    con = ro(sms)
    rows = con.execute(
        "SELECT datetime(date/1000,'unixepoch') AS t, address,"
        " CASE type WHEN 1 THEN 'nhan' WHEN 2 THEN 'gui' ELSE type END AS huong, body"
        " FROM sms ORDER BY date").fetchall()
    for t, addr, huong, body in rows:
        print(f"  {t}  {addr:<14} {huong:<4} {body}")
    con.close()

    h("2. Cai bay WAL: tin moi nhat co the chi nam trong mmssms.db-wal")
    has_wal = os.path.exists(sms + "-wal")
    print(f"  Co file mmssms.db-wal: {has_wal}")
    # doc neu BO -wal (copy mot minh db chinh ra thu muc tam)
    with tempfile.TemporaryDirectory() as td:
        only = os.path.join(td, "mmssms.db")
        shutil.copy(sms, only)  # chi copy db chinh, khong copy -wal
        c = ro(only); n_drop = c.execute("SELECT count(*) FROM sms").fetchone()[0]; c.close()
    c = ro(sms); n_keep = c.execute("SELECT count(*) FROM sms").fetchone()[0]; c.close()
    print(f"  So tin khi BO -wal (chi db chinh): {n_drop}")
    print(f"  So tin khi GIU -wal (db + wal)   : {n_keep}")
    print(f"  => bo -wal mat {n_keep - n_drop} tin (chinh la tin moi nhat, thuong quan trong nhat)")

    h("3. WhatsApp (msgstore.db): timestamp epoch MILIgiay -> /1000")
    if os.path.exists(wa):
        con = ro(wa)
        for t, jid, huong, data in con.execute(
            "SELECT datetime(timestamp/1000,'unixepoch') AS t, key_remote_jid,"
            " CASE key_from_me WHEN 1 THEN 'gui' ELSE 'nhan' END, data"
            " FROM messages ORDER BY timestamp"):
            print(f"  {t}  {jid:<30} {huong:<4} {data}")
        con.close()

    h("4. iOS backup: tra Manifest.db -> fileID -> mo file bam (CoreData nano-giay)")
    import glob
    mans = glob.glob(os.path.join(root, "ios", "*", "Manifest.db"))
    if mans:
        man = mans[0]; bdir = os.path.dirname(man)
        con = ro(man)
        fid = con.execute("SELECT fileID FROM Files WHERE relativePath=?",
                          ("Library/SMS/sms.db",)).fetchone()[0]
        con.close()
        print(f"  Manifest.db: Library/SMS/sms.db -> fileID {fid}")
        hashed = os.path.join(bdir, fid[:2], fid)
        print(f"  Mo file bam: ios/.../{fid[:2]}/{fid}")
        con = ro(hashed)
        for t, text in con.execute(
            "SELECT datetime(date/1000000000 + ?, 'unixepoch') AS t, text"
            " FROM message ORDER BY date", (MAC_EPOCH_OFFSET,)):
            print(f"    {t}  {text}")
        con.close()

    h("KET LUAN / luu y acquisition")
    print("""  Android SMS = Unix epoch MILIgiay (/1000); WhatsApp cung MILIgiay.
  iOS message.date = CoreData nano-giay tu 2001 (/1e9 + 978307200).
  Moi nen mot cong thuc: sai don vi la moc nhay ra tuong lai xa.
  LUON thu ca -wal: o day bo -wal mat dung tin moi nhat.
  Day la logical acquisition mo phong: tin da xoa / app chan backup khong nam trong pham vi.""")
    return 0

if __name__ == "__main__":
    sys.exit(main())
