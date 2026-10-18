#!/usr/bin/env python3
"""
Lab 2.3 - sqlmap + vuot WAF/filter
App Flask + sqlite co lo hong SQLi, kem mot "WAF" ngay tho: chan khoang trang.

  GET  /product?id=<id>   -> SELECT id,name,price FROM products WHERE id=<id>
       (injection dang so). CO WAF: neu gia tri query co KHOANG TRANG -> 403.
       Vuot bang cach thay space bang /**/ (sqlmap --tamper=space2comment).

  POST /api/find  (code=...) -> ... WHERE code='<code>'
       (injection dang chuoi). KHONG qua WAF -> minh hoa sqlmap --data.

Muc tieu: dung sqlmap dump bang `secret` lay FLAG, qua duoc filter space.

Chay local, loopback, cong 8023:
    PORT=8023 python3 app.py
"""
import os
import sqlite3
from flask import Flask, request, Response

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab23.db")


def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE products(
            id INTEGER PRIMARY KEY,
            code TEXT,
            name TEXT,
            price INTEGER
        );
        CREATE TABLE secret(
            id INTEGER PRIMARY KEY,
            note TEXT,
            flag TEXT
        );
        INSERT INTO products(code,name,price) VALUES
            ('kb01','Ban phim co',1200000),
            ('ms02','Chuot khong day',350000),
            ('hp03','Tai nghe',550000);
        INSERT INTO secret(note,flag) VALUES
            ('co mat','WEB{sqlmap_tamper_space2comment_bypass_waf}');
        """
    )
    con.commit()
    con.close()


@app.before_request
def naive_waf():
    # WAF ngay tho: chan moi gia tri trong QUERY STRING co khoang trang.
    # (POST body khong bi soi -> /api/find khong dinh WAF)
    for v in request.args.values():
        if " " in v:
            return Response("403 WAF: phat hien khoang trang trong tham so\n",
                            status=403, mimetype="text/plain")


def run(sql):
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        cur.execute(sql)
        return cur.fetchall(), None
    except Exception as e:
        return None, str(e)
    finally:
        con.close()


@app.route("/product")
def product():
    pid = request.args.get("id", "1")
    # LO HONG: injection dang so, khong tham so hoa
    sql = "SELECT id, name, price FROM products WHERE id=" + pid
    rows, err = run(sql)
    if err is not None:
        return Response("DB error\n", status=500, mimetype="text/plain")
    if not rows:
        return Response("Khong tim thay san pham\n", mimetype="text/plain")
    out = ["<h1>San pham</h1><ul>"]
    for r in rows:
        out.append("<li>#%s %s - %s d</li>" % (r[0], r[1], r[2]))
    out.append("</ul>")
    return "".join(out)


@app.route("/api/find", methods=["POST"])
def find():
    code = request.form.get("code", "")
    # LO HONG: injection dang chuoi qua POST body
    sql = "SELECT id, name FROM products WHERE code='" + code + "'"
    rows, err = run(sql)
    if err is not None:
        return Response("DB error\n", status=500, mimetype="text/plain")
    if rows:
        return Response("San pham: %s\n" % rows[0][1], mimetype="text/plain")
    return Response("Khong tim thay\n", mimetype="text/plain")


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "8023"))
    app.run(host="127.0.0.1", port=port, debug=False)
