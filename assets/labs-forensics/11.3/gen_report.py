#!/usr/bin/env python3
# Lab 11.3 - cong cu nho: sinh KHUNG bao cao forensics tu mot file IOC (JSON) va
# report_template.md. Cac muc auto (timeline, bang IOC, phu luc, metadata) duoc dien
# san; cac muc van ban (executive summary, findings, ket luan) de [TODO] cho dieu tra
# vien viet tay. Day la cong cu/exercise, khong thay the viec viet bao cao.
#
# Dung: python3 -I gen_report.py ioc.json [--analyst "Ten"] [--tlp AMBER] > bao-cao.md

import sys
import json
import argparse
import datetime

def ioc_table(d):
    rows = []
    rows.append("| Loai | Gia tri | Ghi chu |")
    rows.append("|------|---------|---------|")
    for ip in d.get("ip", []):
        rows.append(f"| ip | {ip} | C2 hoac nguon tan cong |")
    for u in d.get("url", []):
        rows.append(f"| url | {u} | kenh C2 |")
    for ua in d.get("user_agent", []):
        rows.append(f"| ua | {ua} | nhan dien ho malware |")
    for m in d.get("mutex", []):
        rows.append(f"| mutex | {m} | nhan dien ho malware |")
    for p in d.get("paths", []):
        rows.append(f"| path | {p} | vi tri tren disk |")
    for path, dg in d.get("sha256", {}).items():
        rows.append(f"| sha256 | {dg} | {path} |")
    for pr in d.get("persistence", []):
        rows.append(f"| persistence | {pr} | co che bam lai |")
    return "\n".join(rows)

def timeline_block(d):
    tl = d.get("timeline", [])
    if not tl:
        return "[TODO: chua co timeline trong IOC, bo sung tay]"
    rows = ["| Thoi gian (UTC) | Su kien | ATT&CK | Phu luc |",
            "|-----------------|---------|--------|---------|"]
    for item in tl:
        t, ev, attack, apx = (list(item) + ["", "", ""])[:4]
        rows.append(f"| {t} | {ev} | {attack} | {apx} |")
    return "\n".join(rows)

def appendix_block(d):
    items = []
    n = 1
    for path, dg in d.get("sha256", {}).items():
        items.append(f"- A-{n}: hash + mo ta `{path}` (sha256 {dg[:16]}...)")
        n += 1
    for pr in d.get("persistence", []):
        items.append(f"- A-{n}: noi dung `{pr}`")
        n += 1
    for af in d.get("anti_forensics", []):
        items.append(f"- A-{n}: bang chung anti-forensic: {af}")
        n += 1
    items.append(f"- A-{n}: [TODO] anh chup output cong cu, mapping ATT&CK Navigator")
    return "\n".join(items)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ioc")
    ap.add_argument("--template", default=None)
    ap.add_argument("--analyst", default="[TODO: ten dieu tra vien]")
    ap.add_argument("--tlp", default="AMBER")
    args = ap.parse_args()

    import os
    tpl_path = args.template or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             "report_template.md")
    with open(args.ioc, encoding="utf-8") as f:
        d = json.load(f)
    with open(tpl_path, encoding="utf-8") as f:
        tpl = f.read()

    repl = {
        "{{CASE}}": d.get("case", "[TODO]"),
        "{{HOST}}": d.get("host", "[TODO]"),
        "{{DATE}}": datetime.date.today().isoformat(),
        "{{ANALYST}}": args.analyst,
        "{{TLP}}": args.tlp,
        "{{INITIAL_ACCESS}}": d.get("initial_access", "[TODO]"),
        "{{TIMELINE}}": timeline_block(d),
        "{{IOC_TABLE}}": ioc_table(d),
        "{{APPENDIX}}": appendix_block(d),
    }
    for k, v in repl.items():
        tpl = tpl.replace(k, v)
    sys.stdout.write(tpl)

if __name__ == "__main__":
    main()
