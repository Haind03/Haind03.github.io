#!/usr/bin/env python3
"""
Lab 2.2 - Blind SQL injection (boolean-based + time-based)
App Flask + sqlite. Khong tra ve du lieu truy van, chi lo gian tiep:

  /api/check?user=<u>  -> SELECT id FROM users WHERE username='<u>'
       Tra "FOUND" neu co row, "NOTFOUND" neu khong. Day la oracle boolean:
       chen dieu kien, quan sat FOUND/NOTFOUND de doan tung bit du lieu.

  /api/log?user=<u>    -> chay dung cau truy van tren NHUNG luon tra "ok".
       Khong lo boolean -> phai dung time-based. sqlite khong co SLEEP() nen
       ta ep tre bang HEX(RANDOMBLOB(N)) (bam N lon -> tinh toan lau).

Muc tieu: trich mat khau cua 'admin' (chinh la FLAG) tung ky tu, chi qua
phan hoi FOUND/NOTFOUND (boolean) hoac qua do tre (time-based).

Chay local, loopback, cong 8022:
    PORT=8022 python3 app.py
"""
import os
import sqlite3
from flask import Flask, request, Response

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab22.db")


def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE users(
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT
        );
        INSERT INTO users(username,password) VALUES
            ('admin','WEB{bl1nd_b00l3an_and_t1me}'),
            ('alice','alice_pw'),
            ('bob','bob_pw');
        """
    )
    con.commit()
    con.close()


def run(sql):
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        cur.execute(sql)
        return cur.fetchall()
    finally:
        con.close()


@app.route("/api/check")
def check():
    u = request.args.get("user", "")
    # LO HONG: noi chuoi. Chi lo boolean qua FOUND/NOTFOUND.
    sql = "SELECT id FROM users WHERE username='" + u + "'"
    try:
        rows = run(sql)
    except Exception:
        # Loi SQL cung coi nhu NOTFOUND -> khong lo error (blind that su)
        return Response("NOTFOUND\n", mimetype="text/plain")
    return Response(("FOUND\n" if rows else "NOTFOUND\n"), mimetype="text/plain")


@app.route("/api/log")
def log():
    u = request.args.get("user", "")
    # LO HONG: noi chuoi. Luon tra "ok" -> khong co oracle boolean, chi con time.
    sql = "SELECT id FROM users WHERE username='" + u + "'"
    try:
        run(sql)
    except Exception:
        pass
    return Response("ok\n", mimetype="text/plain")


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "8022"))
    app.run(host="127.0.0.1", port=port, debug=False)
