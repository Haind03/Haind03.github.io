# Lab 4.3: Program execution (Prefetch / Amcache / Shimcache)

Lab CHAY THAT tren Linux. Lay SHA1 binary tu `Amcache.hve`, doc Shimcache tu `SYSTEM`, doc
UserAssist tu `NTUSER.DAT`, tat ca bang `regipy`. Hive la artifact DU LIEU, khong phai file
thuc thi.

Nguon hive: bo test data `regipy` (github.com/mkorman90/regipy, MIT).

## Cong cu
`regipy[cli]`, `tabulate`, `python3`, `curl`, `xz`.

```bash
pip install 'regipy[cli]' tabulate
```

## Chay lab
```bash
bash fetch.sh    # tai amcache.hve, SYSTEM, NTUSER.DAT
bash solve.sh    # Amcache SHA1 + Shimcache + UserAssist
```
`transcript.txt` la output THAT.

## Nhiem vu (co lab chay that)
1. Amcache: dem so entry co SHA1 (hive nay 1367). Lay SHA1 cua vai file trong `AppData\Temp`
   roi tra IOC (VirusTotal). Nho: Amcache chung minh file HIEN DIEN + cho hash, khong chung
   minh da chay.
2. Shimcache: in path + `last_mod_date`. Khang dinh day la mtime (last modified) cua file,
   KHONG phai gio chay. Thu tu entry (moi nhat o dau) chi goi y thu tu tuong doi.
3. UserAssist: liet ke top theo run_counter + last run. Day la chuong trinh chay QUA
   Explorer (double click, Start menu), co so lan va thoi diem.

## Nhiem vu la bai tap (can Windows 10/11 cho du bo nguon)
- Prefetch: lab khong-root nay khong tao duoc `.pf` (co che cua Windows). Tren VM, chay mot
  binary vai lan, trich `C:\Windows\Prefetch\*.pf`, parse bang `PECmd.exe -f X.pf` de lay
  run count + 8 moc chay gan nhat + danh sach file referenced.
- BAM/DAM: hive Win7 o day khong co (BAM la tu Win10 1709). Tren Win10, chay
  `regipy-plugins-run SYSTEM -p background_activity_moderator` hoac `rip.pl -r SYSTEM -p bam`
  de lay last execution theo SID.
- SRUM: trich `C:\Windows\System32\sru\SRUDB.dat` kem `SOFTWARE`, parse bang `SrumECmd.exe`
  de lay byte gui/nhan theo app (bang chung exfiltration).
- Ghep 6 nguon (Prefetch, BAM, UserAssist, Amcache, SRUM, Shimcache) cho mot binary nghi van
  va viet ket luan 5 dong, neu ro nguon nao noi gi.

## Dap an rut gon
- Amcache co SHA1 cho tung file (vd `setup64.exe` sha1 `e992f0c2...`), dung de tra IOC.
- Shimcache `last_mod_date` la mtime, vd `cmd.exe` mtime 2010-11-20. Khong phai gio chay.
- UserAssist cho thay Welcome Center, Media Center, Calculator... chay qua Explorer.
