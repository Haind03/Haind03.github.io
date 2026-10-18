#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lab 3.2 - Stored XSS: bang comment luu payload chua escape.
Chi chay local, cong 8032.

- GET  /            : trang comment, render tat ca comment chua escape (LO HONG).
- POST /comment     : luu comment moi (text).
- GET  /login       : cap cho "nan nhan" mot cookie session (gia lap da dang nhap).
- Cookie session co co HttpOnly=False de minh ho XSS doc duoc (vi du xau that ngoai
  doi). Neu HttpOnly=True thi document.cookie khong doc duoc cookie nay; o day ta
  co y tat de day la kich ban "cookie khong co HttpOnly".
"""
from flask import Flask, request, redirect, make_response

app = Flask(__name__)
PORT = 8032

# "CSDL" trong bo nho: danh sach comment.
COMMENTS = [
    {"user": "admin", "text": "Chao mung den bang tin noi bo!"},
]

PAGE = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><title>Bang comment noi bo</title></head>
<body>
<h1>Bang comment noi bo</h1>
<p>Trang nay render comment truc tiep, khong escape.</p>
<form method="post" action="/comment">
  <input name="user" placeholder="ten" value="khach">
  <input name="text" placeholder="noi gi do" size="60">
  <button>Gui</button>
</form>
<hr>
<div id="comments">
{comments}
</div>
</body></html>"""


def render_comments():
    rows = []
    for c in COMMENTS:
        # LO HONG: text nhet thang vao HTML, khong escape.
        rows.append("<div class=comment><b>" + c["user"] + "</b>: " + c["text"] + "</div>")
    return "\n".join(rows)


@app.route("/")
def index():
    return PAGE.format(comments=render_comments())


@app.route("/comment", methods=["POST"])
def comment():
    user = request.form.get("user", "khach")
    text = request.form.get("text", "")
    COMMENTS.append({"user": user, "text": text})
    return redirect("/")


@app.route("/login")
def login():
    # Gia lap nan nhan dang nhap: cap cookie session.
    # httponly=False co y de minh ho kich ban cookie doc duoc tu JS.
    resp = make_response(redirect("/"))
    resp.set_cookie("session", "victim-session-7f3a9c2b1e", httponly=False, samesite="Lax")
    return resp


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False)
