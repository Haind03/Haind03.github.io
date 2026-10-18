# Lab 11.1: Mini challenge forensics CTF (pcap + DNS exfil)

Lab chay that di kem [Bai 11.1](../../phan-11-thuc-chien/11.1-ctf-forensics.md). Day la mot
challenge tu chua, tai tao dung ky thuat demo trong bai. Khong dung du lieu that; domain
`files.example.ctf` va dai IP `192.168.56.0/24` deu la dia chi vi du.

De bai: "Nhan vien tai nham mot file. Lay lai noi dung bi mat." Flag dang `flag{...}`.

## File trong lab
- `make_artifacts.py` tao `chal/capture.pcap` (scapy): mot phien HTTP tai `secret.zip`
  (co mat khau ZipCrypto), kem mot truy van DNS TXT mang mat khau da base64. Flag chi nam
  trong zip, buoc nguoi choi phai giai mat khau truoc.
- `solve.sh` di het walkthrough: `tshark -z io,phs` -> `--export-objects http` ->
  nhan ra zip co mat khau -> doc DNS (`dns.qry.name`, `dns.txt`) -> `base64 -d` ->
  `unzip -P` -> `cat flag.txt`.
- `transcript.txt` output that, co flag.

## Chay
```bash
python3 -I make_artifacts.py chal
bash solve.sh chal
```
Can `tshark`, `unzip`, `python3`. Khong can quyen root (chi doc file pcap).

## Walkthrough (tom tat)
1. `file capture.pcap` -> dung la pcap. `tshark -z io,phs` -> co HTTP va DNS.
2. `tshark -Y http.request` -> thay tai `/download/secret.zip`.
3. `tshark --export-objects http,objs` -> lay ra `secret.zip`.
4. `unzip secret.zip` -> doi mat khau.
5. `tshark -Y dns` -> mot query toi `cGFzczpaMXBLM3lfRE5TXzIwMjY.files.example.ctf`
   va TXT tra ve `zippw=...`. Nhan subdomain trong nhu base64.
6. `base64 -d` nhan do -> `pass:Z1pK3y_DNS_2026`.
7. `unzip -P 'Z1pK3y_DNS_2026' secret.zip` -> `cat flag.txt`.

## Flag
```
flag{dns_txt_carried_the_zip_key}
```

## Bai hoc rut ra
- Luon thong ke giao thuc truoc de dinh huong, dung doan mo.
- HTTP object export lay nguyen file ra khoi capture.
- DNS (va ICMP) la kenh giau du lieu kinh dien, de bi bo qua.
- Nhieu flag chi bi encode nhe (base64/hex/rot13); CyberChef giai nhanh neu thich GUI.
