#!/usr/bin/env python3
"""
Lab 0.2 - HTTP noi soi (HTTP inspector)
App Flask nho de nguoi doc gui request va xem lai tung phan cua HTTP:
method, header, query string, body, cookie, status code, Set-Cookie...

Chay local, chi dung de hoc. Cong loopback 8010.

    python3 app.py
    # hoac doi cong:  PORT=8010 python3 app.py
"""
import os
import json
from flask import Flask, request, jsonify, make_response, redirect, Response

app = Flask(__name__)


@app.route("/")
def index():
    html = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><title>Lab 0.2 - HTTP inspector</title></head>
<body style="font-family:sans-serif;max-width:720px;margin:2rem auto">
<h1>Lab 0.2 - HTTP noi soi</h1>
<p>Cac endpoint de thu:</p>
<ul>
  <li><code>/echo</code> - tra ve method, header, query, body, cookie duoi dang JSON</li>
  <li><code>/login</code> (POST user=admin&amp;pass=admin) - tra ve cookie session (Set-Cookie)</li>
  <li><code>/whoami</code> - doc cookie session gui len</li>
  <li><code>/redirect</code> - tra 302 ve /</li>
  <li><code>/secret</code> - 401 neu thieu header Authorization</li>
  <li><code>/teapot</code> - 418 cho vui</li>
</ul>
</body></html>"""
    resp = make_response(html)
    resp.headers["Server"] = "Lab0.2/Flask"
    return resp


@app.route("/echo", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def echo():
    """Guong phan chieu: tra lai dung nhung gi client gui len."""
    data = {
        "method": request.method,
        "path": request.path,
        "query": request.args.to_dict(flat=True),
        "headers": {k: v for k, v in request.headers.items()},
        "cookies": request.cookies.to_dict(),
        "body_raw": request.get_data(as_text=True),
        "form": request.form.to_dict(flat=True),
        "remote_addr": request.remote_addr,
    }
    return app.response_class(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        mimetype="application/json",
    )


@app.route("/login", methods=["POST"])
def login():
    user = request.form.get("user", "")
    pw = request.form.get("pass", "")
    if user == "admin" and pw == "admin":
        resp = make_response(jsonify(status="ok", msg="dang nhap thanh cong"))
        # Set-Cookie minh hoa cac attribute se hoc o bai 0.3
        resp.set_cookie("session", "s3ss10n-demo-abc123",
                        httponly=True, samesite="Lax", path="/")
        return resp
    return make_response(jsonify(status="fail", msg="sai thong tin"), 401)


@app.route("/whoami")
def whoami():
    sess = request.cookies.get("session")
    if sess == "s3ss10n-demo-abc123":
        return jsonify(user="admin", via="cookie session")
    return make_response(jsonify(user=None, msg="chua co cookie session hop le"), 401)


@app.route("/redirect")
def do_redirect():
    return redirect("/", code=302)


@app.route("/secret")
def secret():
    auth = request.headers.get("Authorization")
    if not auth:
        resp = make_response(jsonify(error="can header Authorization"), 401)
        resp.headers["WWW-Authenticate"] = 'Basic realm="lab02"'
        return resp
    return jsonify(secret="co header roi, day la noi dung bi mat", got=auth)


@app.route("/teapot")
def teapot():
    return Response("I'm a teapot\n", status=418, mimetype="text/plain")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8010"))
    # debug=False de output sach, chi lang nghe loopback
    app.run(host="127.0.0.1", port=port, debug=False)
