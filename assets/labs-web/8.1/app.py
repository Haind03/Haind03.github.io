#!/usr/bin/env python3
# Lab 8.1 - SSTI (Server-Side Template Injection) voi Jinja2
# Chay: python3 app.py   (127.0.0.1:8064)
# LOI: ghep input nguoi dung vao chuoi template roi render_template_string.
from flask import Flask, request
from flask import render_template_string

app = Flask(__name__)

HOME = """<!doctype html><title>Loi chao</title>
<h1>Trang loi chao ca nhan hoa</h1>
<form action="/greet" method="get">
  Ten cua ban: <input name="name" value="Hai">
  <button>Gui</button>
</form>
<p>Vi du: <code>/greet?name=Hai</code></p>
"""


@app.route("/")
def home():
    return HOME


@app.route("/greet")
def greet():
    name = request.args.get("name", "khach")
    # LOI CHET NGUOI: noi input vao template roi render => Jinja2 danh gia bieu thuc
    template = "<h2>Xin chao, " + name + "!</h2><p>Chuc ban mot ngay tot lanh.</p>"
    return render_template_string(template)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8064, debug=False)
