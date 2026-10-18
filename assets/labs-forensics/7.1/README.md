# Lab 7.1 - Wireshark/tshark: trich file tu phien HTTP

Lab chay that, 100% local. pcap duoc tao bang scapy nen khong can bat mang that.

## Muc tieu
- Dung `capinfos` xem so goi va cua so thoi gian.
- Dung Conversations tim phien nang nhat (cap IP:port).
- Loc `http.request`, Follow HTTP Stream, xac nhan magic byte `MZ`.
- Export Objects HTTP lay file ra, so SHA-256 voi file goc de chung minh nguyen ven.

## Cong cu
`scapy` (tao pcap), `tshark` + `capinfos` (doc/loc/-z/--export-objects), `sha256sum`, `file`.
Bai goc noi ve Wireshark GUI; o day dung `tshark` (CLI cua Wireshark) de lab chay va script hoa duoc.
Moi thao tac GUI (Conversations, Follow Stream, Export Objects) deu co lenh tshark tuong duong.

## Chay
```
python3 -I make.py    # tao lab71.pcap + expected_update.exe (file goc de doi chieu)
./solve.sh            # dieu tra + trich file + verify hash
```

## File trong lab
- `make.py` - scapy dung mot phien HTTP hoan chinh (DNS, 3-way handshake, GET, 200 OK co body, teardown).
- `lab71.pcap` - artifact (~1.8 KB, < 2 MB).
- `expected_update.exe` - file goc da nhung vao phien, de so hash sau khi trich.
- `solve.sh` - tshark dieu tra 5 buoc.
- `transcript.txt` - output THAT.

## Diem cot loi
- File "tai ve" la mot PE gia vo hai, bat dau bang magic `MZ` (0x4D5A). Follow Stream cho thay magic nay ngay dau body.
- `--export-objects http` tai dung payload HTTP da reassemble tu nhieu TCP segment.
- SHA-256 cua file trich == SHA-256 file goc: chung minh pcap chua du du lieu va khong mat goi.
- `file` nhan dien MZ du ten header co the gia; luon kiem tra loai that, dung tin ten khai bao.

## Nhiem vu tu lam them
1. Doi Content-Disposition filename trong `make.py` thanh ten khac, chay lai, xac nhan `file` van bao MZ (ten khong quyet dinh loai).
2. Xoa bot vai goi response trong pcap (mo phong capture rot goi) va quan sat export that bai hoac file hong.
3. Loc `dns` va doi chieu ten `files.lab.test` phan giai ra IP nao, roi khoanh dung phien TCP den IP do.
