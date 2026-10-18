#!/usr/bin/env python3
"""
Lab 2.4 - NoSQL injection (kieu MongoDB) + auth bypass
App Flask mo phong tang luu tru Mongo bang mongomock (API giong pymongo).

Lo hong: lay truc tiep gia tri nguoi dung nhet vao query find_one():
    users.find_one({"username": <u>, "password": <p>})
Neu <u>/<p> la DICT toan tu ($ne, $gt, $regex...) thay vi chuoi, logic so khop
bi lat nguoc -> auth bypass, hoac trich mat khau tung ky tu bang $regex.

Hai dang dau vao:
  POST /login  (JSON)         : body {"username":..,"password":..}. Neu gui
                                {"$ne": null} thi vao thang query.
  GET  /login  (query string) : ho tro cu phap ngoac kieu framework PHP/Express:
                                ?username=admin&password[$ne]=x  ->  {"$ne":"x"}

Neu dang nhap duoc thanh admin -> tra FLAG.

Yeu cau: pip install flask mongomock
(Neu khong co mongomock, xem bien MOCK ben duoi: ta co san ban mo phong $ne/
 $gt/$regex bang Python thuan de lab van chay.)

Chay local, loopback, cong 8024:
    PORT=8024 python3 app.py
"""
import os
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

FLAG = "WEB{nosql_operator_injection_auth_bypass}"

USERS = [
    {"username": "admin", "password": "Adm1nSecret2024", "role": "admin"},
    {"username": "alice", "password": "alice_pw", "role": "user"},
    {"username": "bob", "password": "bob_pw", "role": "user"},
]

# --- Tang luu tru: dung mongomock neu co, neu khong thi mo phong toan tu ---
USING_MONGOMOCK = False
try:
    import mongomock
    _col = mongomock.MongoClient().db.users
    _col.insert_many([dict(u) for u in USERS])
    USING_MONGOMOCK = True

    def find_one(query):
        return _col.find_one(query)

except ImportError:
    # Mo phong toi thieu cac toan tu Mongo bang Python thuan (noi ro trong README)
    def _match_field(cond, value):
        if isinstance(cond, dict):
            for op, operand in cond.items():
                if op == "$ne":
                    if value == operand:
                        return False
                elif op == "$eq":
                    if value != operand:
                        return False
                elif op == "$gt":
                    if not (value > operand):
                        return False
                elif op == "$regex":
                    if value is None or re.search(operand, value) is None:
                        return False
                elif op == "$in":
                    if value not in operand:
                        return False
                else:
                    return False
            return True
        return value == cond

    def find_one(query):
        for doc in USERS:
            if all(_match_field(cond, doc.get(field))
                   for field, cond in query.items()):
                return doc
        return None


def parse_bracket_args(args):
    # ?username=admin&password[$ne]=x  ->  {"username":"admin","password":{"$ne":"x"}}
    out = {}
    for key in args:
        m = re.match(r"^([^\[]+)\[(\$[a-zA-Z]+)\]$", key)
        if m:
            out.setdefault(m.group(1), {})[m.group(2)] = args.get(key)
        else:
            out[key] = args.get(key)
    return out


def do_login(username, password):
    # LO HONG: nhet thang gia tri (co the la dict toan tu) vao query
    query = {"username": username, "password": password}
    doc = find_one(query)
    if doc:
        resp = {"ok": True, "username": doc["username"], "role": doc["role"]}
        if doc["role"] == "admin":
            resp["flag"] = FLAG
        return jsonify(resp)
    return jsonify({"ok": False, "msg": "sai tai khoan hoac mat khau"}), 401


@app.route("/login", methods=["POST"])
def login_post():
    data = request.get_json(force=True, silent=True) or {}
    return do_login(data.get("username"), data.get("password"))


@app.route("/login", methods=["GET"])
def login_get():
    parsed = parse_bracket_args(request.args)
    return do_login(parsed.get("username"), parsed.get("password"))


@app.route("/")
def index():
    return jsonify({
        "info": "POST /login JSON hoac GET /login query-string",
        "backend": "mongomock" if USING_MONGOMOCK else "python-mo-phong",
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8024"))
    app.run(host="127.0.0.1", port=port, debug=False)
