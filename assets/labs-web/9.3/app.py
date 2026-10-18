#!/usr/bin/env python3
"""
Lab 9.3 - CORS cau hinh sai (victim app).

App co lo hong CO Y de hoc:
  - PHAN HOI CORS theo kieu REFLECT: lay nguyen gia tri header Origin cua
    request dat vao Access-Control-Allow-Origin, DONG THOI bat
    Access-Control-Allow-Credentials: true.
    => bat ky origin nao (ke ca https://evil.example) cung duoc trinh duyet
       cho phep DOC response kem cookie cua nan nhan.
  - Chap nhan ca Origin: null (iframe sandbox, redirect, file://).
  - /api/account la du lieu nhay cam, xac thuc bang COOKIE session.

CHAY LOCAL, CO Y DE LOI. Khong deploy ra Internet.
"""
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)
PORT = 8073

SESSIONS = {}  # session_id -> username
ACCOUNT = {
    "alice": {
        "username": "alice",
        "email": "alice@bank.local",
        "balance": "120,000,000 VND",
        "api_token": "FLAG{9.3_cors_reflect_origin_with_credentials}",
    }
}


@app.after_request
def add_cors(resp):
    origin = request.headers.get("Origin")
    if origin is not None:
        # LO HONG: reflect nguyen Origin + cho phep credentials.
        # Dung ra chi duoc whitelist mot vai origin tin cay, hoac
        # neu ACAO = * thi TUYET DOI khong duoc kem credentials.
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Vary"] = "Origin"
    return resp


@app.route("/login", methods=["POST"])
def login():
    # Gia lap dang nhap, cap cookie session cho nan nhan.
    data = request.get_json(silent=True) or request.form
    username = data.get("username", "alice")
    sid = "sess-%s-abc123" % username
    SESSIONS[sid] = username
    resp = make_response(jsonify(ok=True, user=username))
    # Cookie khong SameSite=Strict => van gui kem khi fetch tu origin khac.
    resp.set_cookie("session", sid, httponly=True, samesite="None", secure=False)
    return resp


@app.route("/api/account")
def account():
    sid = request.cookies.get("session", "")
    username = SESSIONS.get(sid)
    if not username:
        return jsonify(error="unauthorized"), 401
    return jsonify(ACCOUNT.get(username, {}))


@app.route("/")
def index():
    return "Lab 9.3 CORS victim. POST /login roi GET /api/account (can cookie session).\n"


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
