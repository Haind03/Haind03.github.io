# Lab 4.2: Event log .evtx, loc Event ID va tim su kien dang ngo

Lab CHAY THAT tren Linux. Tai mot file Security `.evtx` cong khai roi parse bang
`python-evtx`. File `.evtx` la nhat ky su kien (DU LIEU), khong phai file thuc thi.

Nguon: `EVTX-ATTACK-SAMPLES` (github.com/sbousseaden/EVTX-ATTACK-SAMPLES, GPL), file
`NTLM2SelfRelay-med0x2e-security_4624_4688.evtx` (kenh Security, 11 record).

## Cong cu
`python-evtx` (module `Evtx` + lenh `evtx_dump`), `python3`, `curl`.

```bash
pip install python-evtx
```

## Chay lab
```bash
bash fetch.sh    # tai security_4624_4688.evtx
bash solve.sh    # evtx_dump raw XML + solver loc 4624/4688/4625/1102
```
`transcript.txt` la output THAT cua solver.

## Nhiem vu (co lab chay that)
1. Dem phan bo Event ID. Mau nay co 4672, 4624, 4634, 4688, 1102.
2. Doc 4624: tat ca la LogonType 3 (Network), account `Administrator`, tu IP
   `192.168.1.219`, qua Kerberos, trong khoang 04:41-04:42 ngay 2022-05-01.
3. Doc 4688: `notepad.exe` duoc sinh ra boi `C:\Windows\System32\wbem\WmiPrvSE.exe`.
   Parent la WmiPrvSE.exe => process duoc chay tu xa qua WMI (vd cong cu wmiexec), KHONG
   phai user go tay. Day la su kien dang ngo chinh.
4. `CommandLine` rong: may chua bat "include command line in process creation events", nen
   4688 khong co dong lenh. Bai hoc muc 1.2 noi ro cho nay.
5. Tim 1102: Security log bi XOA luc 04:40:18 boi tai khoan `admin`. Day la anti-forensics
   (Defense Evasion), ban than hanh dong xoa lai sinh ra mot event 1102.

## Nhiem vu la bai tap (can VM Windows)
6. Trong VM, bat "Audit Process Creation" kem command line, cai Sysmon. Dang nhap sai vai
   lan (sinh 4625 voi SubStatus `0xC000006A`), chay `powershell -enc <base64>`, `sc create`
   mot service (sinh 7045 trong System), roi `wevtutil cl Application`. Trich `winevt\Logs`
   va chay lai solver; neu CommandLine van rong thi chuyen sang Sysmon event 1.
7. Chay Hayabusa / Chainsaw tren cung thu muc log, so rule nao bat duoc hanh vi nao.

## Dap an rut gon
- 4 logon Network (type 3) tu `192.168.1.219` la `Administrator` qua Kerberos.
- `notepad.exe` chay qua `WmiPrvSE.exe` => remote WMI execution.
- Security log bi xoa luc `2022-05-01 04:40:18 UTC` boi `admin` (event 1102).
