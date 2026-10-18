#!/usr/bin/env python3
"""
Lab 4.5 - Password reset yeu + bypass MFA.

Lo hong CO Y:
  - Reset token DOAN DUOC: token = md5(email + pepper co dinh)[:12], suy ra offline
    neu biet email victim (khong ngau nhien).
  - Host header poisoning: link reset dung thang Host header cua request => attacker
    ep link tro ve domain cua minh, token ro ri khi victim bam.
  - MFA: /mfa/account KHONG kiem buoc MFA da hoan tat (chi can qua password) => bypass.
  - OTP 4 chu so, KHONG rate limit => brute force.

CHAY LOCAL, CO Y DE LOI.
"""
import hashlib
import random

from flask import Flask, request, jsonify

app = Flask(__name__)
PORT = 8046

PEPPER = "pepper2024"  # co dinh, nen token suy ra duoc

USERS = {
    "ceo@corp.local": {"password": "OnlyCeoKnows!", "flag_account": "FLAG{4.5_reset_token_predictable}"},
    "bob@corp.local": {"password": "bobpass", "otp": None,
                       "flag_mfa": "FLAG{4.5_mfa_bypassed}"},
}

RESET_TOKENS = {}   # token -> email
MFA_PARTIAL = {}    # mfa_token -> email (da qua password, chua qua MFA)


def reset_token_for(email: str) -> str:
    # LO HONG: token deterministic tu email, khong random.
    return hashlib.md5((email + PEPPER).encode()).hexdigest()[:12]


@app.route("/")
def index():
    return "Lab 4.5 reset+MFA on :8046\n"


@app.route("/forgot", methods=["POST"])
def forgot():
    email = request.form.get("email", "")
    if email not in USERS:
        # Tra giong nhau de khong enumerate, nhung token van yeu.
        return jsonify(ok=True, note="neu email ton tai, link da duoc gui")
    token = reset_token_for(email)
    RESET_TOKENS[token] = email
    # LO HONG: xay link tu Host header do client gui.
    host = request.host
    reset_link = "http://%s/reset?token=%s" % (host, token)
    # Trong thuc te link nay di qua email; o lab ta tra ve de quan sat.
    return jsonify(ok=True, email=email, reset_link=reset_link)


@app.route("/reset", methods=["POST"])
def reset():
    token = request.form.get("token", "") or request.args.get("token", "")
    new_password = request.form.get("new_password", "")
    email = RESET_TOKENS.get(token)
    if not email:
        return jsonify(ok=False, error="invalid token"), 400
    USERS[email]["password"] = new_password
    del RESET_TOKENS[token]
    return jsonify(ok=True, email=email, message="password changed",
                   flag=USERS[email].get("flag_account"))


# ---- MFA flow ----
@app.route("/mfa/login", methods=["POST"])
def mfa_login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    u = USERS.get(username)
    if not u or u["password"] != password:
        return jsonify(ok=False, error="bad creds"), 401
    # Sinh OTP 4 chu so, "gui" ra ngoai (o lab khong lo ra).
    otp = "%04d" % random.randint(0, 9999)
    u["otp"] = otp
    mfa_token = hashlib.md5((username + "mfa").encode()).hexdigest()[:10]
    MFA_PARTIAL[mfa_token] = username
    return jsonify(ok=True, stage="mfa_required", mfa_token=mfa_token)


@app.route("/mfa/verify", methods=["POST"])
def mfa_verify():
    mfa_token = request.form.get("mfa_token", "")
    otp = request.form.get("otp", "")
    username = MFA_PARTIAL.get(mfa_token)
    if not username:
        return jsonify(ok=False, error="no partial session"), 401
    # LO HONG: khong rate limit, khong gioi han so lan sai -> brute 0000..9999.
    if otp == USERS[username]["otp"]:
        return jsonify(ok=True, stage="authenticated",
                       flag=USERS[username].get("flag_mfa"))
    return jsonify(ok=False, error="wrong otp"), 401


@app.route("/mfa/account")
def mfa_account():
    # LO HONG: chi kiem da co partial session (qua password), KHONG kiem MFA xong.
    mfa_token = request.args.get("mfa_token", "")
    username = MFA_PARTIAL.get(mfa_token)
    if not username:
        return jsonify(ok=False, error="not logged in"), 401
    return jsonify(ok=True, user=username,
                   flag=USERS[username].get("flag_mfa"),
                   note="truy cap duoc ma khong can nhap OTP")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
