#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lab 3.3 - DOM-based XSS. Cong 8034, loopback.

Diem khac cot loi: server KHONG he xu ly payload. Server chi tra ve mot trang tinh.
Lo hong nam o JavaScript phia client: no lay du lieu tu `location.hash` (source) va
nhet thang vao `innerHTML` (sink). Toan bo chuyen xay ra trong trinh duyet; phan sau
dau `#` cua URL con khong duoc gui len server.
"""
from flask import Flask, Response

app = Flask(__name__)
PORT = 8034

# Trang tinh. Chu y: server tra ve y het nhau du URL la gi.
VULN_PAGE = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><title>Loi chao DOM</title></head>
<body>
<h1>Trang loi chao</h1>
<div id="out">...</div>
<script>
  // source: location.hash (vi du #Hai). slice(1) bo dau '#'.
  var name = decodeURIComponent(location.hash.slice(1));
  // sink: innerHTML. Gan chuoi co the chua the HTML => DOM XSS.
  document.getElementById('out').innerHTML = "Xin chao " + name;
</script>
</body></html>"""


@app.route("/")
def index():
    return Response(VULN_PAGE, mimetype="text/html")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False)
