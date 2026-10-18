#!/usr/bin/env python3
# Lab 9.2 - KHONG phai lab phat hien tu dong; day la EXERCISE mapping artifact -> ATT&CK.
# Script nay chi lay bang mapping (dua tren cac lab khac) va xuat ra:
#  (a) mot ATT&CK Navigator layer JSON de import vao Navigator,
#  (b) tom tat so technique theo tactic + cac tactic con TRONG (de hoc vien di tim).
# Chay: python3 -I build_layer.py
import os, json

HERE = os.path.dirname(os.path.abspath(__file__))

# (artifact, tactic, technique_id, technique_name, nguon_lab)
MAPPING = [
    ("HTTP tai payload MZ (update.exe/payload.exe)", "command-and-control", "T1105", "Ingress Tool Transfer", "7.1 / 7.2"),
    ("C2 beacon nhip deu +/- jitter toi :443",       "command-and-control", "T1071.001", "Application Layer Protocol: Web Protocols", "7.3"),
    ("DNS tunnel nhan base32 tren domain cha",        "command-and-control", "T1071.004", "Application Layer Protocol: DNS", "7.3"),
    ("Du lieu tuon ra qua query DNS",                 "exfiltration",        "T1048.003", "Exfiltration Over Unencrypted Non-C2 Protocol", "7.3"),
    ("upload.php webshell tren web server",           "initial-access",      "T1190", "Exploit Public-Facing Application", "9.1"),
    ("upload.php (webshell ton tai lau dai)",         "persistence",         "T1505.003", "Server Software Component: Web Shell", "9.1"),
    ("sysupd ELF trong /tmp/.cache (chay dropper)",   "execution",           "T1059.004", "Command and Scripting Interpreter: Unix Shell", "9.1"),
    ("/etc/cron.d/apache-check",                      "persistence",         "T1053.003", "Scheduled Task/Job: Cron", "9.1"),
    ("/root/.ssh/authorized_keys them key",           "persistence",         "T1098.004", "Account Manipulation: SSH Authorized Keys", "9.1"),
    ("exfil.tar.gz staging truoc khi tuon",           "collection",          "T1560.001", "Archive Collected Data: Archive via Utility", "9.1"),
    ("exfil.tar.gz bi xoa (va file xoa o lab 2.2)",   "defense-evasion",     "T1070.004", "Indicator Removal: File Deletion", "2.2 / 9.1"),
]

# ATT&CK Enterprise 14 tactic (de biet tactic nao con trong)
ALL_TACTICS = [
    "reconnaissance","resource-development","initial-access","execution","persistence",
    "privilege-escalation","defense-evasion","credential-access","discovery",
    "lateral-movement","collection","command-and-control","exfiltration","impact",
]

# --- xuat Navigator layer ---
techniques = []
seen = {}
for art, tactic, tid, tname, lab in MAPPING:
    seen.setdefault(tid, []).append(f"[{lab}] {art}")
for tid, comments in seen.items():
    techniques.append({
        "techniqueID": tid,
        "score": 100,
        "color": "",
        "comment": " | ".join(comments),
        "enabled": True,
    })
layer = {
    "name": "TechForensics lab 9.2 - case walk",
    "versions": {"attack": "14", "navigator": "4.9.1", "layer": "4.5"},
    "domain": "enterprise-attack",
    "description": "Artifact -> technique tu cac lab 2.2/7.1/7.2/7.3/9.1 (exercise).",
    "techniques": techniques,
    "gradient": {"colors": ["#ffffff", "#ff6666"], "minValue": 0, "maxValue": 100},
    "legendItems": [],
}
out = os.path.join(HERE, "navigator_layer.json")
with open(out, "w") as f:
    json.dump(layer, f, indent=2)

# --- tom tat ---
covered = sorted({m[1] for m in MAPPING})
missing = [t for t in ALL_TACTICS if t not in covered]
print("="*60)
print("MAPPING artifact -> ATT&CK (tu cac lab khac)")
print("="*60)
for art, tactic, tid, tname, lab in MAPPING:
    print(f"{tid:11} {tactic:20} {art}  [lab {lab}]")
print()
print(f"technique duy nhat : {len(seen)}")
print(f"tactic co mat ({len(covered)}): {', '.join(covered)}")
print(f"tactic CON TRONG ({len(missing)}): {', '.join(missing)}")
print()
print(f"Da ghi Navigator layer: {os.path.basename(out)} ({len(techniques)} technique)")
print("Import file nay vao https://mitre-attack.github.io/attack-navigator/ (Open Existing Layer).")
print()
print(">> EXERCISE: voi moi tactic CON TRONG o tren, viet mot gia thuyet + noi se kiem chung.")
