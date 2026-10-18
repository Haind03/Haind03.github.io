# Lab 6.1: Process memory forensics co ban (dump tien trinh + tim secret)

Lab chay that cho Bai 6.1. Thay vi can mot anh RAM Windows nang, lab nay minh hoa
dung ban chat cua memory forensics o quy mo mot tien trinh: mot chuong trinh giu
secret trong RAM, ta chup (dump) bo nho no, roi dung `strings` + `grep` tim lai secret.
Tat ca deu chay that tren Linux, khong can root, khong can tai gi.

## Y tuong

Memory forensics = doc lai nhung gi mot tien trinh (hoac ca he thong) dang giu trong
RAM. `windows.pslist` cua Volatility liet ke tien trinh; buoc sau la soi noi dung bo
nho tung tien trinh. Lab nay lam dung buoc "soi noi dung" do o dang nho nhat va tai
lap duoc: dump RAM cua mot tien trinh roi moi secret ra.

## Chay

```bash
# 1. Chup bo nho tien trinh holder.py ra file dump (thu muc tam, khong commit)
DUMPDIR=_dump python3 -I capture.py

# 2. Dieu tra dump: tim lai secret
DUMPDIR=_dump bash solve.sh
```

Khong dat `DUMPDIR` thi mac dinh dump ra `/tmp/mem6_1`. Dump co the vai MB, la file
tam, KHONG dua vao labs/.

## Ket qua (xem transcript.txt)

- `capture.py` phong `holder.py` nhu tien trinh con, doc `/proc/<pid>/maps`, seek +
  read `/proc/<pid>/mem` cac vung writable/anon/heap/stack, ghi ra `holder.dump`.
- `solve.sh` chay `strings -a | grep` tren dump, trich ra `SECRET{proc_memory_forensics_lab_6_1}`.
  holder giu 64 ban nen marker xuat hien nhieu lan trong dump.

## Vi sao khong dung gcore o day

`gcore` goi `gdb` -> `ptrace(ATTACH)`. Voi `kernel.yama.ptrace_scope=1` (mac dinh
Ubuntu/WSL2), mot tien trinh chi ptrace duoc con chau cua no; `gcore` chay nhu tien
trinh rieng le nen bi tu choi (`ptrace: Operation not permitted`). Doc
`/proc/<pid>/mem` tu CHINH tien trinh cha (`capture.py` la cha cua `holder.py`) thi
duoc phep, nen lab dung cach nay cho on dinh va khong can quyen root.

Neu ban chay voi quyen root, hoac dat `sudo sysctl kernel.yama.ptrace_scope=0`, thi
`gcore` chup duoc tuong tu:

```bash
python3 holder.py &        # lay PID no in ra
sudo gcore -o core <pid>   # tao core.<pid>
strings -a core.<pid> | grep -ao 'SECRET{[^}]*}'
```

## Phan Volatility 3 (anh RAM Windows)

Volatility 3 (`vol`) da cai san trong moi truong. Nhung phan tich mot anh RAM Windows
can anh (`.raw`/`.mem`) cong symbol table (ISF), va nhieu anh mau cong khai (cridex,
zeus, dump CTF...) co chua MALWARE THAT, nen lab nay KHONG tai ve. Duoi day la cac
lenh CHINH XAC de chay khi ban co san mot anh RAM hop phap (tu thu tu VM cua ban, hoac
anh training lanh tinh):

```bash
# Luon xac minh dump truoc: build Windows, SystemTime lam moc thoi gian
vol -f /duong-dan/mem.raw windows.info

# Liet ke tien trinh (nhu tasklist tu danh sach kernel)
vol -f /duong-dan/mem.raw windows.pslist

# Xuat CSV de loc
vol -r csv -f /duong-dan/mem.raw windows.pslist > pslist.csv

# Dump Linux (can tu build ISF truoc; banner cho biet nhan nao)
vol -f /duong-dan/linux.lime banner.Banners
vol -f /duong-dan/linux.lime linux.pslist
```

Lan dau chay `windows.info`/`windows.pslist`, Vol3 se tu tai symbol table khop kernel
cua anh (can mang outbound). Neu bao thieu symbol: kiem mang, va kiem anh khong bi cat
cut (kich thuoc xap xi RAM that).

## Files

- `holder.py`: chuong trinh "nan nhan", giu secret + marker trong RAM roi cho.
- `capture.py`: dumper, chup bo nho tien trinh con qua `/proc/<pid>/mem`.
- `solve.sh`: trich secret bang `strings` + `grep`.
- `transcript.txt`: output that.

## Don dep

```bash
rm -rf _dump /tmp/mem6_1
```
