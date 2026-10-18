#!/usr/bin/env python3
"""
Lab 10.1 - Chuoi recon -> IDOR -> SSTI -> RCE.

Mot app Flask nhieu buoc, moi buoc mo duong cho buoc sau:
  B0 recon: trang chu nhung mot file JS; file JS lo endpoint "noi bo"
            /api/v2/users/<id>/keys (khong co link cong khai).
  B1 IDOR : /api/v2/users/<id>/keys khong xac thuc, khong kiem quyen ->
            doc duoc key cua admin (id=1), trong do co admin_api_key.
  B2 SSTI : /admin/template/preview chi "bao ve" bang admin_api_key (vua
            leak o B1). No render_template_string tren input nguoi dung
            -> Server-Side Template Injection.
  B3 RCE  : payload SSTI Jinja2 chay lenh he thong -> doc flag.txt tren dia.

CHAY LOCAL, CO Y DE LOI. Khong deploy ra Internet.
"""
from flask import Flask, request, jsonify, Response, render_template_string

app = Flask(__name__)
PORT = 8076

# Key "noi bo" cua admin, dang ra khong duoc lo ra ngoai.
ADMIN_API_KEY = "adm_k3y_31337_internal"

USER_KEYS = {
    1: {"id": 1, "username": "admin", "role": "admin",
        "admin_api_key": ADMIN_API_KEY,
        "note": "key dung cho cac endpoint /admin/*"},
    2: {"id": 2, "username": "alice", "role": "user",
        "admin_api_key": None, "note": "user thuong"},
}

INDEX_HTML = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><title>Shop Admin Portal</title></head>
<body>
  <h1>Shop Admin Portal</h1>
  <p>Trang quan tri noi bo. Vui long dang nhap.</p>
  <!-- TODO: go bo file debug truoc khi len production -->
  <script src="/static/app.js"></script>
</body></html>
"""

# File JS "quen xoa" lam lo endpoint noi bo (recon).
APP_JS = """// build: dev
// Bang dieu khien goi API noi bo de lay khoa dich vu.
const API_BASE = "/api/v2";
async function loadKeys(userId) {
  // endpoint noi bo, chua gan xac thuc o moi truong dev
  const r = await fetch(`${API_BASE}/users/${userId}/keys`);
  return await r.json();
}
// preview template qua /admin/template/preview (can header X-Admin-Key)
"""


@app.route("/")
def index():
    return Response(INDEX_HTML, mimetype="text/html")


@app.route("/static/app.js")
def app_js():
    return Response(APP_JS, mimetype="application/javascript")


@app.route("/api/v2/users/<int:user_id>/keys")
def user_keys(user_id):
    # LO HONG IDOR: khong xac thuc, khong kiem quyen. Ai goi cung tra.
    data = USER_KEYS.get(user_id)
    if not data:
        return jsonify(error="not found"), 404
    return jsonify(data)


@app.route("/admin/template/preview", methods=["POST"])
def template_preview():
    # "Bao ve" bang admin_api_key - ma key nay vua bi leak o buoc IDOR.
    key = request.headers.get("X-Admin-Key", "")
    if key != ADMIN_API_KEY:
        return jsonify(error="forbidden"), 403
    body = request.get_json(silent=True) or {}
    template = body.get("template", "")
    # LO HONG SSTI: render thang input nguoi dung bang Jinja2.
    rendered = render_template_string(template)
    return jsonify(rendered=rendered)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
