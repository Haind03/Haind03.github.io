#!/usr/bin/env python3
"""
Hai dich vu NOI BO cho lab 6.1, chi de minh hoa muc tieu cua SSRF.
Deu bind 127.0.0.1 (y nhu dich vu noi bo that chi nghe loopback):

  - 127.0.0.1:8055  admin noi bo: endpoint /admin/config tra config bi mat.
                    Y tuong: tu Internet khong goi duoc, chi goi tu trong host.
  - 127.0.0.1:8056  gia lap cloud metadata. Trong thuc te la
                    http://169.254.169.254/latest/meta-data/... (IP link-local
                    khong route ra ngoai). O lab ta dung 127.0.0.1:8056 thay the.

Chay: python3 internal_services.py  (giu chay song song voi app.py)
"""
import threading
from werkzeug.serving import make_server
from flask import Flask, jsonify

# ---- 8055: dich vu admin noi bo ----
internal = Flask("internal_admin")


@internal.route("/admin/config")
def admin_config():
    return jsonify(service="internal-admin",
                   db_password="sup3r-s3cr3t-db",
                   flag="FLAG{6.1_ssrf_doc_dich_vu_noi_bo}")


# ---- 8056: gia lap metadata cloud ----
metadata = Flask("fake_metadata")


@metadata.route("/latest/meta-data/iam/security-credentials/")
def role_list():
    return "webapp-role"


@metadata.route("/latest/meta-data/iam/security-credentials/webapp-role")
def role_creds():
    return jsonify({
        "AccessKeyId": "AKIA_FAKE_SSRF_DEMO",
        "SecretAccessKey": "fakeSecret/do+not+use",
        "Token": "FLAG{6.1_ssrf_metadata_cloud}",
        "Expiration": "2030-01-01T00:00:00Z",
    })


def serve(app, port):
    srv = make_server("127.0.0.1", port, app)
    srv.serve_forever()


if __name__ == "__main__":
    t1 = threading.Thread(target=serve, args=(internal, 8055), daemon=True)
    t2 = threading.Thread(target=serve, args=(metadata, 8056), daemon=True)
    t1.start()
    t2.start()
    print("internal admin -> 127.0.0.1:8055 ; fake metadata -> 127.0.0.1:8056")
    t1.join()
