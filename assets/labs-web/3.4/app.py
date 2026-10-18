#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lab 3.4 - Vuot filter va CSP. Cong 8035, loopback.

Hai chu de:
  A) Filter blacklist ngay tho: chi xoa literal "<script>" va "</script>" (phan biet
     HOA thuong, chi mot luot). Day la cach loc sai kinh dien, de bi vuot.
  B) CSP (Content-Security-Policy): hai kieu header, mot kieu ho (unsafe-inline), mot
     kieu chat hon nhung van bi vuot nho JSONP tren cung origin.

Endpoint:
  GET /search?q=     reflect q vao HTML body SAU KHI loc blacklist.
  GET /csp-inline?q= reflect q, header CSP co 'unsafe-inline' (vo dung).
  GET /csp-strict?q= reflect q, header CSP 'script-src 'self'' (chan inline).
  GET /jsonp?callback=  endpoint JSONP tren cung origin, reflect callback (dung de vuot CSP strict).
"""
from flask import Flask, request, Response

app = Flask(__name__)
PORT = 8035

PAGE = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><title>{title}</title></head>
<body><h1>{title}</h1>{body}</body></html>"""


def naive_filter(s):
    """Filter blacklist ngay tho: xoa literal the script, phan biet hoa thuong, mot luot.
    Diem yeu: (1) phan biet hoa thuong, (2) chi mot luot nen chen long se qua, (3) chi
    nham vao the <script>, bo qua event handler."""
    s = s.replace("<script>", "")
    s = s.replace("</script>", "")
    return s


@app.route("/")
def index():
    body = ("<p>/search loc blacklist; /csp-inline va /csp-strict minh ho CSP; "
            "/jsonp la endpoint JSONP tren cung origin.</p>")
    return PAGE.format(title="Lab 3.4 Vuot filter va CSP", body=body)


@app.route("/search")
def search():
    q = request.args.get("q", "")
    filtered = naive_filter(q)
    body = "<div id=out>Tim: " + filtered + "</div>"
    return PAGE.format(title="search (co filter blacklist)", body=body)


@app.route("/csp-inline")
def csp_inline():
    q = request.args.get("q", "")
    body = "<div id=out>" + q + "</div>"
    html = PAGE.format(title="CSP co unsafe-inline", body=body)
    resp = Response(html)
    # CSP ho: 'unsafe-inline' cho phep inline script/handler chay => khong bao ve duoc gi.
    resp.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'"
    return resp


@app.route("/csp-strict")
def csp_strict():
    q = request.args.get("q", "")
    body = "<div id=out>" + q + "</div>"
    html = PAGE.format(title="CSP strict (script-src self)", body=body)
    resp = Response(html)
    # CSP chat: khong co 'unsafe-inline' => inline script/handler bi chan.
    # NHUNG 'self' cho phep tai script tu cung origin, va /jsonp phan chieu callback
    # => ke tan cong nap duoc JS "hop le" tu chinh site nay.
    resp.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'"
    return resp


@app.route("/jsonp")
def jsonp():
    # Endpoint JSONP co loi: phan chieu callback nguyen van vao noi dung JavaScript.
    cb = request.args.get("callback", "callback")
    js = cb + "({\"user\":\"admin\",\"id\":1});"
    return Response(js, mimetype="application/javascript")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False)
