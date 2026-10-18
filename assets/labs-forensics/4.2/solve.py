#!/usr/bin/env python3
# Lab 4.2 solver: loc Event ID quan trong tu .evtx bang python-evtx, tim su kien dang ngo.
# Chay: python3 -I solve.py [duong_dan_evtx]
import sys, os, xml.etree.ElementTree as ET
from collections import Counter
from Evtx.Evtx import Evtx

NS = "{http://schemas.microsoft.com/win/2004/08/events/event}"
HERE = os.path.dirname(os.path.abspath(__file__))
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "security_4624_4688.evtx")

def field(root, name):
    for d in root.iter("%sData" % NS):
        if d.get("Name") == name:
            return d.text
    return None

def sysval(root, tag):
    el = root.find("%sSystem/%s%s" % (NS, NS, tag))
    return el.text if el is not None else None

def ts(root):
    el = root.find("%sSystem/%sTimeCreated" % (NS, NS))
    return el.get("SystemTime") if el is not None else None

LOGON_TYPE = {"2": "Interactive", "3": "Network", "4": "Batch", "5": "Service", "7": "Unlock",
              "8": "NetworkCleartext", "9": "NewCredentials", "10": "RemoteInteractive",
              "11": "CachedInteractive"}

print("=== Lab 4.2: Event log triage (python-evtx) ===")
print("file:", os.path.basename(path), "\n")

rows = []
with Evtx(path) as log:
    for rec in log.records():
        root = ET.fromstring(rec.xml())
        rows.append((ts(root), sysval(root, "EventID"), root))

print("--- Phan bo Event ID ---")
for k, v in Counter(r[1] for r in rows).most_common():
    print("   EventID %s : %d" % (k, v))
print()

print("--- 4624 Logon (LogonType, account, nguon) ---")
for t, eid, root in rows:
    if eid == "4624":
        lt = field(root, "LogonType")
        print("   %s  user=%s\\%s  type=%s(%s)  src=%s  auth=%s" % (
            t, field(root, "TargetDomainName"), field(root, "TargetUserName"),
            lt, LOGON_TYPE.get(lt, "?"), field(root, "IpAddress"),
            field(root, "AuthenticationPackageName")))
print()

print("--- 4688 Process creation ---")
for t, eid, root in rows:
    if eid == "4688":
        print("   %s  new=%s  cmdline=%r  parent=%s" % (
            t, field(root, "NewProcessName"), field(root, "CommandLine"),
            field(root, "ParentProcessName")))
print("   (CommandLine rong => may chua bat 'include command line in 4688'; xem bai hoc muc 1.2)")
print()

print("--- 4625 Failed logon ---")
if not any(eid == "4625" for _, eid, _ in rows):
    print("   (khong co 4625 trong mau nay)")
else:
    for t, eid, root in rows:
        if eid == "4625":
            print("   %s  user=%s  status=%s subStatus=%s" % (
                t, field(root, "TargetUserName"), field(root, "Status"), field(root, "SubStatus")))
print()

print("--- SU KIEN DANG NGO ---")
for t, eid, root in rows:
    if eid == "1102":
        su = root.find(".//{http://manifests.microsoft.com/win/2004/08/windows/eventlog}SubjectUserName")
        print("   [1102] Security log BI XOA luc %s, tai khoan: %s"
              % (t, su.text if su is not None else "?"))
    if eid == "4688" and (field(root, "ParentProcessName") or "").lower().endswith("wmiprvse.exe"):
        print("   [4688] %s sinh ra boi WmiPrvSE.exe luc %s => thuc thi tu xa qua WMI (vd wmiexec)"
              % (field(root, "NewProcessName"), t))
