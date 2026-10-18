#!/usr/bin/env python3
"""
Lab 2.5 - Command injection (in-band + blind + loc ky tu)
App Flask co chuc nang "ping" goi shell truc tiep -> command injection.

  GET /ping?host=<h>   -> os: "ping -c 1 <h>"  (shell=True) tra ca output
       IN-BAND: ket qua lenh chen hien thang trong phan hoi.
       vd: host=127.0.0.1; id   hoac  host=127.0.0.1; cat flag.txt

  GET /ping2?host=<h>  -> giong tren nhung LOC bo ; & | $ `
       Bypass bang ky tu xuong dong (%0a) ma filter quen chan.

  GET /ping3?host=<h>  -> BLIND: chay lenh nhung CHI tra "da gui", khong lo output.
       Suy ket qua bang time-based (; sleep N) hoac OOB (ghi ra file / goi ve
       server cua minh). O lab nay OOB minh hoa bang ghi ra file roi doc lai.

Muc tieu: chay lenh tuy y, doc flag.txt.

Chay local, loopback, cong 8025:
    PORT=8025 python3 app.py
"""
import os
import re
import subprocess
from flask import Flask, request, Response

app = Flask(__name__)
HERE = os.path.dirname(os.path.abspath(__file__))


def shell(cmd):
    # LO HONG CO Y: shell=True + noi chuoi = command injection
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=30, cwd=HERE)
    return (p.stdout or "") + (p.stderr or "")


@app.route("/ping")
def ping():
    host = request.args.get("host", "127.0.0.1")
    out = shell("ping -c 1 " + host)      # <-- noi chuoi truc tiep
    return Response(out, mimetype="text/plain")


@app.route("/ping2")
def ping2():
    host = request.args.get("host", "127.0.0.1")
    # Loc ngay tho: bo cac ky tu noi lenh pho bien... nhung quen xuong dong!
    if re.search(r"[;&|`$]", host):
        return Response("Tu choi: ky tu khong hop le\n",
                        status=400, mimetype="text/plain")
    out = shell("ping -c 1 " + host)
    return Response(out, mimetype="text/plain")


@app.route("/ping3")
def ping3():
    host = request.args.get("host", "127.0.0.1")
    # BLIND: van chay lenh nhung khong tra output -> phai dung time-based/OOB
    shell("ping -c 1 " + host)
    return Response("da gui ping\n", mimetype="text/plain")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8025"))
    app.run(host="127.0.0.1", port=port, debug=False)
