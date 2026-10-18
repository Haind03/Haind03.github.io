# Lab 9.3 - IOC/YARA: viet rule va quet mau

Lab chay that, 100% local, dung `yara-python` (import yara, bien dich rule, match).

## Muc tieu
- Viet YARA rule co ca string MANH (hiem) va nhom string YEU (pho bien).
- Quet mot thu muc tron mau "mã độc" gia voi file sach.
- Thay rule YEU false positive, rule MANH thi khong -> hieu vi sao trộn strong/weak.

## An toan
Mau "mã độc" (`invoice_2026.exe`) la file HOAN TOAN VO HAI do `make.py` tu sinh: chi la
PE gia chua vai chuoi dac trung, khong phai binary chay duoc. KHONG tai mã độc that vao lab nay.

## Chay
```
python3 -I make.py    # tao samples/ (1 mau gia + file sach + 1 file lanh chua tu 'malware')
python3 -I scan.py    # bien dich rules.yar va quet samples/, in chuoi khop
```

## File trong lab
- `make.py` - sinh thu muc `samples/`.
- `samples/` - artifact (tong < 2 KB): invoice_2026.exe, setup.exe, readme.txt, photo.jpg, it_report.txt.
- `rules.yar` - 1 rule yeu (`LAB_marker_weak`) + 1 rule manh (`LAB_BADGER_strong`).
- `scan.py` - yara-python quet + in chi tiet chuoi khop (kieu `yara -s`).
- `transcript.txt` - output THAT.

## Ket qua (xem transcript)
| file              | khop                              | ghi chu                        |
|-------------------|-----------------------------------|--------------------------------|
| invoice_2026.exe  | LAB_marker_weak, LAB_BADGER_strong| mau that                       |
| it_report.txt     | LAB_marker_weak                   | FALSE POSITIVE cua rule yeu    |
| setup.exe         | clean                             | co API yeu nhung thieu marker  |
| readme.txt        | clean                             |                                |
| photo.jpg         | clean                             |                                |

## Diem cot loi
- Rule YEU (`$w = "malware"`) khop ca file lanh (ghi chu IT) -> false positive, va de ne (doi tu la truot).
- Rule MANH yeu cau: `uint16(0)==0x5A4D` (magic MZ) + `filesize<1MB` + mot chuoi hiem (`Global\LAB_BADGER_`)
  + bang chung C2 + 2 trong nhom API. Nho vay khong khop `it_report.txt` lan `setup.exe`.
- Trộn string manh (mot la du) voi string yeu (can vai cai) la cach bat ca HO ma it false positive.
- Gioi han bang magic byte va filesize giup quet nhanh va it khop nham tai lieu.

## Nhiem vu tu lam them
1. Doi `invoice_2026.exe` mot byte (ngoai vung chuoi): rule MANH van khop (khong phu thuoc hash), rule theo hash thi truot.
2. Them mot file lanh khac co chua `VirtualAllocEx` + `CreateRemoteThread` nhung khong co marker; xac nhan rule MANH khong khop.
3. Ha nguong trong condition (vi du bo `$mutex`, chi can `2 of ($api*)`) va quan sat false positive xuat hien nhu the nao.
