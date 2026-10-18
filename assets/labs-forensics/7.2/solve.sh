#!/usr/bin/env bash
# Lab 7.2 - Zeek khong cai duoc o day; dung tshark xuat bang TUONG DUONG conn.log / dns.log,
# roi ghep "uid" (stream index) sang http de biet file gi, so hash file carve.
set -euo pipefail
cd "$(dirname "$0")"
PCAP=lab72.pcap
[ -f "$PCAP" ] || { echo "Chua co $PCAP. Chay: python3 -I make.py"; exit 1; }

echo "LUU Y: moi truong nay KHONG co zeek. Ta dung tshark de dung bang tuong duong"
echo "conn.log (tshark -z conv,tcp) va dns.log (tshark -T fields tren dns)."
echo

echo "============================================================"
echo "[1] conn.log tuong duong  (tshark -z conv,tcp)"
echo "============================================================"
tshark -r "$PCAP" -q -z conv,tcp

echo
echo "============================================================"
echo "[2] conn.log dang TSV goi gon (stream = uid de ghep log)"
echo "============================================================"
printf 'uid\tproto\torig_h\torig_p\tresp_h\tresp_p\tservice\n'
tshark -r "$PCAP" -Y "tcp.flags.syn==1 && tcp.flags.ack==0" \
  -T fields -e tcp.stream -e ip.src -e tcp.srcport -e ip.dst -e tcp.dstport \
  | awk -F'\t' '{print $1"\ttcp\t"$2"\t"$3"\t"$4"\t"$5"\thttp"}'

echo
echo "============================================================"
echo "[3] dns.log tuong duong  (query -> answer, TTL)"
echo "============================================================"
printf 'query\tqtype\tanswer\tttl\n'
tshark -r "$PCAP" -Y "dns.flags.response==1" \
  -T fields -e dns.qry.name -e dns.qry.type -e dns.a -e dns.resp.ttl

echo
echo "============================================================"
echo "[4] files.log tuong duong: carve file HTTP + MIME + hash"
echo "============================================================"
rm -rf files && mkdir -p files
tshark -r "$PCAP" --export-objects http,files -q
for f in files/*; do
  printf '%-14s %-22s sha256:%s\n' "$(basename "$f")" "$(file -b --mime-type "$f")" "$(sha256sum "$f" | cut -d' ' -f1)"
done

echo
echo "============================================================"
echo "[5] GHEP LOG + VERIFY: payload.exe carve == file goc; host nao connect bang IP"
echo "============================================================"
EXP=$(sha256sum expected_payload.exe | cut -d' ' -f1)
GOT=$(sha256sum files/payload.exe | cut -d' ' -f1)
printf 'payload.exe goc   : %s\n' "$EXP"
printf 'payload.exe carve : %s\n' "$GOT"
[ "$EXP" = "$GOT" ] && echo "=> MATCH: file carve nguyen ven." || { echo "=> MISMATCH"; exit 1; }
echo
echo "Ket luan ghep log:"
echo " - 10.0.0.50 phan giai files.evil.test -> 10.0.0.66, roi tai payload.exe (MZ) tu do."
echo " - 10.0.0.51 ket noi THANG 10.0.0.99 bang IP: co trong conn.log nhung VANG trong dns.log"
echo "   (khong qua DNS cung la mot ket luan - dang ngo C2 cau hinh cung IP)."
rm -rf files
