#!/usr/bin/env python3
# Lab 4.1 solver: dung regipy doc hive offline -> system context, USB, autorun, user activity.
# Chay: python3 -I solve.py [thu_muc_chua_hive]   (mac dinh: thu muc cua script nay)
import json, subprocess, os, sys, tempfile

HIVES = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))

def run(hive, plugins):
    out = tempfile.mktemp(suffix=".json")
    subprocess.run(["regipy-plugins-run", os.path.join(HIVES, hive), "-o", out,
                    "-p", ",".join(plugins), "--include-unvalidated", "--continue-on-error"],
                   capture_output=True, text=True)
    d = json.load(open(out)); os.remove(out); return d

def cs1(d, key):
    v = d.get(key)
    if isinstance(v, dict):
        for k in v:
            if "ControlSet001" in k: return v[k]
        return next(iter(v.values()), None)
    return v

print("=== Lab 4.1: Registry forensics (hive offline, regipy) ===\n")

sysd = run("SYSTEM", ["computer_name", "timezone_data", "shutdown", "active_control_set",
                      "usbstor_plugin", "usb_devices", "mounted_devices"])
print("--- [1] Boi canh may ---")
cn = sysd.get("computer_name")
print("ComputerName:", [c.get("name") for c in cn] if isinstance(cn, list) else cn)
tz = cs1(sysd, "timezone_data")
if isinstance(tz, list):
    kv = {x["name"]: x["value"] for x in tz if isinstance(x, dict)}
    bias = kv.get("Bias")
    try:
        utc = "UTC%+d" % (-int(bias) / 60)
    except Exception:
        utc = "?"
    print("TimeZone Bias (phut):", bias, "=>", utc, "(moi timestamp registry la UTC)")
print("Select (ControlSet dang dung):", sysd.get("active_control_set"))
print()

print("--- [2] Lich su USB (USBSTOR, ControlSet001) ---")
for dev in (sysd.get("usbstor_plugin") or []):
    if "ControlSet001" in dev.get("key_path", ""):
        print("  %s %s %s | serial=%s | lastwrite=%s" % (
            dev.get("manufacturer"), dev.get("title"), dev.get("version"),
            dev.get("serial_number"), dev.get("last_write")))
print()

print("--- [3] Autorun / persistence ---")
sp = run("SOFTWARE", ["software_plugin"]).get("software_plugin") or {}
for keypath, info in (sp.items() if isinstance(sp, dict) else []):
    print("  SOFTWARE%s (lastwrite %s)" % (keypath, info.get("timestamp")))
    for v in info.get("values", []):
        print("     %s = %s" % (v.get("name"), v.get("value")))
npv = run("NTUSER.DAT", ["ntuser_persistence"]).get("ntuser_persistence") or {}
for keypath, info in (npv.items() if isinstance(npv, dict) else []):
    print("  NTUSER%s (lastwrite %s)" % (keypath, info.get("timestamp")))
    for v in info.get("values", []):
        print("     %s = %s" % (v.get("name"), v.get("value")))
print()

print("--- [4] Hoat dong user (NTUSER) ---")
act = run("NTUSER.DAT", ["user_assist", "word_wheel_query", "winrar_plugin", "typed_paths"])
ua = [x for x in (act.get("user_assist") or []) if isinstance(x, dict)]
print("UserAssist: %d entries. Top 5 theo run_counter:" % len(ua))
seen = set(); shown = 0
for e in sorted(ua, key=lambda x: x.get("run_counter") or 0, reverse=True):
    if e.get("name") in seen: continue
    seen.add(e.get("name"))
    print("   run=%s  last=%s  %s" % (e.get("run_counter"), e.get("timestamp"), e.get("name")))
    shown += 1
    if shown >= 5: break
wwq = act.get("word_wheel_query") or []
print("WordWheelQuery (tu khoa Explorer search):", [e.get("name") for e in wwq if isinstance(e, dict)])
wr = [e for e in (act.get("winrar_plugin") or []) if isinstance(e, dict) and e.get("file_path")]
if wr:
    print("WinRAR history (archive da mo):")
    for e in wr[:4]:
        print("   %s  (%s)" % (e.get("file_path"), e.get("last_write")))
