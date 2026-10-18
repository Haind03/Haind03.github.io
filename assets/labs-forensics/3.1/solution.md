# Dap an Lab 3.1

## Nhiem vu 1-2: xac dinh FS, tim file da xoa

- `mmls case.ext4` khong in gi va exit 1: image la mot phan vung don, khong co MBR/GPT. Khi do dung offset 0 (bo `-o`).
- `fsstat` cho File System Type: Ext4, Volume Name CASE01.
- `fls -rd` liet ke: `r/r * 13: tobedeleted.txt` (dau `*` = deleted). inode = 13.

## Nhiem vu 3: khoi phuc

`icat case.ext4 13` ra nguyen van: `ke hoach ro ri du lieu qua email - xoa gap`. File da xoa van doc duoc vi data block
chua bi ghi de (xem bai 1.2, 1.6).

## Nhiem vu 4: timeline

`fls -r -m / case.ext4 > body.txt` roi `mactime -z UTC -b body.txt` cho timeline (xem `transcript.txt` B5):
- 2024-09-10 08:00:00  keep.txt: `macb` (tao, sua, truy cap cung luc).
- 2024-09-14 02:30:00  tobedeleted.txt: `...b` (born = create time).
- 2024-09-15 07:30:00  tobedeleted.txt: `mac.` (modified/accessed/changed) va danh dau `(deleted)`.

Doc duoc cau chuyen: file ke hoach ro ri tao ngay 14, sua ngay 15, roi bi xoa.

Cam bay mui gio: `debugfs set_inode_field` nhan gio UTC. Neu chay `mactime` khong co `-z UTC`, no hien theo gio local (+07)
va cac moc bi day len 7 tieng -> de ket luan sai thoi diem. Luon thong nhat mui gio khi bao cao.

## Nhiem vu 5 (Autopsy, bai tap GUI)

Add image vao Autopsy -> View -> Deleted Files, chon `tobedeleted.txt`, Extract File. Noi dung trung voi `icat`.
Timeline trong Autopsy (Tools -> Timeline) dung tren cung bodyfile, ket qua tuong duong CLI.

## Ghi nho
- `fls` tim inode, `icat` moi du lieu; `fls -m` + `mactime` dung timeline.
- Image FS don -> offset 0; image o dia day du -> dung `mmls` lay offset roi `-o`.
- Luon ghi ro mui gio trong bao cao.
