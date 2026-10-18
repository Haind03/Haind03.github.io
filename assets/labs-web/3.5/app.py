#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lab 3.5 - Khai thac XSS day du: trom cookie, keylogger, hanh dong thay nan nhan.
App "he thong support ticket" co stored XSS. Cong 8036, loopback.

Kich ban:
  - Nan nhan la nhan vien support, da dang nhap (cookie session + email tai khoan +
    CSRF token gan voi session).
  - Ke tan cong gui mot ticket co payload XSS trong noi dung.
  - Khi nan nhan mo hop thu ticket, payload chay trong trinh duyet nan nhan va:
      1. gui cookie ve server ke tan cong,
      2. doc CSRF token tu trang /account roi POST /change-email doi email nan nhan
         (chiem tai khoan - XSS vo hieu hoa CSRF token vi no chay ngay trong origin),
      3. cai keylogger.

Endpoint:
  GET  /login         cap cookie session + tao CSRF token cho nan nhan
  GET  /inbox         nan nhan xem tat ca ticket (render NGUYEN VAN -> stored XSS)
  POST /ticket        bat ky ai cung gui duoc ticket (noi dung luu chua escape)
  GET  /account       trang tai khoan, co email hien tai + form co CSRF token
  POST /change-email  doi email, YEU CAU CSRF token khop voi session
"""
import secrets
from flask import Flask, request, redirect, make_response, Response

app = Flask(__name__)
PORT = 8036

TICKETS = []                 # danh sach ticket: {"from":..., "message":...}
SESSIONS = {}                # session_id -> {"email":..., "csrf":...}
VICTIM_SESSION = "victim-session-5e9d2a"   # co dinh de transcript on dinh


def page(title, body):
    return ("<!doctype html><html lang=vi><head><meta charset=utf-8><title>"
            + title + "</title></head><body><h1>" + title + "</h1>" + body + "</body></html>")


@app.route("/login")
def login():
    # Gia lap nan nhan dang nhap. Tao CSRF token gan voi session.
    sid = VICTIM_SESSION
    SESSIONS[sid] = {"email": "support@corp.local", "csrf": "csrf-" + secrets.token_hex(6)}
    resp = make_response(redirect("/account"))
    resp.set_cookie("session", sid, httponly=False, samesite="Lax")
    return resp


def current_session():
    sid = request.cookies.get("session", "")
    return sid, SESSIONS.get(sid)


@app.route("/ticket", methods=["POST"])
def ticket():
    frm = request.form.get("from", "khach")
    msg = request.form.get("message", "")
    TICKETS.append({"from": frm, "message": msg})
    return redirect("/inbox")


@app.route("/inbox")
def inbox():
    rows = []
    for t in TICKETS:
        # LO HONG: message render chua escape -> stored XSS.
        rows.append("<div class=ticket><b>Tu " + t["from"] + ":</b> " + t["message"] + "</div>")
    body = "<p>Hop thu ticket (nhan vien support xem).</p>" + "\n".join(rows)
    return page("Inbox ticket", body)


@app.route("/account")
def account():
    sid, sess = current_session()
    if not sess:
        return page("Account", "<p>Chua dang nhap. Vao /login truoc.</p>")
    body = (
        "<p>Email hien tai: <span id=email>" + sess["email"] + "</span></p>"
        "<form method=post action=/change-email>"
        "<input type=hidden name=\"csrf\" value=\"" + sess["csrf"] + "\">"
        "<input name=email placeholder=\"email moi\">"
        "<button>Doi email</button>"
        "</form>"
    )
    return page("Account", body)


@app.route("/change-email", methods=["POST"])
def change_email():
    sid, sess = current_session()
    if not sess:
        return Response("chua dang nhap", status=401)
    token = request.form.get("csrf", "")
    # Bao ve CSRF: token phai khop session. Nhung XSS doc duoc token nen vo hieu.
    if token != sess["csrf"]:
        return Response("CSRF token sai", status=403)
    new_email = request.form.get("email", "")
    sess["email"] = new_email
    return Response("OK doi email thanh " + new_email)


@app.route("/")
def index():
    return page("Lab 3.5", "<p>/login, /inbox, /account, POST /ticket, POST /change-email</p>")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False)
