# Lab 11.3: Khung bao cao forensics tu IOC (exercise)

Lab di kem [Bai 11.3](../../phan-11-thuc-chien/11.3-do-an-bao-cao.md). Day la EXERCISE:
noi dung van ban cua bao cao (executive summary, findings, ket luan) van phai do dieu tra
vien viet tay. Lab cung cap mot template chuan va mot cong cu nho de sinh KHUNG bao cao,
tu dong dien cac muc may lam duoc (timeline, bang IOC, phu luc, metadata) tu mot file IOC.

## File trong lab
- `report_template.md` template bao cao 10 muc theo bai hoc, co placeholder `{{...}}` va cac
  danh dau `[AUTO]` (may dien) va `[TODO]` (nguoi viet).
- `ioc.json` file IOC dau vao (chinh la ket qua cua lab 11.2, co bo sung mot timeline).
- `gen_report.py` doc `ioc.json` + template, dien cac muc AUTO, giu cac muc TODO, in khung
  bao cao ra stdout.
- `transcript.txt` output that cua mot lan sinh khung bao cao.

## Chay
```bash
python3 -I gen_report.py ioc.json --analyst "HaiND" --tlp AMBER > bao-cao.md
```
Co the lay `ioc.json` do chinh `solve.py` cua lab 11.2 sinh ra (no xuat `iocs.json` vao thu
muc case), chi can doi ten/them truong `timeline` neu muon muc Timeline tu dien.

## Nhiem vu (khop muc 3 cua bai hoc)
1. Viet Executive Summary mot trang, khong thuat ngu, cho nguoi khong ky thuat.
2. It nhat nam finding theo khuon fact / opinion / gioi han, moi fact tro phu luc.
3. Timeline tong hop (muc 6 da duoc sinh san tu IOC, bo sung tay neu thieu).
4. Bang IOC day du (muc 7 da sinh san).
5. Bang chain of custody cho moi muc bang chung, co hash.
6. Phu luc danh so khop voi finding.

## Vi sao la exercise
- Cong cu chi lam duoc phan "co cau truc" (bang IOC, timeline, metadata, danh sach phu luc).
- Phan quan trong nhat (dien giai fact/opinion, muc do chac chan, gioi han, khuyen nghi) la
  ky nang con nguoi, khong tu dong hoa duoc, nen de nguyen `[TODO]` trong khung.
