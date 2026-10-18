# Lab 6.2: Process, module nap, va ket noi mang trong RAM

Lab chay that cho Bai 6.2. Mot tien trinh "victim" giu cau hinh C2 (IOC) trong RAM va
mo mot ket noi THAT toi mot stub chay tren loopback. Ta chup bo nho no, bang ket noi
song, va danh sach module nap, roi dieu tra lai. Tat ca local, khong can root, khong
tai gi.

## Anh xa sang Volatility (y tuong)

| Buoc lab (local, chay that)                 | Plugin Vol3 tuong duong (anh Windows) |
|---------------------------------------------|---------------------------------------|
| Tim chuoi C2 nhung trong dump               | tinh than `windows.netscan` + grep RAM |
| Doc bang ket noi song (`ss -tnp`)           | `windows.netscan`                     |
| Liet ke `.so` nap vao tien trinh (`maps`)   | `windows.dlllist`                     |
| Quan he cha-con, process an                 | `windows.pstree`, `windows.psscan`    |

## Chay

```bash
DUMPDIR=_dump python3 -I capture.py   # chup dump + bang ket noi + maps
DUMPDIR=_dump bash solve.sh           # moi IOC C2, doc ket noi, liet ke module
```

## Ket qua (xem transcript.txt)

1. Cau hinh C2 nhung trong RAM hien ra nguyen van sau khi grep dump:
   `C2CONFIG|campaign=LAB62|c2_host=198.51.100.77|c2_port=4444|...`.
2. Trich ra IOC IP:cong: `198.51.100.77`, `203.0.113.9:8443`.
3. Bang ket noi song (`ss -tnp`) cho thay ket noi ESTABLISHED that giua victim va stub
   tren 127.0.0.1, kem PID so huu, dung nhu `netscan` gan ket noi voi process.
4. Tu `/proc/<pid>/maps` liet ke cac `.so` da nap (libc, libpython, _socket...),
   dung buoc `dlllist` o quy mo tien trinh.

Cac IP `198.51.100.x` va `203.0.113.x` la dai TEST-NET (RFC 5737) danh rieng cho tai
lieu, khong tro toi may that. Ket noi thuc su chi la loopback 127.0.0.1, hoan toan vo hai.

## pslist vs psscan (y tuong, khong co trong output local)

- `pslist`/`pstree` doc danh sach lien ket EPROCESS ma kernel giu
  (`ActiveProcessLinks`). Nhanh, nhung rootkit go mot node khoi danh sach (DKOM) la
  process bien mat khoi pslist.
- `psscan` quet TOAN BO bo nho tim cau truc EPROCESS theo pool tag `Proc`, khong dua
  vao danh sach kernel, nen thay ca process da thoat va process bi unlink.
- Quy tac: process co trong `psscan` ma vang trong `pslist` + `ExitTime` trong =
  nghi bi giau bang DKOM. Neu `ExitTime` co gia tri thi chi la process da thoat.

Tren Linux local khong co pool tag kieu Windows nen khong tai lap 1-1 duoc; day la
phan ban chi hieu de ap khi phan tich anh RAM Windows that.

## Lenh Volatility 3 tuong ung (anh RAM Windows that cua ban)

Khong tai anh mau co malware. Khi co anh hop phap:

```bash
vol -f mem.raw windows.pstree                       # cay cha-con
vol -r csv -f mem.raw windows.pslist > pslist.csv
vol -r csv -f mem.raw windows.psscan > psscan.csv
comm -13 <(cut -d, -f3 pslist.csv | sort -u) \
         <(cut -d, -f3 psscan.csv | sort -u)        # PID chi co trong psscan
vol -f mem.raw windows.dlllist --pid <PID>          # DLL nap (bat path la)
vol -f mem.raw windows.handles --pid <PID> | grep -iE "Mutant|File|Key"
vol -f mem.raw windows.netscan | grep -E "ESTABLISHED|LISTENING"
vol -f mem.raw windows.cmdline | grep -iE "powershell|rundll32|mshta"
```

## Files

- `c2_stub.py`: may chu gia lap tren loopback (vo hai), de co ket noi that.
- `victim.py`: tien trinh giu C2 config trong RAM, ket noi toi stub.
- `capture.py`: chup dump + bang ket noi (`ss`) + `/proc/<pid>/maps`.
- `solve.sh`: moi IOC C2, doc ket noi, liet ke module nap.
- `transcript.txt`: output that.

## Don dep

```bash
rm -rf _dump /tmp/mem6_2
```
