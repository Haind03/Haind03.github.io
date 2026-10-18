#!/usr/bin/env python3
"""
Lab 1.3 - Content discovery
App Flask co vai route "an": khong co link nao tro toi, chi tim ra bang
cach brute-force duong dan (ffuf / gobuster / curl + wordlist).

Trang chu chi cho thay / va /about. Con lai la route an de ban tu do ra:
    /admin        -> trang quan tri (an)
    /backup       -> lo file cau hinh
    /.git/config  -> lo thu muc .git (kinh dien)
    /api/v1/users -> endpoint API khong duoc public
    /old          -> trang cu con sot lai

Chay local, cong loopback 8011.

    python3 app.py
"""
import os
from flask import Flask, jsonify, Response, abort

app = Flask(__name__)

PAGE = """<!doctype html><html lang="vi"><head><meta charset="utf-8">
<title>Acme Corp</title></head><body style="font-family:sans-serif">
<h1>Acme Corp</h1><p>{body}</p>
<nav><a href="/">Trang chu</a> | <a href="/about">Gioi thieu</a></nav>
</body></html>"""


@app.route("/")
def index():
    return PAGE.format(body="Chao mung den Acme Corp. Khong co gi de xem o day ca.")


@app.route("/about")
def about():
    return PAGE.format(body="Acme Corp thanh lap nam 2009. Chung toi ban moi thu.")


# ---- Cac route "an" (khong co link tro toi) ----

@app.route("/admin")
def admin():
    return PAGE.format(body="[ADMIN] Bang dieu khien quan tri. Dang le khong duoc public!")


@app.route("/backup")
def backup():
    body = ("# config.bak - lo ra ngoai\n"
            "DB_HOST=127.0.0.1\n"
            "DB_USER=acme\n"
            "DB_PASS=sup3r-s3cr3t-pw\n"
            "FLAG=WEB{content_discovery_tim_ra_backup}\n")
    return Response(body, mimetype="text/plain")


@app.route("/.git/config")
def git_config():
    body = ("[core]\n\trepositoryformatversion = 0\n"
            "[remote \"origin\"]\n"
            "\turl = https://github.com/acme/internal-site.git\n")
    return Response(body, mimetype="text/plain")


@app.route("/api/v1/users")
def api_users():
    return jsonify([
        {"id": 1, "user": "admin", "role": "superuser"},
        {"id": 2, "user": "alice", "role": "staff"},
    ])


@app.route("/old")
def old():
    return PAGE.format(body="[TRANG CU] Phien ban 2012, quen chua go. Co the con lo hong.")


# Cac duong dan khong ton tai tra 404 that su de brute-force phan biet duoc
@app.errorhandler(404)
def not_found(e):
    return Response("Not Found\n", status=404, mimetype="text/plain")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8011"))
    app.run(host="127.0.0.1", port=port, debug=False)
