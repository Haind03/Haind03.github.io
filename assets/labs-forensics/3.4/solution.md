# Dap an Lab 3.4

## Nhiem vu 1: steghide (JPG va WAV)

```
steghide extract -sf stego.jpg -p haind -xf out_jpg.txt   # FLAG{steghide_jpg_works}
steghide extract -sf stego.wav -p haind -xf out_wav.txt   # FLAG{steghide_wav_works}
```
steghide giau trong he so DCT (JPG) hoac mau (WAV), co mat khau. Khong co mat khau thi khong trich duoc,
nhung su ton tai co the doan qua kich thuoc/entropy hoac thu stegdetect.

## Nhiem vu 2: append ZIP sau PNG

`binwalk appended.png` (xem `transcript.txt` B3): PNG o offset 0, Zip archive o 0x10E, End of Zip o 0x1C0.
`unzip appended.png` lay ra `s.txt` = `co mat khau trong day: FLAG{append_zip}`.
Anh van mo binh thuong vi trinh xem anh doc toi chunk `IEND` roi dung, bo qua moi byte phia sau; ZIP nam sau IEND nen
khong anh huong hien thi, nhung van la du lieu trong file.

## Nhiem vu 3: exiftool

`exiftool meta.jpg` doc Artist = `HaiND`, Comment = `hidden-note FLAG{exif_meta}`. Metadata EXIF/IPTC/XMP la cho giau
thong tin re tien ma rat hay bi bo qua; luon chay exiftool som.

## Nhiem vu 4: LSB tren PNG

`python3 lsb.py extract lsb_stego.png` -> `FLAG{lsb_png_works}`. So voi `lsb_cover.png`: chi 81/40000 pixel doi,
muc doi lon nhat moi kenh la 1 (dung bang LSB). Mat thuong khong thay khac biet -> can tool (zsteg, stegsolve) hoac so pixel.

## Nhiem vu 5-6 (bai tap)

- ADS (NTFS): `echo bem > a.txt:hid` tao stream an; `dir /r`, `Get-Item -Stream *` liet ke; `Get-Content a.txt:Zone.Identifier`
  cho URL nguon tai ve. ADS chi co tren NTFS, copy sang FAT/USB FAT la mat.
- Slack: `blkls -s image > slack.raw` roi `strings slack.raw` tim manh file cu con sot (xem bai 1.2, 3.3).

## Ghi nho
- Append steg lo qua binwalk; metadata lo qua exiftool; LSB can tool chuyen.
- Thu tu CTF: file, exiftool, strings, binwalk, roi moi LSB. Dung bo qua buoc don gian.
