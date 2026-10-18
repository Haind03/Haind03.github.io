#!/usr/bin/env python3
"""
Lab 4.4 - OAuth2 provider (IdP) toi gian, CO Y de lo hong.

Luong: authorization code grant.
Lo hong chinh:
  - /authorize KHONG kiem redirect_uri theo allowlist dang ky (chi can client_id ton tai).
    => attacker dat redirect_uri tro ve server cua minh, lay cap authorization code.

CHAY LOCAL, CO Y DE LOI.
"""
import secrets

from flask import Flask, request, jsonify, redirect

app = Flask(__name__)
PORT = 8044

# Client da dang ky. redirect_uri dung LE RA phai la allowlist khop chinh xac.
CLIENTS = {
    "portal": {
        "secret": "portal-secret",           # trong SPA thuong la public
        "redirect_uri": "http://localhost:8045/callback",  # gia tri da dang ky
    }
}

# Resource owner (nguoi dung cuoi). carol la "victim" da dang nhap IdP.
OWNERS = {
    "carol": {"email": "carol@corp.local", "flag": "FLAG{4.4_oauth_code_theft}"},
}

CODES = {}    # code -> {user, client_id, redirect_uri}
TOKENS = {}   # access_token -> user


@app.route("/")
def index():
    return "Lab 4.4 OAuth provider (IdP) on :8044\n"


@app.route("/pv-login", methods=["POST"])
def pv_login():
    # Gia lap: victim dang nhap vao IdP, nhan session SSO (nhu dang nhap Google).
    user = request.form.get("user", "")
    if user not in OWNERS:
        return jsonify(ok=False, error="unknown owner"), 401
    resp = jsonify(ok=True, user=user)
    resp.set_cookie("pv_session", user)
    return resp


@app.route("/authorize")
def authorize():
    client_id = request.args.get("client_id", "")
    redirect_uri = request.args.get("redirect_uri", "")
    state = request.args.get("state", "")

    if client_id not in CLIENTS:
        return jsonify(ok=False, error="unknown client"), 400

    # Victim phai dang co session SSO o IdP.
    user = request.cookies.get("pv_session", "")
    if user not in OWNERS:
        return jsonify(ok=False, error="user not authenticated at IdP"), 401

    # LO HONG: KHONG so sanh redirect_uri voi gia tri da dang ky.
    # Dung ra phai: if redirect_uri != CLIENTS[client_id]["redirect_uri"]: reject
    code = secrets.token_hex(8)
    CODES[code] = {"user": user, "client_id": client_id, "redirect_uri": redirect_uri}

    sep = "&" if "?" in redirect_uri else "?"
    location = "%s%scode=%s" % (redirect_uri, sep, code)
    if state:
        location += "&state=%s" % state
    return redirect(location, code=302)


@app.route("/token", methods=["POST"])
def token():
    grant = request.form.get("grant_type", "")
    code = request.form.get("code", "")
    client_id = request.form.get("client_id", "")
    redirect_uri = request.form.get("redirect_uri", "")
    client_secret = request.form.get("client_secret", "")

    if grant != "authorization_code":
        return jsonify(ok=False, error="unsupported grant"), 400
    rec = CODES.get(code)
    if not rec or rec["client_id"] != client_id:
        return jsonify(ok=False, error="bad code"), 400
    if CLIENTS[client_id]["secret"] != client_secret:
        return jsonify(ok=False, error="bad client secret"), 401
    if rec["redirect_uri"] != redirect_uri:
        return jsonify(ok=False, error="redirect_uri mismatch"), 400

    del CODES[code]  # code dung mot lan
    at = secrets.token_hex(12)
    TOKENS[at] = rec["user"]
    return jsonify(ok=True, access_token=at, token_type="Bearer")


@app.route("/userinfo")
def userinfo():
    auth = request.headers.get("Authorization", "")
    at = auth[len("Bearer "):].strip() if auth.startswith("Bearer ") else ""
    user = TOKENS.get(at)
    if not user:
        return jsonify(ok=False, error="bad token"), 401
    prof = OWNERS[user]
    return jsonify(ok=True, user=user, email=prof["email"], flag=prof["flag"])


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
