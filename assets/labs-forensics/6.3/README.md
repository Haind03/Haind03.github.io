# Lab 6.3: Phat hien vung nho RWX bat thuong (malfind o quy mo tien trinh)

Lab chay that cho Bai 6.3. Mot tien trinh cap mot vung bo nho anonymous RWX (vua ghi
vua chay) va dat vao do "shellcode gia". Ta quet `/proc/<pid>/maps` tim dung vung RWX
do, carve no ra, va thay header MZ + marker, dung cach `windows.malfind` phat hien
injected code. Chay that tren Linux, khong can root, khong tai gi.

## An toan

"Shellcode" o day chi la bytes vo hai: `4d 5a` (MZ gia) + vai NOP + chuoi
`FAKE_SHELLCODE_NOT_EXECUTED_LAB63` + padding. Chuong trinh KHONG BAO GIO nhay vao vung
do, khong thuc thi gi. Day thuan tuy la minh hoa dau hieu, khong phai malware.

## Vi sao vung RWX la co do

Bo nho tien trinh lanh chia vung ro: code thi RX, du lieu thi RW. Vung vua Write vua
Execute (RWX) + private + khong backing file la dau hieu kinh dien cua code injection:
ke tan cong can cho vung de vua ghi payload vua chay no. Them header MZ o dau thi gan
nhu chac la PE map tay.

## Chay

```bash
DUMPDIR=_dump python3 -I capture.py   # tao vung RWX, carve no ra file
DUMPDIR=_dump bash solve.sh           # quet maps + soi header/marker
```

## Ket qua (xem transcript.txt)

1. `maps` co dong `... rwxp 00000000 00:00 0` (RWX, private, inode 0 = anonymous,
   khong backing file) - dung dang malfind san tim.
2. Carve vung do ra, 16 byte dau la `4d 5a 90 90 ...` = "MZ" + NOP, theo sau la marker
   `FAKE_SHELLCODE_NOT_EXECUTED_LAB63`.
3. Ket luan tu dong: vung RWX bat dau bang MZ -> giong PE map tay / injected code.

Dia chi vung doi moi lan chay vi ASLR; dieu quan trong la thuoc tinh (rwxp, anon) va
noi dung (MZ + pattern), khong phai dia chi cu the.

## False positive can nho

JIT cua trinh duyet va .NET sinh vung RWX HOP LE. Dung voi ket toi ngay; phai nhin noi
dung: co MZ/shellcode that khong, hay chi la code JIT binh thuong. Day la ly do
`malfind` in ca hexdump de nguoi phan tich tu danh gia.

## Lenh Volatility 3 tuong ung (anh RAM Windows that cua ban)

Khong tai anh mau co malware. Khi co anh hop phap:

```bash
# Quet toan dump tim vung RWX nghi, dump ca vung ra thu muc
vol -o out_malfind -f mem.raw windows.malfind --dump

# Khoanh vao mot process
vol -f mem.raw windows.malfind --pid <PID>

# Doi chieu VAD (private, RWX, khong FileObject) va DLL bi unlink
vol -f mem.raw windows.vadinfo --pid <PID>
vol -f mem.raw windows.ldrmodules --pid <PID>

# Nghi rootkit kernel: con tro SSDT tro ra ngoai ntoskrnl/win32k
vol -f mem.raw windows.ssdt | grep -viE "ntoskrnl|win32k"
```

## Files

- `victim.py`: tao vung anonymous RWX + dat "shellcode" gia (vo hai), giu roi cho.
- `capture.py`: quet maps, carve vung RWX ra file nho.
- `solve.sh`: phat hien vung RWX, soi header MZ + marker, ket luan.
- `transcript.txt`: output that.

## Don dep

```bash
rm -rf _dump /tmp/mem6_3
```
