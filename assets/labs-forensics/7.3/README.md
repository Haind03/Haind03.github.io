# Lab 7.3 - Phat hien C2 beacon va DNS tunnel exfil

Lab chay that, 100% local. pcap tao bang scapy.

## Muc tieu
- Do nhip beacon: tinh interval trung binh + jitter (stdev), ket luan nhip deu.
- Phat hien DNS tunnel: entropy Shannon ten nhan + so query tren mot domain cha.
- Giai ma du lieu tunnel (base32) de doc bi mat bi tuon ra.

## Cong cu
`scapy` (tao pcap), `tshark` (rut truong `-T fields`), `python3` (interval, entropy, base32 decode).
Khong can zeek: beacon va entropy deu tinh duoc tu truong tshark xuat ra.

## Chay
```
python3 -I make.py     # tao lab73.pcap + expected_secret.txt (ground truth)
python3 -I solve.py    # phat hien beacon + tunnel + giai ma
```

## Noi dung pcap (ground truth)
- Beacon: 10.0.0.50 -> 10.0.0.200:443, 12 ket noi moi ~60s, jitter +/-5s (seed co dinh 1337).
- DNS lanh: www.google.com, api.github.com, update.microsoft.com, cdn.jsdelivr.net (de doi chieu entropy).
- DNS tunnel: 4 query TXT toi `*.t.evil-tunnel.test`, moi nhan la base32 cua mot phan secret.
- Secret: `SESSION_TOKEN=4f9c2a1b7e;card=4111111111111111;exfil-via-dns-labels`.

## File trong lab
- `make.py`, `lab73.pcap` (~8.5 KB, < 2 MB), `expected_secret.txt`, `solve.py`, `transcript.txt`.

## Diem cot loi
- Beacon lo vi nhip qua deu: he so bien thien (stdev/mean) ~0.05, rat thap. Beacon that luon
  co jitter nen interval khong bang nhau tuyet doi; nhin phan bo co cum, dung doi deu tam tap.
- DNS tunnel: domain cha `t.evil-tunnel.test` co nhieu query, nhan rat dai (~29 ky tu),
  entropy ~4.0 bit/ky tu, trong khi domain lanh entropy thap (0-2.6). Phai KET HOP so luong
  query + do dai + entropy, dung chi dua entropy (CDN kieu `d1a2b3c4.cloudfront.net` cung entropy cao).
- Giai ma: ghep cac nhan theo so thu tu, base32-decode ra dung bi mat.

## Nhiem vu tu lam them
1. Tang jitter trong `make.py` (vi du +/-25s), chay lai, xem he so bien thien tang the nao va
   nguong 0.2 con phan biet duoc beacon khong.
2. Them vai query toi mot CDN entropy cao (nhan ngau nhien) va chinh `solve.py` de khong bao
   nham CDN la tunnel (goi y: them dieu kien so luong query va kieu ban ghi TXT).
3. Doi secret trong `make.py`, chay lai, xac nhan `solve.py` giai dung secret moi.
