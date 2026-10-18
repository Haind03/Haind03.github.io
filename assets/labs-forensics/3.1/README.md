# Lab 3.1: Sleuth Kit va Autopsy - timeline va trich file

Lab chay that tren Linux (khong can root): dung ext4 case image co 1 file giu lai + 1 file da xoa,
gan timestamp co that, roi dieu tra bang bo Sleuth Kit.

## Cong cu
`mkfs.ext4`, `debugfs` (gan timestamp), `mmls`, `fsstat`, `fls`, `icat`, `mactime` (Sleuth Kit). Autopsy la GUI tren bo nay.

## Chay lab
```bash
bash make.sh     # tao case.ext4: keep.txt (tao 2024-09-10), tobedeleted.txt (tao 09-14, sua 09-15, roi xoa)
bash solve.sh    # mmls/fsstat, fls -rd, icat khoi phuc, bodyfile + mactime timeline
```
`transcript.txt` la output THAT. `body.txt` la bodyfile sinh ra. Image `case.ext4` (8MB) khong giu, chay `make.sh` tao lai.

## Nhiem vu (co lab chay that)
1. `mmls` va `fsstat`: xac dinh loai FS va offset. Image nay la mot phan vung don nen `mmls` bao khong co partition table (exit 1), dung offset 0.
2. `fls -rd` liet ke file da xoa, tim inode cua `tobedeleted.txt`.
3. `icat` khoi phuc noi dung file da xoa. Con nguyen khong?
4. `fls -r -m` sinh bodyfile, `mactime` dung timeline. Chi ra thoi diem tao va sua file. Luu y mui gio: `debugfs` gan gio UTC,
   `mactime -z UTC` hien dung gio da gan (bo `-z` se ra gio local, de lech, do la cam bay TZ).

## Nhiem vu la bai tap (can GUI)
5. Lam lai toan bo trong Autopsy: add image, vao muc Deleted Files, extract, so voi ket qua `icat`. Autopsy chay tren chinh
   SleuthKit nay nen ket qua tuong duong, chi truc quan hon.

## Dap an
Xem `solution.md`. Output that: `transcript.txt`.
