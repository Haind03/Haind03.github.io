#!/usr/bin/env bash
# Lab 4.2: tai mot file .evtx log CONG KHAI (EVTX-ATTACK-SAMPLES, GPL) de parse offline.
# .evtx la nhat ky su kien (DU LIEU), khong phai file thuc thi, khong phai malware.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
URL="https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Privilege%20Escalation/NTLM2SelfRelay-med0x2e-security_4624_4688.evtx"

echo "[*] Cai dependency: pip install python-evtx"
python3 -m pip install --quiet python-evtx >/dev/null 2>&1 || true

cd "$HERE"
echo "[*] tai security_4624_4688.evtx"
curl -sL -o security_4624_4688.evtx "$URL"
head -c 8 security_4624_4688.evtx | od -c | head -1
echo "[*] xong (nguon: github.com/sbousseaden/EVTX-ATTACK-SAMPLES, kenh Security)"
