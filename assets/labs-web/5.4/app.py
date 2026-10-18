#!/usr/bin/env python3
"""
Lab 5.4 - Mass assignment / parameter tampering.

Chuc nang cap nhat profile nhan NGUYEN body JSON va gan het vao object user:

    for k, v in data.items():
        user[k] = v        # <-- gan hang loat, khong loc truong

Nguoi dung chi duoc phep sua email/bio, nhung vi gan het nen gui kem
isAdmin=true, balance=..., role=admin la tu nang quyen / sua so du.

CHAY LOCAL, CO Y DE LOI. Khong deploy ra Internet.
"""
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)
PORT = 8053

USERS = {
    "eve": {"password": "pw", "email": "eve@shop.local", "bio": "khach moi",
            "isAdmin": False, "balance": 0, "role": "user"},
    "admin": {"password": "root", "email": "admin@shop.local", "bio": "boss",
              "isAdmin": True, "balance": 999999, "role": "admin"},
}

# Truong NGUOI DUNG duoc phep tu sua (dung ra phai chi cho phep nhung truong nay).
ALLOWED = {"email", "bio"}


def current_user():
    u = request.cookies.get("auth", "")
    return u if u in USERS else None


@app.route("/")
def index():
    return ("Lab 5.4 mass assignment. POST /login. "
            "GET/POST /api/profile (JSON). GET /admin.\n")


@app.route("/login", methods=["POST"])
def login():
    u = request.form.get("username", "")
    p = request.form.get("password", "")
    if USERS.get(u, {}).get("password") != p:
        return jsonify(ok=False, error="sai dang nhap"), 401
    resp = make_response(jsonify(ok=True, user=u))
    resp.set_cookie("auth", u, httponly=True, samesite="Lax")
    return resp


@app.route("/api/profile", methods=["GET", "POST"])
def profile():
    u = current_user()
    if not u:
        return jsonify(ok=False, error="chua dang nhap"), 401
    user = USERS[u]
    if request.method == "GET":
        safe = {k: v for k, v in user.items() if k != "password"}
        return jsonify(ok=True, **safe)

    data = request.get_json(force=True, silent=True) or {}
    # LO HONG: gan het cac truong client gui vao user, khong loc theo ALLOWED.
    for k, v in data.items():
        if k == "password":
            continue  # chi "tranh" doi mat khau, van sot isAdmin/balance/role
        user[k] = v
    safe = {k: v for k, v in user.items() if k != "password"}
    return jsonify(ok=True, updated=list(data.keys()), **safe)


@app.route("/admin")
def admin():
    u = current_user()
    if not u:
        return jsonify(ok=False, error="chua dang nhap"), 401
    # Quyen admin suy ra tu truong isAdmin cua user (da bi mass assignment sua).
    if not USERS[u].get("isAdmin"):
        return jsonify(ok=False, error="403 chi admin"), 403
    return jsonify(ok=True, panel="admin",
                   balance=USERS[u]["balance"],
                   flag="FLAG{5.4_mass_assignment_isAdmin_true}")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
