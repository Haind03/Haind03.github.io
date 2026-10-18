#!/usr/bin/env python3
# Lab 4.5 solver: persistence tu Run keys (SOFTWARE+NTUSER), IFEO (SOFTWARE), services (SYSTEM).
# Chay: python3 -I solve.py [thu_muc_chua_hive]
import json, subprocess, os, sys, tempfile, re

HIVES = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))

def run(hive, plugins):
    out = tempfile.mktemp(suffix=".json")
    subprocess.run(["regipy-plugins-run", os.path.join(HIVES, hive), "-o", out,
                    "-p", ",".join(plugins), "--include-unvalidated", "--continue-on-error"],
                   capture_output=True, text=True)
    d = json.load(open(out)); os.remove(out); return d

SUS = re.compile(r"\\temp\\|\\appdata\\|\\users\\public|\\programdata\\|\\dllhost\\|"
                 r"powershell|cmd\.exe|/c |mshta|rundll32|regsvr32", re.I)

print("=== Lab 4.5: Persistence hunting (Run keys / IFEO / services) ===\n")

print("--- [1] Autostart Run keys ---")
sp = run("SOFTWARE", ["software_plugin"]).get("software_plugin") or {}
for kp, info in (sp.items() if isinstance(sp, dict) else []):
    for v in info.get("values", []):
        flag = "   <== DANG NGO" if SUS.search(v.get("value") or "") else ""
        print("   [SOFTWARE%s] %s = %s%s" % (kp, v.get("name"), v.get("value"), flag))
npv = run("NTUSER.DAT", ["ntuser_persistence"]).get("ntuser_persistence") or {}
for kp, info in (npv.items() if isinstance(npv, dict) else []):
    for v in info.get("values", []):
        print("   [NTUSER%s] %s = %s" % (kp, v.get("name"), v.get("value")))
print()

print("--- [2] Image File Execution Options (Debugger hijack) ---")
ifeo = run("SOFTWARE", ["image_file_execution_options"]).get("image_file_execution_options") or []
withdbg = [e for e in ifeo if isinstance(e, dict) and (e.get("Debugger") or e.get("debugger"))]
print("   tong entry IFEO:", len(ifeo), "| co Debugger:", len(withdbg))
for e in withdbg[:8]:
    print("   ", e)
print()

print("--- [3] Services: quet ImagePath tro cho la ---")
svc = run("SYSTEM", ["services"]).get("services") or {}
cs1 = None
for k in svc:
    if "ControlSet001" in k:
        cs1 = svc[k]; break
cs1 = cs1 or (next(iter(svc.values())) if isinstance(svc, dict) else {})
services = cs1.get("services") if isinstance(cs1, dict) else (cs1 if isinstance(cs1, list) else [])

def image_path(s):
    for v in (s.get("values") or []):
        if isinstance(v, dict) and (v.get("name") or "").lower() == "imagepath":
            return v.get("value")
    return None

LEGIT = re.compile(r"system32\\dllhost\.exe /Processid", re.I)  # COMSysApp hop le
total = withip = sus = 0
for s in services:
    if not isinstance(s, dict):
        continue
    total += 1
    ip = image_path(s)
    if not ip:
        continue
    withip += 1
    if SUS.search(ip) and not LEGIT.search(ip):
        sus += 1
        print("   %s -> %s   <== DANG NGO" % (s.get("name"), ip))
print("   tong service: %d | co ImagePath: %d | dang ngo: %d" % (total, withip, sus))
print("   (hive nay la baseline sach: khong co service ImagePath tro Temp/Public/PowerShell.")
print("    COMSysApp dung dllhost.exe la HOP LE (COM+), minh hoa false positive can doi chieu.)")
