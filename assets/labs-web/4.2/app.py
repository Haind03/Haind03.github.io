#!/usr/bin/env python3
"""
Lab 4.2 - Session management: token doan duoc + fixation + cookie thieu co +
khong huy session khi logout.

Lo hong CO Y:
  - Session id cap TUAN TU (0x1000, 0x1001, ...) => doan duoc token cua nguoi khac.
  - Chap nhan session id do CLIENT dua vao (cookie hoac ?sid=) truoc khi login va
    GIU NGUYEN sau khi login => session fixation (khong regenerate sau xac thuc).
  - Set-Cookie KHONG co HttpOnly / Secure / SameSite => cookie de bi JS doc / gui cross-site.
  - /logout chi xoa cookie o client, KHONG xoa session o server => token cu van dung duoc.

CHAY LOCAL, CO Y DE LOI.
"""
import threading
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)
PORT = 8042

# "CSDL" nguoi dung.
USERS = {"mallory": "mallory", "admin": "S3cretAdminPw"}

# Session store phia server: token -> username.
SESSIONS = {}
_lock = threading.Lock()
_counter = 0x1000  # bo dem tuan tu -> token doan duoc


def new_token():
    # LO HONG: token tuan tu, khong ngau nhien.
    global _counter
    with _lock:
        tok = "%08x" % _counter
        _counter += 1
    return tok


def set_session_cookie(resp, token):
    # LO HONG: khong HttpOnly, khong Secure, khong SameSite.
    resp.set_cookie("SESSIONID", token)
    return resp


@app.route("/")
def index():
    return "Lab 4.2 session. POST /login (username,password). GET /me. POST /logout.\n"


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    if USERS.get(username) != password:
        return jsonify(ok=False, error="bad creds"), 401

    # LO HONG fixation: neu client da mang san session id thi DUNG LAI,
    # khong cap token moi sau khi xac thuc.
    supplied = request.args.get("sid") or request.cookies.get("SESSIONID")
    if supplied:
        token = supplied
    else:
        token = new_token()

    with _lock:
        SESSIONS[token] = username

    resp = make_response(jsonify(ok=True, user=username, token=token))
    return set_session_cookie(resp, token)


@app.route("/me")
def me():
    token = request.cookies.get("SESSIONID") or request.args.get("sid", "")
    user = SESSIONS.get(token)
    if not user:
        return jsonify(ok=False, error="no session"), 401
    data = dict(ok=True, user=user, token=token)
    if user == "admin":
        data["flag"] = "FLAG{4.2_weak_session_hijack}"
    return jsonify(data)


@app.route("/logout", methods=["POST"])
def logout():
    # LO HONG: chi bao client xoa cookie, KHONG remove session o server.
    resp = make_response(jsonify(ok=True, note="client cookie cleared"))
    resp.delete_cookie("SESSIONID")
    return resp


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
