#!/usr/bin/env python3
"""
Lab 5.1 - IDOR (Insecure Direct Object Reference).

App co lo hong CO Y de hoc:
  - /api/order/<id>: chi kiem tra "da dang nhap chua", KHONG kiem tra
    order do co phai cua nguoi dang dang nhap khong.
    => bat ky user nao cung doc duoc don hang cua nguoi khac bang cach
       doi so id (id tuan tu, de doan: 1001, 1002, 1003...).
  - POST /api/order/<id>/address: doi dia chi giao hang cung khong kiem
    quyen so huu => IDOR ghi, sua don hang nguoi khac.
  - Co them resource dung "UUID doan duoc" (uuid1 theo thoi gian) de minh
    hoa: id kieu UUID chua chac an toan neu sinh sai cach.

CHAY LOCAL, CO Y DE LOI. Khong deploy ra Internet.
"""
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)
PORT = 8050

# "Dang nhap" rat don gian: cookie auth=<username>. Du de minh hoa IDOR,
# van de nam o THIEU kiem tra quyen so huu, khong phai o co che session.
USERS = {"mallory": "pw", "alice": "pw", "bob": "pw"}

# Don hang: id tuan tu, de doan. Moi don co chu so huu rieng.
ORDERS = {
    1001: {"owner": "alice", "total": "12.000.000 VND",
           "card_last4": "4291", "address": "12 Tran Hung Dao, Ha Noi",
           "note": "FLAG{5.1_idor_doc_don_nguoi_khac}"},
    1002: {"owner": "bob", "total": "350.000 VND",
           "card_last4": "8810", "address": "5 Le Loi, Da Nang",
           "note": "giao gio hanh chinh"},
    1003: {"owner": "mallory", "total": "99.000 VND",
           "card_last4": "0001", "address": "1 Nguyen Trai, TP HCM",
           "note": "don cua chinh mallory"},
    1004: {"owner": "alice", "total": "4.500.000 VND",
           "card_last4": "4291", "address": "12 Tran Hung Dao, Ha Noi",
           "note": "laptop"},
    1005: {"owner": "bob", "total": "1.200.000 VND",
           "card_last4": "8810", "address": "5 Le Loi, Da Nang",
           "note": "tai nghe"},
}


def current_user():
    # LO HONG goc: chi can co cookie auth hop le la "da dang nhap".
    u = request.cookies.get("auth", "")
    return u if u in USERS else None


@app.route("/")
def index():
    return (
        "Lab 5.1 IDOR. Dang nhap: POST /login (form username, password).\n"
        "Xem don: GET /api/order/<id> (vd 1003). Doi dia chi: "
        "POST /api/order/<id>/address (form address).\n"
    )


@app.route("/login", methods=["POST"])
def login():
    u = request.form.get("username", "")
    p = request.form.get("password", "")
    if USERS.get(u) != p:
        return jsonify(ok=False, error="sai dang nhap"), 401
    resp = make_response(jsonify(ok=True, message="xin chao %s" % u))
    # Cookie dinh danh nguoi dung. HttpOnly cho giong that.
    resp.set_cookie("auth", u, httponly=True, samesite="Lax")
    return resp


@app.route("/api/order/<int:oid>")
def get_order(oid):
    user = current_user()
    if not user:
        return jsonify(ok=False, error="chua dang nhap"), 401
    order = ORDERS.get(oid)
    if not order:
        return jsonify(ok=False, error="khong co don"), 404
    # LO HONG: KHONG kiem tra order["owner"] == user.
    # Dang le phai: if order["owner"] != user: return 403
    return jsonify(ok=True, order_id=oid, **order)


@app.route("/api/order/<int:oid>/address", methods=["POST"])
def set_address(oid):
    user = current_user()
    if not user:
        return jsonify(ok=False, error="chua dang nhap"), 401
    order = ORDERS.get(oid)
    if not order:
        return jsonify(ok=False, error="khong co don"), 404
    # LO HONG: cung khong kiem tra quyen so huu => IDOR ghi.
    new_addr = request.form.get("address", "")
    order["address"] = new_addr
    return jsonify(ok=True, order_id=oid, address=new_addr,
                   changed_by=user)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
