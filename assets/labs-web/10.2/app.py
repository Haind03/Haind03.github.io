#!/usr/bin/env python3
"""
Lab 10.2 - Chuoi client-side: Stored XSS -> CSRF -> Account Takeover.

App Flask co lo hong CO Y de hoc. Hai mat xich chinh deu chung minh duoc
truc tiep tu phia server (khong can GUI trinh duyet):

  Mat xich 1 - Stored XSS: POST /comment luu binh luan, GET /feed render
    binh luan KHONG escape -> script cua attacker nam nguyen trong HTML.
  Mat xich 2 - CSRF: POST /account/email doi email tai khoan dang dang nhap,
    KHONG co CSRF token, cookie SameSite=None -> request gia mao tu origin
    khac van doi duoc email.
  Ghep chuoi (dien ra trong trinh duyet nan nhan): nan nhan xem /feed ->
    script attacker chay trong session nan nhan -> goi /account/email doi
    email sang email cua attacker -> attacker /account/forgot -> nhan reset
    token -> /account/reset -> CHIEM tai khoan.

CHAY LOCAL, CO Y DE LOI. Khong deploy ra Internet.
"""
from flask import Flask, request, jsonify, Response, make_response

app = Flask(__name__)
PORT = 8077

USERS = {
    "admin": {"username": "admin", "password": "OrigPassw0rd",
              "email": "admin@corp.local"},
}
SESSIONS = {}          # sid -> username
RESET_TOKENS = {}      # token -> username
COMMENTS = []          # [{author, text}]


def whoami():
    return SESSIONS.get(request.cookies.get("session", ""))


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or request.form
    u = USERS.get(data.get("username", ""))
    if not u or u["password"] != data.get("password", ""):
        return jsonify(error="invalid"), 401
    sid = "sess-%s" % u["username"]
    SESSIONS[sid] = u["username"]
    resp = make_response(jsonify(ok=True))
    # Cookie thieu phong ve CSRF: SameSite=None, khong kem CSRF token.
    resp.set_cookie("session", sid, httponly=True, samesite="None", secure=False)
    return resp


@app.route("/comment", methods=["POST"])
def comment():
    data = request.get_json(silent=True) or request.form
    COMMENTS.append({"author": data.get("author", "anon"),
                     "text": data.get("text", "")})
    return jsonify(ok=True, count=len(COMMENTS))


@app.route("/feed")
def feed():
    # LO HONG Stored XSS: noi thang text vao HTML, khong escape.
    items = "".join("<div class='c'><b>%s</b>: %s</div>\n" %
                    (c["author"], c["text"]) for c in COMMENTS)
    html = "<!doctype html><html><body><h1>Feed</h1>\n%s</body></html>" % items
    return Response(html, mimetype="text/html")


@app.route("/account/email", methods=["POST"])
def change_email():
    # Doi email tai khoan dang dang nhap. LO HONG CSRF: khong kiem CSRF token.
    username = whoami()
    if not username:
        return jsonify(error="unauthorized"), 401
    data = request.get_json(silent=True) or request.form
    USERS[username]["email"] = data.get("email", "")
    return jsonify(ok=True, email=USERS[username]["email"])


@app.route("/account/forgot", methods=["POST"])
def forgot():
    # Gui reset token toi EMAIL HIEN TAI cua tai khoan.
    data = request.get_json(silent=True) or request.form
    u = USERS.get(data.get("username", ""))
    if not u:
        return jsonify(error="not found"), 404
    token = "rst-%s-7f3a" % u["username"]
    RESET_TOKENS[token] = u["username"]
    # Lab: tra luon token + email nhan de minh hoa (that ra gui qua email).
    return jsonify(ok=True, sent_to=u["email"], reset_token=token)


@app.route("/account/reset", methods=["POST"])
def reset():
    data = request.get_json(silent=True) or request.form
    token = data.get("token", "")
    username = RESET_TOKENS.get(token)
    if not username:
        return jsonify(error="invalid token"), 400
    USERS[username]["password"] = data.get("new_password", "")
    return jsonify(ok=True, message="password cua %s da bi doi" % username,
                   flag="FLAG{10.2_stored_xss_csrf_account_takeover}")


@app.route("/")
def index():
    return ("Lab 10.2. POST /comment, GET /feed (stored XSS), "
            "POST /account/email (CSRF), /account/forgot, /account/reset.\n")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
