#!/usr/bin/env python3
"""
Lab 6.1 - SSRF co ban (Server-Side Request Forgery).

App co chuc nang "xem truoc URL" / webhook tester: nguoi dung dua mot URL,
SERVER tu di lay noi dung URL do roi tra ve. Khong co bat ky han che nao
(SSRF co ban) => ke tan cong ep server goi toi:
  - dich vu noi bo chi nghe tren 127.0.0.1 (vd 127.0.0.1:8055 admin noi bo),
  - endpoint metadata cloud (that la http://169.254.169.254/..., o lab ta gia
    lap bang 127.0.0.1:8056).

CHAY LOCAL, CO Y DE LOI. Khong deploy ra Internet.
"""
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
PORT = 8054


@app.route("/")
def index():
    return ("Lab 6.1 SSRF. GET /fetch?url=... (server di lay URL ho ban).\n"
            "Vd binh thuong: /fetch?url=http://127.0.0.1:8054/ping\n")


@app.route("/ping")
def ping():
    return "pong tu app chinh"


@app.route("/fetch")
def fetch():
    url = request.args.get("url", "")
    if not url:
        return jsonify(ok=False, error="thieu tham so url"), 400
    # LO HONG: lay bat ky URL nao client dua, khong kiem host/scheme/IP noi bo.
    try:
        r = requests.get(url, timeout=3)
        return jsonify(ok=True, url=url, status=r.status_code,
                       body=r.text)
    except Exception as e:
        return jsonify(ok=False, url=url, error=str(e)), 502


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
