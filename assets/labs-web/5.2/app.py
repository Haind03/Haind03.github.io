#!/usr/bin/env python3
"""
Lab 5.2 - Broken Access Control / privilege escalation.

Ba kieu loi kiem quyen CO Y de hoc:

  (1) Forced browsing (duyet mo): GET /backup/users.json khong co bat ky
      kiem tra nao, chi "khong duoc link o dau". Doan dung duong dan la doc.

  (2) Tin co (role) tu client: /admin/panel chi kiem tra cookie role == admin.
      Role nam o cookie client tu sua duoc => set role=admin la vao.

  (3) Verb/flow tampering: /admin/promote kiem quyen o buoc HIEN THI form
      (GET) nhung buoc HANH DONG (POST) lai quen kiem tra => POST thang de
      tu phong minh len admin.

CHAY LOCAL, CO Y DE LOI. Khong deploy ra Internet.
"""
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)
PORT = 8051

USERS = {
    "admin": {"password": "S3cr3t-admin", "role": "admin"},
    "carol": {"password": "pw", "role": "user"},
    "dave":  {"password": "pw", "role": "user"},
}


def is_admin():
    # LO HONG (2): role lay thang tu cookie do client gui len.
    return request.cookies.get("role", "") == "admin"


@app.route("/")
def index():
    return ("Lab 5.2 broken access control. POST /login (username,password). "
            "Trang: /dashboard, /admin/panel, /admin/promote.\n")


@app.route("/login", methods=["POST"])
def login():
    u = request.form.get("username", "")
    p = request.form.get("password", "")
    acct = USERS.get(u)
    if not acct or acct["password"] != p:
        return jsonify(ok=False, error="sai dang nhap"), 401
    resp = make_response(jsonify(ok=True, user=u, role=acct["role"]))
    resp.set_cookie("user", u)
    # LO HONG (2): role duoc nhet vao cookie client, server tin tuyet doi.
    resp.set_cookie("role", acct["role"])
    return resp


@app.route("/dashboard")
def dashboard():
    user = request.cookies.get("user", "khach")
    role = request.cookies.get("role", "anonymous")
    return jsonify(ok=True, user=user, role=role,
                   can_see_admin_link=(role == "admin"))


# ---- (1) Forced browsing: khong he co kiem tra ----
@app.route("/backup/users.json")
def backup():
    # Developer "lo" de file sao luu o day, nghi khong ai biet duong dan.
    data = {u: {"role": a["role"]} for u, a in USERS.items()}
    data["_note"] = "FLAG{5.2_forced_browsing_khong_kiem_quyen}"
    return jsonify(data)


# ---- (2) Admin panel: chi dua vao cookie role ----
@app.route("/admin/panel")
def admin_panel():
    if not is_admin():
        return jsonify(ok=False, error="403 chi admin"), 403
    return jsonify(ok=True, panel="admin",
                   users=list(USERS.keys()),
                   flag="FLAG{5.2_tin_role_tu_client}")


# ---- (3) Verb/flow tampering ----
@app.route("/admin/promote", methods=["GET", "POST"])
def promote():
    if request.method == "GET":
        # Chi buoc HIEN THI form moi kiem quyen.
        if not is_admin():
            return jsonify(ok=False, error="403 chi admin"), 403
        return jsonify(ok=True, form="xac nhan phong quyen")
    # LO HONG (3): buoc HANH DONG (POST) QUEN kiem quyen.
    target = request.form.get("user", "")
    if target not in USERS:
        return jsonify(ok=False, error="khong co user"), 404
    USERS[target]["role"] = "admin"
    return jsonify(ok=True, promoted=target, new_role="admin",
                   flag="FLAG{5.2_verb_tampering_bo_qua_kiem_quyen}")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
