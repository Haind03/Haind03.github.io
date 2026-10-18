#!/usr/bin/env python3
"""
Lab 6.2 - Vuot filter SSRF.

App co /fetch?url= nhu 6.1 nhung lan nay co "filter" chong SSRF. Filter nay
NGAY THO: chi chan theo chuoi ky tu trong URL (blocklist mot vai cach viet
noi bo pho bien). Vi khong chuan hoa (normalize) dia chi truoc khi kiem, no
bi vuot bang:
  - bieu dien IP khac: thap phan (2130706433), hex (0x7f000001),
    octal (0177.0.0.1), rut gon (127.1), IPv6-mapped ([::ffff:7f00:1]),
    host "0" (= 0.0.0.0 -> loopback);
  - userinfo "@" (http://allowed@2130706433/);
  - redirect 302: filter chi kiem URL BAN DAU, con requests tu di theo
    Location toi dich noi bo (ke ca dich do dung dung chuoi bi chan).

CHAY LOCAL, CO Y DE LOI. Khong deploy ra Internet.
"""
import requests
from flask import Flask, request, jsonify, redirect

app = Flask(__name__)
PORT = 8057

# Blocklist ngay tho: chi khop chuoi, khong chuan hoa IP.
BLOCK = ["localhost", "127.0.0.1", "0.0.0.0", "::1", "[::]"]


def is_blocked(url: str) -> bool:
    low = url.lower()
    return any(b in low for b in BLOCK)


@app.route("/")
def index():
    return ("Lab 6.2 SSRF bypass. GET /fetch?url=... (co filter ngay tho).\n")


@app.route("/fetch")
def fetch():
    url = request.args.get("url", "")
    if not url:
        return jsonify(ok=False, error="thieu url"), 400
    # LO HONG: chi kiem chuoi URL ban dau, khong chuan hoa, khong kiem lai
    # sau redirect.
    if is_blocked(url):
        return jsonify(ok=False, blocked=True,
                       error="URL tro toi noi bo, bi chan", url=url), 403
    try:
        r = requests.get(url, timeout=3, allow_redirects=True)
        return jsonify(ok=True, url=url, status=r.status_code, body=r.text)
    except Exception as e:
        return jsonify(ok=False, url=url, error=str(e)), 502


@app.route("/bounce")
def bounce():
    # Mo phong mot redirector do ke tan cong kiem soat (hoac mot open redirect).
    # Tra 302 toi dich NOI BO dung chuoi bi chan "127.0.0.1" - nhung filter
    # da duyet URL ban dau (/bounce) roi, khong kiem lai dich redirect.
    return redirect("http://127.0.0.1:8058/admin/secret", code=302)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
