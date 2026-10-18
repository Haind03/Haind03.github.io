#!/usr/bin/env python3
"""
Lab 4.3 - Tan cong JWT.

App phat JWT khi login va kiem token o /admin. Bo verify CO Y de lo hong:
  - Chap nhan alg=none (khong chu ky) => forge token tuy y.
  - HS256 voi secret yeu ("secret") => brute/crack roi ky lai token admin.
  - Header "kid" duoc dung lam DUONG DAN FILE de doc key (kid injection path traversal)
    => tro kid toi /dev/null de ep key rong roi tu ky.

Day la verifier tu viet (hand-rolled) de cac lo hong that su ton tai, khong phu
thuoc vao default an toan cua thu vien. CHAY LOCAL, CO Y DE LOI.
"""
import base64
import hashlib
import hmac
import json

from flask import Flask, request, jsonify

app = Flask(__name__)
PORT = 8043

SECRET = "secret"  # LO HONG: secret yeu, nam trong moi wordlist.

USERS = {"wiener": "peter", "admin": "hunter2"}


def b64url_decode(s: str) -> bytes:
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)


def b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def sign_hs256(signing_input: bytes, key: bytes) -> bytes:
    return hmac.new(key, signing_input, hashlib.sha256).digest()


def make_token(payload: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    h = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    p = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = ("%s.%s" % (h, p)).encode()
    sig = sign_hs256(signing_input, SECRET.encode())
    return "%s.%s.%s" % (h, p, b64url_encode(sig))


def verify_token(token: str):
    """Verifier CO LO HONG. Tra payload neu 'hop le', raise neu khong."""
    h, p, s = token.split(".")
    header = json.loads(b64url_decode(h))
    payload = json.loads(b64url_decode(p))
    alg = header.get("alg", "")

    # LO HONG 1: alg=none duoc chap nhan, bo qua chu ky.
    if alg.lower() == "none":
        return payload

    if alg == "HS256":
        # LO HONG 2 (kid injection): neu co kid, dung lam duong dan file de lay key.
        kid = header.get("kid")
        if kid is not None:
            with open(kid, "rb") as f:
                key = f.read()
        else:
            key = SECRET.encode()  # LO HONG 3: secret yeu
        expected = sign_hs256(("%s.%s" % (h, p)).encode(), key)
        if hmac.compare_digest(expected, b64url_decode(s)):
            return payload
        raise ValueError("bad signature")

    raise ValueError("unsupported alg: %s" % alg)


@app.route("/")
def index():
    return "Lab 4.3 JWT. POST /login (username,password) -> JWT. GET /admin (Bearer token).\n"


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    if USERS.get(username) != password:
        return jsonify(ok=False, error="bad creds"), 401
    role = "admin" if username == "admin" else "user"
    token = make_token({"user": username, "role": role})
    return jsonify(ok=True, token=token)


@app.route("/admin")
def admin():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify(ok=False, error="no token"), 401
    token = auth[len("Bearer "):].strip()
    try:
        payload = verify_token(token)
    except Exception as e:  # noqa: BLE001
        return jsonify(ok=False, error="invalid token: %s" % e), 401
    if payload.get("role") != "admin":
        return jsonify(ok=False, error="not admin", you=payload), 403
    return jsonify(ok=True, user=payload.get("user"),
                   flag="FLAG{4.3_jwt_forged_admin}")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
