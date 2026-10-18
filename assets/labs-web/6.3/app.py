#!/usr/bin/env python3
"""
Lab 6.3 - Open redirect.

Ba chuc nang chuyen huong co loi:

  (1) /go?url=   : chuyen huong toi url tuy y, KHONG kiem gi -> open redirect
                   thuan. Dung de phishing (link tren domain dang tin nhung day
                   nan nhan ra site gia).

  (2) /login?next= : "chi cho phep URL noi bo" nhung kiem NGAY THO bang
                     url.startswith('/'). Bi vuot bang //evil (URL khong scheme,
                     protocol-relative) hay /\evil.

  (3) /sso?next= : mo phong luong SSO/OAuth: sau khi xac thuc, dinh kem token
                   vao URL tra ve roi chuyen huong. next mo => token ro ri sang
                   domain cua ke tan cong.

CHAY LOCAL, CO Y DE LOI. Khong deploy ra Internet.
"""
from flask import Flask, request, redirect, jsonify

app = Flask(__name__)
PORT = 8059

# "Token phien" bi mat, mo phong token SSO se bi ro ri qua open redirect.
SSO_TOKEN = "FLAG{6.3_open_redirect_ro_ri_token}"


@app.route("/")
def index():
    return ("Lab 6.3 open redirect. /go?url=... , /login?next=... , /sso?next=...\n")


@app.route("/go")
def go():
    # LO HONG (1): khong kiem url -> chuyen huong di bat ky dau.
    url = request.args.get("url", "/")
    return redirect(url, code=302)


@app.route("/login")
def login():
    # LO HONG (2): chi cho "URL bat dau bang /" nhung //evil cung bat dau bang
    # / => browser hieu la //evil = https://evil (protocol-relative).
    nxt = request.args.get("next", "/")
    if not nxt.startswith("/"):
        return jsonify(ok=False, error="chi cho phep URL noi bo"), 400
    return redirect(nxt, code=302)


@app.route("/sso")
def sso():
    # LO HONG (3): dinh token vao URL tra ve roi redirect. next khong kiem.
    nxt = request.args.get("next", "/")
    sep = "&" if "?" in nxt else "?"
    target = "%s%stoken=%s" % (nxt, sep, SSO_TOKEN)
    return redirect(target, code=302)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
