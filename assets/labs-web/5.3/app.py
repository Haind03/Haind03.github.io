#!/usr/bin/env python3
"""
Lab 5.3 - CSRF (Cross-Site Request Forgery).

App "tai khoan" co chuc nang doi email.

  - POST /change-email: CO LOI. Doi email chi dua vao cookie phien, KHONG co
    CSRF token. Cookie phien lai dat SameSite=None (cau hinh de bi khai thac)
    nen trinh duyet se kem cookie theo request cross-site => CSRF chay duoc.

  - POST /change-email-safe: ban va. Bat buoc co csrf_token khop voi token
    luu trong phien. Trang attacker khong doc duoc token nay (same-origin
    policy) nen khong gia mao duoc.

CHAY LOCAL, CO Y DE LOI. Khong deploy ra Internet.
"""
import secrets
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)
PORT = 8052

USERS = {"victim": "pw"}
# sid -> {"user":..., "email":..., "csrf":...}
SESSIONS = {}


def current_session():
    sid = request.cookies.get("sid", "")
    return SESSIONS.get(sid)


@app.route("/")
def index():
    return ("Lab 5.3 CSRF. POST /login (username,password). "
            "Doi email: POST /change-email (CO LOI) hoac /change-email-safe.\n")


@app.route("/login", methods=["POST"])
def login():
    u = request.form.get("username", "")
    p = request.form.get("password", "")
    if USERS.get(u) != p:
        return jsonify(ok=False, error="sai dang nhap"), 401
    sid = secrets.token_hex(16)
    SESSIONS[sid] = {"user": u, "email": "%s@shop.local" % u,
                     "csrf": secrets.token_hex(16)}
    resp = make_response(jsonify(ok=True, user=u))
    # LO HONG: SameSite=None khien cookie di theo request cross-site.
    # (de minh hoa; cau hinh an toan la Lax/Strict)
    resp.set_cookie("sid", sid, httponly=True, samesite="None", secure=False)
    return resp


@app.route("/profile")
def profile():
    sess = current_session()
    if not sess:
        return jsonify(ok=False, error="chua dang nhap"), 401
    return jsonify(ok=True, user=sess["user"], email=sess["email"],
                   csrf_token=sess["csrf"])


@app.route("/change-email", methods=["POST"])
def change_email():
    sess = current_session()
    if not sess:
        return jsonify(ok=False, error="chua dang nhap"), 401
    # LO HONG: khong kiem tra CSRF token, khong kiem Origin/Referer.
    new = request.form.get("email", "")
    sess["email"] = new
    return jsonify(ok=True, user=sess["user"], email=new)


@app.route("/change-email-safe", methods=["POST"])
def change_email_safe():
    sess = current_session()
    if not sess:
        return jsonify(ok=False, error="chua dang nhap"), 401
    # BAN VA: token phai khop token trong phien.
    token = request.form.get("csrf_token", "")
    if not token or token != sess["csrf"]:
        return jsonify(ok=False, error="CSRF token sai/thieu"), 403
    new = request.form.get("email", "")
    sess["email"] = new
    return jsonify(ok=True, user=sess["user"], email=new)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
