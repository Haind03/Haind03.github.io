# Lab 4.1: Registry forensics tren hive offline

Lab CHAY THAT tren Linux (khong can root, khong can Windows). Tai hive mau cong khai roi
parse bang `regipy`. Hive la artifact DU LIEU (registry database), khong phai file thuc thi.

Nguon hive: bo test data cua `regipy` (github.com/mkorman90/regipy, giay phep MIT), gom
`SYSTEM`, `SOFTWARE`, `NTUSER.DAT` cua mot may Windows 7 lab.

## Cong cu
`regipy[cli]` (lenh `regipy-plugins-run`), `tabulate`, `python3`, `curl`, `xz`.

```bash
pip install 'regipy[cli]' tabulate
```

## Chay lab
```bash
bash fetch.sh    # tai + giai nen SYSTEM, SOFTWARE, NTUSER.DAT vao thu muc lab
bash solve.sh    # computer name, timezone, USB, autorun, user activity
```
`transcript.txt` la output THAT. Hive (SYSTEM ~11MB, SOFTWARE ~37MB) khong giu trong repo,
chay `fetch.sh` tai lai.

## Nhiem vu (co lab chay that)
1. Xac dinh ten may, timezone (Bias), ControlSet dang dung (`SYSTEM\Select\Current`).
2. Lap bang USB tu USBSTOR: hang, model, serial, lastwrite. Hive nay co mot USB HP v100w
   serial `AA951D0000007252`.
3. Liet ke moi Run key va chi ra cai BAT THUONG. O hive nay co mot entry nguy trang:
   `svchost = c:\windows\system32\dllhost\svchost.exe` (svchost.exe that nam thang trong
   `system32`, khong nam trong thu muc con `dllhost`). Day la masquerading persistence.
4. Tu NTUSER doc UserAssist (run count, last run), WordWheelQuery (tu khoa search trong
   Explorer), WinRAR history (archive user `tony` da mo).

## Nhiem vu la bai tap (can hive Windows 10/11 cua ban hoac VM that)
5. Tren VM Windows 10/11, cam 2 USB, go vai lenh vao Run/Explorer, them mot Run key, tat may,
   trich hive (FTK Imager hoac mount image read-only) roi chay lai `solve.py` tren hive do.
   RegRipper (`rip.pl -r SYSTEM -p usbstor`) va Registry Explorer cho ket qua tuong duong.
6. Doi chieu serial USBSTOR voi `MountedDevices` va `setupapi.dev.log` de chot thoi diem
   cai driver lan dau (bai hoc muc 2.3).

## Dap an rut gon
- May: `WKS-WIN732BITA`, timezone Bias 300 => UTC-5, ControlSet001 dang dung.
- USB: HP v100w, serial `AA951D0000007252`.
- Autorun dang ngo: `svchost -> c:\windows\system32\dllhost\svchost.exe` (gia danh svchost).
- User `tony` mo `RegistryFinder64.zip`, `token.zip`; search cac tu `vibranium`, `adamantium`...
