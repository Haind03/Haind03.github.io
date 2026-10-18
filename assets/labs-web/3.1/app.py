#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lab 3.1 - Reflected XSS theo context.
App co y KHONG escape input de minh ho. Chi chay local, cong 8031.

Ba endpoint phan chieu cung mot tham so `q` vao ba context khac nhau:
  /html  -> than HTML (HTML body)
  /attr  -> gia tri cua mot attribute (value cua the input)
  /js    -> ben trong mot JS string literal
Them /safe de so sanh: cung context HTML body nhung co escape dung cach.
"""
from flask import Flask, request, Response
from markupsafe import escape

app = Flask(__name__)
PORT = 8031


PAGE = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><title>{title}</title></head>
<body>
<h1>{title}</h1>
{body}
</body></html>"""


@app.route("/")
def index():
    body = (
        "<p>Cac context phan chieu (reflect) khong escape:</p>"
        "<ul>"
        "<li><a href=\"/html?q=xin+chao\">/html</a> context than HTML</li>"
        "<li><a href=\"/attr?q=xin+chao\">/attr</a> context attribute value</li>"
        "<li><a href=\"/js?q=xin+chao\">/js</a> context JS string</li>"
        "<li><a href=\"/safe?q=xin+chao\">/safe</a> cung HTML body nhung escape dung</li>"
        "</ul>"
    )
    return PAGE.format(title="Lab 3.1 Reflected XSS", body=body)


@app.route("/html")
def ctx_html():
    # Context: than HTML. Input nhet thang vao, trinh duyet coi la markup.
    q = request.args.get("q", "")
    body = "<div id=greeting>Ket qua tim kiem cho: " + q + "</div>"
    return PAGE.format(title="context HTML body", body=body)


@app.route("/attr")
def ctx_attr():
    # Context: gia tri attribute. Input nam trong value="...".
    q = request.args.get("q", "")
    body = '<form><input name=q value="' + q + '" placeholder="tu khoa"></form>'
    return PAGE.format(title="context attribute", body=body)


@app.route("/js")
def ctx_js():
    # Context: JS string literal trong mot the script.
    q = request.args.get("q", "")
    body = (
        "<div id=out></div>"
        "<script>\n"
        "  var keyword = '" + q + "';\n"
        "  document.getElementById('out').textContent = 'Ban tim: ' + keyword;\n"
        "</script>"
    )
    return PAGE.format(title="context JS string", body=body)


@app.route("/safe")
def ctx_safe():
    # So sanh: escape dung cach thi payload bi vo hieu.
    q = request.args.get("q", "")
    body = "<div id=greeting>Ket qua tim kiem cho: " + str(escape(q)) + "</div>"
    return PAGE.format(title="context HTML body (SAFE)", body=body)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False)
