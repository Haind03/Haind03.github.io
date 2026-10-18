#!/usr/bin/env python3
"""
Lab 2.1 - SQL injection co ban (UNION-based + error-based)
App Flask + sqlite co 2 cho dinh SQLi:

  /login  (POST)  -> SELECT ... FROM users WHERE username='<u>' AND password='<p>'
                     noi chuoi truc tiep -> auth bypass kieu ' OR '1'='1'-- -
  /search (GET)   -> SELECT id,title,body FROM articles WHERE title LIKE '%<q>%'
                     3 cot -> UNION-based de dump bang khac (users, secret_flag)

App bat loi va tra ve thong bao loi sqlite (giong app bat debug) de minh hoa
error-based detection: sqlite bao thang "ORDER BY term out of range - should be
between 1 and N" -> doc ra so cot.

DB tao lai moi lan khoi dong (in-memory file tam). Co secret_flag chua FLAG.

Chay local, loopback, cong 8021:
    PORT=8021 python3 app.py
"""
import os
import sqlite3
from flask import Flask, request, Response

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab21.db")


def init_db():
    # Tao lai sach se moi lan khoi dong de lab tai lap duoc
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE users(
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            role TEXT
        );
        CREATE TABLE articles(
            id INTEGER PRIMARY KEY,
            title TEXT,
            body TEXT
        );
        CREATE TABLE secret_flag(
            id INTEGER PRIMARY KEY,
            name TEXT,
            value TEXT
        );
        INSERT INTO users(username,password,role) VALUES
            ('admin','S3cr3t_Admin_Pw_2024!','admin'),
            ('alice','alice_password_123','user'),
            ('bob','hunter2','user');
        INSERT INTO articles(title,body) VALUES
            ('Chao mung','Bai viet gioi thieu he thong tin tuc Acme.'),
            ('Huong dan','Cach dang ky tai khoan va dang bai.'),
            ('Thong bao bao tri','He thong bao tri luc 2h sang chu nhat.');
        INSERT INTO secret_flag(name,value) VALUES
            ('flag','WEB{un10n_select_dump_toan_bo_db}');
        """
    )
    con.commit()
    con.close()


def q(sql):
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows, None
    except Exception as e:
        return None, str(e)
    finally:
        con.close()


HOME = """<!doctype html><html lang="vi"><head><meta charset="utf-8">
<title>Acme News</title></head><body style="font-family:sans-serif;max-width:720px">
<h1>Acme News</h1>
<h2>Tim bai viet</h2>
<form action="/search" method="get">
  <input name="q" placeholder="tu khoa"><button>Tim</button>
</form>
<h2>Dang nhap</h2>
<form action="/login" method="post">
  <input name="username" placeholder="username">
  <input name="password" type="password" placeholder="password">
  <button>Dang nhap</button>
</form>
</body></html>"""


@app.route("/")
def index():
    return HOME


@app.route("/search")
def search():
    term = request.args.get("q", "")
    # LO HONG: noi chuoi thang vao cau SQL
    sql = ("SELECT id, title, body FROM articles "
           "WHERE title LIKE '%" + term + "%'")
    rows, err = q(sql)
    if err is not None:
        # App o che do debug: lo nguyen van loi sqlite (error-based)
        return Response("Loi truy van: " + err + "\n",
                        status=500, mimetype="text/plain")
    out = ["<p>SQL: <code>" + sql + "</code></p><ul>"]
    for r in rows:
        out.append("<li>[%s] %s : %s</li>" % (r[0], r[1], r[2]))
    out.append("</ul><a href='/'>ve trang chu</a>")
    return "".join(out)


@app.route("/login", methods=["POST"])
def login():
    u = request.form.get("username", "")
    p = request.form.get("password", "")
    # LO HONG: noi chuoi thang, khong tham so hoa
    sql = ("SELECT id, username, role FROM users "
           "WHERE username='" + u + "' AND password='" + p + "'")
    rows, err = q(sql)
    if err is not None:
        return Response("Loi truy van: " + err + "\n",
                        status=500, mimetype="text/plain")
    if rows:
        r = rows[0]
        return Response("Dang nhap thanh cong. id=%s username=%s role=%s\n"
                        % (r[0], r[1], r[2]), mimetype="text/plain")
    return Response("Sai tai khoan hoac mat khau\n",
                    status=401, mimetype="text/plain")


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "8021"))
    app.run(host="127.0.0.1", port=port, debug=False)
