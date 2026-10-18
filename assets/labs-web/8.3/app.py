#!/usr/bin/env python3
# Lab 8.3 - XXE (XML External Entity) voi lxml (co y de lo hong)
# Chay: python3 app.py   (127.0.0.1:8066)
# LOI: parse XML do client gui voi parser cho phep resolve external entity.
from flask import Flask, request, Response
from lxml import etree

app = Flask(__name__)

FORM_HINT = """<!doctype html><meta charset=utf-8><title>Contact XML</title>
<h1>API nhan lien he dang XML</h1>
<p>POST XML toi <code>/contact</code> voi cau truc:</p>
<pre>&lt;contact&gt;&lt;name&gt;...&lt;/name&gt;&lt;msg&gt;...&lt;/msg&gt;&lt;/contact&gt;</pre>
<p>Server tra ve loi cam on, co chen lai ten ban gui.</p>
"""


@app.route("/")
def index():
    return FORM_HINT


@app.route("/contact", methods=["POST"])
def contact():
    xml = request.data
    # LOI CHET NGUOI: bat resolve_entities + load_dtd + cho phep network
    # (mo phong cau hinh parser khong an toan, hay gap voi libxml2 cu)
    parser = etree.XMLParser(resolve_entities=True, load_dtd=True, no_network=False)
    try:
        root = etree.fromstring(xml, parser)
    except Exception as e:
        return Response("Loi parse XML: %s\n" % e, status=400, mimetype="text/plain")

    name_el = root.find("name")
    msg_el = root.find("msg")
    name = name_el.text if name_el is not None else "(khong ro)"
    msg = msg_el.text if msg_el is not None else ""
    body = "Cam on lien he!\n--- name ---\n%s\n--- msg ---\n%s\n" % (name, msg)
    return Response(body, mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8066, debug=False)
