#!/usr/bin/env python3
# Lab 7.1 - Path Traversal / LFI (co y de lo hong de hoc)
# Chay: python3 app.py   (lang nghe 127.0.0.1:8061)
# App "doc tai lieu" theo tham so file, noi ghep duong dan khong loc -> traversal.
import os
from flask import Flask, request, Response

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(BASE, "docs")

INDEX = """<!doctype html><title>DocViewer</title>
<h1>DocViewer noi bo</h1>
<p>Kho tai lieu cong ty. Chon file de xem:</p>
<ul>
  <li><a href="/view?file=welcome.txt">welcome.txt</a></li>
  <li><a href="/view?file=huongdan.txt">huongdan.txt</a></li>
</ul>
<p>Endpoint co "loc" (demo bypass): <code>/safe?file=welcome.txt</code></p>
"""


@app.route("/")
def index():
    return INDEX


# ---- Endpoint LO HONG: noi ghep thang, khong chuan hoa duong dan ----
@app.route("/view")
def view():
    filename = request.args.get("file", "welcome.txt")
    # LOI: ghep thang chuoi nguoi dung vao duong dan, khong kiem ../, khong realpath
    path = os.path.join(DOCS, filename)
    try:
        with open(path, "rb") as f:
            data = f.read()
        return Response(data, mimetype="text/plain")
    except Exception as e:
        return Response("Loi doc file: %s" % e, status=404, mimetype="text/plain")


# ---- Endpoint "loc" so sai: thay '../' MOT lan -> bypass bang ....// ----
@app.route("/safe")
def safe():
    filename = request.args.get("file", "welcome.txt")
    # LOI: chi strip MOT lan, khong de quy -> '....//' sau khi bo '../' con lai '../'
    cleaned = filename.replace("../", "")
    path = os.path.join(DOCS, cleaned)
    try:
        with open(path, "rb") as f:
            data = f.read()
        return Response(data, mimetype="text/plain")
    except Exception as e:
        return Response("Loi doc file: %s" % e, status=404, mimetype="text/plain")


if __name__ == "__main__":
    os.makedirs(DOCS, exist_ok=True)
    # file tai lieu hop le
    with open(os.path.join(DOCS, "welcome.txt"), "w") as f:
        f.write("Chao mung toi DocViewer noi bo.\n")
    with open(os.path.join(DOCS, "huongdan.txt"), "w") as f:
        f.write("Huong dan su dung he thong tai lieu.\n")
    app.run(host="127.0.0.1", port=8061, debug=False)
