# Lab 2.2 - Tao image dia va verify toan ven

Lab chay that, 100% local, khong can root, khong can mount, khong can mang.

## Muc tieu
- Acquisition mot "thiet bi" ra image bang `dd`.
- Chung minh hash nguon KHOP hash image (ban sao bit-by-bit).
- Nhin thay artifact file da xoa va khoi phuc noi dung.
- Hieu vi sao sua dung 1 byte lam ca MD5 lan SHA-256 doi hoan toan.

## Cong cu
`dd`, `md5sum`, `sha256sum`, `mkfs.ext4`, `debugfs`, `fls`, `icat` (The Sleuth Kit).
Tat ca thao tac truc tiep tren file anh, khong mount filesystem nen khong doi quyen root.

## Vi sao khong dung E01/ewfacquire o lab nay
`ewfacquire`/`ewfverify` khong co san trong moi truong nay. Bai da mo ta dinh dang E01
o muc 2. O lab chay that nay ta dung `dd` (raw) de minh hoa nguyen tac cot loi:
acquisition + verify hash. Nguyen tac "hash nguon == hash image" va "doi 1 byte thi
verify fail" la giong het nhau du dinh dang raw hay E01.

## Chay
```
./make.sh      # tao device.img (thiet bi nguon, ext4 1MB)
./solve.sh     # dd ra evidence.img, verify hash, liet ke + khoi phuc file xoa, tamper test
```

## File trong lab
- `make.sh` - tao thiet bi nguon `device.img` (co file thuong, file an `.notes.hidden`, mot file da xoa).
- `device.img` - artifact (1 MB, < 2 MB). Co the tao lai bat ky luc nao bang `make.sh`.
- `solve.sh` - acquisition + verify + khoi phuc + tamper test.
- `transcript.txt` - output THAT da chay tren may.

## Luu y ve hash trong transcript
`mkfs.ext4` nhung UUID va vai metadata, nen gia tri hash cu the co the khac giua cac may.
Dieu LUON dung va la trong tam cua lab: trong cung mot lan chay, `hash(device.img)` phai
bang `hash(evidence.img)`; va sau khi sua 1 byte thi hash doi hoan toan. Lab co dinh UUID
de ket qua on dinh nhat co the.

## Nhiem vu tu lam them
1. Doi `bs=512` sang `bs=1M` trong `solve.sh`, xac nhan hash khong doi (block size khong
   anh huong noi dung, chi anh huong toc do).
2. Dung `fls -r` tim inode cua `.notes.hidden` roi `icat` doc noi dung file an.
3. Chay `dd` chi lay nua dau image (`count=...`) roi hash, giai thich vi sao khong khop.
4. Lam bodyfile `fls -r -m / evidence.img` va so timestamp cua `secret.txt` (bai 9.1 dung lai ky thuat nay).
