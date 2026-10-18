#!/usr/bin/env bash
# Lab 11.1 - walkthrough + script giai mini challenge pcap.
# Di dung quy trinh bai 11.1: thong ke giao thuc -> export HTTP object ->
# nhan ra zip co mat khau -> tim mat khau trong DNS -> giai nen lay flag.
#
# Dung: bash solve.sh [thu_muc_chal]   (mac dinh ./chal)
set -u
C="${1:-chal}"
PCAP="$C/capture.pcap"
line(){ printf '\n==== %s ====\n' "$1"; }
[ -f "$PCAP" ] || { echo "Thieu $PCAP (chay make_artifacts.py truoc)"; exit 1; }

line "1. Quan sat tong the: loai file va thong ke giao thuc"
file "$PCAP"
tshark -r "$PCAP" -q -z io,phs 2>/dev/null | sed -n '/Protocol Hierarchy/,/====/p'

line "2. Cac HTTP request (theo goi y 'tai file')"
tshark -r "$PCAP" -Y http.request -T fields -e http.host -e http.request.uri 2>/dev/null

line "3. Export moi HTTP object"
rm -rf "$C/objs"; mkdir -p "$C/objs"
tshark -r "$PCAP" --export-objects "http,$C/objs" >/dev/null 2>&1
ls -la "$C/objs"
file "$C/objs/secret.zip"

line "4. Thu giai nen: zip co mat khau"
if unzip -o "$C/objs/secret.zip" -d "$C/objs/out" 2>&1 | grep -qi "password"; then
  echo "  -> secret.zip YEU CAU mat khau (unzip bao 'password required')"
else
  echo "  -> (unzip khong doi mat khau; xem output tren)"
fi

line "5. Tim mat khau trong kenh khac: DNS"
tshark -r "$PCAP" -Y dns -T fields -e dns.qry.name -e dns.txt 2>/dev/null | sort -u
LABEL=$(tshark -r "$PCAP" -Y "dns.flags.response==0" -T fields -e dns.qry.name 2>/dev/null \
        | head -1 | cut -d. -f1)
echo "  Nhan subdomain base64: $LABEL"

line "6. Giai base64 nhan DNS -> mat khau"
PASS_FROM_LABEL=$(python3 -I -c "import base64,sys; s=sys.argv[1]; s+='='*(-len(s)%4); print(base64.b64decode(s).decode())" "$LABEL")
echo "  base64 -d: $PASS_FROM_LABEL"
# cung co trong ban ghi TXT: zippw=...
PASS=$(tshark -r "$PCAP" -Y "dns.txt" -T fields -e dns.txt 2>/dev/null | grep -o 'zippw=.*' | head -1 | cut -d= -f2)
echo "  TXT record cho:  zippw=$PASS"

line "7. Giai nen lay flag"
unzip -o -P "$PASS" "$C/objs/secret.zip" -d "$C/objs/out" >/dev/null 2>&1
echo "  Noi dung flag.txt:"
cat "$C/objs/out/flag.txt"

line "KET LUAN"
echo "  Chuoi ky nang: thong ke giao thuc -> export HTTP object -> zip co mat khau"
echo "  -> mat khau giau trong DNS (base64 + ban ghi TXT) -> giai nen ra flag."
echo "  FLAG: $(cat "$C/objs/out/flag.txt")"
