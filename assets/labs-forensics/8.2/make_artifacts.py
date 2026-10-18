#!/usr/bin/env python3
# Lab 8.2 - tao file .eml gia lap: mot email phishing gia danh PayPal va mot
# email that de doi chung. Header dung chuan (Received chain nhieu hop,
# From/Return-Path/Reply-To venh, Authentication-Results, Message-ID).
# Khong dung du lieu rieng tu that; moi domain/IP deu la dia chi vi du.
#
# Dung: python3 -I make_artifacts.py [thu_muc_dich]   (mac dinh ./mail)

import os
import sys

PHISH = """\
Return-Path: <bounce@paypa1-support.com>
Received: from mx.victim.com (mx.victim.com [198.51.100.10])
\tby mbox.victim.com (Postfix) with ESMTP id 4FbK2
\tfor <user@victim.com>; Tue, 07 Jan 2026 14:02:03 +0000 (UTC)
Received: from relay.cheaphost.net (relay.cheaphost.net [203.0.113.200])
\tby mx.victim.com (Postfix) with ESMTPS id 9C1aa
\tfor <user@victim.com>; Tue, 07 Jan 2026 14:02:01 +0000 (UTC)
Received: from paypa1-support.com (unknown [45.77.123.45])
\tby relay.cheaphost.net with ESMTP id 7d0f3a
\tfor <user@victim.com>; Tue, 07 Jan 2026 14:01:55 +0000 (UTC)
Authentication-Results: mx.victim.com;
\tspf=fail (sender IP is 45.77.123.45) smtp.mailfrom=paypa1-support.com;
\tdkim=none;
\tdmarc=fail (p=reject) header.from=paypal.com
From: "PayPal Service" <service@paypal.com>
Reply-To: <verify@secure-paypal-check.info>
To: <user@victim.com>
Subject: [Action Required] Your account has been limited
Date: Tue, 07 Jan 2026 14:01:50 +0000
Message-ID: <9f3a2b1c7e@relay.cheaphost.net>
MIME-Version: 1.0
Content-Type: text/html; charset="utf-8"

<html><body>
<p>Dear customer, your account has been limited.</p>
<p><a href="https://secure-paypal-check.info/login">Verify your account now</a></p>
<p>PayPal Service</p>
</body></html>
"""

LEGIT = """\
Return-Path: <notify@github.com>
Received: from mx.victim.com (mx.victim.com [198.51.100.10])
\tby mbox.victim.com (Postfix) with ESMTP id 1AbC2
\tfor <user@victim.com>; Mon, 06 Jan 2026 02:10:04 +0000 (UTC)
Received: from out-1.smtp.github.com (out-1.smtp.github.com [192.30.252.192])
\tby mx.victim.com (Postfix) with ESMTPS id 3DeF4
\tfor <user@victim.com>; Mon, 06 Jan 2026 02:10:02 +0000 (UTC)
Authentication-Results: mx.victim.com;
\tspf=pass (sender IP is 192.30.252.192) smtp.mailfrom=github.com;
\tdkim=pass header.d=github.com;
\tdmarc=pass (p=none) header.from=github.com
From: "GitHub" <notify@github.com>
Reply-To: <notify@github.com>
To: <user@victim.com>
Subject: [repo] A new sign-in to your account
Date: Mon, 06 Jan 2026 02:10:00 +0000
Message-ID: <abc123@mail.github.com>
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"

A new device signed in to your GitHub account. If this was you, ignore this email.
"""

def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "mail")
    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, "phish.eml"), "w", newline="\r\n") as f:
        f.write(PHISH)
    with open(os.path.join(root, "legit.eml"), "w", newline="\r\n") as f:
        f.write(LEGIT)
    print(f"[+] Da tao: {os.path.join(root, 'phish.eml')}")
    print(f"[+] Da tao: {os.path.join(root, 'legit.eml')}")
    print("[+] Chay tiep:  python3 -I solve.py " + os.path.join(
        (sys.argv[1] if len(sys.argv) > 1 else "mail"), "phish.eml"))

if __name__ == "__main__":
    main()
