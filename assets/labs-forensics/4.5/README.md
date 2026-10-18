# Lab 4.5: Persistence tren Windows (Run keys / IFEO / services)

Lab CHAY THAT tren Linux. Quet cac diem persistence tu hive offline bang `regipy`: Run keys
(SOFTWARE + NTUSER), Image File Execution Options (SOFTWARE), services (SYSTEM). Hive la
artifact DU LIEU, khong phai file thuc thi.

Nguon hive: regipy test data (github.com/mkorman90/regipy, MIT). Dung chung may Windows 7
lab voi Lab 4.1.

## Cong cu
`regipy[cli]`, `tabulate`, `python3`, `curl`, `xz`.

```bash
pip install 'regipy[cli]' tabulate
```

## Chay lab
```bash
bash fetch.sh    # tai SOFTWARE, SYSTEM, NTUSER.DAT
bash solve.sh    # Run keys + IFEO + services, co flag DANG NGO
```
`transcript.txt` la output THAT.

## Nhiem vu (co lab chay that)
1. Run keys: liet ke HKLM (SOFTWARE) va HKCU (NTUSER). Chi ra entry masquerading
   `svchost = c:\windows\system32\dllhost\svchost.exe` (svchost.exe that o thang `system32`,
   khong o thu muc con `dllhost`). Day la persistence do attacker them.
2. IFEO: dem entry co value `Debugger` (hijack mot exe). Hive nay co 32 entry IFEO nhung 0
   cai co Debugger (khong co hijack).
3. Services: quet ImagePath tro Temp/Public/ProgramData/PowerShell. Hive nay sach (0 dang
   ngo). Luu y COMSysApp dung `dllhost.exe` la HOP LE (COM+ System Application), day la mot
   false positive dien hinh can doi chieu voi may sach cung ban Windows.

## Nhiem vu la bai tap (can VM Windows + event log)
4. Tren VM, tu cai 5 persistence vo hai tro toi mot script in log: Run key (HKCU + HKLM),
   `sc create` mot service, `schtasks /create` mot scheduled task, mot WMI subscription
   (`__EventFilter` + `CommandLineEventConsumer` + binding), mot file trong Startup folder.
   Reboot. Trich hive + `System32\Tasks` (XML) + `wbem\Repository\OBJECTS.DATA` + `winevt\Logs`.
5. Chay lai `solve.py` tren hive do. Doc scheduled task tu file XML (`<Command>`, `<Triggers>`),
   doi chieu event 106 (TaskScheduler/Operational). Lay moc service tu 7045 (System).
   Dò WMI bang `PyWMIPersistenceFinder.py OBJECTS.DATA`, doi chieu event 5861.
6. Chay `autorunsc.exe -a * -h -s -c -o autoruns.csv` va kiem no bat duoc may cai, bo sot cai nao.

## Dap an rut gon
- Persistence do attacker: Run key `svchost -> c:\windows\system32\dllhost\svchost.exe`.
- IFEO: 32 entry, 0 co Debugger.
- Services: 467 service, 401 co ImagePath, 0 dang ngo (baseline sach). COMSysApp la legit.
