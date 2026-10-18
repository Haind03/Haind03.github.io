#!/usr/bin/env python3
"""
Lab 4.4 - OAuth2 client (relying party) toi gian, CO Y de lo hong.

Lo hong:
  - /login KHONG sinh tham so `state` => khong chong CSRF luong dang nhap.
  - /callback KHONG kiem tra `state` => chap nhan code tuy y (login CSRF).

CHAY LOCAL.
"""
import requests
from flask import Flask, request, jsonify, redirect

app = Flask(__name__)
PORT = 8045

PROVIDER = "http://localhost:8044"
CLIENT_ID = "portal"
CLIENT_SECRET = "portal-secret"
REDIRECT_URI = "http://localhost:8045/callback"

SESSIONS = {}  # chi de demo


@app.route("/")
def index():
    return "Lab 4.4 OAuth client (portal) on :8045. Vao /login de bat dau SSO.\n"


@app.route("/login")
def login():
    # LO HONG: khong co `state` trong request authorize.
    url = ("%s/authorize?response_type=code&client_id=%s&redirect_uri=%s"
           % (PROVIDER, CLIENT_ID, REDIRECT_URI))
    return redirect(url, code=302)


@app.route("/callback")
def callback():
    code = request.args.get("code", "")
    state = request.args.get("state", "")  # LO HONG: nhan nhung khong kiem tra
    if not code:
        return jsonify(ok=False, error="no code"), 400

    # Doi code lay token tai provider.
    r = requests.post("%s/token" % PROVIDER, data={
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
    })
    tj = r.json()
    if not tj.get("ok"):
        return jsonify(ok=False, error="token exchange failed", detail=tj), 400

    at = tj["access_token"]
    ui = requests.get("%s/userinfo" % PROVIDER,
                      headers={"Authorization": "Bearer %s" % at}).json()
    return jsonify(ok=True, logged_in_as=ui.get("user"),
                   email=ui.get("email"), state_seen=state,
                   note="client khong kiem state -> code nao cung nhan")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
