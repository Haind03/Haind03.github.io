#!/usr/bin/env python3
# Lab 8.3 - tao SQLite gia lap cho mobile forensics:
#   Android SMS  (mmssms.db, sms: address/body/date[ms]/type)  + file -wal that
#   WhatsApp     (msgstore.db, messages)                       timestamp[ms]
#   iOS backup   (Manifest.db anh xa domain+relativePath -> fileID bam; sms.db CoreData)
# Tin nhan mo phong, khong dung du lieu rieng tu that.
#
# Dung: python3 -I make_artifacts.py [thu_muc_dich]   (mac dinh ./backup)

import os
import sys
import shutil
import sqlite3
import datetime

MAC_EPOCH_OFFSET = 978307200

def ms(y, mo, d, h, mi, s):
    return int(datetime.datetime(y, mo, d, h, mi, s,
               tzinfo=datetime.timezone.utc).timestamp()) * 1000

def ns_coredata(y, mo, d, h, mi, s):
    unix = int(datetime.datetime(y, mo, d, h, mi, s,
               tzinfo=datetime.timezone.utc).timestamp())
    return (unix - MAC_EPOCH_OFFSET) * 1_000_000_000

def build_android_sms(path):
    # tao o thu muc tam de giu lai mot -wal that (tin moi nhat nam trong wal)
    work = path + ".work"
    for ext in ("", "-wal", "-shm"):
        for p in (path + ext, work + ext):
            if os.path.exists(p):
                os.remove(p)
    con = sqlite3.connect(work)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA wal_autocheckpoint=0")
    con.execute("CREATE TABLE sms(_id INTEGER PRIMARY KEY, address TEXT, "
                "body TEXT, date INTEGER, type INTEGER)")
    base = [
        ("+84901234567", "Alo, chieu nay hop luc may gio?", ms(2026,1,7,3,10,0), 1),
        ("+84901234567", "3 gio chieu nhe", ms(2026,1,7,3,11,0), 2),
        ("+84988888888", "Ma OTP cua ban la 884213", ms(2026,1,7,6,45,0), 1),
        ("+84901234567", "Ok da nhan", ms(2026,1,7,6,46,0), 2),
    ]
    con.executemany("INSERT INTO sms(address,body,date,type) VALUES(?,?,?,?)", base)
    con.commit()
    con.execute("PRAGMA wal_checkpoint(TRUNCATE)")  # phang base vao db chinh
    # tin NHAN MOI NHAT: chi ghi vao -wal, chua checkpoint
    con.execute("INSERT INTO sms(address,body,date,type) VALUES(?,?,?,?)",
                ("+84901234567", "Nho mang USB qua giup minh", ms(2026,1,7,9,2,30), 1))
    con.commit()
    # copy ca ba file TRUOC khi close (close se checkpoint, mat y nghia demo)
    for ext in ("", "-wal", "-shm"):
        if os.path.exists(work + ext):
            shutil.copy(work + ext, path + ext)
    con.close()
    for ext in ("", "-wal", "-shm"):
        if os.path.exists(work + ext):
            os.remove(work + ext)

def build_whatsapp(path):
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE messages(_id INTEGER PRIMARY KEY, key_remote_jid TEXT, "
                "key_from_me INTEGER, data TEXT, timestamp INTEGER)")
    rows = [
        ("84901234567@s.whatsapp.net", 0, "File da gui chua?", ms(2026,1,7,8,0,0)),
        ("84901234567@s.whatsapp.net", 1, "Dang upload", ms(2026,1,7,8,1,0)),
        ("84901234567@s.whatsapp.net", 1, "https://files.example/x.zip", ms(2026,1,7,8,3,0)),
    ]
    con.executemany("INSERT INTO messages(key_remote_jid,key_from_me,data,timestamp) "
                    "VALUES(?,?,?,?)", rows)
    con.commit(); con.close()

def build_ios(root):
    udid = "00008030-000A1B2C3D4E5F6G"
    bdir = os.path.join(root, "ios", udid)
    os.makedirs(bdir, exist_ok=True)
    # 1. file sms.db bam ten (fileID = hash 40 hex nhu vi du trong bai)
    file_id = "3d0d7e5fb2ce288813306e4d4636395e047a3d28"
    sub = os.path.join(bdir, file_id[:2])
    os.makedirs(sub, exist_ok=True)
    sms_path = os.path.join(sub, file_id)
    if os.path.exists(sms_path):
        os.remove(sms_path)
    con = sqlite3.connect(sms_path)
    con.execute("CREATE TABLE message(ROWID INTEGER PRIMARY KEY, text TEXT, "
                "date INTEGER, handle_id INTEGER)")
    con.executemany("INSERT INTO message(text,date,handle_id) VALUES(?,?,?)", [
        ("iMessage: tai lieu da luu vao iCloud", ns_coredata(2026,1,7,9,30,0), 1),
        ("Da xoa lich su duyet web", ns_coredata(2026,1,7,9,40,0), 1),
    ])
    con.commit(); con.close()

    # 2. Manifest.db anh xa domain + relativePath -> fileID
    man = os.path.join(bdir, "Manifest.db")
    if os.path.exists(man):
        os.remove(man)
    con = sqlite3.connect(man)
    con.execute("CREATE TABLE Files(fileID TEXT PRIMARY KEY, domain TEXT, "
                "relativePath TEXT, flags INTEGER, file BLOB)")
    con.executemany("INSERT INTO Files(fileID,domain,relativePath,flags,file) "
                    "VALUES(?,?,?,?,NULL)", [
        (file_id, "HomeDomain", "Library/SMS/sms.db", 1),
        ("ca1b...addressbook", "HomeDomain", "Library/AddressBook/AddressBook.sqlitedb", 1),
    ])
    con.commit(); con.close()
    return udid, file_id

def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "backup")
    adir = os.path.join(root, "android")
    os.makedirs(adir, exist_ok=True)
    build_android_sms(os.path.join(adir, "mmssms.db"))
    build_whatsapp(os.path.join(adir, "msgstore.db"))
    udid, fid = build_ios(root)

    print(f"[+] Android SMS : {os.path.join(adir, 'mmssms.db')} (kem -wal co tin moi nhat)")
    print(f"[+] WhatsApp    : {os.path.join(adir, 'msgstore.db')}")
    print(f"[+] iOS backup  : ios/{udid}/Manifest.db + ios/{udid}/{fid[:2]}/{fid}")
    print("[+] Chay tiep:  python3 -I solve.py " + (sys.argv[1] if len(sys.argv) > 1 else "backup"))

if __name__ == "__main__":
    main()
