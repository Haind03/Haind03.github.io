#!/usr/bin/env python3
"""
Lab 4.1 - Loi authentication: username enumeration + brute force.

App co lo hong CO Y de hoc:
  - Thong bao loi khac nhau giua "user khong ton tai" va "sai mat khau"
    => username enumeration qua noi dung response.
  - Co timing difference: khi user ton tai, server moi "kiem tra mat khau"
    (gia lap bang time.sleep) => enumeration qua thoi gian phan hoi.
  - KHONG co rate limit, KHONG co lockout => brute force thoai mai.
  - Co tai khoan dung cred yeu/mac dinh.

CHAY LOCAL, CO Y DE LOI. Khong deploy ra Internet.
"""
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# "CSDL" nguoi dung. Mat khau de yeu de minh hoa brute force.
USERS = {
    "admin": "Password123",
    "john.doe": "letmein",
    "alice": "sunshine",
}

PORT = 8041


def check_password(username: str, password: str) -> bool:
    # Gia lap chi phi hash mat khau: CHI chay khi username ton tai.
    # Day la nguyen nhan tao ra timing side-channel.
    time.sleep(0.12)
    return USERS.get(username) == password


@app.route("/")
def index():
    return (
        "Lab 4.1 login. POST /login voi form username, password.\n"
        "Thu: curl -s -X POST localhost:%d/login -d username=admin -d password=x\n"
        % PORT
    )


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # LO HONG 1: thong bao loi khac nhau -> enumeration qua noi dung.
    if username not in USERS:
        return jsonify(ok=False, error="Unknown user"), 401

    # LO HONG 2: chi khi user ton tai moi ton chi phi kiem tra mat khau
    # -> enumeration qua timing.
    if check_password(username, password):
        return jsonify(ok=True, message="Welcome %s" % username,
                       flag="FLAG{4.1_brute_force_no_rate_limit}"), 200

    return jsonify(ok=False, error="Invalid password"), 401


if __name__ == "__main__":
    # Chi bind loopback.
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
