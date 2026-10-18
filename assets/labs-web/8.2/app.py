#!/usr/bin/env python3
# Lab 8.2 - Insecure Deserialization voi Python pickle (co y de lo hong)
# Chay: python3 app.py   (127.0.0.1:8065)
# LOI: luu "prefs" nguoi dung duoi dang pickle base64 trong cookie, roi pickle.loads().
import base64
import pickle
from flask import Flask, request, make_response

app = Flask(__name__)


@app.route("/")
def index():
    cookie = request.cookies.get("prefs")
    if not cookie:
        default = base64.b64encode(pickle.dumps({"theme": "light", "lang": "vi"})).decode()
        resp = make_response(
            "Chua co cookie 'prefs'. Da dat mac dinh (theme=light, lang=vi).\n"
            "Tai lai trang de xem prefs duoc giai ma.\n"
        )
        resp.set_cookie("prefs", default)
        return resp
    try:
        raw = base64.b64decode(cookie)
        data = pickle.loads(raw)  # <-- LOI CHET NGUOI: unpickle du lieu client dieu khien
    except Exception as e:
        return "Loi doc prefs: %s\n" % e, 400
    return "Prefs cua ban: %r\n" % (data,)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8065, debug=False)
