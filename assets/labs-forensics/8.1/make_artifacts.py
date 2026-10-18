#!/usr/bin/env python3
# Lab 8.1 - tao SQLite gia lap kieu Chrome History va Firefox places/formhistory.
# Timestamp dung dung chuan that:
#   Chrome  = WebKit: microgiay tu 1601-01-01  -> webkit = (unix + 11644473600)*1e6
#   Firefox = PRTime: microgiay tu 1970-01-01  -> prtime = unix*1e6
# Khong dung du lieu rieng tu that.
#
# Dung: python3 -I make_artifacts.py [thu_muc_dich]   (mac dinh ./profile)

import os
import sys
import sqlite3
import datetime

EPOCH_1601_DELTA = 11644473600

def unix(y, mo, d, h, mi, s):
    return int(datetime.datetime(y, mo, d, h, mi, s,
               tzinfo=datetime.timezone.utc).timestamp())

def webkit(y, mo, d, h, mi, s):
    return (unix(y, mo, d, h, mi, s) + EPOCH_1601_DELTA) * 1_000_000

def prtime(y, mo, d, h, mi, s):
    return unix(y, mo, d, h, mi, s) * 1_000_000

def build_chrome(path):
    con = sqlite3.connect(path)
    con.executescript("""
    CREATE TABLE urls(id INTEGER PRIMARY KEY, url TEXT, title TEXT,
      visit_count INTEGER, typed_count INTEGER, last_visit_time INTEGER);
    CREATE TABLE visits(id INTEGER PRIMARY KEY, url INTEGER, visit_time INTEGER,
      from_visit INTEGER, transition INTEGER);
    CREATE TABLE downloads(id INTEGER PRIMARY KEY, target_path TEXT, tab_url TEXT,
      total_bytes INTEGER, start_time INTEGER, end_time INTEGER);
    """)
    # transition core types: 1=TYPED, 0=LINK, 7=FORM_SUBMIT
    urls = [
        (1, "https://www.google.com/", "Google", 3, 2, webkit(2026,1,7,14,2,0)),
        (2, "https://www.google.com/search?q=usb+wiping+tool", "usb wiping tool - Google", 1, 1, webkit(2026,1,7,14,2,10)),
        (3, "https://eraser-tools.example/download", "Eraser - Download", 1, 0, webkit(2026,1,7,14,3,5)),
        (4, "https://www.google.com/search?q=how%20to%20wipe%20usb%20without%20trace", "how to wipe usb - Google", 1, 1, webkit(2026,1,7,14,4,20)),
        (5, "https://mail.example.net/inbox", "Webmail Inbox", 2, 0, webkit(2026,1,7,14,20,0)),
    ]
    con.executemany("INSERT INTO urls VALUES(?,?,?,?,?,?)", urls)
    visits = [
        (1, 1, webkit(2026,1,7,14,2,0), 0, 1),   # typed google
        (2, 2, webkit(2026,1,7,14,2,10), 1, 7),  # form submit search
        (3, 3, webkit(2026,1,7,14,3,5), 2, 0),   # link tu ket qua
        (4, 4, webkit(2026,1,7,14,4,20), 1, 7),  # search lan 2
        (5, 5, webkit(2026,1,7,14,20,0), 0, 1),  # typed webmail
    ]
    con.executemany("INSERT INTO visits VALUES(?,?,?,?,?)", visits)
    con.execute("INSERT INTO downloads VALUES(?,?,?,?,?,?)",
                (1, "C:\\Users\\nghiphamt\\Downloads\\eraser-setup.exe",
                 "https://eraser-tools.example/download", 7360512,
                 webkit(2026,1,7,14,5,12), webkit(2026,1,7,14,5,40)))
    con.commit(); con.close()

def build_firefox(places, formhist):
    con = sqlite3.connect(places)
    con.executescript("""
    CREATE TABLE moz_places(id INTEGER PRIMARY KEY, url TEXT, title TEXT,
      visit_count INTEGER, last_visit_date INTEGER);
    CREATE TABLE moz_historyvisits(id INTEGER PRIMARY KEY, place_id INTEGER,
      visit_date INTEGER, visit_type INTEGER);
    """)
    places_rows = [
        (1, "https://duckduckgo.com/?q=secure+erase+flash+drive", "secure erase - DuckDuckGo", 1, prtime(2026,1,7,14,9,0)),
        (2, "https://eraser-tools.example/download", "Eraser - Download", 1, prtime(2026,1,7,14,9,30)),
    ]
    con.executemany("INSERT INTO moz_places VALUES(?,?,?,?,?)", places_rows)
    con.executemany("INSERT INTO moz_historyvisits VALUES(?,?,?,?)",
                    [(1,1,prtime(2026,1,7,14,9,0),1),(2,2,prtime(2026,1,7,14,9,30),1)])
    con.commit(); con.close()

    con = sqlite3.connect(formhist)
    con.executescript("""
    CREATE TABLE moz_formhistory(id INTEGER PRIMARY KEY, fieldname TEXT, value TEXT,
      timesUsed INTEGER, firstUsed INTEGER, lastUsed INTEGER);
    """)
    rows = [
        (1, "searchbar-history", "how to wipe usb without trace", 1, prtime(2026,1,7,14,8,0), prtime(2026,1,7,14,8,0)),
        (2, "q", "secure erase flash drive", 2, prtime(2026,1,7,14,9,0), prtime(2026,1,7,14,9,0)),
        (3, "email", "suspect@example.net", 1, prtime(2026,1,6,10,0,0), prtime(2026,1,6,10,0,0)),
    ]
    con.executemany("INSERT INTO moz_formhistory VALUES(?,?,?,?,?,?)", rows)
    con.commit(); con.close()

def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "profile")
    os.makedirs(root, exist_ok=True)
    chrome = os.path.join(root, "History")
    places = os.path.join(root, "places.sqlite")
    formhist = os.path.join(root, "formhistory.sqlite")
    for p in (chrome, places, formhist):
        if os.path.exists(p):
            os.remove(p)
    build_chrome(chrome)
    build_firefox(places, formhist)
    print(f"[+] Da tao: {chrome}")
    print(f"[+] Da tao: {places}")
    print(f"[+] Da tao: {formhist}")
    print("[+] Chay tiep:  bash solve.sh " + (sys.argv[1] if len(sys.argv) > 1 else "profile"))

if __name__ == "__main__":
    main()
