#!/usr/bin/env python3
"""
Dich vu NOI BO cho lab 6.2, bind 127.0.0.1:8058.
Dang le chi goi duoc tu trong host; SSRF (sau khi vuot filter) se cham toi day.
Chay: python3 internal_service.py (giu chay song song voi app.py)
"""
from flask import Flask, jsonify

app = Flask(__name__)
PORT = 8058


@app.route("/admin/secret")
def secret():
    return jsonify(service="internal-only",
                   flag="FLAG{6.2_vuot_filter_ssrf_toi_noi_bo}")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
