#!/usr/bin/env python3
# Lab 10.1 generator: tao mot ext4 image co dau vet timestomp + log clearing (mo phong).
# Chay THAT bang e2fsprogs (mke2fs, debugfs) o user-mode, KHONG can sudo, KHONG mount.
# Moi thao tac tren FILE image, khong dung thiet bi that.
import os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
IMG  = os.path.join(HERE, "case_disk.img")

def sh(cmd):
    env = dict(os.environ); env["TZ"] = "UTC"
    r = subprocess.run(cmd, shell=True, env=env, capture_output=True, text=True)
    return r.stdout + r.stderr

def dbg(script):
    return sh('debugfs -w -R "%s" "%s"' % (script, IMG))

def write_file(name, content, parent="/"):
    tmp = os.path.join(HERE, ".stage")
    with open(tmp, "w") as f:
        f.write(content)
    dbg("cd %s" % parent)  # no-op per call, debugfs is stateless; keep names flat
    dbg("write %s %s" % (tmp, name))
    os.remove(tmp)

def set_times(name, crtime=None, ctime=None, mtime=None, atime=None):
    for fld, val in (("crtime",crtime),("ctime",ctime),("mtime",mtime),("atime",atime)):
        if val:
            dbg("set_inode_field %s %s %s" % (name, fld, val))

def main():
    if os.path.exists(IMG): os.remove(IMG)
    subprocess.run("dd if=/dev/zero of=%s bs=1M count=8 status=none" % IMG, shell=True)
    sh('mke2fs -F -t ext4 -L CASE01 -U 11111111-2222-3333-4444-555555555555 "%s"' % IMG)

    # 1) File binh thuong (control): moi moc bang nhau, hop ly.
    write_file("meeting_notes.txt", "Q4 planning sync. Attendees: ndhai, lan, minh.\n")
    set_times("meeting_notes.txt", "20261014083000","20261014083000","20261014083000","20261014083000")

    write_file("holiday_photo.jpg", "(benign placeholder bytes for a jpg)\n")
    set_times("holiday_photo.jpg", "20261010201500","20261010201500","20261010201500","20261010201500")

    # 2) File BI TIMESTOMP: crtime/ctime that (2026), mtime/atime bi lui ve 2009.
    #    mtime < crtime la bat kha thi voi file that -> dau hieu timestomp.
    write_file("report_q4.pdf", "quarterly financial report - confidential\n")
    set_times("report_q4.pdf", crtime="20261015091200", ctime="20261015091200",
                               mtime="20090105070000", atime="20090105070000")

    # 3) Log clearing (mo phong): auth.log noi dung chi con toi 02:11,
    #    nhung inode mtime/ctime = 03:05 (ke tan cong sua file sau do).
    auth = []
    for mm in range(0, 12):  # 02:00 .. 02:11
        auth.append("2026-10-16T02:%02d:%02d+00:00 host01 sshd[%d]: Accepted publickey for ndhai from 10.0.0.5 port 51000 ssh2"
                    % (mm, (mm*7) % 60, 1400+mm))
    write_file("auth.log", "\n".join(auth) + "\n")
    # inode cua auth.log bi dung toi luc 03:05 (tre hon dong log cuoi 02:11) -> co nguoi ghi de
    set_times("auth.log", crtime="20261016020000", ctime="20261016030500",
                          mtime="20261016030500", atime="20261016030500")

    # 4) Nguon doc lap (gia lap da trich tu he thong khac), de neo su that:
    #    - upload_server.log: report_q4.pdf that su xuat hien 2026-10-15, KHONG phai 2009.
    with open(os.path.join(HERE, "upload_server.log"), "w") as f:
        f.write("2026-10-15T09:12:03+00:00 fileserver AUDIT upload user=ndhai "
                "name=report_q4.pdf size=42 src=10.0.0.5\n")
    #    - wtmp_last.txt: output `last` tu wtmp, con giu phien 02:45 ma auth.log da bi xoa.
    with open(os.path.join(HERE, "wtmp_last.txt"), "w") as f:
        f.write("ndhai    pts/1        10.0.0.5         Fri Oct 16 02:45   still logged in\n")
        f.write("ndhai    pts/0        10.0.0.5         Fri Oct 16 02:03 - 02:11  (00:08)\n")
        f.write("reboot   system boot  6.1.0            Fri Oct 16 01:58   still running\n")

    print("Created", IMG)
    print(sh('dumpe2fs -h "%s" 2>/dev/null | grep -iE "Volume name|Filesystem UUID"' % IMG).strip())

if __name__ == "__main__":
    main()
