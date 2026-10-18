# Lab 7.2 - Zeek/NetworkMiner thay bang tshark: conn.log / dns.log / files.log

Lab chay that, 100% local.

## Vi sao dung tshark thay Zeek
Moi truong nay KHONG cai duoc `zeek` va `NetworkMiner`. Nhung muc tieu cua bai (bang
tong hop phien kieu conn.log, bang DNS kieu dns.log, carve file kieu files.log) deu lam
duoc bang `tshark`:

| Zeek            | tshark tuong duong                                             |
|-----------------|----------------------------------------------------------------|
| conn.log        | `tshark -q -z conv,tcp`  hoac `-T fields` tren goi SYN         |
| dns.log         | `tshark -Y "dns.flags.response==1" -T fields -e dns.qry.name ...` |
| files.log + carve (NetworkMiner) | `tshark --export-objects http,<dir>` + `file` + `sha256sum` |
| `uid` ghep log  | `tcp.stream` (chi so stream) dong vai tro uid                  |

## Chay
```
python3 -I make.py    # tao lab72.pcap (3 ket noi TCP, 2 DNS) + expected_payload.exe
./solve.sh            # xuat conn.log/dns.log/files.log tuong duong + ghep log + verify
```

## File trong lab
- `make.py` - scapy dung 3 phien HTTP va 2 lan DNS (2 workstation).
- `lab72.pcap` - artifact (~3.6 KB, < 2 MB).
- `expected_payload.exe` - file goc de so hash sau carve.
- `solve.sh` - 5 buoc dieu tra.
- `transcript.txt` - output THAT.

## Diem cot loi
- `tcp.stream` (0, 1, 2) dong vai tro `uid`: ghep conn.log voi file carve va DNS.
- 10.0.0.50 phan giai `files.evil.test` -> 10.0.0.66 roi tai `payload.exe` (magic MZ).
- 10.0.0.51 ket noi THANG 10.0.0.99 bang IP: co trong conn.log nhung VANG trong dns.log.
  "Khong qua DNS" cung la mot ket luan dieu tra (C2 cau hinh cung IP, khong can resolve).
- Hash file carve == hash file goc: carve khong lam hong du lieu.

## Nhiem vu tu lam them
1. Doi service HTTP sang port khac trong `make.py`, xem conn.log con nhan "http" khong va vi sao.
2. Them mot phien TLS gia (port 443, khong co payload HTTP) va kiem tra files.log trong (khong carve duoc vi ma hoa) - noi sang bai 7.3.
3. Viet mot dong tom tat phien theo mau: ai (orig_h) - ten mien (dns.log) - luc nao (conn start) - tai bao nhieu (bytes).
