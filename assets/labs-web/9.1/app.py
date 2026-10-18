#!/usr/bin/env python3
"""
Lab 9.1 - REST API security: BOLA + BFLA + lo field + khong rate limit.

App co lo hong CO Y de hoc:
  - BOLA (Broken Object Level Authorization / IDOR cap object):
    GET /api/users/<id> chi kiem tra token HOP LE, KHONG kiem tra token
    co thuoc ve dung <id> hay khong => doc duoc object cua nguoi khac.
  - Lo field (excessive data exposure): tra ca ssn, card, secret_note
    thay vi chi field can thiet.
  - BFLA (Broken Function Level Authorization):
    POST /api/admin/promote chi can dang nhap (co token), KHONG kiem tra
    role = admin => user thuong goi duoc ham cua admin.
  - Khong co rate limit tren /api/login => brute force thoai mai.

CHAY LOCAL, CO Y DE LOI. Khong deploy ra Internet.
"""
from flask import Flask, request, jsonify

app = Flask(__name__)
PORT = 8071

# "CSDL" nguoi dung. token = bearer token cap sau khi dang nhap.
USERS = {
    1: {
        "id": 1, "username": "alice", "password": "alice123", "role": "user",
        "token": "tok-alice-111", "email": "alice@shop.local",
        "ssn": "001-11-1111", "card": "4111-1111-1111-1111",
        "secret_note": "ghi chu rieng cua alice",
    },
    2: {
        "id": 2, "username": "bob", "password": "bob123", "role": "user",
        "token": "tok-bob-222", "email": "bob@shop.local",
        "ssn": "002-22-2222", "card": "5500-0000-0000-0004",
        "secret_note": "FLAG{9.1_bola_read_other_users_object}",
    },
    9: {
        "id": 9, "username": "admin", "password": "S3cr3tAdminPw", "role": "admin",
        "token": "tok-admin-999", "email": "admin@shop.local",
        "ssn": "999-99-9999", "card": "0000-0000-0000-0000",
        "secret_note": "quan tri he thong",
    },
}

TOKEN_INDEX = {u["token"]: u for u in USERS.values()}


def current_user():
    """Lay user tu bearer token. CHI xac thuc (authentication),
    KHONG lam authorization theo object."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return TOKEN_INDEX.get(auth[len("Bearer "):])


@app.route("/")
def index():
    return (
        "Lab 9.1 REST API.\n"
        "POST /api/login {username,password} -> token\n"
        "GET  /api/users/<id>            (Bearer token) -> ho so\n"
        "GET  /api/users/<id>/orders     (Bearer token) -> don hang\n"
        "POST /api/admin/promote {user_id} (Bearer token) -> nang quyen\n"
    )


@app.route("/api/login", methods=["POST"])
def login():
    # LO HONG: khong co rate limit / lockout.
    data = request.get_json(silent=True) or request.form
    username = data.get("username", "")
    password = data.get("password", "")
    for u in USERS.values():
        if u["username"] == username and u["password"] == password:
            return jsonify(ok=True, token=u["token"], user_id=u["id"],
                           role=u["role"])
    return jsonify(ok=False, error="invalid credentials"), 401


@app.route("/api/users/<int:user_id>")
def get_user(user_id):
    me = current_user()
    if me is None:
        return jsonify(error="unauthorized"), 401
    # LO HONG BOLA: KHONG kiem tra me["id"] == user_id.
    # Chi can co token hop le la doc duoc BAT KY object nao.
    target = USERS.get(user_id)
    if target is None:
        return jsonify(error="not found"), 404
    # LO HONG lo field: tra het ca ssn, card, secret_note.
    return jsonify({k: v for k, v in target.items() if k != "password"})


@app.route("/api/users/<int:user_id>/orders")
def get_orders(user_id):
    me = current_user()
    if me is None:
        return jsonify(error="unauthorized"), 401
    # Cung dinh BOLA: khong rang buoc chu so huu.
    demo = {
        1: [{"order": "A-1001", "total": 120000}],
        2: [{"order": "B-2002", "total": 9900000, "note": "don hang VIP cua bob"}],
        9: [{"order": "Z-9009", "total": 1}],
    }
    return jsonify(user_id=user_id, orders=demo.get(user_id, []))


@app.route("/api/admin/promote", methods=["POST"])
def admin_promote():
    me = current_user()
    if me is None:
        return jsonify(error="unauthorized"), 401
    # LO HONG BFLA: chi kiem tra "da dang nhap", KHONG kiem tra role == admin.
    data = request.get_json(silent=True) or request.form
    target_id = int(data.get("user_id", 0))
    target = USERS.get(target_id)
    if target is None:
        return jsonify(error="not found"), 404
    target["role"] = "admin"
    return jsonify(ok=True, message="user %d da thanh admin" % target_id,
                   promoted_by=me["username"],
                   flag="FLAG{9.1_bfla_function_level_bypass}")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
